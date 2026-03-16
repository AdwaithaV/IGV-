#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, LaserScan
from geometry_msgs.msg import PointStamped
from visualization_msgs.msg import Marker, MarkerArray
from cv_bridge import CvBridge
import cv2
import numpy as np
import math


class ObstacleDetector(Node):

    def __init__(self):
        super().__init__('obstacle_detector')

        self.bridge = CvBridge()
        self.depth = None
        self.scan = None

        # Tunable parameters
        self.camera_frame = "camera_link"
        self.min_contour_area = 300
        self.min_height_threshold = 0.06   # 6cm obstacle height
        self.max_obstacle_distance = 3.0

        self.hsv_lower = np.array([18, 100, 100])
        self.hsv_upper = np.array([35, 255, 255])

        # Camera intrinsics (REPLACE WITH CALIBRATED VALUES)
        self.fx = 913.1740112304688
        self.fy = 913.633544921875
        self.cx = 689.267822265625
        self.cy = 365.14556884765625

        self.create_subscription(Image, '/camera/rgb/image_rect', self.color_callback, 10)
        self.create_subscription(Image, '/camera/depth/image_raw', self.depth_callback, 10)
        self.create_subscription(LaserScan, '/scan_filtered', self.scan_callback, 10)

        self.pub_markers = self.create_publisher(MarkerArray, '/perception/obstacles_markers', 10)
        self.pub_nearest = self.create_publisher(PointStamped, '/perception/nearest_obstacle', 10)

        self.get_logger().info("Obstacle detector started.")

    def scan_callback(self, msg):
        self.scan = msg

    def depth_callback(self, msg):
        try:
            self.depth = self.bridge.imgmsg_to_cv2(msg, desired_encoding='32FC1')
        except:
            self.depth = self.bridge.imgmsg_to_cv2(msg, desired_encoding='16UC1').astype(np.float32) / 1000.0

    def color_callback(self, msg):

        if self.depth is None:
            return

        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.hsv_lower, self.hsv_upper)

        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        marker_array = MarkerArray()
        nearest_dist = 999
        nearest_point = None
        marker_id = 0

        for cnt in contours:

            if cv2.contourArea(cnt) < self.min_contour_area:
                continue

            x, y, w, h = cv2.boundingRect(cnt)

            patch = self.depth[y:y+h, x:x+w]
            valid = patch[np.isfinite(patch) & (patch > 0)]

            if valid.size == 0:
                continue

            depth_val = float(np.median(valid))
            if depth_val > self.max_obstacle_distance:
                continue

            # Estimate vertical height
            top = patch[0:int(h*0.3), :]
            bottom = patch[int(h*0.7):h, :]

            if top.size == 0 or bottom.size == 0:
                continue

            height_est = abs(np.median(bottom) - np.median(top))

            if height_est < self.min_height_threshold:
                continue  # Likely painted line

            # 3D projection
            cx = x + w//2
            cy = y + h//2

            Z = depth_val
            X = (cx - self.cx) * Z / self.fx
            Y = (cy - self.cy) * Z / self.fy

            # Publish marker
            marker = Marker()
            marker.header = msg.header
            marker.ns = "obstacles"
            marker.id = marker_id
            marker.type = Marker.CUBE
            marker.action = Marker.ADD

            marker.pose.position.x = Z
            marker.pose.position.y = X
            marker.pose.position.z = -Y

            marker.scale.x = 0.2
            marker.scale.y = 0.2
            marker.scale.z = max(0.05, height_est)

            marker.color.r = 1.0
            marker.color.g = 0.0
            marker.color.b = 0.0
            marker.color.a = 0.8

            marker_array.markers.append(marker)
            marker_id += 1

            if Z < nearest_dist:
                nearest_dist = Z
                nearest_point = (Z, X, -Y)

        self.pub_markers.publish(marker_array)

        if nearest_point:
            msg_pt = PointStamped()
            msg_pt.header = msg.header
            msg_pt.point.x = nearest_point[0]
            msg_pt.point.y = nearest_point[1]
            msg_pt.point.z = nearest_point[2]
            self.pub_nearest.publish(msg_pt)


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleDetector()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()