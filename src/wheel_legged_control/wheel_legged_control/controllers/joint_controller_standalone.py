#!/usr/bin/env python3
"""
独立关节控制器类

用于测试和非ROS2环境的关节控制功能。
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import time


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


class JointController:
    """
    独立关节控制器类
    
    功能：
    - PID控制算法
    - 关节限制检查
    - 轨迹生成和插值
    - 安全机制
    """
    
    def __init__(self, joint_names: List[str]):
        self.joint_names = joint_names
        
        # 初始化关节状态
        self.current_positions = {name: 0.0 for name in joint_names}
        self.current_velocities = {name: 0.0 for name in joint_names}
        self.current_efforts = {name: 0.0 for name in joint_names}
        self.target_positions = {name: 0.0 for name in joint_names}
        
        # 初始化关节限制
        self.joint_limits = {}
        for joint_name in joint_names:
            self.joint_limits[joint_name] = JointLimits()
        
        # 初始化PID控制器
        self.pid_controllers = {}
        default_gains = ControlGains()
        for joint_name in joint_names:
            self.pid_controllers[joint_name] = PIDController(default_gains)
        
        # 控制器状态
        self.controller_enabled = True
        self.last_update_time = time.time()
    
    def set_joint_limits(self, limits: Dict[str, Tuple[float, float]]):
        """
        设置关节限制
        
        Args:
            limits: 关节限制字典 {joint_name: (min_pos, max_pos)}
        """
        for joint_name, (min_pos, max_pos) in limits.items():
            if joint_name in self.joint_limits:
                self.joint_limits[joint_name].min_position = min_pos
                self.joint_limits[joint_name].max_position = max_pos
    
    def set_pid_parameters(self, pid_params: Dict[str, Dict[str, float]]):
        """
        设置PID参数
        
        Args:
            pid_params: PID参数字典 {joint_name: {kp, ki, kd}}
        """
        for joint_name, params in pid_params.items():
            if joint_name in self.pid_controllers:
                gains = ControlGains(
                    kp=params.get('kp', 10.0),
                    ki=params.get('ki', 0.1),
                    kd=params.get('kd', 0.5),
                    max_integral=params.get('max_integral', 1.0),
                    max_output=params.get('max_output', 30.0)
                )
                self.pid_controllers[joint_name] = PIDController(gains)
    
    def set_target_positions(self, positions: Dict[str, float]):
        """
        设置目标位置
        
        Args:
            positions: 目标位置字典
        """
        for joint_name, position in positions.items():
            if joint_name in self.joint_names:
                # 应用关节限制
                limits = self.joint_limits[joint_name]
                position = np.clip(position, limits.min_position, limits.max_position)
                self.target_positions[joint_name] = position
    
    def compute_control(self, target_positions: List[float], current_positions: List[float]) -> List[float]:
        """
        计算控制输出
        
        Args:
            target_positions: 目标位置列表
            current_positions: 当前位置列表
            
        Returns:
            控制输出列表
        """
        if len(target_positions) != len(self.joint_names):
            raise ValueError(f"目标位置数量不匹配。期望: {len(self.joint_names)}, 实际: {len(target_positions)}")
        
        if len(current_positions) != len(self.joint_names):
            raise ValueError(f"当前位置数量不匹配。期望: {len(self.joint_names)}, 实际: {len(current_positions)}")
        
        # 更新当前状态
        for i, joint_name in enumerate(self.joint_names):
            self.current_positions[joint_name] = current_positions[i]
            self.target_positions[joint_name] = target_positions[i]
        
        # 计算时间间隔
        current_time = time.time()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # 计算控制输出
        control_outputs = []
        for i, joint_name in enumerate(self.joint_names):
            if not self.controller_enabled:
                control_outputs.append(0.0)
                continue
            
            target = target_positions[i]
            current = current_positions[i]
            
            # 应用关节限制
            limits = self.joint_limits[joint_name]
            target = np.clip(target, limits.min_position, limits.max_position)
            
            # PID控制
            effort = self.pid_controllers[joint_name].update(target, current, dt)
            
            # 应用力矩限制
            effort = np.clip(effort, -limits.max_effort, limits.max_effort)
            
            control_outputs.append(effort)
            self.current_efforts[joint_name] = effort
        
        return control_outputs
    
    def generate_trajectory(self, start_positions: List[float], end_positions: List[float], 
                          duration: float, num_points: int = 50) -> List[List[float]]:
        """
        生成轨迹
        
        Args:
            start_positions: 起始位置
            end_positions: 结束位置
            duration: 持续时间
            num_points: 轨迹点数量
            
        Returns:
            轨迹点列表
        """
        if len(start_positions) != len(self.joint_names):
            raise ValueError("起始位置数量不匹配")
        
        if len(end_positions) != len(self.joint_names):
            raise ValueError("结束位置数量不匹配")
        
        trajectory = []
        
        for i in range(num_points):
            t = i / (num_points - 1)  # 归一化时间 [0, 1]
            
            # 使用三次多项式插值
            # s(t) = 2t³ - 3t² + 1 (起始位置权重)
            # e(t) = -2t³ + 3t² (结束位置权重)
            s_weight = 2 * t**3 - 3 * t**2 + 1
            e_weight = -2 * t**3 + 3 * t**2
            
            point = []
            for j in range(len(self.joint_names)):
                pos = s_weight * start_positions[j] + e_weight * end_positions[j]
                
                # 应用关节限制
                limits = self.joint_limits[self.joint_names[j]]
                pos = np.clip(pos, limits.min_position, limits.max_position)
                
                point.append(pos)
            
            trajectory.append(point)
        
        return trajectory
    
    def get_joint_states(self) -> Dict[str, Tuple[float, float, float]]:
        """
        获取关节状态
        
        Returns:
            关节状态字典 {joint_name: (position, velocity, effort)}
        """
        states = {}
        for joint_name in self.joint_names:
            states[joint_name] = (
                self.current_positions[joint_name],
                self.current_velocities[joint_name],
                self.current_efforts[joint_name]
            )
        return states
    
    def reset(self):
        """重置控制器"""
        # 重置PID控制器
        for controller in self.pid_controllers.values():
            controller.reset()
        
        # 重置目标位置为当前位置
        for joint_name in self.joint_names:
            self.target_positions[joint_name] = self.current_positions[joint_name]
    
    def emergency_stop(self):
        """紧急停止"""
        self.controller_enabled = False
        self.reset()
    
    def enable(self):
        """启用控制器"""
        self.controller_enabled = True
    
    def disable(self):
        """禁用控制器"""
        self.controller_enabled = False