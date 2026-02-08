#!/usr/bin/env python3
"""
增强型关节控制器启动文件

启动集成算法管理器的关节控制器节点，支持多种控制算法动态切换。
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration, TextSubstitution
from launch_ros.actions import Node
from launch.conditions import IfCondition, UnlessCondition


def generate_launch_description():
    """生成启动描述"""
    
    # 声明启动参数
    control_frequency_arg = DeclareLaunchArgument(
        'control_frequency',
        default_value='100.0',
        description='控制循环频率 (Hz)'
    )
    
    performance_report_interval_arg = DeclareLaunchArgument(
        'performance_report_interval',
        default_value='10.0',
        description='性能报告发布间隔 (秒)'
    )
    
    joint_names_arg = DeclareLaunchArgument(
        'joint_names',
        default_value="['lf0_joint', 'lf1_joint', 'rf0_joint', 'rf1_joint', 'l_wheel_joint', 'r_wheel_joint']",
        description='关节名称列表'
    )
    
    min_position_arg = DeclareLaunchArgument(
        'min_position',
        default_value='-3.14159',
        description='关节最小位置限制 (rad)'
    )
    
    max_position_arg = DeclareLaunchArgument(
        'max_position',
        default_value='3.14159',
        description='关节最大位置限制 (rad)'
    )
    
    max_velocity_arg = DeclareLaunchArgument(
        'max_velocity',
        default_value='1000.0',
        description='关节最大速度限制 (rad/s)'
    )
    
    max_effort_arg = DeclareLaunchArgument(
        'max_effort',
        default_value='30.0',
        description='关节最大力矩限制 (N·m)'
    )
    
    enable_monitoring_arg = DeclareLaunchArgument(
        'enable_monitoring',
        default_value='true',
        description='是否启用性能监控'
    )
    
    log_level_arg = DeclareLaunchArgument(
        'log_level',
        default_value='info',
        description='日志级别 (debug, info, warn, error)'
    )
    
    # 增强型关节控制器节点
    enhanced_joint_controller_node = Node(
        package='wheel_legged_control',
        executable='enhanced_joint_controller',
        name='enhanced_joint_controller',
        output='screen',
        parameters=[{
            'control_frequency': LaunchConfiguration('control_frequency'),
            'performance_report_interval': LaunchConfiguration('performance_report_interval'),
            'joint_names': LaunchConfiguration('joint_names'),
            'joint_limits.min_position': LaunchConfiguration('min_position'),
            'joint_limits.max_position': LaunchConfiguration('max_position'),
            'joint_limits.max_velocity': LaunchConfiguration('max_velocity'),
            'joint_limits.max_effort': LaunchConfiguration('max_effort'),
        }],
        arguments=['--ros-args', '--log-level', LaunchConfiguration('log_level')],
        remappings=[
            ('/joint_commands', '/enhanced_joint_commands'),
            ('/joint_trajectory', '/enhanced_joint_trajectory'),
            ('/joint_states', '/enhanced_joint_states'),
            ('/joint_efforts', '/enhanced_joint_efforts'),
            ('/algorithm_performance', '/enhanced_algorithm_performance'),
            ('/algorithm_status', '/enhanced_algorithm_status'),
        ]
    )
    
    # 启动信息
    start_info = LogInfo(
        msg=[
            '启动增强型关节控制器',
            '\n  - 控制频率: ', LaunchConfiguration('control_frequency'), ' Hz',
            '\n  - 性能报告间隔: ', LaunchConfiguration('performance_report_interval'), ' 秒',
            '\n  - 关节数量: ', LaunchConfiguration('joint_names'),
            '\n  - 位置限制: [', LaunchConfiguration('min_position'), ', ', LaunchConfiguration('max_position'), '] rad',
            '\n  - 速度限制: ±', LaunchConfiguration('max_velocity'), ' rad/s',
            '\n  - 力矩限制: ±', LaunchConfiguration('max_effort'), ' N·m',
            '\n  - 日志级别: ', LaunchConfiguration('log_level'),
        ]
    )
    
    return LaunchDescription([
        # 启动参数
        control_frequency_arg,
        performance_report_interval_arg,
        joint_names_arg,
        min_position_arg,
        max_position_arg,
        max_velocity_arg,
        max_effort_arg,
        enable_monitoring_arg,
        log_level_arg,
        
        # 启动信息
        start_info,
        
        # 节点
        enhanced_joint_controller_node,
    ])


if __name__ == '__main__':
    generate_launch_description()