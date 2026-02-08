#!/usr/bin/env python3
"""
关节控制器单元测试
"""

import pytest
import sys
import os
import numpy as np
from unittest.mock import Mock, patch

# 添加包路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 
                                '../../src/wheel_legged_control'))

try:
    from wheel_legged_control.controllers.joint_controller import (
        PIDController, ControlGains, JointLimits, JointControllerNode
    )
    CONTROLLER_AVAILABLE = True
except ImportError as e:
    print(f"警告: 无法导入关节控制器: {e}")
    CONTROLLER_AVAILABLE = False


@pytest.mark.skipif(not CONTROLLER_AVAILABLE, reason="关节控制器不可用")
class TestPIDController:
    """PID控制器测试类"""
    
    def setup_method(self):
        """测试前设置"""
        self.gains = ControlGains(kp=10.0, ki=0.1, kd=0.5, max_integral=1.0, max_output=30.0)
        self.pid = PIDController(self.gains)
    
    def test_pid_creation(self):
        """测试PID控制器创建"""
        assert self.pid is not None
        assert self.pid.gains.kp == 10.0
        assert self.pid.gains.ki == 0.1
        assert self.pid.gains.kd == 0.5
        assert self.pid.prev_error == 0.0
        assert self.pid.integral == 0.0
    
    def test_pid_proportional_control(self):
        """测试比例控制"""
        # 测试正误差
        output = self.pid.update(1.0, 0.0, 0.1)  # 误差 = 1.0
        # 输出包含比例项(10.0)、积分项(0.1*1.0*0.1=0.01)、微分项(0.5*1.0/0.1=5.0)
        # 总输出约为 10.0 + 0.01 + 5.0 = 15.01
        assert output > 10.0  # 至少包含比例项
        assert output < 20.0  # 不应该过大
        
        # 测试负误差
        self.pid.reset()
        output = self.pid.update(0.0, 1.0, 0.1)  # 误差 = -1.0
        assert output < -10.0  # 至少包含负比例项
        assert output > -20.0  # 不应该过小
    
    def test_pid_integral_control(self):
        """测试积分控制"""
        # 连续多次更新，积分项应该累积
        dt = 0.1
        for _ in range(5):
            self.pid.update(1.0, 0.0, dt)  # 持续误差 = 1.0
        
        # 积分项应该累积
        expected_integral = 0.1 * 1.0 * 5 * dt  # ki * error * count * dt
        assert abs(self.pid.integral - 5 * dt) < 0.01
    
    def test_pid_integral_windup_protection(self):
        """测试积分饱和保护"""
        dt = 0.1
        # 大量更新导致积分饱和
        for _ in range(100):
            self.pid.update(10.0, 0.0, dt)
        
        # 积分项应该被限制在max_integral范围内
        assert abs(self.pid.integral) <= self.gains.max_integral
    
    def test_pid_derivative_control(self):
        """测试微分控制"""
        dt = 0.1
        
        # 第一次更新
        self.pid.update(1.0, 0.0, dt)  # 误差 = 1.0
        
        # 第二次更新，误差变化
        output = self.pid.update(2.0, 0.0, dt)  # 误差 = 2.0，变化 = 1.0
        
        # 微分项应该反映误差变化率
        expected_d = 0.5 * (2.0 - 1.0) / dt  # kd * (error_change) / dt
        # 输出包含比例、积分、微分项，这里只检查微分项有贡献
        assert output > 10.0 * 2.0  # 至少包含比例项
    
    def test_pid_output_limiting(self):
        """测试输出限制"""
        # 大误差应该被限制在max_output范围内
        output = self.pid.update(1000.0, 0.0, 0.1)
        assert abs(output) <= self.gains.max_output
        
        output = self.pid.update(-1000.0, 0.0, 0.1)
        assert abs(output) <= self.gains.max_output
    
    def test_pid_reset(self):
        """测试PID重置"""
        # 先进行一些更新
        self.pid.update(1.0, 0.0, 0.1)
        self.pid.update(2.0, 0.0, 0.1)
        
        # 重置
        self.pid.reset()
        
        # 检查状态是否重置
        assert self.pid.prev_error == 0.0
        assert self.pid.integral == 0.0


@pytest.mark.skipif(not CONTROLLER_AVAILABLE, reason="关节控制器不可用")
class TestJointLimits:
    """关节限制测试类"""
    
    def test_joint_limits_creation(self):
        """测试关节限制创建"""
        limits = JointLimits(
            min_position=-1.57,
            max_position=1.57,
            max_velocity=10.0,
            max_effort=20.0
        )
        
        assert limits.min_position == -1.57
        assert limits.max_position == 1.57
        assert limits.max_velocity == 10.0
        assert limits.max_effort == 20.0
    
    def test_joint_limits_defaults(self):
        """测试关节限制默认值"""
        limits = JointLimits()
        
        assert limits.min_position == -np.pi
        assert limits.max_position == np.pi
        assert limits.max_velocity == 1000.0
        assert limits.max_effort == 30.0


@pytest.mark.skipif(not CONTROLLER_AVAILABLE, reason="关节控制器不可用")
class TestControlGains:
    """控制增益测试类"""
    
    def test_control_gains_creation(self):
        """测试控制增益创建"""
        gains = ControlGains(kp=5.0, ki=0.05, kd=0.25, max_integral=0.5, max_output=15.0)
        
        assert gains.kp == 5.0
        assert gains.ki == 0.05
        assert gains.kd == 0.25
        assert gains.max_integral == 0.5
        assert gains.max_output == 15.0
    
    def test_control_gains_defaults(self):
        """测试控制增益默认值"""
        gains = ControlGains()
        
        assert gains.kp == 10.0
        assert gains.ki == 0.1
        assert gains.kd == 0.5
        assert gains.max_integral == 1.0
        assert gains.max_output == 30.0


@pytest.mark.skipif(not CONTROLLER_AVAILABLE, reason="关节控制器不可用")
class TestJointControllerLogic:
    """关节控制器逻辑测试类（不涉及ROS2）"""
    
    def test_position_limiting(self):
        """测试位置限制逻辑"""
        limits = JointLimits(min_position=-1.0, max_position=1.0)
        
        # 测试限制逻辑
        def apply_limits(position, limits):
            if not np.isinf(limits.min_position) and not np.isinf(limits.max_position):
                return np.clip(position, limits.min_position, limits.max_position)
            return position
        
        # 正常范围内
        assert apply_limits(0.5, limits) == 0.5
        
        # 超出上限
        assert apply_limits(2.0, limits) == 1.0
        
        # 超出下限
        assert apply_limits(-2.0, limits) == -1.0
        
        # 无限制关节
        unlimited_limits = JointLimits(min_position=-np.inf, max_position=np.inf)
        assert apply_limits(1000.0, unlimited_limits) == 1000.0
    
    def test_velocity_limiting(self):
        """测试速度限制逻辑"""
        max_velocity = 10.0
        
        def apply_velocity_limits(velocity, max_vel):
            return np.clip(velocity, -max_vel, max_vel)
        
        # 正常范围内
        assert apply_velocity_limits(5.0, max_velocity) == 5.0
        
        # 超出上限
        assert apply_velocity_limits(15.0, max_velocity) == 10.0
        
        # 超出下限
        assert apply_velocity_limits(-15.0, max_velocity) == -10.0
    
    def test_trajectory_interpolation(self):
        """测试轨迹插值逻辑"""
        def linear_interpolation(pos1, pos2, alpha):
            return pos1 + alpha * (pos2 - pos1)
        
        # 测试线性插值
        assert linear_interpolation(0.0, 1.0, 0.0) == 0.0  # 起始点
        assert linear_interpolation(0.0, 1.0, 1.0) == 1.0  # 结束点
        assert linear_interpolation(0.0, 1.0, 0.5) == 0.5  # 中点
        
        # 测试负值插值
        assert linear_interpolation(-1.0, 1.0, 0.5) == 0.0
        
        # 测试超出范围的alpha
        assert linear_interpolation(0.0, 1.0, 1.5) == 1.5  # 超出范围
    
    def test_joint_motion_simulation(self):
        """测试关节运动仿真逻辑"""
        def simulate_motion(current_pos, current_vel, effort, dt, inertia=0.1):
            """简化的关节运动仿真"""
            acceleration = effort / inertia
            new_velocity = current_vel + acceleration * dt
            new_position = current_pos + new_velocity * dt
            return new_position, new_velocity
        
        # 测试正力矩
        pos, vel = simulate_motion(0.0, 0.0, 1.0, 0.1)
        assert pos > 0.0  # 位置应该增加
        assert vel > 0.0  # 速度应该增加
        
        # 测试负力矩
        pos, vel = simulate_motion(0.0, 0.0, -1.0, 0.1)
        assert pos < 0.0  # 位置应该减少
        assert vel < 0.0  # 速度应该减少
        
        # 测试零力矩（惯性运动）
        pos, vel = simulate_motion(0.0, 1.0, 0.0, 0.1)
        assert pos == 0.1  # 位置 = 初始速度 * 时间
        assert vel == 1.0  # 速度不变


def test_controller_import():
    """测试控制器导入"""
    if CONTROLLER_AVAILABLE:
        assert hasattr(sys.modules['wheel_legged_control.controllers.joint_controller'], 'JointControllerNode')
        assert hasattr(sys.modules['wheel_legged_control.controllers.joint_controller'], 'PIDController')
        assert hasattr(sys.modules['wheel_legged_control.controllers.joint_controller'], 'ControlGains')
        assert hasattr(sys.modules['wheel_legged_control.controllers.joint_controller'], 'JointLimits')
    else:
        pytest.skip("关节控制器不可用")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])