#!/usr/bin/env python3
"""
lane_nav_node.py (improved)

Edited to address the major robustness issues discussed:
 - synchronizes color, depth and camera_info using message_filters (approximate sync)
 - uses image/header timestamps for TF transforms (avoids stamping with now())
 - handles common depth encodings robustly (16UC1 -> meters, 32FC1 -> meters)
 - simple goal lifecycle management: track active goal, cancel if replaced
 - avoid spamming Nav2: distance + time gating + check active-goal state
 - compute goal orientation (yaw) from robot pose in map -> smoother final orientation
 - publishes lane PoseStamped to /lane_point (so perception can be decoupled from planning)
 - safer debug window handling for headless operation
 - clearer logs and defensive checks

Notes:
 - Requires: rclpy, cv2, numpy, cv_bridge, tf2_ros, nav2_msgs, message_filters, tf_transformations (or use tf2 for quaternion)
 - Put this file in a ROS2 Python package (scripts/), make executable.
"""

import math
import time

import cv2
import numpy as np

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.duration import Duration

from sensor_msgs.msg import Image as SensorImage
from sensor_msgs.msg import CameraInfo
from geometry_msgs.msg import PointStamped, PoseStamped
from nav2_msgs.action import NavigateToPose
from std_msgs.msg import Header

from cv_bridge import CvBridge
import tf2_ros
import message_filters

# quaternion helper
try:
    import tf_transformations as tft
except Exception:
    # fallback: small util to make quaternion from yaw
    def quaternion_from_euler(roll, pitch, yaw):
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)

        w = cy * cr * cp + sy * sr * sp
        x = cy * sr * cp - sy * cr * sp
        y = cy * cr * sp + sy * sr * cp
        z = sy * cr * cp - cy * sr * sp
        return (x, y, z, w)
else:
    def quaternion_from_euler(roll, pitch, yaw):
        return tft.quaternion_from_euler(roll, pitch, yaw)


class LaneNavNode(Node):
    def __init__(self):
        super().__init__('lane_nav_node')

        # --- Parameters (tune these) ---
        self.declare_parameter('color_image_topic', '/camera/color/image_raw')
        self.declare_parameter('depth_image_topic', '/camera/depth/image_raw')
        self.declare_parameter('camera_info_topic', '/camera/color/camera_info')
        self.declare_parameter('camera_frame', 'camera_color_frame')
        self.declare_parameter('base_frame', 'base_link')
        self.declare_parameter('map_frame', 'map')
        self.declare_parameter('height_threshold', 0.05)
        self.declare_parameter('min_depth', 0.2)
        self.declare_parameter('max_depth', 5.0)
        self.declare_parameter('send_distance_thresh', 0.5)
        self.declare_parameter('send_time_thresh', 1.0)  # seconds between sends
        self.declare_parameter('sync_slop', 0.05)  # seconds for approximate sync
        self.declare_parameter('show_debug_windows', False)

        # fetch params
        color_topic = self.get_parameter('color_image_topic').get_parameter_value().string_value
        depth_topic = self.get_parameter('depth_image_topic').get_parameter_value().string_value
        caminfo_topic = self.get_parameter('camera_info_topic').get_parameter_value().string_value
        self.camera_frame = self.get_parameter('camera_frame').get_parameter_value().string_value
        self.base_frame = self.get_parameter('base_frame').get_parameter_value().string_value
        self.map_frame = self.get_parameter('map_frame').get_parameter_value().string_value
        self.HEIGHT_THRESHOLD = float(self.get_parameter('height_threshold').get_parameter_value().double_value)
        self.MIN_DEPTH = float(self.get_parameter('min_depth').get_parameter_value().double_value)
        self.MAX_DEPTH = float(self.get_parameter('max_depth').get_parameter_value().double_value)
        self.SEND_DISTANCE_THRESH = float(self.get_parameter('send_distance_thresh').get_parameter_value().double_value)
        self.SEND_TIME_THRESH = float(self.get_parameter('send_time_thresh').get_parameter_value().double_value)
        self.SYNC_SLOP = float(self.get_parameter('sync_slop').get_parameter_value().double_value)
        self.SHOW_DEBUG = bool(self.get_parameter('show_debug_windows').get_parameter_value().bool_value)

        # CvBridge
        self.bridge = CvBridge()

        # camera intrinsics
        self.intrinsics = None

        # TF
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        # Nav2 action client
        self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        # don't block forever; wait a short while at init (non-critical)
        if not self.nav_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().warning('Nav2 action server not available at init; will retry at send time.')

        # goal lifecycle vars
        self.current_goal_handle = None
        self.last_sent_goal_xy = None
        self.last_sent_time = 0.0

        # small kernel for morphology
        self.morph_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

        # lane point publisher (allow decoupling perception vs planning)
        self.lane_pub = self.create_publisher(PoseStamped, 'lane_point', 10)

        # ---------- message_filters-based synchronized subscribers ----------
        # Subscribe using message_filters so color+depth+caminfo are approximately time-synced.
        self.get_logger().info('Creating synchronized subscribers...')
        color_sub = message_filters.Subscriber(self, SensorImage, color_topic)
        depth_sub = message_filters.Subscriber(self, SensorImage, depth_topic)
        caminfo_sub = message_filters.Subscriber(self, CameraInfo, caminfo_topic)

        # ApproximateTimeSynchronizer: queue size and slop tuned by param
        ats = message_filters.ApproximateTimeSynchronizer(
            [color_sub, depth_sub, caminfo_sub],
            queue_size=10,
            slop=self.SYNC_SLOP,
            allow_headerless=False
        )
        ats.registerCallback(self.synced_cb)

        self.get_logger().info('lane_nav_node started (improved, synchronized).')

    # -------------------- Synchronized callback --------------------
    def synced_cb(self, color_msg: SensorImage, depth_msg: SensorImage, caminfo_msg: CameraInfo):
        """
        Main synchronized callback: color+depth+caminfo arrive together (approx).
        We use the image header stamps for TF transforms.
        """
        # update intrinsics (use camera_info from the synced stream)
        if self.intrinsics is None:
            try:
                fx = caminfo_msg.k[0]
                fy = caminfo_msg.k[4]
                cx = caminfo_msg.k[2]
                cy = caminfo_msg.k[5]
                self.intrinsics = {'fx': float(fx), 'fy': float(fy), 'cx': float(cx), 'cy': float(cy)}
                self.get_logger().info(f'Camera intrinsics: fx={fx:.1f}, fy={fy:.1f}, cx={cx:.1f}, cy={cy:.1f}')
            except Exception as e:
                self.get_logger().warning(f'Failed to read intrinsics from CameraInfo: {e}')
                return

        # convert color image
        try:
            frame = self.bridge.imgmsg_to_cv2(color_msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f'cv_bridge color convert failed: {e}')
            return

        # Build mask for lane detection: yellow OR black
        mask_yellow = self._mask_yellow(frame)
        mask_black = self._mask_black(frame)
        mask = cv2.bitwise_or(mask_yellow, mask_black)

        # clean mask
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, self.morph_kernel, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.morph_kernel, iterations=1)

        if cv2.countNonZero(mask) == 0:
            if self.SHOW_DEBUG:
                cv2.imshow('frame', frame)
                cv2.imshow('mask', mask)
                cv2.waitKey(1)
            return

        # find bottom pixel & top pixel
        bot_pixel = self._bottom_pixel_from_mask(mask)
        if bot_pixel is None:
            return
        u_bot, v_bot = bot_pixel

        top_pixel = self._top_pixel_from_mask_percentile(mask, top_pct=2)
        if top_pixel is None:
            # proceed with only bottom but height classification will fallback
            u_top, v_top = u_bot, max(0, v_bot - 20)
        else:
            u_top, v_top = top_pixel

        # Get median depth around bottom & top pixels (returns meters)
        Z_bot = self._depth_patch_median(depth_msg, u_bot, v_bot, k=7)
        if not np.isfinite(Z_bot) or Z_bot <= 0.0:
            Z_bot = self._depth_patch_median(depth_msg, u_bot, v_bot, k=15)
        if (not np.isfinite(Z_bot)) or (Z_bot < self.MIN_DEPTH) or (Z_bot > self.MAX_DEPTH):
            self.get_logger().debug('depth invalid or out of range; skipping detection')
            if self.SHOW_DEBUG:
                debug_frame = frame.copy()
                cv2.circle(debug_frame, (u_bot, v_bot), 6, (0, 0, 255), -1)
                cv2.imshow('frame', debug_frame)
                cv2.imshow('mask', mask)
                cv2.waitKey(1)
            return

        # Unproject to camera coordinates
        P_bot_cam = self._pixel_to_cam(u_bot, v_bot, Z_bot, self.intrinsics)  # X,Y,Z in camera frame

        # Transform both bottom and top using image stamp (prefer depth header stamp)
        stamp = depth_msg.header.stamp if depth_msg.header.stamp is not None else color_msg.header.stamp

        P_bot_map = self._transform_point_with_stamp(P_bot_cam, src_frame=self.camera_frame, tgt_frame=self.map_frame, stamp=stamp)
        if P_bot_map is None:
            self.get_logger().warning('TF transform for bottom point failed; skipping')
            return

        # Top depth may be invalid; handle gracefully
        Z_top = self._depth_patch_median(depth_msg, u_top, v_top, k=7)
        if not np.isfinite(Z_top):
            Z_top = self._depth_patch_median(depth_msg, u_top, v_top, k=15)

        if not np.isfinite(Z_top):
            # fallback to treat as very small height (so it's likely lane)
            height = 0.0
        else:
            P_top_cam = self._pixel_to_cam(u_top, v_top, Z_top, self.intrinsics)
            P_top_map = self._transform_point_with_stamp(P_top_cam, src_frame=self.camera_frame, tgt_frame=self.map_frame, stamp=stamp)
            if P_top_map is None:
                self.get_logger().warning('TF transform for top point failed; skipping')
                return
            height = abs(P_top_map[2] - P_bot_map[2])

        # Classification
        if height >= self.HEIGHT_THRESHOLD:
            self.get_logger().info(f'Classified OBSTACLE (height={height:.3f} m). Not sending to Nav2.')
            # publish lane_point? No — it's obstacle
        else:
            self.get_logger().info(f'Classified LANE (height={height:.3f} m). Preparing lane point.')
            # Build PoseStamped (map frame) for publish and for Nav2 goal
            lane_pose = PoseStamped()
            lane_pose.header = Header()
            lane_pose.header.stamp = stamp
            lane_pose.header.frame_id = self.map_frame
            lane_pose.pose.position.x = float(P_bot_map[0])
            lane_pose.pose.position.y = float(P_bot_map[1])
            lane_pose.pose.position.z = float(P_bot_map[2])
            # orientation: compute yaw so robot faces along vector from robot -> lane point (if possible)
            yaw = self._compute_yaw_towards_point(lane_pose, stamp)
            q = quaternion_from_euler(0.0, 0.0, yaw)
            lane_pose.pose.orientation.x = float(q[0])
            lane_pose.pose.orientation.y = float(q[1])
            lane_pose.pose.orientation.z = float(q[2])
            lane_pose.pose.orientation.w = float(q[3])

            # publish perception output for debugging / decoupling
            try:
                self.lane_pub.publish(lane_pose)
            except Exception:
                pass

            # Decide whether to send to Nav2 (distance + time gating + lifecycle)
            now_t = self.get_clock().now().seconds_nanoseconds()[0] + self.get_clock().now().seconds_nanoseconds()[1] * 1e-9
            send_allowed = False
            if self.last_sent_goal_xy is None:
                send_allowed = True
            else:
                lx, ly = self.last_sent_goal_xy
                d = math.hypot(lane_pose.pose.position.x - lx, lane_pose.pose.position.y - ly)
                if d >= self.SEND_DISTANCE_THRESH:
                    send_allowed = True
            if (now_t - self.last_sent_time) < self.SEND_TIME_THRESH:
                send_allowed = False

            if send_allowed:
                # if there's an active goal and it's not done, cancel it before sending a new one
                if self.current_goal_handle is not None:
                    try:
                        # only attempt cancel if goal handle still active and accepted
                        if not self.current_goal_handle.is_canceling() and not self.current_goal_handle.is_cancel_requested():
                            self.get_logger().info('Cancelling previous Nav2 goal before sending new one.')
                            cancel_future = self.current_goal_handle.cancel_goal_async()
                            # don't block: attach callback to proceed sending after cancel completes if desired
                            # here we will still send the new goal immediately (Nav2 will preempt), which is acceptable
                    except Exception:
                        # some goal handles may not support cancel or are already finished; ignore
                        pass

                self._send_nav2_goal(lane_pose)
                self.last_sent_goal_xy = (lane_pose.pose.position.x, lane_pose.pose.position.y)
                self.last_sent_time = now_t
            else:
                self.get_logger().debug('Lane goal skipped due to distance/time gating or active goal.')

        # debug visuals
        if self.SHOW_DEBUG:
            debug = frame.copy()
            cv2.circle(debug, (u_bot, v_bot), 6, (0, 255, 0), -1)
            cv2.circle(debug, (u_top, v_top), 4, (255, 0, 0), -1)
            cv2.putText(debug, f'h={height:.3f}m', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            cv2.imshow('frame', debug)
            cv2.imshow('mask', mask)
            cv2.waitKey(1)

    # -------------------- Utilities --------------------
    def _mask_yellow(self, frame_bgr):
        hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        lower_y = np.array([15, 100, 100], dtype=np.uint8)
        upper_y = np.array([35, 255, 255], dtype=np.uint8)
        return cv2.inRange(hsv, lower_y, upper_y)

    def _mask_black(self, frame_bgr):
        hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        lower_b = np.array([0, 0, 0], dtype=np.uint8)
        upper_b = np.array([180, 255, 60], dtype=np.uint8)
        return cv2.inRange(hsv, lower_b, upper_b)

    def _bottom_pixel_from_mask(self, mask):
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
        if num_labels <= 1:
            return None
        areas = stats[1:, cv2.CC_STAT_AREA]
        largest_label = 1 + int(np.argmax(areas))
        comp_mask = (labels == largest_label).astype('uint8') * 255
        ys, xs = np.where(comp_mask > 0)
        if ys.size == 0:
            return None
        v_bot = int(np.max(ys))
        cols = xs[ys == v_bot]
        if cols.size == 0:
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
        """
        Returns median depth in meters for patch around (u,v).
        Handles common encodings: 16UC1 (mm) and 32FC1 (m).
        """
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
        patch = depth_cv[v0:v1, u0:u1].astype('float64', copy=False)

        # check encoding for units
        enc = ''
        try:
            enc = depth_msg.encoding
        except Exception:
            enc = ''

        # If encoding indicates 16-bit (usually millimeters)
        if enc in ('16UC1', 'mono16') or patch.dtype == np.uint16:
            patch = patch.astype('float64') / 1000.0  # mm -> m
        # If float32 (32FC1), assume meters already
        # Mask invalid values (0) and NaNs
        patch = patch[np.isfinite(patch) & (patch > 0)]
        if patch.size == 0:
            return float('nan')
        return float(np.median(patch))

    def _pixel_to_cam(self, u, v, Z, intr):
        fx = intr['fx']; fy = intr['fy']; cx = intr['cx']; cy = intr['cy']
        X = (float(u) - cx) * Z / fx
        Y = (float(v) - cy) * Z / fy
        return np.array([X, Y, Z], dtype=float)

    def _transform_point_with_stamp(self, point_xyz, src_frame, tgt_frame, stamp, timeout_sec=0.5):
        """
        Transform a 3D point expressed in src_frame to tgt_frame using the provided header stamp.
        stamp: builtin_interfaces/Time message (header.stamp from image)
        """
        ps = PointStamped()
        ps.header.frame_id = src_frame
        ps.header.stamp = stamp
        ps.point.x = float(point_xyz[0])
        ps.point.y = float(point_xyz[1])
        ps.point.z = float(point_xyz[2])
        try:
            out = self.tf_buffer.transform(ps, tgt_frame, timeout=Duration(seconds=timeout_sec))
            return np.array([out.point.x, out.point.y, out.point.z], dtype=float)
        except Exception as e:
            self.get_logger().debug(f'TF transform failed ({src_frame} -> {tgt_frame}) at stamp {stamp}: {e}')
            return None

    def _compute_yaw_towards_point(self, lane_pose: PoseStamped, stamp):
        """
        Compute yaw so robot faces the lane point. We attempt to get robot pose in map frame by
        transforming the origin (0,0,0) in base_frame to the map frame at the same stamp.
        If transform fails, return yaw=0 (identity).
        """
        try:
            origin = PointStamped()
            origin.header.frame_id = self.base_frame
            origin.header.stamp = stamp
            origin.point.x = 0.0
            origin.point.y = 0.0
            origin.point.z = 0.0
            robot_pt = self.tf_buffer.transform(origin, self.map_frame, timeout=Duration(seconds=0.5))
            rx, ry = robot_pt.point.x, robot_pt.point.y
            dx = lane_pose.pose.position.x - rx
            dy = lane_pose.pose.position.y - ry
            if abs(dx) < 1e-6 and abs(dy) < 1e-6:
                return 0.0
            return math.atan2(dy, dx)
        except Exception as e:
            self.get_logger().debug(f'Could not compute robot position for yaw: {e}')
            return 0.0

    # ----------------- Nav2 goal sending and lifecycle -----------------
    def _send_nav2_goal(self, pose_stamped: PoseStamped):
        # Ensure action server available
        if not self.nav_client.wait_for_server(timeout_sec=2.0):
            self.get_logger().warning('Nav2 action server not available; cannot send goal now.')
            return

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = pose_stamped

        send_goal_future = self.nav_client.send_goal_async(goal_msg)
        send_goal_future.add_done_callback(lambda fut: self._goal_response_callback(fut, pose_stamped))

    def _goal_response_callback(self, future, pose_sent):
        try:
            goal_handle = future.result()
            if not goal_handle.accepted:
                self.get_logger().warning('Nav2 rejected the goal')
                return
            self.get_logger().info('Nav2 accepted the goal; tracking goal handle.')
            # store current goal handle for potential cancellation
            self.current_goal_handle = goal_handle
            # update last sent if not updated earlier
            try:
                self.last_sent_goal_xy = (pose_sent.pose.position.x, pose_sent.pose.position.y)
            except Exception:
                pass
            result_future = goal_handle.get_result_async()
            result_future.add_done_callback(self._result_callback)
        except Exception as e:
            self.get_logger().error(f'Error sending goal: {e}')

    def _result_callback(self, future):
        try:
            res = future.result()
            status = res.status
            # goal finished; clear handle
            self.get_logger().info(f'Nav2 goal finished with status: {status}')
            self.current_goal_handle = None
        except Exception as e:
            self.get_logger().warning(f'Error retrieving goal result: {e}')
            self.current_goal_handle = None


def main(args=None):
    rclpy.init(args=args)
    node = LaneNavNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node.SHOW_DEBUG:
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass
        node.get_logger().info('Shutting down lane_nav_node')
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()