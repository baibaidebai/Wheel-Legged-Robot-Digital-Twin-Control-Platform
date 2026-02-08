#!/usr/bin/env python3
"""
增强型关节控制器节点

集成算法管理器，支持多种控制算法动态切换和性能监控。
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import threading
import time

# ROS2消息类型
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64MultiArray, Header, String
from geometry_msgs.msg import Twist
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

# 导入算法管理器
from wheel_legged_control.algorithms.algorithm_manager import (
    AlgorithmManager, AlgorithmType, AlgorithmConfig, BaseAlgorithm,
    create_default_algorithms
)


class RobotSpecificPIDAlgorithm(BaseAlgorithm):
    """机器人专用PID控制算法"""
    
    def __init__(self, config: AlgorithmConfig):
        super().__init__(config)
        self.kp = config.parameters.get('kp', 10.0)
        self.ki = config.parameters.get('ki', 0.1)
        self.kd = config.parameters.get('kd', 0.5)
        self.max_integral = config.parameters.get('max_integral', 1.0)
        self.max_output = config.parameters.get('max_output', 30.0)
        
        # 每个关节的PID状态
        self.joint_states = {}
        
    def initialize(self) -> bool:
        """初始化PID控制器"""
        try:
            self.joint_states = {}
            self.status = self.status.IDLE
            self.logger.info(f"机器人PID控制器初始化成功: kp={self.kp}, ki={self.ki}, kd={self.kd}")
            return True
        except Exception as e:
            self.logger.error(f"机器人PID控制器初始化失败: {e}")
            return False
    
    def execute(self, inputs: Dict[str, any]) -> Dict[str, any]:
        """执行PID控制"""
        try:
            joint_name = inputs.get('joint_name')
            setpoint = inputs.get('setpoint', 0.0)
            current_value = inputs.get('current_value', 0.0)
            dt = inputs.get('dt', 0.01)
            
            if joint_name not in self.joint_states:
                self.joint_states[joint_name] = {
                    'prev_error': 0.0,
                    'integral': 0.0
                }
            
            state = self.joint_states[joint_name]
            
            # 计算误差
            error = setpoint - current_value
            
            # 比例项
            proportional = self.kp * error
            
            # 积分项
            state['integral'] += error * dt
            state['integral'] = np.clip(state['integral'], -self.max_integral, self.max_integral)
            integral = self.ki * state['integral']
            
            # 微分项
            if dt > 0:
                derivative = self.kd * (error - state['prev_error']) / dt
            else:
                derivative = 0.0
            
            # 控制输出
            output = proportional + integral + derivative
            output = np.clip(output, -self.max_output, self.max_output)
            
            # 更新状态
            state['prev_error'] = error
            
            return {
                'output': output,
                'error': error,
                'proportional': proportional,
                'integral': integral,
                'derivative': derivative,
                'joint_name': joint_name
            }
            
        except Exception as e:
            self.logger.error(f"机器人PID控制执行失败: {e}")
            raise
    
    def cleanup(self) -> bool:
        """清理PID控制器"""
        try:
            self.joint_states = {}
            self.status = self.status.STOPPED
            return True
        except Exception as e:
            self.logger.error(f"机器人PID控制器清理失败: {e}")
            return False


class AdaptivePIDAlgorithm(BaseAlgorithm):
    """自适应PID控制算法"""
    
    def __init__(self, config: AlgorithmConfig):
        super().__init__(config)
        self.base_kp = config.parameters.get('base_kp', 10.0)
        self.base_ki = config.parameters.get('base_ki', 0.1)
        self.base_kd = config.parameters.get('base_kd', 0.5)
        self.adaptation_rate = config.parameters.get('adaptation_rate', 0.01)
        self.max_output = config.parameters.get('max_output', 30.0)
        
        self.joint_states = {}
        
    def initialize(self) -> bool:
        """初始化自适应PID控制器"""
        try:
            self.joint_states = {}
            self.status = self.status.IDLE
            self.logger.info("自适应PID控制器初始化成功")
            return True
        except Exception as e:
            self.logger.error(f"自适应PID控制器初始化失败: {e}")
            return False
    
    def execute(self, inputs: Dict[str, any]) -> Dict[str, any]:
        """执行自适应PID控制"""
        try:
            joint_name = inputs.get('joint_name')
            setpoint = inputs.get('setpoint', 0.0)
            current_value = inputs.get('current_value', 0.0)
            dt = inputs.get('dt', 0.01)
            
            if joint_name not in self.joint_states:
                self.joint_states[joint_name] = {
                    'prev_error': 0.0,
                    'integral': 0.0,
                    'kp': self.base_kp,
                    'ki': self.base_ki,
                    'kd': self.base_kd,
                    'error_history': []
                }
            
            state = self.joint_states[joint_name]
            error = setpoint - current_value
            
            # 记录误差历史
            state['error_history'].append(abs(error))
            if len(state['error_history']) > 10:
                state['error_history'].pop(0)
            
            # 自适应调整增益
            if len(state['error_history']) >= 5:
                avg_error = np.mean(state['error_history'][-5:])
                if avg_error > 0.1:  # 误差较大，增加增益
                    state['kp'] = min(state['kp'] * (1 + self.adaptation_rate), self.base_kp * 2)
                elif avg_error < 0.01:  # 误差较小，减少增益
                    state['kp'] = max(state['kp'] * (1 - self.adaptation_rate), self.base_kp * 0.5)
            
            # PID计算
            proportional = state['kp'] * error
            
            state['integral'] += error * dt
            state['integral'] = np.clip(state['integral'], -1.0, 1.0)
            integral = state['ki'] * state['integral']
            
            if dt > 0:
                derivative = state['kd'] * (error - state['prev_error']) / dt
            else:
                derivative = 0.0
            
            output = proportional + integral + derivative
            output = np.clip(output, -self.max_output, self.max_output)
            
            state['prev_error'] = error
            
            return {
                'output': output,
                'error': error,
                'proportional': proportional,
                'integral': integral,
                'derivative': derivative,
                'adaptive_kp': state['kp'],
                'joint_name': joint_name
            }
            
        except Exception as e:
            self.logger.error(f"自适应PID控制执行失败: {e}")
            raise
    
    def cleanup(self) -> bool:
        """清理自适应PID控制器"""
        try:
            self.joint_states = {}
            self.status = self.status.STOPPED
            return True
        except Exception as e:
            self.logger.error(f"自适应PID控制器清理失败: {e}")
            return False


@dataclass
class JointLimits:
    """关节限制参数"""
    min_position: float = -np.pi
    max_position: float = np.pi
    max_velocity: float = 1000.0
    max_effort: float = 30.0


class EnhancedJointControllerNode(Node):
    """
    增强型关节控制器节点
    
    功能：
    - 集成算法管理器
    - 支持多种控制算法动态切换
    - 性能监控和记录
    - 算法性能比较
    """
    
    def __init__(self):
        super().__init__('enhanced_joint_controller')
        
        # 初始化算法管理器
        self.algorithm_manager = AlgorithmManager()
        self.setup_algorithms()
        
        # 声明参数
        self.setup_parameters()
        
        # 初始化关节配置
        self.setup_joints()
        
        # 创建发布者和订阅者
        self.setup_communication()
        
        # 初始化状态
        self.current_positions = {name: 0.0 for name in self.joint_names}
        self.current_velocities = {name: 0.0 for name in self.joint_names}
        self.current_efforts = {name: 0.0 for name in self.joint_names}
        self.target_positions = {name: 0.0 for name in self.joint_names}
        
        # 控制循环
        self.control_frequency = 100.0
        self.control_timer = self.create_timer(
            1.0 / self.control_frequency,
            self.control_loop
        )
        
        # 轨迹执行状态
        self.trajectory_active = False
        self.trajectory_start_time = None
        self.current_trajectory = None
        self.trajectory_lock = threading.Lock()
        
        # 控制器状态
        self.controller_enabled = True
        self.current_algorithm = 'robot_pid'  # 默认算法
        
        # 性能监控
        self.performance_data = []
        self.last_performance_report_time = time.time()
        
        # 创建服务
        self.setup_services()
        
        # 启动算法管理器监控
        self.algorithm_manager.start_monitoring()
        
        self.get_logger().info('增强型关节控制器节点已启动')
        self.get_logger().info(f'控制关节: {self.joint_names}')
        self.get_logger().info(f'可用算法: {list(self.algorithm_manager.algorithms.keys())}')
    
    def setup_algorithms(self):
        """设置控制算法"""
        # 注册算法工厂
        self.algorithm_manager.register_algorithm_factory('robot_pid', RobotSpecificPIDAlgorithm)
        self.algorithm_manager.register_algorithm_factory('adaptive_pid', AdaptivePIDAlgorithm)
        
        # 创建机器人专用PID算法
        robot_pid_config = AlgorithmConfig(
            name="机器人专用PID控制器",
            algorithm_type=AlgorithmType.CONTROL,
            parameters={
                'kp': 10.0,
                'ki': 0.1,
                'kd': 0.5,
                'max_integral': 1.0,
                'max_output': 30.0
            },
            priority=2
        )
        
        # 创建自适应PID算法
        adaptive_pid_config = AlgorithmConfig(
            name="自适应PID控制器",
            algorithm_type=AlgorithmType.CONTROL,
            parameters={
                'base_kp': 10.0,
                'base_ki': 0.1,
                'base_kd': 0.5,
                'adaptation_rate': 0.01,
                'max_output': 30.0
            },
            priority=1
        )
        
        # 创建算法实例
        success = True
        success &= self.algorithm_manager.create_algorithm('robot_pid', 'robot_pid', robot_pid_config)
        success &= self.algorithm_manager.create_algorithm('adaptive_pid', 'adaptive_pid', adaptive_pid_config)
        
        if success:
            # 设置默认活跃算法
            self.algorithm_manager.set_active_algorithm(AlgorithmType.CONTROL, 'robot_pid')
            self.get_logger().info("算法管理器初始化成功")
        else:
            self.get_logger().error("算法管理器初始化失败")
    
    def setup_parameters(self):
        """设置ROS2参数"""
        # 控制频率
        self.declare_parameter('control_frequency', 100.0)
        
        # 关节名称列表
        self.declare_parameter('joint_names', [
            'lf0_joint', 'lf1_joint',
            'rf0_joint', 'rf1_joint',
            'l_wheel_joint', 'r_wheel_joint'
        ])
        
        # 关节限制参数
        self.declare_parameter('joint_limits.min_position', -3.14159)
        self.declare_parameter('joint_limits.max_position', 3.14159)
        self.declare_parameter('joint_limits.max_velocity', 1000.0)
        self.declare_parameter('joint_limits.max_effort', 30.0)
        
        # 性能监控参数
        self.declare_parameter('performance_report_interval', 10.0)  # 秒
    
    def setup_joints(self):
        """设置关节配置"""
        self.joint_names = self.get_parameter('joint_names').value
        
        # 创建关节限制
        self.joint_limits = {}
        for joint_name in self.joint_names:
            self.joint_limits[joint_name] = JointLimits(
                min_position=self.get_parameter('joint_limits.min_position').value,
                max_position=self.get_parameter('joint_limits.max_position').value,
                max_velocity=self.get_parameter('joint_limits.max_velocity').value,
                max_effort=self.get_parameter('joint_limits.max_effort').value
            )
        
        # 轮子关节特殊处理
        for wheel_joint in ['l_wheel_joint', 'r_wheel_joint']:
            if wheel_joint in self.joint_limits:
                self.joint_limits[wheel_joint].min_position = -np.inf
                self.joint_limits[wheel_joint].max_position = np.inf
    
    def setup_communication(self):
        """设置ROS2通信"""
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
            depth=10
        )
        
        # 订阅者
        self.joint_command_sub = self.create_subscription(
            Float64MultiArray,
            '/joint_commands',
            self.joint_command_callback,
            qos_profile
        )
        
        self.trajectory_sub = self.create_subscription(
            JointTrajectory,
            '/joint_trajectory',
            self.trajectory_callback,
            qos_profile
        )
        
        self.algorithm_switch_sub = self.create_subscription(
            String,
            '/algorithm_switch',
            self.algorithm_switch_callback,
            qos_profile
        )
        
        # 发布者
        self.joint_state_pub = self.create_publisher(
            JointState,
            '/joint_states',
            qos_profile
        )
        
        self.joint_effort_pub = self.create_publisher(
            Float64MultiArray,
            '/joint_efforts',
            qos_profile
        )
        
        self.performance_pub = self.create_publisher(
            String,
            '/algorithm_performance',
            qos_profile
        )
        
        self.algorithm_status_pub = self.create_publisher(
            String,
            '/algorithm_status',
            qos_profile
        )
    
    def setup_services(self):
        """设置ROS2服务"""
        from std_srvs.srv import Trigger, SetBool
        from std_msgs.srv import SetString
        
        # 紧急停止服务
        self.emergency_stop_service = self.create_service(
            Trigger,
            '/enhanced_joint_controller/emergency_stop',
            self.emergency_stop_service_callback
        )
        
        # 复位服务
        self.reset_service = self.create_service(
            Trigger,
            '/enhanced_joint_controller/reset',
            self.reset_service_callback
        )
        
        # 使能服务
        self.enable_service = self.create_service(
            SetBool,
            '/enhanced_joint_controller/enable',
            self.enable_service_callback
        )
        
        # 算法切换服务
        self.algorithm_switch_service = self.create_service(
            SetString,
            '/enhanced_joint_controller/switch_algorithm',
            self.algorithm_switch_service_callback
        )
        
        self.get_logger().info('ROS2服务已创建')
    
    def joint_command_callback(self, msg: Float64MultiArray):
        """处理关节位置指令"""
        if len(msg.data) != len(self.joint_names):
            self.get_logger().warn(
                f'关节指令数量不匹配: 期望{len(self.joint_names)}, 收到{len(msg.data)}'
            )
            return
        
        # 停止当前轨迹执行
        with self.trajectory_lock:
            self.trajectory_active = False
        
        # 更新目标位置
        for i, joint_name in enumerate(self.joint_names):
            target_pos = msg.data[i]
            
            # 应用关节限制
            limits = self.joint_limits[joint_name]
            if not np.isinf(limits.min_position) and not np.isinf(limits.max_position):
                target_pos = np.clip(target_pos, limits.min_position, limits.max_position)
            
            self.target_positions[joint_name] = target_pos
        
        self.get_logger().debug(f'收到关节指令: {dict(zip(self.joint_names, msg.data))}')
    
    def trajectory_callback(self, msg: JointTrajectory):
        """处理轨迹指令"""
        if not msg.points:
            self.get_logger().warn('收到空轨迹')
            return
        
        if set(msg.joint_names) != set(self.joint_names):
            self.get_logger().warn('轨迹关节名称与控制器不匹配')
            return
        
        with self.trajectory_lock:
            self.current_trajectory = msg
            self.trajectory_start_time = self.get_clock().now()
            self.trajectory_active = True
        
        self.get_logger().info(f'开始执行轨迹，包含{len(msg.points)}个点')
    
    def algorithm_switch_callback(self, msg: String):
        """处理算法切换指令"""
        algorithm_name = msg.data
        if self.switch_algorithm(algorithm_name):
            self.get_logger().info(f'算法已切换到: {algorithm_name}')
        else:
            self.get_logger().error(f'算法切换失败: {algorithm_name}')
    
    def control_loop(self):
        """主控制循环"""
        if not self.controller_enabled:
            return
        
        current_time = self.get_clock().now()
        dt = 1.0 / self.control_frequency
        
        # 处理轨迹执行
        self.update_trajectory_targets(current_time)
        
        # 计算控制输出
        efforts = {}
        for joint_name in self.joint_names:
            target = self.target_positions[joint_name]
            current = self.current_positions[joint_name]
            
            # 使用算法管理器执行控制算法
            control_inputs = {
                'joint_name': joint_name,
                'setpoint': target,
                'current_value': current,
                'dt': dt
            }
            
            result = self.algorithm_manager.execute_algorithm(AlgorithmType.CONTROL, control_inputs)
            
            if result:
                effort = result['output']
                
                # 应用力矩限制
                limits = self.joint_limits[joint_name]
                effort = np.clip(effort, -limits.max_effort, limits.max_effort)
                
                efforts[joint_name] = effort
                self.current_efforts[joint_name] = effort
            else:
                # 算法执行失败，使用零力矩
                efforts[joint_name] = 0.0
                self.current_efforts[joint_name] = 0.0
        
        # 模拟关节运动
        self.simulate_joint_motion(efforts, dt)
        
        # 发布状态
        self.publish_joint_states(current_time)
        self.publish_joint_efforts(efforts)
        
        # 定期发布性能报告
        self.publish_performance_report()
    
    def update_trajectory_targets(self, current_time):
        """更新轨迹目标位置（与原版相同）"""
        with self.trajectory_lock:
            if not self.trajectory_active or not self.current_trajectory:
                return
            
            elapsed_time = (current_time - self.trajectory_start_time).nanoseconds / 1e9
            trajectory = self.current_trajectory
            current_point = None
            next_point = None
            
            for i, point in enumerate(trajectory.points):
                point_time = point.time_from_start.sec + point.time_from_start.nanosec / 1e9
                
                if elapsed_time <= point_time:
                    if i == 0:
                        current_point = point
                    else:
                        current_point = trajectory.points[i-1]
                        next_point = point
                    break
            
            if current_point is None:
                if trajectory.points:
                    final_point = trajectory.points[-1]
                    for i, joint_name in enumerate(trajectory.joint_names):
                        if i < len(final_point.positions):
                            self.target_positions[joint_name] = final_point.positions[i]
                
                self.trajectory_active = False
                self.get_logger().info('轨迹执行完成')
                return
            
            # 插值计算目标位置
            if next_point is None:
                for i, joint_name in enumerate(trajectory.joint_names):
                    if i < len(current_point.positions):
                        self.target_positions[joint_name] = current_point.positions[i]
            else:
                current_time_point = (current_point.time_from_start.sec + 
                                    current_point.time_from_start.nanosec / 1e9)
                next_time_point = (next_point.time_from_start.sec + 
                                 next_point.time_from_start.nanosec / 1e9)
                
                if next_time_point > current_time_point:
                    alpha = ((elapsed_time - current_time_point) / 
                           (next_time_point - current_time_point))
                    alpha = np.clip(alpha, 0.0, 1.0)
                    
                    for i, joint_name in enumerate(trajectory.joint_names):
                        if (i < len(current_point.positions) and 
                            i < len(next_point.positions)):
                            pos1 = current_point.positions[i]
                            pos2 = next_point.positions[i]
                            interpolated_pos = pos1 + alpha * (pos2 - pos1)
                            self.target_positions[joint_name] = interpolated_pos
    
    def simulate_joint_motion(self, efforts: Dict[str, float], dt: float):
        """简化的关节运动仿真（与原版相同）"""
        for joint_name in self.joint_names:
            effort = efforts[joint_name]
            
            joint_inertia = 0.1
            acceleration = effort / joint_inertia
            
            old_velocity = self.current_velocities[joint_name]
            new_velocity = old_velocity + acceleration * dt
            
            limits = self.joint_limits[joint_name]
            new_velocity = np.clip(new_velocity, -limits.max_velocity, limits.max_velocity)
            
            new_position = self.current_positions[joint_name] + new_velocity * dt
            
            if not np.isinf(limits.min_position) and not np.isinf(limits.max_position):
                new_position = np.clip(new_position, limits.min_position, limits.max_position)
            
            self.current_velocities[joint_name] = new_velocity
            self.current_positions[joint_name] = new_position
    
    def publish_joint_states(self, timestamp):
        """发布关节状态"""
        msg = JointState()
        msg.header = Header()
        msg.header.stamp = timestamp.to_msg()
        msg.header.frame_id = 'base_link'
        
        msg.name = self.joint_names
        msg.position = [self.current_positions[name] for name in self.joint_names]
        msg.velocity = [self.current_velocities[name] for name in self.joint_names]
        msg.effort = [self.current_efforts[name] for name in self.joint_names]
        
        self.joint_state_pub.publish(msg)
    
    def publish_joint_efforts(self, efforts: Dict[str, float]):
        """发布关节力矩"""
        msg = Float64MultiArray()
        msg.data = [efforts[name] for name in self.joint_names]
        self.joint_effort_pub.publish(msg)
    
    def publish_performance_report(self):
        """发布性能报告"""
        current_time = time.time()
        report_interval = self.get_parameter('performance_report_interval').value
        
        if current_time - self.last_performance_report_time >= report_interval:
            report = self.algorithm_manager.get_performance_report()
            
            # 发布性能数据
            performance_msg = String()
            performance_msg.data = str(report)
            self.performance_pub.publish(performance_msg)
            
            # 发布算法状态
            status_msg = String()
            active_algorithms = self.algorithm_manager.get_active_algorithms()
            status_msg.data = f"Active: {active_algorithms}"
            self.algorithm_status_pub.publish(status_msg)
            
            self.last_performance_report_time = current_time
            
            # 记录性能日志
            for alg_id, info in report['algorithms'].items():
                if info['total_calls'] > 0:
                    self.get_logger().info(
                        f"算法 {alg_id}: 调用{info['total_calls']}次, "
                        f"成功率{info['success_rate']:.2%}, "
                        f"平均执行时间{info['avg_execution_time']:.2f}ms"
                    )
    
    def switch_algorithm(self, algorithm_name: str) -> bool:
        """切换控制算法"""
        if algorithm_name in self.algorithm_manager.algorithms:
            success = self.algorithm_manager.set_active_algorithm(AlgorithmType.CONTROL, algorithm_name)
            if success:
                self.current_algorithm = algorithm_name
                self.get_logger().info(f'算法已切换到: {algorithm_name}')
                return True
        
        self.get_logger().error(f'算法切换失败: {algorithm_name}')
        return False
    
    def emergency_stop(self):
        """紧急停止"""
        self.get_logger().warn('执行紧急停止')
        
        with self.trajectory_lock:
            self.trajectory_active = False
        
        for joint_name in self.joint_names:
            self.target_positions[joint_name] = self.current_positions[joint_name]
    
    def reset_to_home(self):
        """复位到初始位置"""
        self.get_logger().info('复位到初始位置')
        home_positions = {name: 0.0 for name in self.joint_names}
        for joint_name, position in home_positions.items():
            self.target_positions[joint_name] = position
    
    def emergency_stop_service_callback(self, request, response):
        """紧急停止服务回调"""
        try:
            self.emergency_stop()
            response.success = True
            response.message = "紧急停止执行成功"
        except Exception as e:
            response.success = False
            response.message = f"紧急停止失败: {str(e)}"
        return response
    
    def reset_service_callback(self, request, response):
        """复位服务回调"""
        try:
            self.reset_to_home()
            response.success = True
            response.message = "复位执行成功"
        except Exception as e:
            response.success = False
            response.message = f"复位失败: {str(e)}"
        return response
    
    def enable_service_callback(self, request, response):
        """使能服务回调"""
        try:
            self.controller_enabled = request.data
            if request.data:
                response.message = "控制器已启用"
            else:
                response.message = "控制器已禁用"
                self.emergency_stop()
            response.success = True
        except Exception as e:
            response.success = False
            response.message = f"设置使能状态失败: {str(e)}"
        return response
    
    def algorithm_switch_service_callback(self, request, response):
        """算法切换服务回调"""
        try:
            success = self.switch_algorithm(request.data)
            response.success = success
            if success:
                response.message = f"算法已切换到: {request.data}"
            else:
                response.message = f"算法切换失败: {request.data}"
        except Exception as e:
            response.success = False
            response.message = f"算法切换服务失败: {str(e)}"
        return response
    
    def __del__(self):
        """析构函数"""
        if hasattr(self, 'algorithm_manager'):
            self.algorithm_manager.cleanup()


def main(args=None):
    """主函数"""
    rclpy.init(args=args)
    
    try:
        node = EnhancedJointControllerNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f'节点运行错误: {e}')
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()