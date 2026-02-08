#!/usr/bin/env python3
"""
关节控制ROS2通信接口
提供标准化的关节状态发布和指令订阅功能
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
import numpy as np
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
import threading
import time

# ROS2消息类型
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64MultiArray, Header, Bool
from geometry_msgs.msg import Twist
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from control_msgs.msg import JointTrajectoryControllerState
from std_srvs.srv import SetBool, Trigger
# from wheel_legged_control_msgs.srv import SetJointPositions, GetJointStates  # 暂时注释掉


@dataclass
class JointStateData:
    """关节状态数据结构"""
    name: str
    position: float
    velocity: float
    effort: float
    timestamp: float


@dataclass
class QoSConfig:
    """QoS配置"""
    reliability: ReliabilityPolicy = ReliabilityPolicy.RELIABLE
    durability: DurabilityPolicy = DurabilityPolicy.VOLATILE
    history: HistoryPolicy = HistoryPolicy.KEEP_LAST
    depth: int = 10


class JointStatePublisher:
    """关节状态发布器"""
    
    def __init__(self, node: Node, topic_name: str = '/joint_states', 
                 qos_config: Optional[QoSConfig] = None):
        self.node = node
        self.topic_name = topic_name
        
        # 设置QoS
        if qos_config is None:
            qos_config = QoSConfig()
        
        qos_profile = QoSProfile(
            reliability=qos_config.reliability,
            durability=qos_config.durability,
            history=qos_config.history,
            depth=qos_config.depth
        )
        
        # 创建发布器
        self.publisher = node.create_publisher(
            JointState,
            topic_name,
            qos_profile
        )
        
        self.node.get_logger().info(f'关节状态发布器已创建: {topic_name}')
    
    def publish_joint_states(self, joint_data: Dict[str, JointStateData], 
                           frame_id: str = 'base_link'):
        """
        发布关节状态
        
        Args:
            joint_data: 关节数据字典
            frame_id: 坐标系ID
        """
        msg = JointState()
        msg.header = Header()
        msg.header.stamp = self.node.get_clock().now().to_msg()
        msg.header.frame_id = frame_id
        
        # 按名称排序确保一致性
        sorted_joints = sorted(joint_data.items())
        
        msg.name = [name for name, _ in sorted_joints]
        msg.position = [data.position for _, data in sorted_joints]
        msg.velocity = [data.velocity for _, data in sorted_joints]
        msg.effort = [data.effort for _, data in sorted_joints]
        
        self.publisher.publish(msg)
    
    def publish_simple_states(self, joint_names: List[str], 
                            positions: List[float],
                            velocities: Optional[List[float]] = None,
                            efforts: Optional[List[float]] = None,
                            frame_id: str = 'base_link'):
        """
        发布简单关节状态
        
        Args:
            joint_names: 关节名称列表
            positions: 位置列表
            velocities: 速度列表（可选）
            efforts: 力矩列表（可选）
            frame_id: 坐标系ID
        """
        if velocities is None:
            velocities = [0.0] * len(joint_names)
        if efforts is None:
            efforts = [0.0] * len(joint_names)
        
        msg = JointState()
        msg.header = Header()
        msg.header.stamp = self.node.get_clock().now().to_msg()
        msg.header.frame_id = frame_id
        
        msg.name = joint_names
        msg.position = positions
        msg.velocity = velocities
        msg.effort = efforts
        
        self.publisher.publish(msg)


class JointCommandSubscriber:
    """关节指令订阅器"""
    
    def __init__(self, node: Node, callback: Callable[[List[float]], None],
                 topic_name: str = '/joint_commands',
                 qos_config: Optional[QoSConfig] = None):
        self.node = node
        self.callback = callback
        self.topic_name = topic_name
        
        # 设置QoS
        if qos_config is None:
            qos_config = QoSConfig()
        
        qos_profile = QoSProfile(
            reliability=qos_config.reliability,
            durability=qos_config.durability,
            history=qos_config.history,
            depth=qos_config.depth
        )
        
        # 创建订阅器
        self.subscription = node.create_subscription(
            Float64MultiArray,
            topic_name,
            self._command_callback,
            qos_profile
        )
        
        self.node.get_logger().info(f'关节指令订阅器已创建: {topic_name}')
    
    def _command_callback(self, msg: Float64MultiArray):
        """内部回调函数"""
        try:
            self.callback(list(msg.data))
        except Exception as e:
            self.node.get_logger().error(f'处理关节指令时发生错误: {e}')


class JointTrajectorySubscriber:
    """关节轨迹订阅器"""
    
    def __init__(self, node: Node, callback: Callable[[JointTrajectory], None],
                 topic_name: str = '/joint_trajectory',
                 qos_config: Optional[QoSConfig] = None):
        self.node = node
        self.callback = callback
        self.topic_name = topic_name
        
        # 设置QoS
        if qos_config is None:
            qos_config = QoSConfig()
        
        qos_profile = QoSProfile(
            reliability=qos_config.reliability,
            durability=qos_config.durability,
            history=qos_config.history,
            depth=qos_config.depth
        )
        
        # 创建订阅器
        self.subscription = node.create_subscription(
            JointTrajectory,
            topic_name,
            self._trajectory_callback,
            qos_profile
        )
        
        self.node.get_logger().info(f'关节轨迹订阅器已创建: {topic_name}')
    
    def _trajectory_callback(self, msg: JointTrajectory):
        """内部回调函数"""
        try:
            self.callback(msg)
        except Exception as e:
            self.node.get_logger().error(f'处理关节轨迹时发生错误: {e}')


class JointControllerStatePublisher:
    """关节控制器状态发布器"""
    
    def __init__(self, node: Node, topic_name: str = '/joint_controller_state',
                 qos_config: Optional[QoSConfig] = None):
        self.node = node
        self.topic_name = topic_name
        
        # 设置QoS
        if qos_config is None:
            qos_config = QoSConfig()
        
        qos_profile = QoSProfile(
            reliability=qos_config.reliability,
            durability=qos_config.durability,
            history=qos_config.history,
            depth=qos_config.depth
        )
        
        # 创建发布器
        self.publisher = node.create_publisher(
            JointTrajectoryControllerState,
            topic_name,
            qos_profile
        )
        
        self.node.get_logger().info(f'控制器状态发布器已创建: {topic_name}')
    
    def publish_controller_state(self, joint_names: List[str],
                               desired_positions: List[float],
                               desired_velocities: List[float],
                               actual_positions: List[float],
                               actual_velocities: List[float],
                               error_positions: List[float],
                               error_velocities: List[float]):
        """
        发布控制器状态
        
        Args:
            joint_names: 关节名称
            desired_positions: 期望位置
            desired_velocities: 期望速度
            actual_positions: 实际位置
            actual_velocities: 实际速度
            error_positions: 位置误差
            error_velocities: 速度误差
        """
        msg = JointTrajectoryControllerState()
        msg.header = Header()
        msg.header.stamp = self.node.get_clock().now().to_msg()
        
        msg.joint_names = joint_names
        
        # 期望状态
        desired_point = JointTrajectoryPoint()
        desired_point.positions = desired_positions
        desired_point.velocities = desired_velocities
        msg.desired = desired_point
        
        # 实际状态
        actual_point = JointTrajectoryPoint()
        actual_point.positions = actual_positions
        actual_point.velocities = actual_velocities
        msg.actual = actual_point
        
        # 误差
        error_point = JointTrajectoryPoint()
        error_point.positions = error_positions
        error_point.velocities = error_velocities
        msg.error = error_point
        
        self.publisher.publish(msg)


class JointControlServices:
    """关节控制服务"""
    
    def __init__(self, node: Node, joint_controller):
        self.node = node
        self.joint_controller = joint_controller
        
        # 创建服务
        self.emergency_stop_service = node.create_service(
            Trigger,
            '/joint_controller/emergency_stop',
            self._emergency_stop_callback
        )
        
        self.reset_service = node.create_service(
            Trigger,
            '/joint_controller/reset',
            self._reset_callback
        )
        
        self.enable_service = node.create_service(
            SetBool,
            '/joint_controller/enable',
            self._enable_callback
        )
        
        self.node.get_logger().info('关节控制服务已创建')
    
    def _emergency_stop_callback(self, request, response):
        """紧急停止服务回调"""
        try:
            self.joint_controller.emergency_stop()
            response.success = True
            response.message = "紧急停止执行成功"
        except Exception as e:
            response.success = False
            response.message = f"紧急停止失败: {str(e)}"
        
        return response
    
    def _reset_callback(self, request, response):
        """复位服务回调"""
        try:
            self.joint_controller.reset_to_home()
            response.success = True
            response.message = "复位执行成功"
        except Exception as e:
            response.success = False
            response.message = f"复位失败: {str(e)}"
        
        return response
    
    def _enable_callback(self, request, response):
        """使能服务回调"""
        try:
            if request.data:
                # 启用控制器
                self.joint_controller.enable()
                response.success = True
                response.message = "控制器已启用"
            else:
                # 禁用控制器
                self.joint_controller.disable()
                response.success = True
                response.message = "控制器已禁用"
        except Exception as e:
            response.success = False
            response.message = f"设置使能状态失败: {str(e)}"
        
        return response


class JointInterfaceManager:
    """关节接口管理器"""
    
    def __init__(self, node: Node, joint_controller):
        self.node = node
        self.joint_controller = joint_controller
        
        # 创建接口组件
        self.state_publisher = JointStatePublisher(node)
        
        self.command_subscriber = JointCommandSubscriber(
            node, 
            self._handle_joint_command
        )
        
        self.trajectory_subscriber = JointTrajectorySubscriber(
            node,
            self._handle_trajectory_command
        )
        
        self.controller_state_publisher = JointControllerStatePublisher(node)
        
        self.services = JointControlServices(node, joint_controller)
        
        # 状态发布定时器
        self.state_publish_timer = node.create_timer(
            0.01,  # 100Hz
            self._publish_states
        )
        
        self.node.get_logger().info('关节接口管理器已初始化')
    
    def _handle_joint_command(self, positions: List[float]):
        """处理关节位置指令"""
        if hasattr(self.joint_controller, 'joint_names'):
            if len(positions) == len(self.joint_controller.joint_names):
                position_dict = dict(zip(self.joint_controller.joint_names, positions))
                self.joint_controller.set_joint_positions(position_dict)
            else:
                self.node.get_logger().warn(
                    f'关节指令数量不匹配: 期望{len(self.joint_controller.joint_names)}, '
                    f'收到{len(positions)}'
                )
    
    def _handle_trajectory_command(self, trajectory: JointTrajectory):
        """处理轨迹指令"""
        if hasattr(self.joint_controller, 'execute_trajectory'):
            self.joint_controller.execute_trajectory(trajectory)
    
    def _publish_states(self):
        """发布关节状态"""
        if hasattr(self.joint_controller, 'get_joint_states'):
            try:
                # 获取关节状态
                joint_states = self.joint_controller.get_joint_states()
                
                # 发布基本关节状态
                joint_data = {}
                for name, (pos, vel, eff) in joint_states.items():
                    joint_data[name] = JointStateData(
                        name=name,
                        position=pos,
                        velocity=vel,
                        effort=eff,
                        timestamp=time.time()
                    )
                
                self.state_publisher.publish_joint_states(joint_data)
                
                # 发布控制器状态（如果有目标状态）
                if hasattr(self.joint_controller, 'target_positions'):
                    joint_names = list(joint_states.keys())
                    actual_positions = [joint_states[name][0] for name in joint_names]
                    actual_velocities = [joint_states[name][1] for name in joint_names]
                    desired_positions = [self.joint_controller.target_positions.get(name, 0.0) 
                                       for name in joint_names]
                    desired_velocities = [0.0] * len(joint_names)  # 简化处理
                    
                    error_positions = [desired_positions[i] - actual_positions[i] 
                                     for i in range(len(joint_names))]
                    error_velocities = [0.0] * len(joint_names)  # 简化处理
                    
                    self.controller_state_publisher.publish_controller_state(
                        joint_names,
                        desired_positions,
                        desired_velocities,
                        actual_positions,
                        actual_velocities,
                        error_positions,
                        error_velocities
                    )
                    
            except Exception as e:
                self.node.get_logger().error(f'发布关节状态时发生错误: {e}')


def create_joint_interface(node: Node, joint_controller) -> JointInterfaceManager:
    """
    创建关节接口管理器的工厂函数
    
    Args:
        node: ROS2节点
        joint_controller: 关节控制器实例
        
    Returns:
        关节接口管理器
    """
    return JointInterfaceManager(node, joint_controller)