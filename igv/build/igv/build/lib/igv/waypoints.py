#!/usr/bin/env python3
"""
qr_to_waypoints.py

Subscribes to camera image (/camera/image_raw), decodes QR codes using pyzbar,
parses payloads:

- GOTO:x,y,yaw    -> single PoseStamped (frame 'map' by default)
- WAYPOINTS:x1,y1,yaw1;x2,y2,yaw2  -> multiple semicolon-separated points
- If QR encodes coordinates in robot frame, the prefix should be 'REL:' e.g. 'REL:GOTO:0.5,0,0'

Sends FollowWaypoints action to Nav2 with list of PoseStamped (map frame).
"""

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from nav2_msgs.action import FollowWaypoints
from geometry_msgs.msg import PoseStamped
import tf2_ros
from tf2_geometry_msgs import do_transform_pose
import tf_transformations
import numpy as np
from pyzbar import pyzbar
import cv2
import time


class QRToWaypoints(Node):
    def __init__(self):
        super().__init__('qr_to_waypoints')
        self.declare_parameter('image_topic', '/camera/image_raw')
        self.declare_parameter('camera_frame', 'camera_link')
        self.declare_parameter('map_frame', 'map')
        self.declare_parameter('nav_action_name', 'follow_waypoints')

        self.image_topic = self.get_parameter('image_topic').value
        self.camera_frame = self.get_parameter('camera_frame').value
        self.map_frame = self.get_parameter('map_frame').value
        self.nav_action_name = self.get_parameter('nav_action_name').value

        self.bridge = CvBridge()
        self.sub = self.create_subscription(Image, self.image_topic, self.image_cb, 2)

        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        self._action_client = ActionClient(self, FollowWaypoints, self.nav_action_name)

        self.last_qr_time = 0.0
        self.qr_cooldown = 1.0  # seconds between processing same QR

        self.get_logger().info(f"QR->Waypoints listening on {self.image_topic}")

    def image_cb(self, msg: Image):
        # Convert to OpenCV
        try:
            cv_img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f"cv_bridge failed: {e}")
            return

        codes = pyzbar.decode(cv_img)
        if not codes:
            return

        for c in codes:
            data = c.data.decode('utf-8').strip()
            now = time.time()
            if now - self.last_qr_time < self.qr_cooldown:
                self.get_logger().debug("QR cooldown; skipping")
                continue
            self.last_qr_time = now
            self.get_logger().info(f"Decoded QR: {data}")
            try:
                waypoints = self.parse_qr_payload(data, msg.header)
            except Exception as e:
                self.get_logger().warn(f"Failed to parse QR payload: {e}")
                continue

            if not waypoints:
                self.get_logger().warn("No waypoints parsed")
                continue

            # Send FollowWaypoints action
            if not self._action_client.wait_for_server(timeout_sec=2.0):
                self.get_logger().warn("FollowWaypoints action server not available")
                continue

            goal_msg = FollowWaypoints.Goal()
            goal_msg.poses = waypoints
            send_goal_future = self._action_client.send_goal_async(goal_msg)
            send_goal_future.add_done_callback(self._goal_response_cb)
            self.get_logger().info(f"Sent FollowWaypoints with {len(waypoints)} poses")

    def _goal_response_cb(self, future):
        try:
            goal_handle = future.result()
            if not goal_handle.accepted:
                self.get_logger().warn("Nav2 rejected FollowWaypoints goal")
                return
            self.get_logger().info("FollowWaypoints goal accepted")
            result_future = goal_handle.get_result_async()
            result_future.add_done_callback(self._get_result_cb)
        except Exception as e:
            self.get_logger().error(f"Error sending FollowWaypoints goal: {e}")

    def _get_result_cb(self, future):
        try:
            res = future.result().result
            status = future.result().status
            self.get_logger().info(f"FollowWaypoints finished with status {status}")
        except Exception as e:
            self.get_logger().error(f"Error getting FollowWaypoints result: {e}")

    def parse_qr_payload(self, payload: str, header):
        """
        Accepts payload like:
        - GOTO:x,y,yaw
        - WAYPOINTS:x1,y1,yaw1;x2,y2,yaw2
        - REL:GOTO:x,y,yaw  (relative to camera_frame)
        Returns list of PoseStamped in map frame.
        """
        payload = payload.strip()
        is_relative = False
        if payload.startswith('REL:'):
            is_relative = True
            payload = payload[len('REL:'):]

        if payload.startswith('GOTO:'):
            coords = payload[len('GOTO:'):].split(',')
            if len(coords) < 3:
                raise ValueError("GOTO requires x,y,yaw")
            x, y, yaw = map(float, coords[:3])
            pose = PoseStamped()
            pose.header.frame_id = self.map_frame if not is_relative else self.camera_frame
            pose.header.stamp = self.get_clock().now().to_msg()
            pose.pose.position.x = x
            pose.pose.position.y = y
            q = tf_transformations.quaternion_from_euler(0, 0, yaw)
            pose.pose.orientation.x = q[0]
            pose.pose.orientation.y = q[1]
            pose.pose.orientation.z = q[2]
            pose.pose.orientation.w = q[3]
            if is_relative:
                pose = self._transform_to_map(pose)
            return [pose]

        if payload.startswith('WAYPOINTS:'):
            rest = payload[len('WAYPOINTS:'):]
            parts = rest.split(';')
            poses = []
            for p in parts:
                coords = p.split(',')
                if len(coords) < 3:
                    continue
                x, y, yaw = map(float, coords[:3])
                pose = PoseStamped()
                pose.header.frame_id = self.map_frame if not is_relative else self.camera_frame
                pose.header.stamp = self.get_clock().now().to_msg()
                pose.pose.position.x = x
                pose.pose.position.y = y
                q = tf_transformations.quaternion_from_euler(0, 0, yaw)
                pose.pose.orientation.x = q[0]
                pose.pose.orientation.y = q[1]
                pose.pose.orientation.z = q[2]
                pose.pose.orientation.w = q[3]
                if is_relative:
                    pose = self._transform_to_map(pose)
                poses.append(pose)
            return poses

        raise ValueError("Unknown QR payload format")

    def _transform_to_map(self, pose_stamped: PoseStamped):
        # transform from pose_stamped.header.frame_id -> map_frame
        try:
            trans = self.tf_buffer.lookup_transform(self.map_frame, pose_stamped.header.frame_id, rclpy.time.Time())
            mapped = do_transform_pose(pose_stamped, trans)
            return mapped
        except Exception as e:
            self.get_logger().warn(f"TF transform to map failed: {e}")
            raise


def main(args=None):
    rclpy.init(args=args)
    node = QRToWaypoints()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
