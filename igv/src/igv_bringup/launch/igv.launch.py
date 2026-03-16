from launch import LaunchDescription
from launch.actions import ExecuteProcess, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    lidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('ydlidar_ros2_driver'),
                'launch',
                'ydlidar_launch.py'
            )
        )
    )

    microros_agent = ExecuteProcess(
        cmd=[
            'docker','run','--rm',
            '--net=host',
            '--device=/dev/ttyACM0',
            '--privileged',
            'microros/micro-ros-agent:latest',
            'micro-ros-agent','serial',
            '--dev','/dev/ttyACM0','-b','115200'
        ],
        output='screen'
    )

    return LaunchDescription([

        Node(
            package='depthai_ros_driver',
            executable='camera_node',
            name='camera_node',
            parameters=[{
                'driver.i_publish_tf_from_calibration': True,
                'driver.i_tf_base_frame': 'base_link',
                'driver.i_tf_camera_frame': 'camera_link',
                'driver.i_tf_parent_frame': 'base_footprint',
                'driver.i_tf_cam_pos_x': 0.0,
                'driver.i_tf_cam_pos_y': 0.0,
                'driver.i_tf_cam_pos_z': 0.0,
                'driver.i_tf_cam_rot_roll': 0.0,
                'driver.i_tf_cam_rot_pitch': 0.0,
                'driver.i_tf_cam_rot_yaw': 0.0,
            }]
        ),

        Node(
            package='igv',
            executable='camera_node',
            name='frameid_republisher'
        ),

        lidar_launch,

        Node(
            package='igv',
            executable='velocity_tune',
            name='velocity_tune'
        ),
        microros_agent
    ])