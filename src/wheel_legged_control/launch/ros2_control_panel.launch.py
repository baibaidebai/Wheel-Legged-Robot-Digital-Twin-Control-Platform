#!/usr/bin/env python3
"""
ROS2集成控制面板启动文件

启动轮腿机器人的ROS2集成控制面板，包括：
- ROS2集成控制面板GUI
- 关节控制器节点
- IMU发布器节点
- 数字孪生映射器服务
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, TimerAction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
import os


def generate_launch_description():
    """生成启动描述"""
    
    # 声明启动参数
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation time'
    )
    
    robot_name_arg = DeclareLaunchArgument(
        'robot_name',
        default_value='wheel_legged_robot',
        description='Robot name'
    )
    
    config_file_arg = DeclareLaunchArgument(
        'config_file',
        default_value=PathJoinSubstitution([
            FindPackageShare('wheel_legged_control'),
            'config',
            'joint_controller.yaml'
        ]),
        description='Path to joint controller config file'
    )
    
    # 获取参数值
    use_sim_time = LaunchConfiguration('use_sim_time')
    robot_name = LaunchConfiguration('robot_name')
    config_file = LaunchConfiguration('config_file')
    
    # 关节控制器节点
    joint_controller_node = Node(
        package='wheel_legged_control',
        executable='joint_controller_node',
        name='joint_controller',
        parameters=[
            config_file,
            {'use_sim_time': use_sim_time}
        ],
        output='screen',
        emulate_tty=True
    )
    
    # IMU发布器节点
    imu_publisher_node = Node(
        package='wheel_legged_control',
        executable='imu_publisher_node',
        name='imu_publisher',
        parameters=[
            {'use_sim_time': use_sim_time},
            {'publish_rate': 100.0},
            {'frame_id': 'imu_link'}
        ],
        output='screen',
        emulate_tty=True
    )
    
    # 数字孪生映射器服务节点（如果需要）
    # digital_twin_service_node = Node(
    #     package='wheel_legged_control',
    #     executable='digital_twin_service',
    #     name='digital_twin_mapper',
    #     parameters=[
    #         {'use_sim_time': use_sim_time},
    #         {'urdf_file': 'src/model/RM_Serial_Wheeled-leg_Robot/urdf/RM_Serial_Wheeled-leg_Robot.urdf'}
    #     ],
    #     output='screen',
    #     emulate_tty=True
    # )
    
    # ROS2集成控制面板（延迟启动以确保其他节点先启动）
    control_panel_action = TimerAction(
        period=2.0,  # 延迟2秒启动
        actions=[
            ExecuteProcess(
                cmd=[
                    'python3',
                    PathJoinSubstitution([
                        FindPackageShare('wheel_legged_control'),
                        'wheel_legged_control',
                        'gui',
                        'ros2_control_panel.py'
                    ])
                ],
                output='screen',
                emulate_tty=True,
                shell=True
            )
        ]
    )
    
    return LaunchDescription([
        # 启动参数
        use_sim_time_arg,
        robot_name_arg,
        config_file_arg,
        
        # 节点
        joint_controller_node,
        imu_publisher_node,
        # digital_twin_service_node,  # 暂时注释掉
        
        # GUI（延迟启动）
        control_panel_action,
    ])