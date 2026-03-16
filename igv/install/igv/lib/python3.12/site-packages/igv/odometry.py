#!/usr/bin/env python3
"""
rmcs_encoder_odom_node.py

ROS2 node to compute raw odometry (/odom_raw) from RMCS encoder motor tick data.

EXPECTED INPUT:
- Left encoder ticks topic  (std_msgs/Int32)
- Right encoder ticks topic (std_msgs/Int32)

You must remap these to match your RMCS driver topics.

PARAMETERS:
- left_ticks_topic   (default: /left_encoder_ticks)
- right_ticks_topic  (default: /right_encoder_ticks)
- ticks_per_rev      (default: 500)
- wheel_radius       (meters, default: 0.075)
- wheel_base         (meters, default: 0.35)
- odom_frame         (default: odom)
- base_frame         (default: base_link)
- publish_tf         (default: false)  <-- KEEP FALSE if using EKF

OUTPUT:
- /odom_raw (nav_msgs/Odometry)
- Optional TF: odom -> base_link

This node assumes cumulative tick counts (monotonic increasing/decreasing).
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
import tf2_ros
import math
from tf_transformations import quaternion_from_euler


class RMCSOdom(Node):
    def __init__(self):
        super().__init__('rmcs_encoder_odom')

        # Parameters
        self.declare_parameter('left_ticks_topic', '/left_encoder_ticks')
        self.declare_parameter('right_ticks_topic', '/right_encoder_ticks')
        self.declare_parameter('ticks_per_rev', 500.0)
        self.declare_parameter('wheel_radius', 0.075)
        self.declare_parameter('wheel_base', 0.35)
        self.declare_parameter('odom_frame', 'odom')
        self.declare_parameter('base_frame', 'base_link')
        self.declare_parameter('publish_tf', False)

        self.left_topic = self.get_parameter('left_ticks_topic').value
        self.right_topic = self.get_parameter('right_ticks_topic').value
        self.ticks_per_rev = float(self.get_parameter('ticks_per_rev').value)
        self.R = float(self.get_parameter('wheel_radius').value)
        self.L = float(self.get_parameter('wheel_base').value)
        self.odom_frame = self.get_parameter('odom_frame').value
        self.base_frame = self.get_parameter('base_frame').value
        self.publish_tf_flag = self.get_parameter('publish_tf').value

        # State
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0

        self.last_left_ticks = None
        self.last_right_ticks = None
        self.last_time = None

        # Subscribers
        self.create_subscription(Int32, self.left_topic, self.left_cb, 10)
        self.create_subscription(Int32, self.right_topic, self.right_cb, 10)

        self.left_ticks = None
        self.right_ticks = None

        # Publisher
        self.odom_pub = self.create_publisher(Odometry, '/odom_raw', 10)

        if self.publish_tf_flag:
            self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)

        self.get_logger().info('RMCS Encoder Odom Node Started')

    def left_cb(self, msg):
        self.left_ticks = msg.data
        self.compute()

    def right_cb(self, msg):
        self.right_ticks = msg.data
        self.compute()

    def compute(self):
        if self.left_ticks is None or self.right_ticks is None:
            return

        now = self.get_clock().now()
        t = now.nanoseconds * 1e-9

        if self.last_left_ticks is None:
            self.last_left_ticks = self.left_ticks
            self.last_right_ticks = self.right_ticks
            self.last_time = t
            return

        dt = t - self.last_time
        if dt <= 0:
            return

        # Tick difference
        d_left = self.left_ticks - self.last_left_ticks
        d_right = self.right_ticks - self.last_right_ticks

        # Convert ticks -> radians
        dphi_l = (2.0 * math.pi * d_left) / self.ticks_per_rev
        dphi_r = (2.0 * math.pi * d_right) / self.ticks_per_rev

        # Distance traveled
        dl = dphi_l * self.R
        dr = dphi_r * self.R

        dc = (dl + dr) / 2.0
        dtheta = (dr - dl) / self.L

        # Integrate pose
        if abs(dtheta) < 1e-6:
            dx = dc * math.cos(self.theta)
            dy = dc * math.sin(self.theta)
        else:
            r_icc = dc / dtheta
            dx = r_icc * (math.sin(self.theta + dtheta) - math.sin(self.theta))
            dy = -r_icc * (math.cos(self.theta + dtheta) - math.cos(self.theta))

        self.x += dx
        self.y += dy
        self.theta = math.atan2(math.sin(self.theta + dtheta), math.cos(self.theta + dtheta))

        vx = dc / dt
        vth = dtheta / dt

        self.publish_odom(t, vx, vth)

        self.last_left_ticks = self.left_ticks
        self.last_right_ticks = self.right_ticks
        self.last_time = t

    def publish_odom(self, stamp_sec, vx, vth):
        msg = Odometry()
        msg.header.stamp.sec = int(stamp_sec)
        msg.header.stamp.nanosec = int((stamp_sec - int(stamp_sec)) * 1e9)
        msg.header.frame_id = self.odom_frame
        msg.child_frame_id = self.base_frame

        msg.pose.pose.position.x = self.x
        msg.pose.pose.position.y = self.y
        msg.pose.pose.position.z = 0.0

        q = quaternion_from_euler(0.0, 0.0, self.theta)
        msg.pose.pose.orientation.x = q[0]
        msg.pose.pose.orientation.y = q[1]
        msg.pose.pose.orientation.z = q[2]
        msg.pose.pose.orientation.w = q[3]

        msg.twist.twist.linear.x = vx
        msg.twist.twist.angular.z = vth

        self.odom_pub.publish(msg)

        if self.publish_tf_flag:
            t = TransformStamped()
            t.header = msg.header
            t.child_frame_id = self.base_frame
            t.transform.translation.x = self.x
            t.transform.translation.y = self.y
            t.transform.translation.z = 0.0
            t.transform.rotation = msg.pose.pose.orientation
            self.tf_broadcaster.sendTransform(t)


def main(args=None):
    rclpy.init(args=args)
    node = RMCSOdom()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
