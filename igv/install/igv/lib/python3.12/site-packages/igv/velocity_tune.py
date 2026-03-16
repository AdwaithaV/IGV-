import geometry_msgs
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32

class VelocityTune(Node):
    def __init__(self):
        super().__init__('velocity_tune')
        self.x=0.0
        self.y=0.0
        self.z=0.0
        self.r=0.0
        self.p=0.0
        self.y_=0.0
        self.speed_factor=1.0
        self.sub=self.create_subscription(Twist,'/tux_cmd_vel',self.cmd_vel_cb,10)
        self.sub_1=self.create_subscription(Float32,'/terrian_speed_factor',self.terrian_speed_factor_cb,10)
        self.pub=self.create_publisher(Twist,'/cmd_vel',10)
        self.get_logger().info('velocity_tune started')
        self.timer=self.create_timer(0.1,self.tune)

    def cmd_vel_cb(self,msg:Twist):
         self.x=msg.linear.x
         self.y=msg.linear.y
         self.z=msg.linear.z
         self.r=msg.angular.x
         self.p=msg.angular.y
         self.y_=msg.angular.z
         
    def terrian_speed_factor_cb(self,msg:Float32):
        self.get_logger().info(f"terrian_speed_factor: {msg.data}")
        self.speed_factor=msg.data

    
    def tune(self):
        msg=Twist()
        msg.linear.x=self.x*self.speed_factor
        msg.linear.y=self.y*self.speed_factor
        msg.linear.z=self.z*self.speed_factor
        msg.angular.x=self.r*self.speed_factor
        msg.angular.y=self.p*self.speed_factor
        msg.angular.z=self.y_*self.speed_factor
        self.pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node=VelocityTune()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()