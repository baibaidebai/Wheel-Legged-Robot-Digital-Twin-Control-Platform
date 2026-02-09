#!/usr/bin/env python3
"""
快速启动脚本

最小化配置，快速启动基本功能用于开发和测试。
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """生成快速启动描述"""
    
    # 启动参数
    declare_sim_mode = DeclareLaunchArgument(
        'sim_mode',
        default_value='mujoco',
        description='Simulation backend: gazebo or mujoco'
    )
    
    declare_enable_gui = DeclareLaunchArgument(
        'enable_gui',
        default_value='true',
        description='Enable GUI'
    )
    
    sim_mode = LaunchConfiguration('sim_mode')
    enable_gui = LaunchConfiguration('enable_gui')
    
    # 最小节点集
    nodes = [
        LogInfo(msg='========== Quick Start Mode =========='),
        
        # 关节控制器
        Node(
            package='wheel_legged_control',
            executable='joint_controller_node',
            name='joint_controller',
            output='screen',
            parameters=[{'use_sim_time': False}]
        ),
        
        # IMU仿真器
        Node(
            package='wheel_legged_control',
            executable='imu_simulator_node',
            name='imu_simulator',
            output='screen',
            parameters=[{'use_sim_time': False}]
        ),
    ]
    
    ld = LaunchDescription()
    ld.add_action(declare_sim_mode)
    ld.add_action(declare_enable_gui)
    
    for node in nodes:
        ld.add_action(node)
    
    return ld
