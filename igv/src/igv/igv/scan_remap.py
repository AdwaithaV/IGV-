import rclpy 
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
import numpy as np  

class ScanRemap(Node):
    def __init__(self):
        super().__init__('scan_remap')
        self.create_subscription(LaserScan,'/scan',self.re,10)
        self.pub=self.create_publisher(LaserScan,'/scan_raw',10)
        self.get_logger().info('scan_remap started')

    def re(self,msg:LaserScan):
        new=LaserScan()
        new.header=msg.header
        new.angle_min=msg.angle_min
        new.angle_max=msg.angle_max
        new.angle_increment=msg.angle_increment
        new.time_increment=msg.time_increment
        new.scan_time=msg.scan_time
        new.range_min=msg.range_min
        new.range_max=msg.range_max
        new.ranges=np.array(msg.ranges, dtype=np.float32).tolist()
        new.intensities=msg.intensities
        self.pub.publish(new)

def main(args=None):
    rclpy.init(args=args)
    node = ScanRemap()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()