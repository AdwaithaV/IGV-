#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image, CompressedImage
from cv_bridge import CvBridge, CvBridgeError
import numpy as np
import cv2
import sys

class ShowImage(Node):
    def __init__(self, topic_raw='/camera/color/image_raw', topic_comp=None):
        super().__init__('show_oakd_image_dbg')
        self.bridge = CvBridge()
        self.frame = None
        self.last_stamp = None

        # subscribe to raw Image
        self.sub_raw = self.create_subscription(
            Image, topic_raw, self.cb_image, qos_profile_sensor_data)
        self.get_logger().info(f"Subscribed to raw Image topic: {topic_raw}")

        # optionally subscribe to compressed if you passed a compressed topic
        if topic_comp:
            self.sub_comp = self.create_subscription(
                CompressedImage, topic_comp, self.cb_compressed, qos_profile_sensor_data)
            self.get_logger().info(f"Subscribed to CompressedImage topic: {topic_comp}")

        # timer to show frame in main thread (prevents some GUI issues)
        self.timer = self.create_timer(0.03, self.timer_cb)  # ~30 Hz

    def cb_image(self, msg: Image):
        try:
            # attempt a safe conversion; do not assume bgr8
            encoding = msg.encoding if hasattr(msg, 'encoding') else 'unknown'
            self.get_logger().debug(f"Raw Image received. encoding={encoding}, size={msg.width}x{msg.height}")
            # try common color encodings, fallback to whatever bridge returns
            if encoding in ('rgb8', 'rgb16'):
                cv_img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='rgb8')
                cv_img = cv2.cvtColor(cv_img, cv2.COLOR_RGB2BGR)
            else:
                cv_img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            self.frame = cv_img
        except CvBridgeError as e:
            self.get_logger().error(f"cv_bridge error (raw): {e}")

    def cb_compressed(self, msg: CompressedImage):
        try:
            self.get_logger().debug(f"CompressedImage received. format={msg.format}")
            np_arr = np.frombuffer(msg.data, np.uint8)
            cv_img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if cv_img is None:
                self.get_logger().error("cv2.imdecode returned None")
                return
            self.frame = cv_img
        except Exception as e:
            self.get_logger().error(f"error decoding compressed image: {e}")

    def timer_cb(self):
        if self.frame is None:
            return
        cv2.imshow('OAK-D', self.frame)
        # use small waitKey to keep GUI responsive
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            self.get_logger().info("ESC pressed, shutting down")
            rclpy.shutdown()

def main(argv=None):
    rclpy.init(args=argv or [])
    # allow user to pass topics as CLI args
    raw_topic = '/camera/color/image_raw'
    comp_topic = None
    if len(sys.argv) > 1:
        raw_topic = sys.argv[1]
    if len(sys.argv) > 2:
        comp_topic = sys.argv[2]

    node = ShowImage(topic_raw=raw_topic, topic_comp=comp_topic)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    cv2.destroyAllWindows()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()