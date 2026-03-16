#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, LaserScan, Imu
from std_msgs.msg import String
from cv_bridge import CvBridge
import numpy as np
import math


class TerrainClassifier(Node):

    def __init__(self):
        super().__init__('terrain_classifier')

        self.bridge = CvBridge()

        # Parameters
        self.declare_parameter('ramp_slope_thresh', 5.0)
        self.declare_parameter('bridge_edge_dist', 0.8)
        self.declare_parameter('bridge_center_dist', 1.5)
        self.declare_parameter('rough_variance_thresh', 0.08)

        self.ramp_thresh = self.get_parameter('ramp_slope_thresh').value
        self.bridge_edge = self.get_parameter('bridge_edge_dist').value
        self.bridge_center = self.get_parameter('bridge_center_dist').value
        self.rough_thresh = self.get_parameter('rough_variance_thresh').value

        # Data
        self.depth = None
        self.scan = None
        self.imu_pitch = 0.0
        self.imu_buffer = []

        # Subscribers
        self.create_subscription(Image, '/camera/depth/image_rect', self.depth_cb, 10)
        self.create_subscription(LaserScan, '/scan', self.scan_cb, 10)
        self.create_subscription(Imu, '/imu', self.imu_cb, 20)

        # Publisher
        self.pub = self.create_publisher(String, '/terrain_type', 10)

        self.timer = self.create_timer(0.1, self.update)

        self.get_logger().info("Terrain classifier started")

    # ---------------- IMU ----------------

    def imu_cb(self, msg):
        q = msg.orientation

        qw = q.w
        qx = q.x
        qy = q.y
        qz = q.z

        t2 = 2.0 * (qw * qy - qz * qx)
        t2 = max(min(t2, 1.0), -1.0)
        pitch = math.asin(t2)

        self.imu_pitch = pitch

        w = msg.angular_velocity
        mag = math.sqrt(w.x*w.x + w.y*w.y + w.z*w.z)

        self.imu_buffer.append(mag)

        if len(self.imu_buffer) > 30:
            self.imu_buffer.pop(0)

    # ---------------- Depth ----------------

    def depth_cb(self, msg):
        try:
            self.depth = self.bridge.imgmsg_to_cv2(msg, desired_encoding='32FC1')
        except:
            pass

    # ---------------- Lidar ----------------

    def scan_cb(self, msg):
        self.scan = msg

    # ---------------- Ramp Detection ----------------

    def detect_ramp(self):

        if self.depth is None:
            return False

        d = self.depth

        h = d.shape[0]
        w = d.shape[1]

        roi = d[int(h*0.4):int(h*0.8), :]

        ys, xs = np.where(np.isfinite(roi))

        if len(xs) < 200:
            return False

        z = roi[ys, xs]

        slope = np.std(z)

        if slope > 0.15:
            return True

        pitch_deg = abs(math.degrees(self.imu_pitch))

        if pitch_deg > self.ramp_thresh:
            return True

        return False

    # ---------------- Bridge Detection ----------------

    def detect_bridge(self):

        if self.scan is None:
            return False

        ranges = np.array(self.scan.ranges)

        n = len(ranges)

        left = np.nanmean(ranges[0:30])
        center = np.nanmean(ranges[n//2 - 20:n//2 + 20])
        right = np.nanmean(ranges[-30:])

        if left < self.bridge_edge and right < self.bridge_edge and center > self.bridge_center:
            return True

        return False

    # ---------------- Rough Terrain ----------------

    def detect_rough(self):

        if len(self.imu_buffer) < 10:
            return False

        var = np.var(self.imu_buffer)

        if var > self.rough_thresh:
            return True

        return False

    # ---------------- Update ----------------

    def update(self):

        terrain = "flat"

        if self.detect_bridge():
            terrain = "bridge"

        elif self.detect_ramp():
            pitch = math.degrees(self.imu_pitch)

            if pitch > 0:
                terrain = "ramp_up"
            else:
                terrain = "ramp_down"

        elif self.detect_rough():
            terrain = "rough"

        msg = String()
        msg.data = terrain
        self.pub.publish(msg)


def main(args=None):

    rclpy.init(args=args)

    node = TerrainClassifier()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()