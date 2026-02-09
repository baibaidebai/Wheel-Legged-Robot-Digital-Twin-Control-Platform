#!/usr/bin/env python3
"""
Gazebo仿真后端

基于Gazebo物理引擎的仿真后端实现，提供与现有ROS2系统的兼容性。
"""

import numpy as np
import os
import time
import logging
from typing import Dict, List, Tuple, Optional, Any, Union

from .simulation_manager import BaseSimulationBackend, SimulationConfig

# ROS2导入（可选）
try:
    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import JointState
    from geometry_msgs.msg import Twist
    from std_msgs.msg import Float64MultiArray
    ROS2_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  ROS2不可用: {e}")
    rclpy = None
    Node = None
    ROS2_AVAILABLE = False


class GazeboSimulationBackend(BaseSimulationBackend):
    """Gazebo仿真后端"""
    
    def __init__(self, config: SimulationConfig):
        super().__init__(config)
        
        self.ros_node = None
        self.joint_state_subscriber = None
        self.joint_command_publisher = None
        self.cmd_vel_publisher = None
        
        # 关节名称列表
        self.joint_names = [
            'lf0_joint', 'lf1_joint', 'rf0_joint', 'rf1_joint',
            'l_wheel_joint', 'r_wheel_joint'
        ]
        
        # 初始化关节状态
        for joint_name in self.joint_names:
            self.joint_positions[joint_name] = 0.0
            self.joint_velocities[joint_name] = 0.0
            self.joint_efforts[joint_name] = 0.0
        
        self.logger.info("Gazebo仿真后端初始化完成")
    
    def initialize(self, model_path: str) -> bool:
        """初始化Gazebo仿真环境"""
        try:
            if not ROS2_AVAILABLE:
                self.logger.warning("⚠️  ROS2不可用，使用模拟模式")
                self.is_initialized = True
                return True
            
            # 初始化ROS2节点
            if not rclpy.ok():
                rclpy.init()
            
            self.ros_node = Node('gazebo_simulation_backend')
            
            # 创建订阅者和发布者
            self.joint_state_subscriber = self.ros_node.create_subscription(
                JointState,
                '/joint_states',
                self._joint_state_callback,
                10
            )
            
            self.joint_command_publisher = self.ros_node.create_publisher(
                Float64MultiArray,
                '/joint_group_velocity_controller/commands',
                10
            )
            
            self.cmd_vel_publisher = self.ros_node.create_publisher(
                Twist,
                '/cmd_vel',
                10
            )
            
            self.is_initialized = True
            self.logger.info(f"✅ Gazebo后端初始化成功")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Gazebo初始化失败: {e}")
            return False
    
    def _joint_state_callback(self, msg):
        """关节状态回调函数"""
        try:
            for i, name in enumerate(msg.name):
                if name in self.joint_names:
                    if i < len(msg.position):
                        self.joint_positions[name] = msg.position[i]
                    if i < len(msg.velocity):
                        self.joint_velocities[name] = msg.velocity[i]
                    if i < len(msg.effort):
                        self.joint_efforts[name] = msg.effort[i]
            
            # 简化的基座状态估计（基于轮子状态）
            self._estimate_base_state()
            
        except Exception as e:
            self.logger.debug(f"关节状态回调错误: {e}")
    
    def _estimate_base_state(self):
        """基于关节状态估计基座状态"""
        try:
            # 简化的差分驱动模型
            left_wheel_vel = self.joint_velocities.get('l_wheel_joint', 0.0)
            right_wheel_vel = self.joint_velocities.get('r_wheel_joint', 0.0)
            
            wheel_radius = 0.05  # 轮子半径
            wheel_base = 0.3     # 轮距
            
            # 计算基座线性和角速度
            linear_vel = (left_wheel_vel + right_wheel_vel) * wheel_radius / 2
            angular_vel = (right_wheel_vel - left_wheel_vel) * wheel_radius / wheel_base
            
            self.base_linear_velocity[0] = linear_vel
            self.base_angular_velocity[2] = angular_vel
            
            # 积分得到位置（简化）
            dt = self.config.dt
            self.base_position[0] += self.base_linear_velocity[0] * dt
            self.base_position[1] += self.base_linear_velocity[1] * dt
            
        except Exception as e:
            self.logger.debug(f"基座状态估计错误: {e}")
    
    def reset(self) -> bool:
        """重置仿真状态"""
        if not self.is_initialized:
            return False
        
        try:
            # 重置内部状态
            self.current_step = 0
            
            # 重置关节状态
            for joint_name in self.joint_names:
                self.joint_positions[joint_name] = 0.0
                self.joint_velocities[joint_name] = 0.0
                self.joint_efforts[joint_name] = 0.0
            
            # 重置基座状态
            self.base_position = np.array([0.0, 0.0, 0.3])
            self.base_orientation = np.array([0, 0, 0, 1])
            self.base_linear_velocity = np.zeros(3)
            self.base_angular_velocity = np.zeros(3)
            
            # 发送零速度指令
            if self.joint_command_publisher:
                zero_cmd = Float64MultiArray()
                zero_cmd.data = [0.0] * len(self.joint_names)
                self.joint_command_publisher.publish(zero_cmd)
            
            if self.cmd_vel_publisher:
                zero_twist = Twist()
                self.cmd_vel_publisher.publish(zero_twist)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 重置失败: {e}")
            return False
    
    def step(self, action: Dict[str, float] = None) -> bool:
        """执行一步仿真"""
        if not self.is_initialized:
            return False
        
        try:
            # 应用控制输入
            if action:
                self._apply_control(action)
            
            # 处理ROS2消息
            if self.ros_node and ROS2_AVAILABLE:
                rclpy.spin_once(self.ros_node, timeout_sec=0.001)
            else:
                # 模拟模式：简单的物理更新
                self._simulate_physics()
            
            # 更新步数
            self.current_step += 1
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 仿真步执行失败: {e}")
            return False
    
    def _apply_control(self, action: Dict[str, float]):
        """应用控制输入"""
        try:
            if self.joint_command_publisher and ROS2_AVAILABLE:
                # 发布关节速度指令
                cmd_msg = Float64MultiArray()
                cmd_data = []
                
                for joint_name in self.joint_names:
                    velocity = action.get(joint_name, 0.0)
                    # 移除可能的后缀
                    clean_name = joint_name.replace('_motor', '')
                    velocity = action.get(clean_name, velocity)
                    cmd_data.append(velocity)
                
                cmd_msg.data = cmd_data
                self.joint_command_publisher.publish(cmd_msg)
            
            # 如果有轮子速度，也发布cmd_vel
            if self.cmd_vel_publisher and ROS2_AVAILABLE:
                left_wheel_vel = action.get('l_wheel_joint', action.get('l_wheel_motor', 0.0))
                right_wheel_vel = action.get('r_wheel_joint', action.get('r_wheel_motor', 0.0))
                
                if left_wheel_vel != 0.0 or right_wheel_vel != 0.0:
                    wheel_radius = 0.05
                    wheel_base = 0.3
                    
                    linear_vel = (left_wheel_vel + right_wheel_vel) * wheel_radius / 2
                    angular_vel = (right_wheel_vel - left_wheel_vel) * wheel_radius / wheel_base
                    
                    twist_msg = Twist()
                    twist_msg.linear.x = linear_vel
                    twist_msg.angular.z = angular_vel
                    self.cmd_vel_publisher.publish(twist_msg)
            
        except Exception as e:
            self.logger.debug(f"控制应用错误: {e}")
    
    def _simulate_physics(self):
        """简化的物理仿真（模拟模式）"""
        dt = self.config.dt
        
        # 简单的关节运动学积分
        for joint_name in self.joint_names:
            velocity = self.joint_velocities[joint_name]
            self.joint_positions[joint_name] += velocity * dt
            
            # 应用关节限制
            self.joint_positions[joint_name] = np.clip(
                self.joint_positions[joint_name], -np.pi, np.pi
            )
        
        # 更新基座状态
        self._estimate_base_state()
    
    def get_state(self) -> Dict[str, Any]:
        """获取当前仿真状态"""
        return {
            'time': self.current_step * self.config.dt,
            'step': self.current_step,
            'joint_positions': self.joint_positions.copy(),
            'joint_velocities': self.joint_velocities.copy(),
            'joint_efforts': self.joint_efforts.copy(),
            'base_position': self.base_position.copy(),
            'base_orientation': self.base_orientation.copy(),
            'base_linear_velocity': self.base_linear_velocity.copy(),
            'base_angular_velocity': self.base_angular_velocity.copy()
        }
    
    def set_joint_positions(self, positions: Dict[str, float]) -> bool:
        """设置关节位置"""
        if not self.is_initialized:
            return False
        
        try:
            for joint_name, position in positions.items():
                if joint_name in self.joint_names:
                    self.joint_positions[joint_name] = position
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 设置关节位置失败: {e}")
            return False
    
    def set_joint_velocities(self, velocities: Dict[str, float]) -> bool:
        """设置关节速度"""
        if not self.is_initialized:
            return False
        
        try:
            # 通过控制指令设置速度
            self._apply_control(velocities)
            
            # 更新内部状态
            for joint_name, velocity in velocities.items():
                if joint_name in self.joint_names:
                    self.joint_velocities[joint_name] = velocity
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 设置关节速度失败: {e}")
            return False
    
    def set_joint_efforts(self, efforts: Dict[str, float]) -> bool:
        """设置关节力矩"""
        if not self.is_initialized:
            return False
        
        try:
            # Gazebo通常使用速度控制，这里转换为速度指令
            velocities = {}
            for joint_name, effort in efforts.items():
                if joint_name in self.joint_names:
                    # 简化的力矩到速度转换
                    velocity = np.tanh(effort / 10.0) * 5.0  # 限制速度范围
                    velocities[joint_name] = velocity
            
            return self.set_joint_velocities(velocities)
            
        except Exception as e:
            self.logger.error(f"❌ 设置关节力矩失败: {e}")
            return False
    
    def get_joint_states(self) -> Dict[str, Dict[str, float]]:
        """获取关节状态"""
        joint_states = {}
        
        for joint_name in self.joint_names:
            joint_states[joint_name] = {
                'position': self.joint_positions.get(joint_name, 0.0),
                'velocity': self.joint_velocities.get(joint_name, 0.0),
                'effort': self.joint_efforts.get(joint_name, 0.0)
            }
        
        return joint_states
    
    def render(self, mode: str = 'human') -> Optional[np.ndarray]:
        """渲染仿真画面"""
        if mode == 'human':
            # Gazebo有自己的GUI
            print(f"Gazebo渲染 - 步骤: {self.current_step}")
            print(f"基座位置: {self.base_position}")
            return None
            
        elif mode == 'rgb_array':
            # 返回模拟图像
            return np.zeros((self.config.render_height, self.config.render_width, 3), dtype=np.uint8)
        
        return None
    
    def close(self):
        """关闭仿真环境"""
        if self.ros_node and ROS2_AVAILABLE:
            self.ros_node.destroy_node()
            self.ros_node = None
        
        self.joint_state_subscriber = None
        self.joint_command_publisher = None
        self.cmd_vel_publisher = None
        
        self.is_initialized = False
        self.logger.info("Gazebo仿真后端已关闭")


if __name__ == "__main__":
    # 测试Gazebo后端
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 测试Gazebo仿真后端")
    
    # 创建配置
    config = SimulationConfig(
        backend=SimulationBackend.GAZEBO,
        enable_rendering=True,
        dt=0.01
    )
    
    try:
        # 创建后端
        backend = GazeboSimulationBackend(config)
        
        # 初始化
        success = backend.initialize("dummy_model_path")
        print(f"初始化: {'✅' if success else '❌'}")
        
        if success:
            # 重置
            backend.reset()
            print("✅ 重置成功")
            
            # 执行几步仿真
            for i in range(10):
                # 随机控制输入
                action = {
                    'lf0_joint': np.random.uniform(-1, 1),
                    'rf0_joint': np.random.uniform(-1, 1),
                    'l_wheel_joint': np.random.uniform(-1, 1),
                    'r_wheel_joint': np.random.uniform(-1, 1)
                }
                
                backend.step(action)
                
                if i % 5 == 0:
                    state = backend.get_state()
                    print(f"步骤 {i}: 时间={state['time']:.3f}, 基座位置={state['base_position']}")
            
            print("✅ 仿真测试成功")
        
        # 清理
        backend.close()
        
        print("🎉 Gazebo后端测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()