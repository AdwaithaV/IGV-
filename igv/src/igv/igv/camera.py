#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo

class FrameIdRepublisher(Node):
    def __init__(self):
        super().__init__('frameid_republisher')
        self.new_frame = 'camera_link'   # <- set to your URDF camera link
        self.sub_img = self.create_subscription(Image, '/camera_node/rgb/image_raw', self.img_cb, 10)
        self.sub_info = self.create_subscription(CameraInfo, '/camera_node/rgb/camera_info', self.info_cb, 10)
        self.pub_img = self.create_publisher(Image, '/camera_node/rgb/image_raw_fixed', 10)
        self.pub_info = self.create_publisher(CameraInfo, '/camera_node/rgb/camera_info_fixed', 10)

    def img_cb(self, msg):
        msg.header.frame_id = self.new_frame
        self.pub_img.publish(msg)

    def info_cb(self, msg):
        msg.header.frame_id = self.new_frame
        self.pub_info.publish(msg)

def main():
    rclpy.init()
    node = FrameIdRepublisher()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()