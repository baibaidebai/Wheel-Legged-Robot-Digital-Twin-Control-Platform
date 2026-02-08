#!/usr/bin/env python3
"""
状态同步器启动文件

启动状态同步器节点，用于虚实状态同步仿真。
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """生成状态同步器启动描述"""
    
    # 包路径
    pkg_wheel_legged_control = FindPackageShare(package='wheel_legged_control').find('wheel_legged_control')
    
    # 配置文件路径
    config_file = PathJoinSubstitution([
        pkg_wheel_legged_control,
        'config',
        'state_synchronizer.yaml'
    ])
    
    # 启动参数
    use_sim_time = LaunchConfiguration('use_sim_time')
    config_file_path = LaunchConfiguration('config_file')
    
    # 声明启动参数
    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true'
    )
    
    declare_config_file_cmd = DeclareLaunchArgument(
        'config_file',
        default_value=config_file,
        description='Path to state synchronizer configuration file'
    )
    
    # 状态同步器节点
    state_synchronizer_node = Node(
        package='wheel_legged_control',
        executable='state_synchronizer_node',
        name='state_synchronizer_node',
        output='screen',
        parameters=[
            config_file_path,
            {
                'use_sim_time': use_sim_time
            }
        ],
        remappings=[
            # 虚拟状态话题映射
            ('/virtual/joint_states', '/gazebo/joint_states'),
            ('/virtual/imu/data', '/gazebo/imu/data'),
            # 物理状态话题映射（模拟）
            ('/joint_states', '/simulated_physical/joint_states'),
            ('/imu/data', '/simulated_physical/imu/data')
        ]
    )
    
    # 创建启动描述
    ld = LaunchDescription()
    
    # 添加启动参数声明
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_config_file_cmd)
    
    # 添加节点
    ld.add_action(state_synchronizer_node)
    
    return ld


if __name__ == '__main__':
    generate_launch_description()