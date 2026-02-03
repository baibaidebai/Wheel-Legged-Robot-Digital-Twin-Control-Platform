#!/usr/bin/env python3
"""
轮腿机器人孪生控制系统主启动文件

启动完整的仿真控制系统，包括Gazebo仿真、控制器和监控界面。
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """生成系统启动描述"""
    
    # 包路径
    pkg_wheel_legged_control = FindPackageShare(package='wheel_legged_control').find('wheel_legged_control')
    
    # 启动参数
    use_sim_time = LaunchConfiguration('use_sim_time')
    enable_gui = LaunchConfiguration('enable_gui')
    
    # 声明启动参数
    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true'
    )
    
    declare_enable_gui_cmd = DeclareLaunchArgument(
        'enable_gui',
        default_value='true',
        description='Enable control panel GUI if true'
    )
    
    # 包含Gazebo仿真启动文件
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([pkg_wheel_legged_control, 'launch', 'gazebo_simulation.launch.py'])
        ]),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'robot_name': 'wheel_legged_robot',
            'x_pose': '0.0',
            'y_pose': '0.0',
            'z_pose': '0.2'
        }.items()
    )
    
    # 关节控制器节点
    joint_controller_node = Node(
        package='wheel_legged_control',
        executable='joint_controller_node',
        name='joint_controller_node',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time
        }]
    )
    
    # IMU仿真器节点
    imu_simulator_node = Node(
        package='wheel_legged_control',
        executable='imu_simulator_node',
        name='imu_simulator_node',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time
        }]
    )
    
    # 状态同步器节点
    state_synchronizer_node = Node(
        package='wheel_legged_control',
        executable='state_synchronizer_node',
        name='state_synchronizer_node',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time
        }]
    )
    
    # 控制面板（延迟启动，等待其他节点就绪）
    control_panel_node = TimerAction(
        period=5.0,  # 延迟5秒启动
        actions=[
            Node(
                package='wheel_legged_control',
                executable='control_panel',
                name='control_panel',
                output='screen',
                parameters=[{
                    'use_sim_time': use_sim_time
                }],
                condition=IfCondition(enable_gui)
            )
        ]
    )
    
    # 创建启动描述
    ld = LaunchDescription()
    
    # 添加启动参数声明
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_enable_gui_cmd)
    
    # 添加启动项
    ld.add_action(gazebo_launch)
    
    # 延迟启动控制节点，等待Gazebo就绪
    ld.add_action(TimerAction(
        period=3.0,
        actions=[
            joint_controller_node,
            imu_simulator_node,
            state_synchronizer_node
        ]
    ))
    
    ld.add_action(control_panel_node)
    
    return ld


if __name__ == '__main__':
    generate_launch_description()