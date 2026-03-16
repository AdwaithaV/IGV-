#!/usr/bin/env python3
"""
lane_nav_node.py

Detect lane points (yellow or black paint) using color + depth, classify by height,
and send lane points (only) as NavigateToPose goals to Nav2.

Usage:
 - Put this file in a ROS2 Python package (scripts/), make executable.
 - Adjust topic names / frame names / intrinsics source as needed.

Notes:
 - Requires: rclpy, cv2, numpy, cv_bridge, tf2_ros, nav2_msgs
 - This node DOES NOT send obstacle waypoints; it only sends lane (low-height) points.
"""

import rclpy
from rclpy.node import Node
from rclpy.duration import Duration
from rclpy.action import ActionClient

from sensor_msgs.msg import Image as SensorImage
from sensor_msgs.msg import CameraInfo
from geometry_msgs.msg import PointStamped, PoseStamped
from nav2_msgs.action import NavigateToPose

import tf2_ros
import cv2
from cv_bridge import CvBridge
import numpy as np
import math
import time


class LaneNavNode(Node):
    def __init__(self):
        super().__init__('lane_nav_node')

        # --- Parameters (tune these) ---
        self.declare_parameter('color_image_topic', '/camera/color/image_raw')
        self.declare_parameter('depth_image_topic', '/camera/depth/image_raw')
        self.declare_parameter('camera_info_topic', '/camera/color/camera_info')
        self.declare_parameter('camera_frame', 'camera_color_frame')   # adjust to your camera frame
        self.declare_parameter('map_frame', 'map')                    # frame to send Nav2 goals in
        self.declare_parameter('height_threshold', 0.05)              # meters: > this => obstacle
        self.declare_parameter('min_depth', 0.2)                      # ignore nearer than this (m)
        self.declare_parameter('max_depth', 5.0)                      # ignore farther than this (m)
        self.declare_parameter('send_distance_thresh', 0.5)          # min distance between goals (m)
        self.declare_parameter('show_debug_windows', True)           # show cv windows for debugging

        # fetch params
        color_topic = self.get_parameter('color_image_topic').get_parameter_value().string_value
        depth_topic = self.get_parameter('depth_image_topic').get_parameter_value().string_value
        camera_info_topic = self.get_parameter('camera_info_topic').get_parameter_value().string_value
        self.camera_frame = self.get_parameter('camera_frame').get_parameter_value().string_value
        self.map_frame = self.get_parameter('map_frame').get_parameter_value().string_value
        self.HEIGHT_THRESHOLD = float(self.get_parameter('height_threshold').get_parameter_value().double_value)
        self.MIN_DEPTH = float(self.get_parameter('min_depth').get_parameter_value().double_value)
        self.MAX_DEPTH = float(self.get_parameter('max_depth').get_parameter_value().double_value)
        self.SEND_DISTANCE_THRESH = float(self.get_parameter('send_distance_thresh').get_parameter_value().double_value)
        self.SHOW_DEBUG = bool(self.get_parameter('show_debug_windows').get_parameter_value().bool_value)

        # CvBridge
        self.bridge = CvBridge()

        # subs: color, depth, camera_info
        self.color_sub = self.create_subscription(SensorImage, color_topic, self.color_cb, 10)
        self.depth_sub = self.create_subscription(SensorImage, depth_topic, self.depth_cb, 10)
        self.caminfo_sub = self.create_subscription(CameraInfo, camera_info_topic, self.caminfo_cb, 10)

        self.latest_color = None
        self.latest_depth = None
        self.latest_caminfo = None
        self.intrinsics = None  # dict with fx,fy,cx,cy after camera_info arrives

        # TF
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        # Action client to Nav2 NavigateToPose
        self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.get_logger().info('Waiting for Nav2 action server...')

        # last sent goal position (to avoid spamming small changes)
        self.last_sent_goal_xy = None

        # small kernel for morphology
        self.morph_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

        self.get_logger().info('lane_nav_node started')

    # -------------------- Callbacks --------------------
    def caminfo_cb(self, msg: CameraInfo):
        # store intrinsics once
        if self.intrinsics is None:
            fx = msg.k[0]
            fy = msg.k[4]
            cx = msg.k[2]
            cy = msg.k[5]
            self.intrinsics = {'fx': float(fx), 'fy': float(fy), 'cx': float(cx), 'cy': float(cy)}
            self.get_logger().info(f'Camera intrinsics received: fx={fx:.1f}, fy={fy:.1f}, cx={cx:.1f}, cy={cy:.1f}')

        self.latest_caminfo = msg

    def depth_cb(self, msg: SensorImage):
        # store latest depth message
        self.latest_depth = msg

    def color_cb(self, msg: SensorImage):
        # main processing happens here
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f'cv_bridge color convert failed: {e}')
            return

        self.latest_color = frame.copy()

        # Build mask for lane detection: yellow OR black
        mask_yellow = self._mask_yellow(frame)
        mask_black = self._mask_black(frame)
        mask = cv2.bitwise_or(mask_yellow, mask_black)

        # clean mask
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, self.morph_kernel, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.morph_kernel, iterations=1)

        # If no lane pixels, nothing to do
        if cv2.countNonZero(mask) == 0:
            if self.SHOW_DEBUG:
                cv2.imshow('frame', frame)
                cv2.imshow('mask', mask)
                cv2.waitKey(1)
            return

        # Compute bottom pixel of the lane blob (a good target for a vehicle)
        bot_pixel = self._bottom_pixel_from_mask(mask)
        if bot_pixel is None:
            return
        u_bot, v_bot = bot_pixel

        # Get median depth around bottom pixel
        Z_bot = self._depth_patch_median(self.latest_depth, u_bot, v_bot, k=7)
        if not np.isfinite(Z_bot) or Z_bot <= 0.0:
            # try a slightly larger neighborhood
            Z_bot = self._depth_patch_median(self.latest_depth, u_bot, v_bot, k=15)
        if (not np.isfinite(Z_bot)) or (Z_bot < self.MIN_DEPTH) or (Z_bot > self.MAX_DEPTH):
            self.get_logger().debug('depth invalid or out of range; skipping this detection')
            if self.SHOW_DEBUG:
                debug_frame = frame.copy()
                cv2.circle(debug_frame, (u_bot, v_bot), 6, (0, 0, 255), -1)
                cv2.imshow('frame', debug_frame)
                cv2.imshow('mask', mask)
                cv2.waitKey(1)
            return

        # Unproject to camera coordinates
        if self.intrinsics is None:
            self.get_logger().warning('No camera intrinsics yet; cannot unproject')
            return
        P_cam = self._pixel_to_cam(u_bot, v_bot, Z_bot, self.intrinsics)  # [X, Y, Z] in camera frame

        # Transform to map frame (or base_link) where Z is vertical; we will request map frame
        P_map = self._transform_point(P_cam, src_frame=self.camera_frame, tgt_frame=self.map_frame)
        if P_map is None:
            self.get_logger().warning('TF transform to map failed; cannot send goal')
            return

        # To decide lane vs obstacle we need height. We'll get top pixel too and compute its world Z,
        # but for lanes generally paint is flat so the height between top and bottom in map frame will be tiny.
        # For speed we'll compute a simple estimate: check a point slightly above bottom (v_bot - N rows).
        # More robust approach is to compute top pixel; here we compute top using percentile method.
        top_pixel = self._top_pixel_from_mask_percentile(mask, top_pct=2)
        if top_pixel is None:
            self.get_logger().warning('Could not compute top pixel reliably; skipping')
            return
        u_top, v_top = top_pixel
        Z_top = self._depth_patch_median(self.latest_depth, u_top, v_top, k=7)
        if not np.isfinite(Z_top):
            Z_top = self._depth_patch_median(self.latest_depth, u_top, v_top, k=15)
        if not np.isfinite(Z_top):
            # fallback: assume very small height (treat as lane) if top depth invalid but bottom valid
            height = 0.0
        else:
            P_top_cam = self._pixel_to_cam(u_top, v_top, Z_top, self.intrinsics)
            P_top_map = self._transform_point(P_top_cam, src_frame=self.camera_frame, tgt_frame=self.map_frame)
            if P_top_map is None:
                self.get_logger().warning('TF transform for top point failed; skipping')
                return
            # height along map Z
            height = abs(P_top_map[2] - P_map[2])

        # Classification
        if height >= self.HEIGHT_THRESHOLD:
            # obstacle — we do NOT send obstacle waypoints (user requested)
            self.get_logger().info(f'Classified OBSTACLE (height={height:.3f} m). Not sending to Nav2.')
        else:
            # lane paint / flat -> send to Nav2
            self.get_logger().info(f'Classified LANE (height={height:.3f} m). Sending lane point to Nav2.')
            # only send new goal if it's far enough from previous goal
            if self._should_send_goal(P_map):
                self._send_nav2_goal(P_map)
            else:
                self.get_logger().debug('Lane goal too close to previous; skipping send.')

        # debug visuals
        if self.SHOW_DEBUG:
            debug = frame.copy()
            cv2.circle(debug, (u_bot, v_bot), 6, (0, 255, 0), -1)
            cv2.circle(debug, (u_top, v_top), 4, (255, 0, 0), -1)
            cv2.putText(debug, f'h={height:.3f}m', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)
            cv2.imshow('frame', debug)
            cv2.imshow('mask', mask)
            cv2.waitKey(1)

    # --------------- Utilities -------------------
    def _mask_yellow(self, frame_bgr):
        hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        # tuned yellow range: you may want to change depending on lighting
        lower_y = np.array([15, 100, 100], dtype=np.uint8)
        upper_y = np.array([35, 255, 255], dtype=np.uint8)
        return cv2.inRange(hsv, lower_y, upper_y)

    def _mask_black(self, frame_bgr):
        # black paint tends to have low V; allow low saturation so dark gray counts
        hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        lower_b = np.array([0, 0, 0], dtype=np.uint8)
        upper_b = np.array([180, 255, 60], dtype=np.uint8)  # V <= 60
        return cv2.inRange(hsv, lower_b, upper_b)

    def _bottom_pixel_from_mask(self, mask):
        # find the largest connected component (assume lane is dominant)
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
        if num_labels <= 1:
            return None
        areas = stats[1:, cv2.CC_STAT_AREA]
        largest_label = 1 + int(np.argmax(areas))
        comp_mask = (labels == largest_label).astype('uint8') * 255
        ys, xs = np.where(comp_mask > 0)
        if ys.size == 0:
            return None
        # bottom row index
        v_bot = int(np.max(ys))
        # choose median x among pixels at that row (or nearby if none)
        cols = xs[ys == v_bot]
        if cols.size == 0:
            # search up to 5 rows
            for dr in range(1, 6):
                cols = xs[ys == (v_bot - dr)]
                if cols.size:
                    v_bot = v_bot - dr
                    break
        if cols.size == 0:
            return None
        u_bot = int(np.median(cols))
        return (u_bot, v_bot)

    def _top_pixel_from_mask_percentile(self, mask, top_pct=2):
        ys, xs = np.where(mask > 0)
        if ys.size == 0:
            return None
        v_top = int(np.percentile(ys, top_pct))
        # choose median x for that row (fallback to nearby)
        cols = xs[ys == v_top]
        if cols.size == 0:
            for dr in range(1, 8):
                cols = xs[ys == (v_top + dr)]
                if cols.size:
                    v_top = v_top + dr
                    break
                cols = xs[ys == (v_top - dr)]
                if cols.size:
                    v_top = v_top - dr
                    break
        if cols.size == 0:
            return None
        u_top = int(np.median(cols))
        return (u_top, v_top)

    def _depth_patch_median(self, depth_msg, u, v, k=5):
        if depth_msg is None:
            return float('nan')
        try:
            depth_cv = self.bridge.imgmsg_to_cv2(depth_msg, desired_encoding='passthrough')
        except Exception as e:
            self.get_logger().warning(f'cv_bridge depth convert failed: {e}')
            return float('nan')
        if depth_cv is None:
            return float('nan')
        h, w = depth_cv.shape[:2]
        r = k // 2
        u0 = max(0, u - r); u1 = min(w, u + r + 1)
        v0 = max(0, v - r); v1 = min(h, v + r + 1)
        patch = depth_cv[v0:v1, u0:u1].astype('float64')

        # Handle common encodings: 16-bit unsigned (mm) or 32-bit float (m)
        enc = ''
        try:
            enc = depth_msg.encoding
        except Exception:
            enc = ''
        if enc == '16UC1' or enc == 'mono16' or depth_cv.dtype == np.uint16:
            patch = patch / 1000.0  # mm -> m
        # mask invalid values (0) and NaNs
        patch = patch[np.isfinite(patch) & (patch > 0)]
        if patch.size == 0:
            return float('nan')
        return float(np.median(patch))

    def _pixel_to_cam(self, u, v, Z, intr):
        fx = intr['fx']; fy = intr['fy']; cx = intr['cx']; cy = intr['cy']
        X = (float(u) - cx) * Z / fx
        Y = (float(v) - cy) * Z / fy
        return np.array([X, Y, Z], dtype=float)

    def _transform_point(self, point_xyz, src_frame, tgt_frame, timeout_sec=0.5):
        # point_xyz = [x,y,z] in src_frame
        ps = PointStamped()
        ps.header.frame_id = src_frame
        ps.header.stamp = self.get_clock().now().to_msg()
        ps.point.x = float(point_xyz[0])
        ps.point.y = float(point_xyz[1])
        ps.point.z = float(point_xyz[2])
        try:
            # wait for transform to exist (non-blocking)
            if not self.tf_buffer.can_transform(tgt_frame, src_frame, rclpy.time.Time(), timeout=Duration(seconds=timeout_sec)):
                # try one quick wait
                # NOTE: can_transform signature may vary across ROS2 versions; keep a try/except fallback below
                pass
        except Exception:
            pass
        try:
            out = self.tf_buffer.transform(ps, tgt_frame, timeout=Duration(seconds=timeout_sec))
            return np.array([out.point.x, out.point.y, out.point.z], dtype=float)
        except Exception as e:
            # transformation failed
            self.get_logger().debug(f'TF transform failed ({src_frame} -> {tgt_frame}): {e}')
            return None

    def _should_send_goal(self, P_map_xyz):
        # send only if further than SEND_DISTANCE_THRESH from last sent goal
        x, y = float(P_map_xyz[0]), float(P_map_xyz[1])
        if self.last_sent_goal_xy is None:
            return True
        lx, ly = self.last_sent_goal_xy
        d = math.hypot(x - lx, y - ly)
        return (d >= self.SEND_DISTANCE_THRESH)

    def _send_nav2_goal(self, P_map_xyz):
        # Ensure action server available
        if not self.nav_client.wait_for_server(timeout_sec=2.0):
            self.get_logger().warning('Nav2 action server not available; cannot send goal')
            return

        # Build PoseStamped in map frame
        pose = PoseStamped()
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.header.frame_id = self.map_frame
        pose.pose.position.x = float(P_map_xyz[0])
        pose.pose.position.y = float(P_map_xyz[1])
        pose.pose.position.z = float(P_map_xyz[2])
        # orientation: keep identity (no rotation). Nav2 will plan orientation as necessary.
        pose.pose.orientation.w = 1.0

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = pose

        send_goal_future = self.nav_client.send_goal_async(goal_msg)
        send_goal_future.add_done_callback(lambda fut: self._goal_response_callback(fut, pose))

    def _goal_response_callback(self, future, pose_sent):
        try:
            goal_handle = future.result()
            if not goal_handle.accepted:
                self.get_logger().warning('Nav2 rejected the goal')
                return
            self.get_logger().info('Nav2 accepted the goal; waiting for result...')
            self.last_sent_goal_xy = (pose_sent.pose.position.x, pose_sent.pose.position.y)
            result_future = goal_handle.get_result_async()
            result_future.add_done_callback(self._result_callback)
        except Exception as e:
            self.get_logger().error(f'Error sending goal: {e}')

    def _result_callback(self, future):
        try:
            result = future.result().result
            status = future.result().status
            self.get_logger().info(f'Nav2 goal finished with status: {status}')
        except Exception as e:
            self.get_logger().warning(f'Error retrieving goal result: {e}')


def main(args=None):
    rclpy.init(args=args)
    node = LaneNavNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node.SHOW_DEBUG:
            cv2.destroyAllWindows()
        node.get_logger().info('Shutting down lane_nav_node')
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()