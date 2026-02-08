#!/usr/bin/env python3
"""
关节控制器启动文件
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    """生成启动描述"""
    
    # 获取包路径
    pkg_share = FindPackageShare('wheel_legged_control')
    
    # 声明启动参数
    config_file_arg = DeclareLaunchArgument(
        'config_file',
        default_value=PathJoinSubstitution([
            pkg_share, 'config', 'joint_controller.yaml'
        ]),
        description='关节控制器配置文件路径'
    )
    
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='是否使用仿真时间'
    )
    
    log_level_arg = DeclareLaunchArgument(
        'log_level',
        default_value='info',
        description='日志级别'
    )
    
    # 关节控制器节点
    joint_controller_node = Node(
        package='wheel_legged_control',
        executable='joint_controller',
        name='joint_controller',
        parameters=[
            LaunchConfiguration('config_file'),
            {'use_sim_time': LaunchConfiguration('use_sim_time')}
        ],
        arguments=['--ros-args', '--log-level', LaunchConfiguration('log_level')],
        output='screen',
        emulate_tty=True,
        respawn=True,
        respawn_delay=2.0
    )
    
    # 启动信息
    launch_info = LogInfo(
        msg=[
            '启动关节控制器节点...\n',
            '配置文件: ', LaunchConfiguration('config_file'), '\n',
            '仿真时间: ', LaunchConfiguration('use_sim_time'), '\n',
            '日志级别: ', LaunchConfiguration('log_level')
        ]
    )
    
    return LaunchDescription([
        config_file_arg,
        use_sim_time_arg,
        log_level_arg,
        launch_info,
        joint_controller_node
    ])


if __name__ == '__main__':
    generate_launch_description()