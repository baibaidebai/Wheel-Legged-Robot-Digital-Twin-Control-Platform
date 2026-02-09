#!/usr/bin/env python3
"""
完整系统启动文件 - 增强版

协调所有节点启动，包含依赖关系管理、参数传递和环境配置。
支持多种启动模式和配置选项。
"""

import os
from pathlib import Path
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
    ExecuteProcess,
    RegisterEventHandler,
    LogInfo,
    EmitEvent,
    GroupAction
)
from launch.conditions import IfCondition, UnlessCondition
from launch.event_handlers import OnProcessStart, OnProcessExit
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    LaunchConfiguration,
    PathJoinSubstitution,
    PythonExpression,
    TextSubstitution
)
from launch_ros.actions import Node, SetParameter
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """生成完整系统启动描述"""
    
    # ========== 包路径 ==========
    pkg_share = FindPackageShare(package='wheel_legged_control').find('wheel_legged_control')
    
    # ========== 启动参数声明 ==========
    
    # 仿真模式
    declare_sim_mode = DeclareLaunchArgument(
        'sim_mode',
        default_value='gazebo',
        description='Simulation mode: gazebo, mujoco, or none (hardware)',
        choices=['gazebo', 'mujoco', 'none']
    )
    
    # 使用仿真时间
    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation clock if true'
    )
    
    # 启用GUI
    declare_enable_gui = DeclareLaunchArgument(
        'enable_gui',
        default_value='true',
        description='Enable control panel GUI'
    )
    
    # 启用可视化
    declare_enable_rviz = DeclareLaunchArgument(
        'enable_rviz',
        default_value='false',
        description='Enable RViz visualization'
    )
    
    # 机器人模型
    declare_robot_model = DeclareLaunchArgument(
        'robot_model',
        default_value='wheel_legged_robot',
        description='Robot model name'
    )
    
    # 配置文件
    declare_config_file = DeclareLaunchArgument(
        'config_file',
        default_value='',
        description='Path to configuration file (optional)'
    )
    
    # 日志级别
    declare_log_level = DeclareLaunchArgument(
        'log_level',
        default_value='info',
        description='Logging level: debug, info, warn, error',
        choices=['debug', 'info', 'warn', 'error']
    )
    
    # 启用数据记录
    declare_enable_recording = DeclareLaunchArgument(
        'enable_recording',
        default_value='false',
        description='Enable data recording'
    )
    
    # 启用算法管理器
    declare_enable_algorithm_manager = DeclareLaunchArgument(
        'enable_algorithm_manager',
        default_value='false',
        description='Enable algorithm manager for RL/control experiments'
    )
    
    # 机器人初始位置
    declare_x_pose = DeclareLaunchArgument('x_pose', default_value='0.0')
    declare_y_pose = DeclareLaunchArgument('y_pose', default_value='0.0')
    declare_z_pose = DeclareLaunchArgument('z_pose', default_value='0.2')
    
    # ========== 启动配置 ==========
    sim_mode = LaunchConfiguration('sim_mode')
    use_sim_time = LaunchConfiguration('use_sim_time')
    enable_gui = LaunchConfiguration('enable_gui')
    enable_rviz = LaunchConfiguration('enable_rviz')
    robot_model = LaunchConfiguration('robot_model')
    config_file = LaunchConfiguration('config_file')
    log_level = LaunchConfiguration('log_level')
    enable_recording = LaunchConfiguration('enable_recording')
    enable_algorithm_manager = LaunchConfiguration('enable_algorithm_manager')
    x_pose = LaunchConfiguration('x_pose')
    y_pose = LaunchConfiguration('y_pose')
    z_pose = LaunchConfiguration('z_pose')
    
    # ========== 全局参数设置 ==========
    set_use_sim_time = SetParameter(name='use_sim_time', value=use_sim_time)
    
    # ========== 仿真环境启动 ==========
    
    # Gazebo仿真
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([pkg_share, 'launch', 'gazebo_simulation.launch.py'])
        ]),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'robot_name': robot_model,
            'x_pose': x_pose,
            'y_pose': y_pose,
            'z_pose': z_pose
        }.items(),
        condition=IfCondition(PythonExpression(["'", sim_mode, "' == 'gazebo'"]))
    )
    
    # MuJoCo仿真（占位符，需要实现）
    mujoco_info = LogInfo(
        msg='MuJoCo simulation mode selected. Launch MuJoCo separately.',
        condition=IfCondition(PythonExpression(["'", sim_mode, "' == 'mujoco'"]))
    )
    
    # ========== 核心控制节点 ==========
    
    # 关节控制器
    joint_controller_node = Node(
        package='wheel_legged_control',
        executable='joint_controller_node',
        name='joint_controller',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'robot_model': robot_model,
            'log_level': log_level
        }],
        arguments=['--ros-args', '--log-level', log_level],
        respawn=True,
        respawn_delay=2.0
    )
    
    # IMU仿真器
    imu_simulator_node = Node(
        package='wheel_legged_control',
        executable='imu_simulator_node',
        name='imu_simulator',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'publish_rate': 100.0,
            'log_level': log_level
        }],
        arguments=['--ros-args', '--log-level', log_level],
        respawn=True,
        respawn_delay=2.0
    )
    
    # 状态同步器
    state_synchronizer_node = Node(
        package='wheel_legged_control',
        executable='state_synchronizer_node',
        name='state_synchronizer',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'sync_rate': 50.0,
            'log_level': log_level
        }],
        arguments=['--ros-args', '--log-level', log_level],
        respawn=True,
        respawn_delay=2.0
    )
    
    # ========== 可选节点 ==========
    
    # 数据记录器
    data_recorder_node = Node(
        package='wheel_legged_control',
        executable='data_recorder_node',
        name='data_recorder',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'output_dir': '/tmp/wheel_legged_recordings',
            'log_level': log_level
        }],
        arguments=['--ros-args', '--log-level', log_level],
        condition=IfCondition(enable_recording)
    )
    
    # 算法管理器
    algorithm_manager_node = Node(
        package='wheel_legged_control',
        executable='algorithm_manager_node',
        name='algorithm_manager',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'log_level': log_level
        }],
        arguments=['--ros-args', '--log-level', log_level],
        condition=IfCondition(enable_algorithm_manager)
    )
    
    # 控制面板GUI
    control_panel_node = Node(
        package='wheel_legged_control',
        executable='control_panel',
        name='control_panel',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'log_level': log_level
        }],
        condition=IfCondition(enable_gui)
    )
    
    # RViz可视化
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', PathJoinSubstitution([pkg_share, 'config', 'robot_view.rviz'])],
        condition=IfCondition(enable_rviz)
    )
    
    # ========== 启动序列编排 ==========
    
    # 阶段1: 启动仿真环境
    stage1_simulation = GroupAction([
        LogInfo(msg='========== Stage 1: Starting Simulation Environment =========='),
        gazebo_launch,
        mujoco_info
    ])
    
    # 阶段2: 启动核心控制节点（延迟3秒，等待仿真就绪）
    stage2_control = TimerAction(
        period=3.0,
        actions=[
            LogInfo(msg='========== Stage 2: Starting Core Control Nodes =========='),
            joint_controller_node,
            imu_simulator_node,
            state_synchronizer_node
        ]
    )
    
    # 阶段3: 启动可选节点（延迟5秒）
    stage3_optional = TimerAction(
        period=5.0,
        actions=[
            LogInfo(msg='========== Stage 3: Starting Optional Nodes =========='),
            data_recorder_node,
            algorithm_manager_node
        ]
    )
    
    # 阶段4: 启动用户界面（延迟7秒）
    stage4_ui = TimerAction(
        period=7.0,
        actions=[
            LogInfo(msg='========== Stage 4: Starting User Interface =========='),
            control_panel_node,
            rviz_node,
            LogInfo(msg='========== System Startup Complete ==========')
        ]
    )
    
    # ========== 事件处理 ==========
    
    # 监控关键节点退出
    on_joint_controller_exit = RegisterEventHandler(
        OnProcessExit(
            target_action=joint_controller_node,
            on_exit=[
                LogInfo(msg='Joint controller exited. System may be unstable.'),
            ]
        )
    )
    
    # ========== 构建启动描述 ==========
    ld = LaunchDescription()
    
    # 添加参数声明
    ld.add_action(declare_sim_mode)
    ld.add_action(declare_use_sim_time)
    ld.add_action(declare_enable_gui)
    ld.add_action(declare_enable_rviz)
    ld.add_action(declare_robot_model)
    ld.add_action(declare_config_file)
    ld.add_action(declare_log_level)
    ld.add_action(declare_enable_recording)
    ld.add_action(declare_enable_algorithm_manager)
    ld.add_action(declare_x_pose)
    ld.add_action(declare_y_pose)
    ld.add_action(declare_z_pose)
    
    # 添加全局参数
    ld.add_action(set_use_sim_time)
    
    # 添加启动阶段
    ld.add_action(LogInfo(msg='========== Wheel-Legged Robot Digital Twin Control System =========='))
    ld.add_action(stage1_simulation)
    ld.add_action(stage2_control)
    ld.add_action(stage3_optional)
    ld.add_action(stage4_ui)
    
    # 添加事件处理
    ld.add_action(on_joint_controller_exit)
    
    return ld


if __name__ == '__main__':
    generate_launch_description()
