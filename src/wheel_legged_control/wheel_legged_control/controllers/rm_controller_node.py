#!/usr/bin/env python3
"""
RM轮腿机器人ROS2控制器节点
集成PID和LQR控制器，支持多种运动模式控制
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
import numpy as np
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
import json
import threading

# ROS2消息类型
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64MultiArray, String
from std_srvs.srv import SetBool, Trigger
from geometry_msgs.msg import Twist

# 导入控制器算法
try:
    from ..controllers.rm_robot_controller import (
        HybridRMController, PIDGains, LQRConfig
    )
    from ..algorithms.lqr_controller import create_wheel_legged_robot_model
    CONTROLLERS_AVAILABLE = True
except ImportError as e:
    print(f"警告: 控制器模块导入失败: {e}")
    CONTROLLERS_AVAILABLE = False


@dataclass
class MotionPattern:
    """运动模式配置"""
    name: str
    description: str
    joint_trajectory_func: callable
    duration: float


class RMControllerNode(Node):
    """RM轮腿机器人控制器节点"""
    
    def __init__(self):
        super().__init__('rm_controller')
        
        if not CONTROLLERS_AVAILABLE:
            self.get_logger().error("控制器模块不可用，节点无法启动")
            return
            
        # RM机器人关节配置
        self.joint_names = [
            'lf0_Joint', 'lf1_Joint', 'l_wheel_Joint',
            'rf0_Joint', 'rf1_Joint', 'r_wheel_Joint'
        ]
        
        # 优化的关节限位设置（弧度）
        self.joint_limits = {
            'lf0_Joint': (-1.5, 1.5),    # 髋关节 - 更宽松的范围
            'lf1_Joint': (-2.0, 2.0),    # 膝关节 - 增大活动范围
            'l_wheel_Joint': (-10.0, 10.0),  # 轮子关节 - 几乎无限制
            'rf0_Joint': (-1.5, 1.5),    # 右侧髋关节
            'rf1_Joint': (-2.0, 2.0),    # 右侧膝关节
            'r_wheel_Joint': (-10.0, 10.0)   # 右侧轮子关节
        }
        
        # 初始化控制器
        self._setup_controllers()
        
        # 设置ROS2通信
        self._setup_ros_interface()
        
        # 运动模式管理
        self._setup_motion_patterns()
        
        # 控制状态
        self.controller_enabled = True
        self.current_motion = 'stand'
        self.motion_start_time = 0.0
        self.control_frequency = 100.0  # Hz
        
        # 腿部测试模式相关
        self.leg_test_active = False
        self.leg_test_step = 0
        self.leg_test_start_time = None
        self.leg_test_positions = []  # 存储测试轨迹点
        self.leg_test_index = 0
        
        # 控制定时器
        self.control_timer = self.create_timer(
            1.0 / self.control_frequency,
            self.control_loop
        )
        
        # 性能监控
        self.performance_stats = {
            'control_cycles': 0,
            'average_cycle_time': 0.0,
            'last_update': time.time()
        }
        
        self.get_logger().info('RM控制器节点已启动')
        self.get_logger().info(f'控制关节: {self.joint_names}')
        self.get_logger().info(f'控制频率: {self.control_frequency} Hz')
    
    def _setup_controllers(self):
        """设置控制器"""
        # 优化的PID参数配置（针对站立模式）
        pid_gains_dict = {
            'lf0_Joint': PIDGains(kp=20.0, ki=0.3, kd=1.2),  # 增加Kp和Kd提高响应速度
            'lf1_Joint': PIDGains(kp=18.0, ki=0.25, kd=1.0),  # 优化腿部关节控制
            'l_wheel_Joint': PIDGains(kp=12.0, ki=0.1, kd=0.5),  # 轮子关节相对较低的增益
            'rf0_Joint': PIDGains(kp=20.0, ki=0.3, kd=1.2),  # 右侧对称配置
            'rf1_Joint': PIDGains(kp=18.0, ki=0.25, kd=1.0),
            'r_wheel_Joint': PIDGains(kp=12.0, ki=0.1, kd=0.5)
        }
        
        # 优化的LQR配置
        lqr_config = LQRConfig(
            state_dim=12,
            control_dim=6,
            Q_weights=[15.0] * 6 + [2.0] * 6,  # 提高位置权重，降低速度权重
            R_weights=[0.08] * 6,  # 降低控制权重以提高能效
            dt=0.01
        )
        
        # 创建混合控制器
        self.controller = HybridRMController(self.joint_names, pid_gains_dict, lqr_config)
        
        # 初始化关节状态为有利于站立的位置
        initial_positions = {
            'lf0_Joint': 0.1,    # 轻微向前倾斜帮助站立
            'lf1_Joint': -0.3,   # 膝关节轻微弯曲
            'l_wheel_Joint': 0.0,
            'rf0_Joint': 0.1,    # 对称配置
            'rf1_Joint': -0.3,
            'r_wheel_Joint': 0.0
        }
        
        # 使用优化的初始状态初始化控制器
        for joint_name in self.joint_names:
            initial_pos = initial_positions.get(joint_name, 0.0)
            self.controller.update_joint_state(joint_name, initial_pos, 0.0, 0.0)
        
        # 重力补偿参数
        self.gravity_compensation_enabled = True
        self.robot_mass = 15.0  # kg
        self.gravity = 9.81     # m/s²
        
        self.get_logger().info('控制器参数已优化配置')
        self.get_logger().info(f'初始关节位置: {initial_positions}')
        self.get_logger().info('重力补偿功能已启用')
    
    def _compute_gravity_compensation(self, target_positions: Dict[str, float]) -> Dict[str, float]:
        """计算重力补偿力矩"""
        compensation = {}
        
        # 简化的重力补偿模型
        # 基于关节位置和机器人质量分布计算
        for joint_name in self.joint_names:
            target_pos = target_positions.get(joint_name, 0.0)
            
            # 不同关节的重力补偿系数
            if 'Joint' in joint_name and 'wheel' not in joint_name:
                # 腿部关节需要更多重力补偿
                compensation_factor = 0.3 * self.robot_mass * self.gravity
                compensation[joint_name] = compensation_factor * np.sin(target_pos)
            else:
                # 轮子关节重力补偿较少
                compensation[joint_name] = 0.0
        
        return compensation
    
    def _setup_ros_interface(self):
        """设置ROS2通信接口"""
        # QoS配置
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
            depth=10
        )
        
        # 订阅者
        self.joint_state_sub = self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_state_callback,
            qos_profile
        )
        
        # 发布者
        self.joint_command_pub = self.create_publisher(
            Float64MultiArray,
            '/joint_commands',
            qos_profile
        )
        
        self.status_pub = self.create_publisher(
            String,
            '/rm_controller/status',
            qos_profile
        )
        
        # 服务
        self.enable_service = self.create_service(
            SetBool,
            '/rm_controller/enable',
            self.enable_callback
        )
        
        self.emergency_stop_service = self.create_service(
            Trigger,
            '/rm_controller/emergency_stop',
            self.emergency_stop_callback
        )
        
        # 使用标准服务替代自定义服务
        self.set_motion_service = self.create_service(
            Trigger,  # 临时使用Trigger服务
            '/rm_controller/set_motion',
            self.temp_set_motion_callback
        )
        
        self.get_status_service = self.create_service(
            Trigger,
            '/rm_controller/get_status',
            self.get_status_callback
        )
    
    def _setup_motion_patterns(self):
        """设置运动模式"""
        self.motion_patterns = {
            'stand': MotionPattern(
                name='stand',
                description='站立稳定',
                joint_trajectory_func=self._stand_trajectory,
                duration=float('inf')  # 持续模式
            ),
            'walk': MotionPattern(
                name='walk',
                description='前进步行',
                joint_trajectory_func=self._walk_trajectory,
                duration=10.0
            ),
            'turn': MotionPattern(
                name='turn',
                description='转向运动',
                joint_trajectory_func=self._turn_trajectory,
                duration=8.0
            ),
            'jump': MotionPattern(
                name='jump',
                description='跳跃动作',
                joint_trajectory_func=self._jump_trajectory,
                duration=5.0
            )
        }
    
    def joint_state_callback(self, msg: JointState):
        """关节状态回调"""
        try:
            for i, name in enumerate(msg.name):
                if name in self.joint_names:
                    position = msg.position[i] if i < len(msg.position) else 0.0
                    velocity = msg.velocity[i] if i < len(msg.velocity) else 0.0
                    effort = msg.effort[i] if i < len(msg.effort) else 0.0
                    
                    self.controller.update_joint_state(name, position, velocity, effort)
        except Exception as e:
            self.get_logger().warn(f'处理关节状态时出错: {e}')
    
    def control_loop(self):
        """主控制循环"""
        if not self.controller_enabled:
            return
            
        try:
            current_time = time.time()
            
            # 检查是否在腿部测试模式
            if self.leg_test_active:
                target_positions = self.get_current_leg_test_target(current_time)
                # 如果测试完成，自动停止
                if (self.leg_test_index == len(self.leg_test_positions) - 1 and 
                    current_time - self.leg_test_start_time > self.leg_test_positions[-1][0] + 1.0):
                    self.stop_leg_test()
                    self.get_logger().info('腿部测试序列完成')
            else:
                # 获取当前运动模式的轨迹
                if self.current_motion in self.motion_patterns:
                    pattern = self.motion_patterns[self.current_motion]
                    elapsed_time = current_time - self.motion_start_time
                    
                    # 如果是限时模式且超时，则回到站立模式
                    if pattern.duration != float('inf') and elapsed_time > pattern.duration:
                        self.set_motion('stand')
                        pattern = self.motion_patterns['stand']
                        elapsed_time = 0.0
                    
                    target_positions = pattern.joint_trajectory_func(elapsed_time)
                else:
                    target_positions = {name: 0.0 for name in self.joint_names}
            
            # 计算控制输出
            dt = 1.0 / self.control_frequency
            control_outputs = self.controller.compute_control(target_positions, dt)
            
            # 应用重力补偿
            if self.gravity_compensation_enabled:
                gravity_compensation = self._compute_gravity_compensation(target_positions)
                for joint_name in self.joint_names:
                    control_outputs[joint_name] += gravity_compensation.get(joint_name, 0.0)
            
            # 发布控制命令
            self.publish_control_commands(control_outputs)
            
            # 更新性能统计
            self.update_performance_stats()
            
        except Exception as e:
            self.get_logger().error(f'控制循环出错: {e}')
    
    def publish_control_commands(self, control_outputs: Dict[str, float]):
        """发布控制命令"""
        try:
            msg = Float64MultiArray()
            msg.data = [float(control_outputs[name]) for name in self.joint_names]
            self.joint_command_pub.publish(msg)
        except Exception as e:
            self.get_logger().error(f'发布控制命令失败: {e}')
    
    def update_performance_stats(self):
        """更新性能统计"""
        self.performance_stats['control_cycles'] += 1
        current_time = time.time()
        cycle_time = current_time - self.performance_stats['last_update']
        self.performance_stats['last_update'] = current_time
        
        # 指数移动平均
        alpha = 0.01
        self.performance_stats['average_cycle_time'] = (
            self.performance_stats['average_cycle_time'] * (1 - alpha) +
            cycle_time * alpha
        )
    
    def set_motion(self, motion_name: str):
        """设置运动模式"""
        if motion_name in self.motion_patterns:
            self.current_motion = motion_name
            self.motion_start_time = time.time()
            self.get_logger().info(f'切换到运动模式: {motion_name}')
            return True
        else:
            self.get_logger().warn(f'未知运动模式: {motion_name}')
            return False
    
    def start_leg_test(self):
        """开始腿部测试序列"""
        self.get_logger().info('开始腿部收腿伸腿测试')
        
        # 定义测试轨迹点：[时间, {关节目标位置}]
        self.leg_test_positions = [
            # 初始站立位置 (0秒)
            (0.0, {
                'lf0_Joint': 0.1,    # 髋关节轻微前倾
                'lf1_Joint': -0.3,   # 膝关节轻微弯曲
                'l_wheel_Joint': 0.0,
                'rf0_Joint': 0.1,
                'rf1_Joint': -0.3,
                'r_wheel_Joint': 0.0
            }),
            # 收腿位置 (2秒)
            (2.0, {
                'lf0_Joint': 0.8,    # 髋关节大幅前倾
                'lf1_Joint': -1.5,   # 膝关节大幅弯曲（收腿）
                'l_wheel_Joint': 0.0,
                'rf0_Joint': 0.8,
                'rf1_Joint': -1.5,
                'r_wheel_Joint': 0.0
            }),
            # 伸腿位置 (4秒)
            (4.0, {
                'lf0_Joint': -0.5,   # 髋关节后倾
                'lf1_Joint': 0.8,    # 膝关节伸直
                'l_wheel_Joint': 0.0,
                'rf0_Joint': -0.5,
                'rf1_Joint': 0.8,
                'r_wheel_Joint': 0.0
            }),
            # 回到站立位置 (6秒)
            (6.0, {
                'lf0_Joint': 0.1,
                'lf1_Joint': -0.3,
                'l_wheel_Joint': 0.0,
                'rf0_Joint': 0.1,
                'rf1_Joint': -0.3,
                'r_wheel_Joint': 0.0
            })
        ]
        
        self.leg_test_active = True
        self.leg_test_index = 0
        self.leg_test_start_time = time.time()
        self.get_logger().info('腿部测试序列已启动，共4个测试点')
    
    def stop_leg_test(self):
        """停止腿部测试"""
        self.leg_test_active = False
        self.leg_test_index = 0
        self.leg_test_start_time = None
        self.get_logger().info('腿部测试已停止')
    
    def get_current_leg_test_target(self, current_time: float) -> Dict[str, float]:
        """获取当前测试点的目标位置"""
        if not self.leg_test_active or not self.leg_test_positions:
            return {name: 0.0 for name in self.joint_names}
        
        elapsed_time = current_time - self.leg_test_start_time
        
        # 找到当前应该执行的测试点
        while (self.leg_test_index < len(self.leg_test_positions) - 1 and 
               elapsed_time >= self.leg_test_positions[self.leg_test_index + 1][0]):
            self.leg_test_index += 1
            self.get_logger().info(f'执行测试步骤 {self.leg_test_index + 1}/{len(self.leg_test_positions)}')
        
        # 获取当前测试点
        current_point = self.leg_test_positions[self.leg_test_index]
        
        # 如果是最后一个点，保持该位置
        if self.leg_test_index == len(self.leg_test_positions) - 1:
            return current_point[1].copy()
        
        # 线性插值到下一个点
        next_point = self.leg_test_positions[self.leg_test_index + 1]
        current_time_point = current_point[0]
        next_time_point = next_point[0]
        ratio = (elapsed_time - current_time_point) / (next_time_point - current_time_point)
        ratio = max(0.0, min(1.0, ratio))  # 限制在[0,1]范围内
        
        # 计算插值位置
        interpolated_positions = {}
        for joint_name in self.joint_names:
            current_pos = current_point[1][joint_name]
            next_pos = next_point[1][joint_name]
            interpolated_positions[joint_name] = current_pos + ratio * (next_pos - current_pos)
        
        return interpolated_positions
    
    # 运动轨迹生成函数
    def _stand_trajectory(self, time: float) -> Dict[str, float]:
        """优化的站立轨迹 - 稳定的零位置控制"""
        # 添加轻微的姿态调整以维持平衡
        balance_adjustment = 0.02 * np.sin(time * 0.5)  # 轻微的平衡调节
        
        return {
            'lf0_Joint': balance_adjustment * 0.3,      # 左前髋关节轻微调节
            'lf1_Joint': balance_adjustment * 0.5,      # 左前膝关节
            'l_wheel_Joint': balance_adjustment * 0.1,  # 左轮子
            'rf0_Joint': balance_adjustment * 0.3,      # 右前髋关节
            'rf1_Joint': balance_adjustment * 0.5,      # 右前膝关节
            'r_wheel_Joint': -balance_adjustment * 0.1  # 右轮子（反向）
        }
    
    def _walk_trajectory(self, time: float) -> Dict[str, float]:
        """步行轨迹"""
        cycle_time = 2.0
        normalized_time = (time % cycle_time) / cycle_time
        left_phase = normalized_time * 2 * np.pi
        right_phase = left_phase + np.pi
        
        return {
            'lf0_Joint': 0.3 * np.sin(left_phase),
            'lf1_Joint': -0.5 * np.abs(np.sin(left_phase)),
            'l_wheel_Joint': 0.1 * np.sin(time * 2),
            'rf0_Joint': 0.3 * np.sin(right_phase),
            'rf1_Joint': -0.5 * np.abs(np.sin(right_phase)),
            'r_wheel_Joint': -0.1 * np.sin(time * 2)
        }
    
    def _turn_trajectory(self, time: float) -> Dict[str, float]:
        """转向轨迹"""
        cycle_time = 1.5
        normalized_time = (time % cycle_time) / cycle_time
        phase = normalized_time * 2 * np.pi
        
        left_swing = 0.4 * np.sin(phase)
        right_swing = 0.4 * np.sin(phase + np.pi * 0.7)
        
        return {
            'lf0_Joint': left_swing,
            'lf1_Joint': -0.3 * np.abs(np.sin(phase)),
            'l_wheel_Joint': 0.2 * np.sin(time * 3),
            'rf0_Joint': right_swing,
            'rf1_Joint': -0.3 * np.abs(np.sin(phase + np.pi * 0.7)),
            'r_wheel_Joint': -0.2 * np.sin(time * 3)
        }
    
    def _jump_trajectory(self, time: float) -> Dict[str, float]:
        """跳跃轨迹"""
        jump_duration = 3.0
        phase = (time % jump_duration) / jump_duration
        
        if phase < 0.3:  # 蹲下
            leg_bend = -0.6 * (phase / 0.3)
        elif phase < 0.6:  # 起跳
            progress = (phase - 0.3) / 0.3
            leg_bend = -0.6 + 1.2 * progress
        else:  # 着陆
            progress = (phase - 0.6) / 0.4
            leg_bend = 0.6 * (1 - progress)
        
        return {joint: leg_bend for joint in self.joint_names}
    
    # ROS2服务回调函数
    def enable_callback(self, request, response):
        """使能控制器服务"""
        self.controller_enabled = request.data
        status = "启用" if self.controller_enabled else "禁用"
        response.success = True
        response.message = f'控制器已{status}'
        self.get_logger().info(response.message)
        return response
    
    def emergency_stop_callback(self, request, response):
        """紧急停止服务"""
        self.controller_enabled = False
        # 发布零力矩命令
        zero_commands = {name: 0.0 for name in self.joint_names}
        self.publish_control_commands(zero_commands)
        response.success = True
        response.message = '紧急停止已激活'
        self.get_logger().warn(response.message)
        return response
    
    def temp_set_motion_callback(self, request, response):
        """临时运动设置回调（使用Trigger服务）"""
        # 这里可以解析request.message来获取运动模式
        # 临时实现：默认设置为步行模式
        self.set_motion('walk')
        response.success = True
        response.message = '运动模式已设置为步行'
        return response
    
    def set_motion_callback(self, request, response):
        """设置运动模式服务"""
        motion_name = request.motion_name.lower()
        if self.set_motion(motion_name):
            response.success = True
            response.message = f'运动模式设置为: {motion_name}'
        else:
            response.success = False
            response.message = f'无效的运动模式: {motion_name}'
        return response
    
    def get_status_callback(self, request, response):
        """获取状态信息服务"""
        status_info = {
            'enabled': self.controller_enabled,
            'current_motion': self.current_motion,
            'control_frequency': self.control_frequency,
            'control_cycles': self.performance_stats['control_cycles'],
            'average_cycle_time': self.performance_stats['average_cycle_time']
        }
        
        response.success = True
        response.message = json.dumps(status_info)
        return response
    
    def destroy_node(self):
        """清理资源"""
        # 发布零力矩命令确保安全停止
        if hasattr(self, 'joint_command_pub'):
            zero_commands = {name: 0.0 for name in self.joint_names}
            self.publish_control_commands(zero_commands)
        
        super().destroy_node()


def main(args=None):
    """主函数"""
    rclpy.init(args=args)
    
    try:
        node = RMControllerNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        print("控制器节点被用户中断")
    except Exception as e:
        print(f"控制器节点运行出错: {e}")
    finally:
        if 'node' in locals():
            node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()