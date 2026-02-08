#!/usr/bin/env python3
"""
IMU仿真器单元测试
"""

import pytest
import numpy as np
import time
import sys
import os

# 添加源码路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 
                                '../../src/wheel_legged_control'))

from wheel_legged_control.sensors.imu_simulator import (
    IMUSimulator, IMUConfig, RobotState, create_test_robot_state
)


class TestIMUSimulator:
    """IMU仿真器测试类"""
    
    def setup_method(self):
        """测试前设置"""
        self.config = IMUConfig(
            gyro_noise_std=0.01,
            accel_noise_std=0.1,
            gravity=9.81,
            update_rate=100.0
        )
        self.imu_sim = IMUSimulator(self.config)
        
    def test_imu_simulator_creation(self):
        """测试IMU仿真器创建"""
        assert self.imu_sim is not None
        assert self.imu_sim.config.gravity == 9.81
        assert self.imu_sim.config.gyro_noise_std == 0.01
        
    def test_imu_config_defaults(self):
        """测试IMU配置默认值"""
        default_config = IMUConfig()
        assert default_config.gyro_noise_std == 0.01
        assert default_config.accel_noise_std == 0.1
        assert default_config.gravity == 9.81
        assert default_config.update_rate == 100.0
        assert len(default_config.gyro_bias) == 3
        assert len(default_config.accel_bias) == 3
        
    def test_quaternion_to_rotation_matrix(self):
        """测试四元数到旋转矩阵转换"""
        # 单位四元数
        q_identity = np.array([0.0, 0.0, 0.0, 1.0])
        R_identity = self.imu_sim.quaternion_to_rotation_matrix(q_identity)
        
        # 应该是单位矩阵
        np.testing.assert_allclose(R_identity, np.eye(3), atol=1e-6)
        
        # 90度绕Z轴旋转
        q_z90 = np.array([0.0, 0.0, np.sin(np.pi/4), np.cos(np.pi/4)])
        R_z90 = self.imu_sim.quaternion_to_rotation_matrix(q_z90)
        
        # 验证旋转矩阵性质
        assert np.allclose(np.linalg.det(R_z90), 1.0, atol=1e-6)  # 行列式为1
        assert np.allclose(R_z90 @ R_z90.T, np.eye(3), atol=1e-6)  # 正交矩阵
        
    def test_static_imu_data(self):
        """测试静止状态IMU数据"""
        static_imu = self.imu_sim.create_static_imu_data()
        
        # 检查消息结构
        assert static_imu.header.frame_id == "imu_link"
        
        # 检查姿态（应该是单位四元数）
        q = np.array([static_imu.orientation.x, static_imu.orientation.y,
                     static_imu.orientation.z, static_imu.orientation.w])
        assert np.allclose(np.linalg.norm(q), 1.0, atol=1e-3)
        
        # 检查角速度（应该接近零，考虑噪声）
        w = np.array([static_imu.angular_velocity.x, static_imu.angular_velocity.y,
                     static_imu.angular_velocity.z])
        assert np.all(np.abs(w) < 0.1)  # 噪声应该很小
        
        # 检查线性加速度（Z轴应该接近重力）
        a = np.array([static_imu.linear_acceleration.x, static_imu.linear_acceleration.y,
                     static_imu.linear_acceleration.z])
        assert abs(a[2] - 9.81) < 1.0  # Z轴接近重力，考虑噪声
        
    def test_robot_state_creation(self):
        """测试机器人状态创建"""
        robot_state = create_test_robot_state(0.0)
        
        assert robot_state.timestamp > 0
        assert len(robot_state.joint_positions) == 6
        assert len(robot_state.joint_velocities) == 6
        assert len(robot_state.base_position) == 3
        assert len(robot_state.base_orientation) == 4
        assert len(robot_state.base_linear_velocity) == 3
        assert len(robot_state.base_angular_velocity) == 3
        
    def test_imu_data_generation(self):
        """测试IMU数据生成"""
        robot_state = create_test_robot_state(1.0)
        
        orientation, angular_velocity, linear_acceleration = self.imu_sim.generate_imu_data(robot_state)
        
        # 检查数据类型和形状
        assert isinstance(orientation, np.ndarray)
        assert isinstance(angular_velocity, np.ndarray)
        assert isinstance(linear_acceleration, np.ndarray)
        
        assert len(orientation) == 4
        assert len(angular_velocity) == 3
        assert len(linear_acceleration) == 3
        
        # 检查四元数归一化
        assert np.allclose(np.linalg.norm(orientation), 1.0, atol=1e-6)
        
    def test_imu_message_creation(self):
        """测试IMU消息创建"""
        robot_state = create_test_robot_state(2.0)
        imu_msg = self.imu_sim.create_imu_message(robot_state, "test_frame")
        
        # 检查消息结构
        assert imu_msg.header.frame_id == "test_frame"
        assert imu_msg.header.stamp.sec > 0
        
        # 检查协方差矩阵
        assert len(imu_msg.orientation_covariance) == 9
        assert len(imu_msg.angular_velocity_covariance) == 9
        assert len(imu_msg.linear_acceleration_covariance) == 9
        
        # 检查协方差矩阵对角元素
        assert imu_msg.orientation_covariance[0] > 0
        assert imu_msg.angular_velocity_covariance[4] > 0
        assert imu_msg.linear_acceleration_covariance[8] > 0
        
    def test_imu_data_validation(self):
        """测试IMU数据验证"""
        robot_state = create_test_robot_state(0.5)
        imu_msg = self.imu_sim.create_imu_message(robot_state)
        
        # 正常数据应该通过验证
        assert self.imu_sim.validate_imu_data(imu_msg) == True
        
        # 测试无效四元数
        imu_msg.orientation.x = 10.0  # 使四元数非归一化
        assert self.imu_sim.validate_imu_data(imu_msg) == False
        
        # 恢复正常四元数，测试过大角速度
        imu_msg.orientation.x = 0.0
        imu_msg.angular_velocity.x = 100.0  # 过大的角速度
        assert self.imu_sim.validate_imu_data(imu_msg) == False
        
        # 恢复正常角速度，测试过大加速度
        imu_msg.angular_velocity.x = 0.0
        imu_msg.linear_acceleration.x = 200.0  # 过大的加速度
        assert self.imu_sim.validate_imu_data(imu_msg) == False
        
    def test_noise_and_bias(self):
        """测试噪声和偏差"""
        # 创建有偏差的配置
        biased_config = IMUConfig(
            gyro_bias=np.array([0.1, 0.2, 0.3]),
            accel_bias=np.array([0.5, 0.6, 0.7]),
            gyro_noise_std=0.0,  # 关闭噪声以测试偏差
            accel_noise_std=0.0
        )
        
        biased_imu = IMUSimulator(biased_config)
        
        # 创建静止状态
        static_state = RobotState(
            timestamp=time.time(),
            joint_positions={},
            joint_velocities={},
            base_position=np.zeros(3),
            base_orientation=np.array([0.0, 0.0, 0.0, 1.0]),
            base_linear_velocity=np.zeros(3),
            base_angular_velocity=np.zeros(3)
        )
        
        orientation, angular_velocity, linear_acceleration = biased_imu.generate_imu_data(static_state)
        
        # 检查偏差是否被正确添加
        np.testing.assert_allclose(angular_velocity, biased_config.gyro_bias, atol=1e-6)
        
    def test_filtered_data(self):
        """测试滤波数据"""
        # 生成多个数据点
        for i in range(10):
            robot_state = create_test_robot_state(i * 0.1)
            self.imu_sim.generate_imu_data(robot_state)
            
        # 获取滤波数据
        filtered_gyro, filtered_accel = self.imu_sim.get_filtered_data()
        
        assert len(filtered_gyro) == 3
        assert len(filtered_accel) == 3
        assert not np.any(np.isnan(filtered_gyro))
        assert not np.any(np.isnan(filtered_accel))
        
    def test_reset_functionality(self):
        """测试重置功能"""
        # 生成一些数据
        for i in range(5):
            robot_state = create_test_robot_state(i * 0.1)
            self.imu_sim.generate_imu_data(robot_state)
            
        # 检查历史数据存在
        assert len(self.imu_sim.gyro_history) > 0
        assert len(self.imu_sim.accel_history) > 0
        
        # 重置
        self.imu_sim.reset()
        
        # 检查历史数据被清空
        assert len(self.imu_sim.gyro_history) == 0
        assert len(self.imu_sim.accel_history) == 0
        
    def test_config_update(self):
        """测试配置更新"""
        new_config = IMUConfig(
            gyro_noise_std=0.05,
            accel_noise_std=0.2,
            gravity=9.8
        )
        
        self.imu_sim.update_config(new_config)
        
        assert self.imu_sim.config.gyro_noise_std == 0.05
        assert self.imu_sim.config.accel_noise_std == 0.2
        assert self.imu_sim.config.gravity == 9.8
        
    def test_time_dependent_behavior(self):
        """测试时间相关行为"""
        # 测试连续的时间步
        states = []
        imu_data = []
        
        for i in range(5):
            t = i * 0.1
            robot_state = create_test_robot_state(t)
            states.append(robot_state)
            
            orientation, angular_velocity, linear_acceleration = self.imu_sim.generate_imu_data(robot_state)
            imu_data.append((orientation, angular_velocity, linear_acceleration))
            
            # 小延迟以确保时间差
            time.sleep(0.01)
            
        # 检查数据随时间变化
        assert len(imu_data) == 5
        
        # 检查角速度变化（应该反映机器人运动）
        angular_velocities = [data[1] for data in imu_data]
        
        # 至少应该有一些变化
        velocity_changes = []
        for i in range(1, len(angular_velocities)):
            change = np.linalg.norm(angular_velocities[i] - angular_velocities[i-1])
            velocity_changes.append(change)
            
        # 应该有一些变化（不是完全静止）
        assert np.mean(velocity_changes) > 0


def test_create_test_robot_state():
    """测试创建测试机器人状态函数"""
    state = create_test_robot_state(1.0)
    
    assert isinstance(state, RobotState)
    assert state.timestamp > 0
    assert "lf0_joint" in state.joint_positions
    assert "rf1_joint" in state.joint_velocities
    assert len(state.base_position) == 3
    assert len(state.base_orientation) == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])