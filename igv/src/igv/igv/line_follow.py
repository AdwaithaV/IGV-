#!/usr/bin/env python3
import sys
import time
import math

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.time import Time
from rclpy.duration import Duration

import cv2
import numpy as np
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from geometry_msgs.msg import Point, PoseStamped
from nav2_msgs.action import NavigateToPose

# TF imports
from tf2_ros import Buffer, TransformListener
from tf2_ros import LookupException, ConnectivityException, ExtrapolationException
import tf2_geometry_msgs.tf2_geometry_msgs as tf2_geometry_msgs


class YellowToNav2(Node):
    def __init__(self):
        super().__init__('yellow_to_nav2')

        # Parameters (adjust to your camera / robot)
        self.declare_parameter('camera_frame', 'camera_link')
        self.declare_parameter('base_frame', 'base_link')
        # default target_frame set to 'odom' because you said TF comes from odom
        self.declare_parameter('target_frame', 'odom')  # nav2 can accept odom or map
        self.declare_parameter('fx', 525.0)  # focal length in pixels (approx)
        self.declare_parameter('depth_m', 1.0)  # assumed forward distance for the goal (meters)
        self.declare_parameter('min_contour_area', 150.0)
        self.declare_parameter('goal_send_distance_threshold', 0.5)  # don't resend similar goals
        self.declare_parameter('min_send_interval_s', 2.0)

        self.camera_frame = self.get_parameter('camera_frame').value
        self.base_frame = self.get_parameter('base_frame').value
        self.target_frame = self.get_parameter('target_frame').value
        self.fx = float(self.get_parameter('fx').value)
        self.depth_m = float(self.get_parameter('depth_m').value)
        self.min_contour_area = float(self.get_parameter('min_contour_area').value)
        self.goal_send_distance_threshold = float(self.get_parameter('goal_send_distance_threshold').value)
        self.min_send_interval_s = float(self.get_parameter('min_send_interval_s').value)

        self.bridge = CvBridge()
        self.sub = self.create_subscription(Image, '/image/raw', self.image_callback, 10)

        # optional publisher for raw centroid (keeps compatibility with your earlier code)
        self.coord_pub = self.create_publisher(Point, 'coordinates', 10)

        # TF2 setup
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # Nav2 action client
        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

        # State to avoid flooding nav2
        self.last_sent_goal_pos = None  # (x,y) in target_frame
        self.last_sent_time = 0.0

        self.get_logger().info('yellow_to_nav2 node started - publishing detected positions to Nav2')

    def image_callback(self, msg: Image):
        # Convert image to OpenCV
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f"cv_bridge failure: {e}")
            return

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # your yellow target color (BGR) -> compute limits same as original
        yellow_bgr = [0, 255, 255]
        lowerlimit, upperlimit = self.get_limits(yellow_bgr)

        mask = cv2.inRange(hsv, lowerlimit, upperlimit)
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        points = []
        for cnt in contours:
            if cv2.contourArea(cnt) > self.min_contour_area:
                M = cv2.moments(cnt)
                if M.get("m00", 0) == 0:
                    continue
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                points.append((cx, cy))
                cv2.circle(frame, (cx, cy), 6, (0, 0, 255), -1)

        if len(points) == 0:
            cv2.imshow("frame", frame)
            cv2.imshow("mask", mask)
            cv2.waitKey(1)
            return

        avg_x = sum([p[0] for p in points]) / len(points)
        avg_y = sum([p[1] for p in points]) / len(points)

        # publish the raw pixel centroid as Point (compat)
        pt_msg = Point()
        pt_msg.x = float(avg_x)
        pt_msg.y = float(avg_y)
        pt_msg.z = 0.0
        self.coord_pub.publish(pt_msg)
        self.get_logger().info(f"detected centroid pixels: ({avg_x:.1f},{avg_y:.1f})")

        # Convert pixel centroid -> robot-relative goal in base_frame (same math as before)
        height, width = frame.shape[:2]
        cx_img = width / 2.0
        cy_img = height / 2.0

        dx_pixels = avg_x - cx_img
        # simple pinhole model (small-angle)
        angle_rad = math.atan2(dx_pixels, self.fx)

        # Place goal at depth_m distance in robot base frame (x forward, y left)
        goal_x_base = self.depth_m * math.cos(angle_rad)
        goal_y_base = self.depth_m * math.sin(angle_rad)

        self.get_logger().info(
            f"computed base_goal (x={goal_x_base:.2f}, y={goal_y_base:.2f}, yaw={angle_rad:.2f} rad)")

        # Build PoseStamped in base_frame and use the image timestamp so TF can match it
        pose_base = PoseStamped()
        pose_base.header.stamp = msg.header.stamp  # important: use image time for TF queries
        pose_base.header.frame_id = self.base_frame
        pose_base.pose.position.x = float(goal_x_base)
        pose_base.pose.position.y = float(goal_y_base)
        pose_base.pose.position.z = 0.0

        qz = math.sin(angle_rad / 2.0)
        qw = math.cos(angle_rad / 2.0)
        pose_base.pose.orientation.x = 0.0
        pose_base.pose.orientation.y = 0.0
        pose_base.pose.orientation.z = float(qz)
        pose_base.pose.orientation.w = float(qw)

        # Transform pose_base -> target frame (try image time first, fallback to latest time, fallback target)
        target = self.target_frame
        try:
            # First, try transform using the image timestamp (most correct)
            tf_time = Time.from_msg(msg.header.stamp)
            transform_stamped = self.tf_buffer.lookup_transform(
                target,
                pose_base.header.frame_id,
                tf_time,
                timeout=Duration(seconds=1.0)
            )
            pose_in_target = tf2_geometry_msgs.do_transform_pose(pose_base, transform_stamped)
            # ensure header stamp is current for Nav2
            pose_in_target.header.stamp = self.get_clock().now().to_msg()

        except ExtrapolationException as ex:
            # timestamp mismatch — fall back to latest available transform
            self.get_logger().warning(f"TF extrapolation for time {msg.header.stamp}: {ex}. Falling back to latest transform.")
            try:
                transform_stamped = self.tf_buffer.lookup_transform(
                    target,
                    pose_base.header.frame_id,
                    Time(),  # latest
                    timeout=Duration(seconds=1.0)
                )
                pose_in_target = tf2_geometry_msgs.do_transform_pose(pose_base, transform_stamped)
                pose_in_target.header.stamp = self.get_clock().now().to_msg()
            except (LookupException, ConnectivityException, ExtrapolationException) as ex2:
                self.get_logger().warn(f"TF latest lookup failed {pose_base.header.frame_id}->{target}: {ex2}; trying 'map' fallback")
                # fallback to map
                try:
                    transform_stamped = self.tf_buffer.lookup_transform(
                        'map',
                        pose_base.header.frame_id,
                        Time(),
                        timeout=Duration(seconds=1.0)
                    )
                    pose_in_target = tf2_geometry_msgs.do_transform_pose(pose_base, transform_stamped)
                    pose_in_target.header.stamp = self.get_clock().now().to_msg()
                    target = 'map'
                except Exception as ex3:
                    self.get_logger().error(f"All TF fallbacks failed: {ex3}. Not sending a Nav2 goal.")
                    cv2.imshow("frame", frame)
                    cv2.imshow("mask", mask)
                    cv2.waitKey(1)
                    return

        except (LookupException, ConnectivityException) as ex:
            # direct lookup failed (no chain between base_frame and target)
            self.get_logger().warn(
                f"TF lookup transform failed {pose_base.header.frame_id}->{target}: {ex}; trying 'map' fallback")
            try:
                transform_stamped = self.tf_buffer.lookup_transform(
                    'map',
                    pose_base.header.frame_id,
                    Time(),
                    timeout=Duration(seconds=1.0)
                )
                pose_in_target = tf2_geometry_msgs.do_transform_pose(pose_base, transform_stamped)
                pose_in_target.header.stamp = self.get_clock().now().to_msg()
                target = 'map'
            except Exception as ex2:
                self.get_logger().error(f"TF fallback failed too: {ex2}. Not sending a Nav2 goal.")
                cv2.imshow("frame", frame)
                cv2.imshow("mask", mask)
                cv2.waitKey(1)
                return
        except Exception as ex:
            self.get_logger().error(f"Unexpected TF error: {ex}")
            cv2.imshow("frame", frame)
            cv2.imshow("mask", mask)
            cv2.waitKey(1)
            return

        # decide whether to send (avoid flooding)
        now = time.time()
        send = False
        if self.last_sent_goal_pos is None:
            send = True
        else:
            lx, ly = self.last_sent_goal_pos
            dx = pose_in_target.pose.position.x - lx
            dy = pose_in_target.pose.position.y - ly
            dist = math.hypot(dx, dy)
            if dist > self.goal_send_distance_threshold:
                send = True
            elif (now - self.last_sent_time) > self.min_send_interval_s:
                send = True

        if send:
            # send to nav2
            self.send_nav2_goal(pose_in_target)
            self.last_sent_goal_pos = (pose_in_target.pose.position.x, pose_in_target.pose.position.y)
            self.last_sent_time = now
        else:
            self.get_logger().debug("goal too close to last sent; skipping send")

        # show windows (optional)
        cv2.imshow("frame", frame)
        cv2.imshow("mask", mask)
        cv2.waitKey(1)

    def send_nav2_goal(self, pose_stamped: PoseStamped):
        # wait for action server
        if not self._action_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error("NavigateToPose action server not available. Is nav2 running?")
            return

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = pose_stamped

        self.get_logger().info(
            f"Sending NavigateToPose goal in frame {pose_stamped.header.frame_id} at "
            f"({pose_stamped.pose.position.x:.2f}, {pose_stamped.pose.position.y:.2f})")

        send_goal_future = self._action_client.send_goal_async(goal_msg, feedback_callback=self._feedback_callback)
        send_goal_future.add_done_callback(self._goal_response_callback)

    def _goal_response_callback(self, future):
        try:
            goal_handle = future.result()
        except Exception as e:
            self.get_logger().error(f"Exception while sending goal: {e}")
            return

        if not goal_handle.accepted:
            self.get_logger().warn("Nav2 rejected goal")
            return

        self.get_logger().info("Nav2 accepted goal, waiting for result...")
        get_result_future = goal_handle.get_result_async()
        get_result_future.add_done_callback(self._get_result_callback)

    def _get_result_callback(self, future):
        try:
            result = future.result().result
            status = future.result().status
            self.get_logger().info(f"Nav2 result received: status={status}, result={result}")
        except Exception as e:
            self.get_logger().error(f"Exception receiving Nav2 result: {e}")

    def _feedback_callback(self, feedback_msg):
        # optional: you can inspect feedback_msg.feedback
        pass

    def get_limits(self, color_bgr):
        # same logic as your original function, convert BGR integer color to HSV center and +/-10 hue
        c = np.uint8([[color_bgr]])
        hsvc = cv2.cvtColor(c, cv2.COLOR_BGR2HSV)
        h = int(hsvc[0][0][0])
        lower = (max(h - 10, 0), 100, 100)
        upper = (min(h + 10, 179), 255, 255)
        lower_np = np.array(lower, dtype=np.uint8)
        upper_np = np.array(upper, dtype=np.uint8)
        return lower_np, upper_np


def main(args=None):
    rclpy.init(args=args)
    node = YellowToNav2()
    rclpy.spin(node)
    node.get_logger().info("Keyboard interrupt, shutting down")
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
