#!/usr/bin/env python3
"""
sensor_fusion_node.py

Robust sensor-fusion node that fuses OAK-D (RGB + depth) + 2D LIDAR to produce a
clean obstacle PointCloud2 suitable as a Nav2 observation source (costmap).
This node implements:
 - HSV-based color masking (tunable)
 - Depth-based height estimation (top/bottom patch)
 - LIDAR cross-check (azimuth match)
 - Simple voting rule (requires at least 2 votes to consider an obstacle)
 - Temporal smoothing / tracking (requires repeated detections to publish)
 - Publishes PointCloud2 in a configurable frame (default: camera_link)

Topics:
 - Subscribes:
    /camera/color/image_raw (sensor_msgs/Image)
    /camera/depth/image_rect (sensor_msgs/Image)   (32FC1 or 16UC1)
    /scan_filtered (sensor_msgs/LaserScan)         (optional)
 - Publishes:
    /perception/obstacles_pointcloud (sensor_msgs/PointCloud2)

Tuning parameters (edit or expose as ROS params if desired):
 - HSV thresholds for yellow paint
 - min_contour_area: ignore tiny blobs
 - min_obstacle_height: minimum vertical thickness to consider a raised object
 - min_votes: how many of {height, lidar, shape} are required
 - min_hits: number of frames a track must be seen before it's published
 - match_radius: meters for associating new detections to existing tracks
 - stale_time: seconds after which an unseen track is removed
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, LaserScan, PointCloud2, PointField
from std_msgs.msg import Header
from cv_bridge import CvBridge
import numpy as np
import cv2
import struct
import time
import math


def create_cloud_xyz32(header: Header, points):
    """
    Create a PointCloud2 message with dtype float32 XYZ from a list of (x,y,z).
    """
    cloud = PointCloud2()
    cloud.header = header
    cloud.height = 1
    cloud.width = len(points)
    cloud.is_bigendian = False
    cloud.is_dense = True if len(points) > 0 else False

    # three float32 fields: x, y, z
    cloud.fields = [
        PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
        PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
        PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
    ]
    cloud.point_step = 12  # 3 * 4 bytes
    cloud.row_step = cloud.point_step * cloud.width

    buffer = []
    for p in points:
        buffer.append(struct.pack('fff', float(p[0]), float(p[1]), float(p[2])))

    cloud.data = b''.join(buffer)
    return cloud


class SensorFusion(Node):
    def __init__(self):
        super().__init__('sensor_fusion')

        # -------------------------
        # Tunable parameters
        # -------------------------
        # HSV for yellow (competition lighting will need tuning)
        self.hsv_lower = np.array([18, 90, 90])
        self.hsv_upper = np.array([35, 255, 255])

        self.min_contour_area = 150            # px, ignore small specks
        self.min_obstacle_height = 0.05        # meters (5 cm)
        self.min_votes = 2                     # need >= 2 votes to consider obstacle
        self.min_hits = 2                      # number of frames a track must be seen before published
        self.match_radius = 0.25               # meters to associate detections to tracks
        self.stale_time = 1.0                  # seconds to remove tracks not seen recently
        self.max_obstacle_dist = 4.0           # ignore very distant detections
        self.lidar_tolerance = 0.30            # meters tolerance when matching lidar range to depth

        # Camera intrinsics (REPLACE with your calibrated values)
        self.fx = 400.0
        self.fy = 400.0
        self.cx = 320.0
        self.cy = 240.0

        # Frames
        self.camera_frame = 'camera_link'      # frame of the input camera images / depth
        self.publish_frame = 'camera_link'     # frame in which PointCloud2 will be published

        # -------------------------
        # State
        # -------------------------
        self.bridge = CvBridge()
        self.depth = None           # latest depth image as float32 meters
        self.depth_header = None
        self.scan = None            # latest LaserScan
        # tracks: list of dicts with keys: pos (x,y,z), hits, last_seen (float timestamp)
        self.tracks = []

        # ROS subscriptions / publishers
        self.create_subscription(Image, '/camera/color/image_raw', self.color_cb, 5)
        self.create_subscription(Image, '/camera/depth/image_rect', self.depth_cb, 5)
        # accept either /scan_filtered or /scan if user doesn't filter
        try:
            self.create_subscription(LaserScan, '/scan_filtered', self.scan_cb, 10)
        except Exception:
            self.create_subscription(LaserScan, '/scan', self.scan_cb, 10)

        self.pub_cloud = self.create_publisher(PointCloud2, '/perception/obstacles_pointcloud', 5)

        # Timer to clean stale tracks and publish cloud at modest rate
        self.publish_rate = 8.0  # Hz
        self.create_timer(1.0 / self.publish_rate, self.timer_cb)

        self.get_logger().info('sensor_fusion node started.')

    # -------------------------
    # Callbacks
    # -------------------------
    def depth_cb(self, msg: Image):
        """
        Store latest depth image as float32 meters.
        Supports 32FC1 and 16UC1.
        """
        try:
            d = self.bridge.imgmsg_to_cv2(msg, desired_encoding='32FC1')
            self.depth = d
            self.depth_header = msg.header
        except Exception:
            try:
                d = self.bridge.imgmsg_to_cv2(msg, desired_encoding='16UC1').astype(np.float32) / 1000.0
                self.depth = d
                self.depth_header = msg.header
            except Exception as e:
                self.get_logger().warn('Depth image conversion failed: ' + str(e))
                self.depth = None
                self.depth_header = None

    def scan_cb(self, msg: LaserScan):
        self.scan = msg

    def color_cb(self, msg: Image):
        """
        Process color frame and (if available) depth to extract candidate obstacles.
        Update temporal tracks with candidates.
        """
        if self.depth is None:
            # depth required for reliable classification
            return

        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().warn('Color image conversion failed: ' + str(e))
            return

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.hsv_lower, self.hsv_upper)

        # small morphological cleanup
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        now = self.get_clock().now().nanoseconds * 1e-9

        candidates = []  # list of (cam_x_forward, cam_y_lateral, cam_z_up) using convention x=forward

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < self.min_contour_area:
                continue

            x, y, w, h = cv2.boundingRect(cnt)
            # extract depth patch
            h_img, w_img = self.depth.shape
            xs = max(0, x)
            ys = max(0, y)
            xe = min(w_img, x + w)
            ye = min(h_img, y + h)
            patch = self.depth[ys:ye, xs:xe]
            valid = patch[np.isfinite(patch) & (patch > 0.0)]
            if valid.size == 0:
                # missing depth -> likely paint or saturation; treat as non-obstacle
                continue

            depth_m = float(np.median(valid))
            if depth_m <= 0.0 or depth_m > self.max_obstacle_dist:
                continue

            # estimate vertical height: difference between bottom and top medians of the patch
            top_region = patch[0:max(1, int(h * 0.2)), :]
            bottom_region = patch[max(0, int(h * 0.7)):patch.shape[0], :]

            top_valid = top_region[np.isfinite(top_region) & (top_region > 0)]
            bottom_valid = bottom_region[np.isfinite(bottom_region) & (bottom_region > 0)]

            if top_valid.size == 0 or bottom_valid.size == 0:
                height_est = 0.0
            else:
                height_est = abs(float(np.median(bottom_valid)) - float(np.median(top_valid)))

            # pixel centroid
            cx = x + w // 2
            cy = y + h // 2

            # convert to camera coords (X lateral, Y vertical) using pinhole model
            Z = depth_m                        # forward distance
            X = (cx - self.cx) * Z / self.fx   # left/right
            Y = (cy - self.cy) * Z / self.fy   # up/down from image

            # Voting checks
            votes = 0
            if height_est >= self.min_obstacle_height:
                votes += 1

            # shape test: fairly square blob -> likely 3D object (not a long line)
            aspect = float(h) / max(1.0, float(w))
            if aspect > 0.6:
                votes += 1

            # lidar cross-check (if available)
            lidar_vote = False
            if self.scan is not None:
                angle = math.atan2(X, Z)  # azimuth relative to camera forward
                # map angle to scan index
                try:
                    idx = int(round((angle - self.scan.angle_min) / self.scan.angle_increment))
                except Exception:
                    idx = None
                if idx is not None and 0 <= idx < len(self.scan.ranges):
                    r = self.scan.ranges[idx]
                    if r > 0.0 and r < (Z + self.lidar_tolerance) and r > (Z - self.lidar_tolerance):
                        lidar_vote = True
                        votes += 1

            # require at least min_votes to be a candidate
            if votes >= self.min_votes:
                # convert to camera-frame XYZ convention used elsewhere: x=forward, y=left, z=up
                # Note: earlier nodes used center_msg.point.x = z, .y = X, .z = -Y
                # Here we use x=Z, y=X, z=-Y for compatibility with RViz/other nodes expecting that mapping.
                cam_x = Z
                cam_y = X
                cam_z = -Y
                candidates.append((cam_x, cam_y, cam_z))

        # Update temporal tracks with candidates
        self._update_tracks(candidates, now)

    # -------------------------
    # Tracking + publish logic
    # -------------------------
    def _update_tracks(self, candidates, now_ts):
        """
        candidates: list of (x,y,z) in camera frame (x forward, y left, z up)
        now_ts: float seconds timestamp
        """
        # mark all tracks as unseen initially
        for t in self.tracks:
            t['seen_this_frame'] = False

        # associate each candidate to existing track or create a new one
        for c in candidates:
            matched = False
            for t in self.tracks:
                dx = c[0] - t['pos'][0]
                dy = c[1] - t['pos'][1]
                dz = c[2] - t['pos'][2]
                dist = math.sqrt(dx * dx + dy * dy + dz * dz)
                if dist <= self.match_radius:
                    # update running average position
                    alpha = 0.6
                    t['pos'] = (alpha * np.array(c) + (1 - alpha) * np.array(t['pos'])).tolist()
                    t['hits'] += 1
                    t['last_seen'] = now_ts
                    t['seen_this_frame'] = True
                    matched = True
                    break
            if not matched:
                # new track
                self.tracks.append({
                    'pos': [float(c[0]), float(c[1]), float(c[2])],
                    'hits': 1,
                    'first_seen': now_ts,
                    'last_seen': now_ts,
                    'seen_this_frame': True
                })

        # prune stale tracks (not seen for stale_time) OR reduce hits for those fading
        new_tracks = []
        for t in self.tracks:
            age = now_ts - t['last_seen']
            if age > self.stale_time:
                # drop track
                continue
            # keep track
            new_tracks.append(t)
        self.tracks = new_tracks

    def timer_cb(self):
        """
        Called periodically to publish the pointcloud consisting of tracks
        that have sufficient hits (persistence). Also does periodic pruning.
        """
        now = self.get_clock().now().nanoseconds * 1e-9

        # prune stale tracks
        self.tracks = [t for t in self.tracks if (now - t['last_seen']) <= self.stale_time]

        # prepare points to publish: only tracks with hits >= min_hits
        points = []
        for t in self.tracks:
            if t['hits'] >= self.min_hits:
                # ensure points are within max distance
                x, y, z = t['pos']
                if x > 0 and x <= self.max_obstacle_dist:
                    points.append((x, y, z))

        header = Header()
        header.stamp = self.get_clock().now().to_msg()
        header.frame_id = self.publish_frame

        cloud = create_cloud_xyz32(header, points)
        self.pub_cloud.publish(cloud)

        # Optionally decay hits slowly so stale tracks eventually require re-detection
        for t in self.tracks:
            # small decay to avoid tracks staying forever if rarely seen
            if (now - t['last_seen']) > 0.2:
                t['hits'] = max(0, t['hits'] - 0.5)

        # minimal logging for debug (comment out if noisy)
        # self.get_logger().debug(f"Published {len(points)} fused obstacle points; tracks: {len(self.tracks)}")


def main(args=None):
    rclpy.init(args=args)
    node = SensorFusion()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()