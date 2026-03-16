# gj_description/launch/gj_launch.py
import os

from launch import LaunchDescription
from launch.substitutions import Command
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg_share = get_package_share_directory('gj_description')
    urdf_path = os.path.join(pkg_share, 'urdf', 'igv.urdf')
    rviz_path = os.path.join(pkg_share, 'rviz', 'igv.rviz')

    # robot_description will be populated by running xacro on igv.urdf
    rsp_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': Command(['xacro ', urdf_path])
        }]
    )

    jsp_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_path],
        parameters=[{'use_sim_time': True}],
    )

    return LaunchDescription([
        rsp_node,
        jsp_node,
        rviz_node,
    ])