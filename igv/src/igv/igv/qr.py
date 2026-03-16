import cv2
import rclpy
from rclpy.node import Node
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from std_msgs.msg import String
import numpy as np
from PIL import Image as IP

class QRScanner(Node):

    def __init__(self):
        super().__init__('qr_scanner')
        
        self.bridge = CvBridge()
        self.image_ = self.create_subscription(Image, "image/raw",self.process_frame,10)
        self.qr_text_pub = self.create_publisher(String, 'qr_text', 10)


        self.detector = cv2.QRCodeDetector()
        self.cap = self.image_

        # if not self.cap.isOpened():
        #     self.get_logger().error("Could not open camera.")
        # else:
        #     self.get_logger().info("Camera opened using native OpenCV detector.")

        # Timer for periodic frame reading
        # self.timer = self.create_timer(0.03, self.process_frame(self.msg_1))  # ~30 FPS

    def process_frame(self,msg_1:Image):
        frame=self.bridge.imgmsg_to_cv2(msg_1,desired_encoding='bgr8')
    
        retval, decoded_info, points, _ = self.detector.detectAndDecodeMulti(frame)

        if retval:
            for s, p in zip(decoded_info, points):
                if s:
                    self.get_logger().info(f"Found QR Code: {s}")
                    # publish detected string over ROS
                    msg = String()
                    msg.data = s
                    self.qr_text_pub.publish(msg)

                    pts = p.astype(np.int32).reshape(-1, 1, 2)
                    cv2.polylines(frame, [pts], True, (0,255,0), 2)
                    cv2.putText(frame, s, (pts[0][0][0], pts[0][0][1]-10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)

        # publish camera frame to ROS topic
        # img_msg = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")
        # self.publisher_.publish(img_msg)

        cv2.imshow("QR Scanner", frame)
        cv2.waitKey(1)

def main(args=None):
    rclpy.init(args=args)
    node=QRScanner()
    rclpy.spin(node)
    cv2.destroyAllWindows()
    rclpy.shutdown()