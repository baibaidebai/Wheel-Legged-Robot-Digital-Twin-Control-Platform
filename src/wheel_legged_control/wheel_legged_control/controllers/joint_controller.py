#!/usr/bin/env python3
"""
关节控制器节点
实现轮腿机器人的关节位置控制、PID控制算法和轨迹插值
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
from std_msgs.msg import Float64MultiArray, Header
from geometry_msgs.msg import Twist
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint


@dataclass
class ControlGains:
    """PID控制增益参数"""
    kp: float = 10.0  # 比例增益
    ki: float = 0.1   # 积分增益
    kd: float = 0.5   # 微分增益
    max_integral: float = 1.0  # 积分限幅
    max_output: float = 30.0   # 输出限幅 (N·m)


@dataclass
class JointLimits:
    """关节限制参数"""
    min_position: float = -np.pi  # 最小位置 (rad)
    max_position: float = np.pi   # 最大位置 (rad)
    max_velocity: float = 1000.0  # 最大速度 (rad/s)
    max_effort: float = 30.0      # 最大力矩 (N·m)


class PIDController:
    """PID控制器实现"""
    
    def __init__(self, gains: ControlGains):
        self.gains = gains
        self.reset()
    
    def reset(self):
        """重置PID状态"""
        self.prev_error = 0.0
        self.integral = 0.0
        self.prev_time = None
    
    def update(self, setpoint: float, current: float, dt: float) -> float:
        """
        更新PID控制器
        
        Args:
            setpoint: 目标值
            current: 当前值
            dt: 时间间隔
            
        Returns:
            控制输出
        """
        error = setpoint - current
        
        # 比例项
        proportional = self.gains.kp * error
        
        # 积分项
        self.integral += error * dt
        # 积分限幅
        self.integral = np.clip(self.integral, -self.gains.max_integral, self.gains.max_integral)
        integral = self.gains.ki * self.integral
        
        # 微分项
        if dt > 0:
            derivative = self.gains.kd * (error - self.prev_error) / dt
        else:
            derivative = 0.0
        
        # 总输出
        output = proportional + integral + derivative
        
        # 输出限幅
        output = np.clip(output, -self.gains.max_output, self.gains.max_output)
        
        # 更新状态
        self.prev_error = error
        
        return output


class JointControllerNode(Node):
    """
    关节控制器节点
    
    功能：
    - 接收关节位置指令
    - 实现PID控制算法
    - 发布关节状态
    - 处理关节限制和安全机制
    - 支持轨迹执行
    """
    
    def __init__(self):
        super().__init__('joint_controller')
        
        # 声明参数
        self.setup_parameters()
        
        # 初始化关节配置
        self.setup_joints()
        
        # 初始化PID控制器
        self.setup_controllers()
        
        # 创建发布者和订阅者
        self.setup_communication()
        
        # 初始化状态
        self.current_positions = {name: 0.0 for name in self.joint_names}
        self.current_velocities = {name: 0.0 for name in self.joint_names}
        self.current_efforts = {name: 0.0 for name in self.joint_names}
        self.target_positions = {name: 0.0 for name in self.joint_names}
        
        # 控制循环
        self.control_frequency = 100.0  # Hz
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
        
        # 创建服务
        self.setup_services()
        
        self.get_logger().info('关节控制器节点已启动')
        self.get_logger().info(f'控制关节: {self.joint_names}')
    
    def setup_parameters(self):
        """设置ROS2参数"""
        # 控制增益参数
        self.declare_parameter('control_gains.kp', 10.0)
        self.declare_parameter('control_gains.ki', 0.1)
        self.declare_parameter('control_gains.kd', 0.5)
        self.declare_parameter('control_gains.max_integral', 1.0)
        self.declare_parameter('control_gains.max_output', 30.0)
        
        # 关节限制参数
        self.declare_parameter('joint_limits.min_position', -3.14159)
        self.declare_parameter('joint_limits.max_position', 3.14159)
        self.declare_parameter('joint_limits.max_velocity', 1000.0)
        self.declare_parameter('joint_limits.max_effort', 30.0)
        
        # 控制频率
        self.declare_parameter('control_frequency', 100.0)
        
        # 关节名称列表
        self.declare_parameter('joint_names', [
            'lf0_joint', 'lf1_joint', 
            'rf0_joint', 'rf1_joint',
            'l_wheel_joint', 'r_wheel_joint'
        ])
    
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
        
        # 轮子关节特殊处理（连续旋转）
        for wheel_joint in ['l_wheel_joint', 'r_wheel_joint']:
            if wheel_joint in self.joint_limits:
                self.joint_limits[wheel_joint].min_position = -np.inf
                self.joint_limits[wheel_joint].max_position = np.inf
    
    def setup_controllers(self):
        """设置PID控制器"""
        gains = ControlGains(
            kp=self.get_parameter('control_gains.kp').value,
            ki=self.get_parameter('control_gains.ki').value,
            kd=self.get_parameter('control_gains.kd').value,
            max_integral=self.get_parameter('control_gains.max_integral').value,
            max_output=self.get_parameter('control_gains.max_output').value
        )
        
        self.pid_controllers = {}
        for joint_name in self.joint_names:
            self.pid_controllers[joint_name] = PIDController(gains)
    
    def setup_communication(self):
        """设置ROS2通信"""
        # QoS配置
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
    
    def setup_services(self):
        """设置ROS2服务"""
        # 导入服务类型
        from std_srvs.srv import Trigger, SetBool
        
        # 紧急停止服务
        self.emergency_stop_service = self.create_service(
            Trigger,
            '/joint_controller/emergency_stop',
            self.emergency_stop_service_callback
        )
        
        # 复位服务
        self.reset_service = self.create_service(
            Trigger,
            '/joint_controller/reset',
            self.reset_service_callback
        )
        
        # 使能服务
        self.enable_service = self.create_service(
            SetBool,
            '/joint_controller/enable',
            self.enable_service_callback
        )
        
        self.get_logger().info('ROS2服务已创建')
    
    def joint_command_callback(self, msg: Float64MultiArray):
        """
        处理关节位置指令
        
        Args:
            msg: 包含关节位置指令的消息
        """
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
                
                if target_pos != msg.data[i]:
                    self.get_logger().warn(
                        f'关节{joint_name}指令超出限制，已限制到{target_pos:.3f}'
                    )
            
            self.target_positions[joint_name] = target_pos
        
        self.get_logger().debug(f'收到关节指令: {dict(zip(self.joint_names, msg.data))}')
    
    def trajectory_callback(self, msg: JointTrajectory):
        """
        处理轨迹指令
        
        Args:
            msg: 关节轨迹消息
        """
        if not msg.points:
            self.get_logger().warn('收到空轨迹')
            return
        
        # 验证关节名称
        if set(msg.joint_names) != set(self.joint_names):
            self.get_logger().warn('轨迹关节名称与控制器不匹配')
            return
        
        with self.trajectory_lock:
            self.current_trajectory = msg
            self.trajectory_start_time = self.get_clock().now()
            self.trajectory_active = True
        
        self.get_logger().info(f'开始执行轨迹，包含{len(msg.points)}个点')
    
    def control_loop(self):
        """主控制循环"""
        # 检查控制器是否启用
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
            
            # PID控制
            effort = self.pid_controllers[joint_name].update(target, current, dt)
            
            # 应用力矩限制
            limits = self.joint_limits[joint_name]
            effort = np.clip(effort, -limits.max_effort, limits.max_effort)
            
            efforts[joint_name] = effort
            self.current_efforts[joint_name] = effort
        
        # 模拟关节运动（简化的积分器模型）
        self.simulate_joint_motion(efforts, dt)
        
        # 发布状态
        self.publish_joint_states(current_time)
        self.publish_joint_efforts(efforts)
    
    def update_trajectory_targets(self, current_time):
        """更新轨迹目标位置"""
        with self.trajectory_lock:
            if not self.trajectory_active or not self.current_trajectory:
                return
            
            # 计算轨迹执行时间
            elapsed_time = (current_time - self.trajectory_start_time).nanoseconds / 1e9
            
            # 查找当前轨迹点
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
                # 轨迹执行完成
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
                # 使用当前点
                for i, joint_name in enumerate(trajectory.joint_names):
                    if i < len(current_point.positions):
                        self.target_positions[joint_name] = current_point.positions[i]
            else:
                # 线性插值
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
        """
        简化的关节运动仿真
        
        Args:
            efforts: 关节力矩
            dt: 时间步长
        """
        for joint_name in self.joint_names:
            effort = efforts[joint_name]
            
            # 简化的动力学模型：τ = J * α (忽略摩擦和重力)
            # 假设关节惯量为0.1 kg·m²
            joint_inertia = 0.1
            acceleration = effort / joint_inertia
            
            # 更新速度和位置
            old_velocity = self.current_velocities[joint_name]
            new_velocity = old_velocity + acceleration * dt
            
            # 应用速度限制
            limits = self.joint_limits[joint_name]
            new_velocity = np.clip(new_velocity, -limits.max_velocity, limits.max_velocity)
            
            # 更新位置
            new_position = self.current_positions[joint_name] + new_velocity * dt
            
            # 应用位置限制（非连续关节）
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
    
    def set_joint_positions(self, positions: Dict[str, float]) -> bool:
        """
        设置关节位置
        
        Args:
            positions: 关节位置字典
            
        Returns:
            设置是否成功
        """
        try:
            for joint_name, position in positions.items():
                if joint_name in self.joint_names:
                    # 应用关节限制
                    limits = self.joint_limits[joint_name]
                    if not np.isinf(limits.min_position) and not np.isinf(limits.max_position):
                        position = np.clip(position, limits.min_position, limits.max_position)
                    
                    self.target_positions[joint_name] = position
                else:
                    self.get_logger().warn(f'未知关节: {joint_name}')
                    return False
            
            # 停止轨迹执行
            with self.trajectory_lock:
                self.trajectory_active = False
            
            return True
        except Exception as e:
            self.get_logger().error(f'设置关节位置失败: {e}')
            return False
    
    def get_joint_states(self) -> Dict[str, Tuple[float, float, float]]:
        """
        获取关节状态
        
        Returns:
            关节状态字典 (位置, 速度, 力矩)
        """
        states = {}
        for joint_name in self.joint_names:
            states[joint_name] = (
                self.current_positions[joint_name],
                self.current_velocities[joint_name],
                self.current_efforts[joint_name]
            )
        return states
    
    def emergency_stop(self):
        """紧急停止"""
        self.get_logger().warn('执行紧急停止')
        
        # 停止轨迹执行
        with self.trajectory_lock:
            self.trajectory_active = False
        
        # 将目标位置设为当前位置
        for joint_name in self.joint_names:
            self.target_positions[joint_name] = self.current_positions[joint_name]
        
        # 重置PID控制器
        for controller in self.pid_controllers.values():
            controller.reset()
    
    def reset_to_home(self):
        """复位到初始位置"""
        self.get_logger().info('复位到初始位置')
        
        home_positions = {name: 0.0 for name in self.joint_names}
        self.set_joint_positions(home_positions)
    
    def emergency_stop_service_callback(self, request, response):
        """紧急停止服务回调"""
        try:
            self.emergency_stop()
            response.success = True
            response.message = "紧急停止执行成功"
            self.get_logger().info("通过服务执行紧急停止")
        except Exception as e:
            response.success = False
            response.message = f"紧急停止失败: {str(e)}"
            self.get_logger().error(f"紧急停止服务失败: {e}")
        
        return response
    
    def reset_service_callback(self, request, response):
        """复位服务回调"""
        try:
            self.reset_to_home()
            response.success = True
            response.message = "复位执行成功"
            self.get_logger().info("通过服务执行复位")
        except Exception as e:
            response.success = False
            response.message = f"复位失败: {str(e)}"
            self.get_logger().error(f"复位服务失败: {e}")
        
        return response
    
    def enable_service_callback(self, request, response):
        """使能服务回调"""
        try:
            self.controller_enabled = request.data
            if request.data:
                response.message = "控制器已启用"
                self.get_logger().info("控制器已启用")
            else:
                response.message = "控制器已禁用"
                self.get_logger().info("控制器已禁用")
                # 禁用时停止当前运动
                self.emergency_stop()
            
            response.success = True
        except Exception as e:
            response.success = False
            response.message = f"设置使能状态失败: {str(e)}"
            self.get_logger().error(f"使能服务失败: {e}")
        
        return response
    
    def enable(self):
        """启用控制器"""
        self.controller_enabled = True
        self.get_logger().info("控制器已启用")
    
    def disable(self):
        """禁用控制器"""
        self.controller_enabled = False
        self.emergency_stop()
        self.get_logger().info("控制器已禁用")


def main(args=None):
    """主函数"""
    rclpy.init(args=args)
    
    try:
        node = JointControllerNode()
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