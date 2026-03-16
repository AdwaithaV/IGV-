#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from std_msgs.msg import String, Bool
from geometry_msgs.msg import Twist

from collections import deque


class BehaviorManager(Node):

    def __init__(self):

        super().__init__('behavior_manager')

        # ---- robot state ----
        self.state = "LANE_FOLLOW"
        self.terrain = "flat"
        self.obstacle = False

        # smoothing buffer
        self.terrain_buffer = deque(maxlen=5)

        # velocity limits
        self.max_vel = 1.0
        self.max_turn = 1.2

        # subscriptions
        self.create_subscription(String, '/terrain_type', self.terrain_cb, 10)
        self.create_subscription(Bool, '/obstacle_detected', self.obstacle_cb, 10)
        self.create_subscription(Twist, '/cmd_vel', self.cmd_cb, 10)

        # publisher
        self.pub = self.create_publisher(Twist, '/cmd_vel_final', 10)

        self.get_logger().info("Behavior manager started")

    # ---------------- Terrain ----------------

    def terrain_cb(self, msg):

        self.terrain_buffer.append(msg.data)

        # majority vote filter
        terrain = max(set(self.terrain_buffer), key=self.terrain_buffer.count)

        self.terrain = terrain

        self.update_state()

    # ---------------- Obstacle ----------------

    def obstacle_cb(self, msg):

        self.obstacle = msg.data

        self.update_state()

    # ---------------- State Machine ----------------

    def update_state(self):

        prev_state = self.state

        if self.obstacle:
            self.state = "OBSTACLE_AVOID"

        elif self.terrain == "ramp_up":
            self.state = "RAMP_UP"

        elif self.terrain == "ramp_down":
            self.state = "RAMP_DOWN"

        elif self.terrain == "bridge":
            self.state = "BRIDGE"

        elif self.terrain == "rough":
            self.state = "ROUGH"

        else:
            self.state = "LANE_FOLLOW"

        if prev_state != self.state:
            self.get_logger().info(f"State changed: {prev_state} -> {self.state}")

    # ---------------- Command Handling ----------------

    def cmd_cb(self, msg):

        cmd = Twist()

        linear = msg.linear.x
        angular = msg.angular.z

        # ----- state behaviour -----

        if self.state == "LANE_FOLLOW":

            max_vel = 1.0
            turn_gain = 1.0

        elif self.state == "RAMP_UP":

            max_vel = 0.8
            turn_gain = 0.9

        elif self.state == "RAMP_DOWN":

            max_vel = 0.6
            turn_gain = 0.8

        elif self.state == "BRIDGE":

            max_vel = 0.5
            turn_gain = 0.6

        elif self.state == "ROUGH":

            max_vel = 0.4
            turn_gain = 0.7

        elif self.state == "OBSTACLE_AVOID":

            max_vel = 0.3
            turn_gain = 1.0

        else:

            max_vel = 0.5
            turn_gain = 1.0

        # ----- apply limits -----

        linear = min(linear, max_vel)

        angular = angular * turn_gain

        angular = max(min(angular, self.max_turn), -self.max_turn)

        # publish
        cmd.linear.x = linear
        cmd.angular.z = angular

        self.pub.publish(cmd)


def main(args=None):

    rclpy.init(args=args)

    node = BehaviorManager()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()