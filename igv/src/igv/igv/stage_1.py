#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
import cv2
import numpy as np
import math

from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped


class BEVLaneFollower(Node):

    def __init__(self):

        super().__init__("bev_lane_follower")

        self.bridge = CvBridge()

        self.image_sub = self.create_subscription(
            Image,
            "/camera/color/image_raw",
            self.image_callback,
            10
        )

        self.path_pub = self.create_publisher(Path,"/lane_path",10)

        self.prev_left = None
        self.prev_right = None

        # Perspective transform points (example values)
        src = np.float32([
            [200,720],
            [1080,720],
            [550,450],
            [730,450]
        ])

        dst = np.float32([
            [300,720],
            [980,720],
            [300,0],
            [980,0]
        ])

        self.H = cv2.getPerspectiveTransform(src,dst)

    # ------------------------------------------------

    def image_callback(self,msg):

        frame = self.bridge.imgmsg_to_cv2(msg,"bgr8")

        bev = cv2.warpPerspective(frame,self.H,(1280,720))

        mask = self.lane_mask(bev)

        left,right = self.sliding_window(mask)

        if left is None or right is None:
            return

        centerline = (left + right) / 2

        path = self.build_path(centerline)

        self.path_pub.publish(path)

    # ------------------------------------------------

    def lane_mask(self,frame):

        hsv = cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)

        yellow_low = np.array([15,100,100])
        yellow_high = np.array([35,255,255])

        black_low = np.array([0,0,0])
        black_high = np.array([180,255,60])

        mask_y = cv2.inRange(hsv,yellow_low,yellow_high)
        mask_b = cv2.inRange(hsv,black_low,black_high)

        mask = cv2.bitwise_or(mask_y,mask_b)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT,(5,5))
        mask = cv2.morphologyEx(mask,cv2.MORPH_CLOSE,kernel)

        return mask

    # ------------------------------------------------

    def sliding_window(self,mask):

        histogram = np.sum(mask[mask.shape[0]//2:,:],axis=0)

        midpoint = histogram.shape[0]//2
        leftx = np.argmax(histogram[:midpoint])
        rightx = np.argmax(histogram[midpoint:]) + midpoint

        n_windows = 9
        window_height = mask.shape[0]//n_windows
        margin = 80
        minpix = 50

        nonzero = mask.nonzero()
        nonzeroy = np.array(nonzero[0])
        nonzerox = np.array(nonzero[1])

        left_lane_inds = []
        right_lane_inds = []

        for window in range(n_windows):

            win_y_low = mask.shape[0] - (window+1)*window_height
            win_y_high = mask.shape[0] - window*window_height

            win_xleft_low = leftx - margin
            win_xleft_high = leftx + margin

            win_xright_low = rightx - margin
            win_xright_high = rightx + margin

            good_left = ((nonzeroy >= win_y_low) &
                         (nonzeroy < win_y_high) &
                         (nonzerox >= win_xleft_low) &
                         (nonzerox < win_xleft_high)).nonzero()[0]

            good_right = ((nonzeroy >= win_y_low) &
                          (nonzeroy < win_y_high) &
                          (nonzerox >= win_xright_low) &
                          (nonzerox < win_xright_high)).nonzero()[0]

            left_lane_inds.append(good_left)
            right_lane_inds.append(good_right)

            if len(good_left) > minpix:
                leftx = int(np.mean(nonzerox[good_left]))

            if len(good_right) > minpix:
                rightx = int(np.mean(nonzerox[good_right]))

        left_lane_inds = np.concatenate(left_lane_inds)
        right_lane_inds = np.concatenate(right_lane_inds)

        leftx = nonzerox[left_lane_inds]
        lefty = nonzeroy[left_lane_inds]

        rightx = nonzerox[right_lane_inds]
        righty = nonzeroy[right_lane_inds]

        if len(leftx) < 50 or len(rightx) < 50:
            return None,None

        left_fit = np.polyfit(lefty,leftx,2)
        right_fit = np.polyfit(righty,rightx,2)

        ploty = np.linspace(0,mask.shape[0]-1,50)

        left_fitx = left_fit[0]*ploty**2 + left_fit[1]*ploty + left_fit[2]
        right_fitx = right_fit[0]*ploty**2 + right_fit[1]*ploty + right_fit[2]

        left = np.vstack((left_fitx,ploty)).T
        right = np.vstack((right_fitx,ploty)).T

        return left,right

    # ------------------------------------------------

    def build_path(self,centerline):

        path = Path()

        path.header.frame_id = "base_link"
        path.header.stamp = self.get_clock().now().to_msg()

        for i in range(len(centerline)-1):

            p = centerline[i]
            p2 = centerline[i+1]

            pose = PoseStamped()

            pose.pose.position.x = float(p[1]/100)
            pose.pose.position.y = float((p[0]-640)/100)
            pose.pose.position.z = 0.0

            yaw = math.atan2(p2[1]-p[1],p2[0]-p[0])

            pose.pose.orientation.z = math.sin(yaw/2)
            pose.pose.orientation.w = math.cos(yaw/2)

            path.poses.append(pose)

        return path


def main():

    rclpy.init()

    node = BEVLaneFollower()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == "__main__":
    main()