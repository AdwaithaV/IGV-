import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
import numpy as np
from collections import deque

class LidarFilter(Node):
    def __init__(self):
        super().__init__('lidar_filter')
        self.buf_len = 5
        self.ring = deque(maxlen=self.buf_len)
        self.sub = self.create_subscription(LaserScan, '/scan', self.cb, 10)
        self.pub = self.create_publisher(LaserScan, '/scan_filtered', 10)
        self.get_logger().info('lidar_filter started')

    def cb(self, scan: LaserScan):
        ranges = np.array(scan.ranges, dtype=np.float32)
        self.ring.append(ranges)
        stacked = np.vstack(self.ring)
        med = np.median(stacked, axis=0)
        new = LaserScan()
        new.header = scan.header
        new.angle_min = scan.angle_min
        new.angle_max = scan.angle_max
        new.angle_increment = scan.angle_increment
        new.time_increment = scan.time_increment
        new.scan_time = scan.scan_time
        new.range_min = scan.range_min
        new.range_max = scan.range_max
        new.ranges = med.tolist()
        new.intensities = scan.intensities
        self.pub.publish(new)

def main(args=None):
    rclpy.init(args=args)
    node = LidarFilter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()