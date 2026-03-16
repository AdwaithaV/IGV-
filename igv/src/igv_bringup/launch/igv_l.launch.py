from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    pkg_share = get_package_share_directory('igv')

    rviz_config = os.path.join(
        pkg_share,
        'rviz',
        'urdf.rviz'
    )

    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('slam_toolbox'),
                'launch',
                'async_slam.launch.py'
            )
        )
    )

    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('nav2_bringup'),
                'launch',
                'bringup_launch.py'
            )
        ),
        launch_arguments={
            'use_sim_time': 'false',
            'autostart': 'true',
            'params_file': os.path.join(
                get_package_share_directory('igv'),
                'config',
                'nav2_params.yaml','slam.yaml'
            )
        }.items()
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config]
    )
    
    return LaunchDescription([

        

        Node(
            package='igv',
            executable='fusion',
            name='fusion'
        ),

        Node(
            package='igv',
            executable='remap_scan',
            name='remap_scan'
        ),

        Node(
            package='igv',
            executable='terrain',
            name='terrain'
        ),

        Node(
            package='igv',
            executable='lidar_filter',
            name='lidar_filter'
        ),

        Node(
            package='igv',
            executable='path',
            name='path'
        ),
        slam_launch,
        nav2_launch,
        rviz_node

    ])