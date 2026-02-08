#!/usr/bin/env python3
"""
IMU传感器仿真器
基于机器人状态生成IMU数据，包括姿态、角速度和线性加速度
"""

import numpy as np
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import time
import math

from geometry_msgs.msg import Vector3, Quaternion
from sensor_msgs.msg import Imu


@dataclass
class RobotState:
    """机器人状态数据结构"""
    timestamp: float
    joint_positions: Dict[str, float]
    joint_velocities: Dict[str, float]
    base_position: np.ndarray  # [x, y, z]
    base_orientation: np.ndarray  # 四元数 [x, y, z, w]
    base_linear_velocity: np.ndarray  # [vx, vy, vz]
    base_angular_velocity: np.ndarray  # [wx, wy, wz]


@dataclass
class IMUConfig:
    """IMU配置参数"""
    # 噪声参数
    gyro_noise_std: float = 0.01  # 陀螺仪噪声标准差 (rad/s)
    accel_noise_std: float = 0.1  # 加速度计噪声标准差 (m/s²)
    
    # 偏差参数
    gyro_bias: np.ndarray = None  # 陀螺仪偏差 [wx, wy, wz]
    accel_bias: np.ndarray = None  # 加速度计偏差 [ax, ay, az]
    
    # 物理参数
    gravity: float = 9.81  # 重力加速度 (m/s²)
    
    # 更新频率
    update_rate: float = 100.0  # Hz
    
    def __post_init__(self):
        """初始化默认偏差"""
        if self.gyro_bias is None:
            self.gyro_bias = np.zeros(3)
        if self.accel_bias is None:
            self.accel_bias = np.zeros(3)


class IMUSimulator:
    """IMU传感器仿真器"""
    
    def __init__(self, config: Optional[IMUConfig] = None):
        """
        初始化IMU仿真器
        
        Args:
            config: IMU配置参数，如果为None则使用默认配置
        """
        self.config = config if config is not None else IMUConfig()
        
        # 状态变量
        self.last_update_time = time.time()
        self.last_velocity = np.zeros(3)
        self.last_position = np.zeros(3)
        
        # 噪声生成器
        self.rng = np.random.RandomState(42)  # 固定种子以便重现
        
        # IMU数据历史（用于滤波）
        self.gyro_history = []
        self.accel_history = []
        self.max_history_length = 10
        
    def update_config(self, config: IMUConfig):
        """更新IMU配置"""
        self.config = config
        
    def reset(self):
        """重置IMU仿真器状态"""
        self.last_update_time = time.time()
        self.last_velocity = np.zeros(3)
        self.last_position = np.zeros(3)
        self.gyro_history.clear()
        self.accel_history.clear()
        
    def quaternion_to_rotation_matrix(self, q: np.ndarray) -> np.ndarray:
        """
        将四元数转换为旋转矩阵
        
        Args:
            q: 四元数 [x, y, z, w]
            
        Returns:
            3x3旋转矩阵
        """
        x, y, z, w = q
        
        # 归一化四元数
        norm = np.sqrt(x*x + y*y + z*z + w*w)
        if norm > 0:
            x, y, z, w = x/norm, y/norm, z/norm, w/norm
        
        # 计算旋转矩阵
        R = np.array([
            [1 - 2*(y*y + z*z), 2*(x*y - z*w), 2*(x*z + y*w)],
            [2*(x*y + z*w), 1 - 2*(x*x + z*z), 2*(y*z - x*w)],
            [2*(x*z - y*w), 2*(y*z + x*w), 1 - 2*(x*x + y*y)]
        ])
        
        return R
        
    def compute_linear_acceleration(self, robot_state: RobotState) -> np.ndarray:
        """
        计算线性加速度
        
        Args:
            robot_state: 机器人状态
            
        Returns:
            线性加速度 [ax, ay, az] (m/s²)
        """
        current_time = time.time()
        dt = current_time - self.last_update_time
        
        if dt <= 0 or dt > 1.0:  # 防止过大的时间间隔
            dt = 1.0 / self.config.update_rate
            
        # 计算加速度（数值微分）
        current_velocity = robot_state.base_linear_velocity
        acceleration = (current_velocity - self.last_velocity) / dt
        
        # 限制加速度幅值以避免数值问题
        max_accel = 50.0  # m/s²
        accel_magnitude = np.linalg.norm(acceleration)
        if accel_magnitude > max_accel:
            acceleration = acceleration * (max_accel / accel_magnitude)
        
        # 添加重力分量（在机器人坐标系中）
        # 重力在世界坐标系中是 [0, 0, -g]
        gravity_world = np.array([0, 0, -self.config.gravity])
        
        # 将重力转换到机器人坐标系
        R = self.quaternion_to_rotation_matrix(robot_state.base_orientation)
        gravity_robot = R.T @ gravity_world  # 逆旋转
        
        # IMU测量的是机器人相对于惯性系的加速度减去重力
        # 所以我们需要加上重力分量
        imu_acceleration = acceleration - gravity_robot
        
        # 添加偏差和噪声
        imu_acceleration += self.config.accel_bias
        imu_acceleration += self.rng.normal(0, self.config.accel_noise_std, 3)
        
        # 更新历史
        self.last_velocity = current_velocity.copy()
        self.last_update_time = current_time
        
        return imu_acceleration
        
    def compute_angular_velocity(self, robot_state: RobotState) -> np.ndarray:
        """
        计算角速度
        
        Args:
            robot_state: 机器人状态
            
        Returns:
            角速度 [wx, wy, wz] (rad/s)
        """
        # 直接使用机器人状态中的角速度
        angular_velocity = robot_state.base_angular_velocity.copy()
        
        # 添加偏差和噪声
        angular_velocity += self.config.gyro_bias
        angular_velocity += self.rng.normal(0, self.config.gyro_noise_std, 3)
        
        return angular_velocity
        
    def compute_orientation(self, robot_state: RobotState) -> np.ndarray:
        """
        计算姿态（四元数）
        
        Args:
            robot_state: 机器人状态
            
        Returns:
            姿态四元数 [x, y, z, w]
        """
        # 直接使用机器人状态中的姿态
        # 在实际应用中，这里可能需要添加姿态估计算法
        orientation = robot_state.base_orientation.copy()
        
        # 归一化四元数
        norm = np.linalg.norm(orientation)
        if norm > 0:
            orientation = orientation / norm
            
        return orientation
        
    def generate_imu_data(self, robot_state: RobotState) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        生成IMU数据
        
        Args:
            robot_state: 机器人状态
            
        Returns:
            (orientation, angular_velocity, linear_acceleration)
            - orientation: 四元数 [x, y, z, w]
            - angular_velocity: 角速度 [wx, wy, wz] (rad/s)
            - linear_acceleration: 线性加速度 [ax, ay, az] (m/s²)
        """
        # 计算各个分量
        orientation = self.compute_orientation(robot_state)
        angular_velocity = self.compute_angular_velocity(robot_state)
        linear_acceleration = self.compute_linear_acceleration(robot_state)
        
        # 添加到历史记录
        self.gyro_history.append(angular_velocity.copy())
        self.accel_history.append(linear_acceleration.copy())
        
        # 限制历史长度
        if len(self.gyro_history) > self.max_history_length:
            self.gyro_history.pop(0)
        if len(self.accel_history) > self.max_history_length:
            self.accel_history.pop(0)
            
        return orientation, angular_velocity, linear_acceleration
        
    def create_imu_message(self, robot_state: RobotState, frame_id: str = "imu_link") -> Imu:
        """
        创建ROS2 IMU消息
        
        Args:
            robot_state: 机器人状态
            frame_id: 坐标系ID
            
        Returns:
            sensor_msgs/Imu消息
        """
        # 生成IMU数据
        orientation, angular_velocity, linear_acceleration = self.generate_imu_data(robot_state)
        
        # 创建IMU消息
        imu_msg = Imu()
        
        # 设置头部信息
        imu_msg.header.stamp.sec = int(robot_state.timestamp)
        imu_msg.header.stamp.nanosec = int((robot_state.timestamp % 1) * 1e9)
        imu_msg.header.frame_id = frame_id
        
        # 设置姿态
        imu_msg.orientation.x = orientation[0]
        imu_msg.orientation.y = orientation[1]
        imu_msg.orientation.z = orientation[2]
        imu_msg.orientation.w = orientation[3]
        
        # 设置角速度
        imu_msg.angular_velocity.x = angular_velocity[0]
        imu_msg.angular_velocity.y = angular_velocity[1]
        imu_msg.angular_velocity.z = angular_velocity[2]
        
        # 设置线性加速度
        imu_msg.linear_acceleration.x = linear_acceleration[0]
        imu_msg.linear_acceleration.y = linear_acceleration[1]
        imu_msg.linear_acceleration.z = linear_acceleration[2]
        
        # 设置协方差矩阵（简化版本）
        # 姿态协方差
        orientation_covariance = np.zeros(9)
        orientation_covariance[0] = orientation_covariance[4] = orientation_covariance[8] = 0.01
        imu_msg.orientation_covariance = orientation_covariance.tolist()
        
        # 角速度协方差
        angular_velocity_covariance = np.zeros(9)
        gyro_var = self.config.gyro_noise_std ** 2
        angular_velocity_covariance[0] = angular_velocity_covariance[4] = angular_velocity_covariance[8] = gyro_var
        imu_msg.angular_velocity_covariance = angular_velocity_covariance.tolist()
        
        # 线性加速度协方差
        linear_acceleration_covariance = np.zeros(9)
        accel_var = self.config.accel_noise_std ** 2
        linear_acceleration_covariance[0] = linear_acceleration_covariance[4] = linear_acceleration_covariance[8] = accel_var
        imu_msg.linear_acceleration_covariance = linear_acceleration_covariance.tolist()
        
        return imu_msg
        
    def create_static_imu_data(self, orientation: Optional[np.ndarray] = None) -> Imu:
        """
        创建静止状态的IMU数据（用于测试）
        
        Args:
            orientation: 可选的姿态四元数，默认为单位四元数
            
        Returns:
            sensor_msgs/Imu消息
        """
        if orientation is None:
            orientation = np.array([0.0, 0.0, 0.0, 1.0])  # 单位四元数
            
        # 创建静止状态
        static_state = RobotState(
            timestamp=time.time(),
            joint_positions={},
            joint_velocities={},
            base_position=np.zeros(3),
            base_orientation=orientation,
            base_linear_velocity=np.zeros(3),
            base_angular_velocity=np.zeros(3)
        )
        
        return self.create_imu_message(static_state)
        
    def get_filtered_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        获取滤波后的IMU数据
        
        Returns:
            (filtered_gyro, filtered_accel)
        """
        if not self.gyro_history or not self.accel_history:
            return np.zeros(3), np.zeros(3)
            
        # 简单的移动平均滤波
        filtered_gyro = np.mean(self.gyro_history, axis=0)
        filtered_accel = np.mean(self.accel_history, axis=0)
        
        return filtered_gyro, filtered_accel
        
    def validate_imu_data(self, imu_msg: Imu) -> bool:
        """
        验证IMU数据的合理性
        
        Args:
            imu_msg: IMU消息
            
        Returns:
            数据是否合理
        """
        # 检查四元数归一化
        q = np.array([imu_msg.orientation.x, imu_msg.orientation.y, 
                     imu_msg.orientation.z, imu_msg.orientation.w])
        q_norm = np.linalg.norm(q)
        if abs(q_norm - 1.0) > 0.1:
            return False
            
        # 检查角速度范围
        w = np.array([imu_msg.angular_velocity.x, imu_msg.angular_velocity.y, 
                     imu_msg.angular_velocity.z])
        if np.any(np.abs(w) > 50.0):  # 50 rad/s 限制
            return False
            
        # 检查加速度范围
        a = np.array([imu_msg.linear_acceleration.x, imu_msg.linear_acceleration.y, 
                     imu_msg.linear_acceleration.z])
        if np.any(np.abs(a) > 100.0):  # 100 m/s² 限制
            return False
            
        return True


def create_test_robot_state(t: float = 0.0) -> RobotState:
    """
    创建测试用的机器人状态
    
    Args:
        t: 时间参数
        
    Returns:
        测试机器人状态
    """
    # 创建简单的运动状态
    return RobotState(
        timestamp=time.time() + t,
        joint_positions={
            "lf0_joint": 0.1 * math.sin(t),
            "lf1_joint": 0.2 * math.cos(t),
            "rf0_joint": 0.1 * math.sin(t + math.pi),
            "rf1_joint": 0.2 * math.cos(t + math.pi),
            "l_wheel_joint": t,
            "r_wheel_joint": t
        },
        joint_velocities={
            "lf0_joint": 0.1 * math.cos(t),
            "lf1_joint": -0.2 * math.sin(t),
            "rf0_joint": 0.1 * math.cos(t + math.pi),
            "rf1_joint": -0.2 * math.sin(t + math.pi),
            "l_wheel_joint": 1.0,
            "r_wheel_joint": 1.0
        },
        base_position=np.array([t * 0.1, 0.0, 0.2]),
        base_orientation=np.array([0.0, 0.0, math.sin(t * 0.1), math.cos(t * 0.1)]),
        base_linear_velocity=np.array([0.1, 0.0, 0.0]),
        base_angular_velocity=np.array([0.0, 0.0, 0.1])
    )


if __name__ == "__main__":
    # 测试IMU仿真器
    print("🚀 测试IMU仿真器")
    
    # 创建IMU仿真器
    imu_sim = IMUSimulator()
    
    # 测试静止状态
    print("\n=== 测试静止状态 ===")
    static_imu = imu_sim.create_static_imu_data()
    print(f"静止状态IMU数据:")
    print(f"  姿态: [{static_imu.orientation.x:.3f}, {static_imu.orientation.y:.3f}, {static_imu.orientation.z:.3f}, {static_imu.orientation.w:.3f}]")
    print(f"  角速度: [{static_imu.angular_velocity.x:.3f}, {static_imu.angular_velocity.y:.3f}, {static_imu.angular_velocity.z:.3f}]")
    print(f"  线性加速度: [{static_imu.linear_acceleration.x:.3f}, {static_imu.linear_acceleration.y:.3f}, {static_imu.linear_acceleration.z:.3f}]")
    
    # 测试运动状态
    print("\n=== 测试运动状态 ===")
    for i in range(5):
        t = i * 0.1
        robot_state = create_test_robot_state(t)
        imu_msg = imu_sim.create_imu_message(robot_state)
        
        print(f"时间 {t:.1f}s:")
        print(f"  角速度: [{imu_msg.angular_velocity.x:.3f}, {imu_msg.angular_velocity.y:.3f}, {imu_msg.angular_velocity.z:.3f}]")
        print(f"  线性加速度: [{imu_msg.linear_acceleration.x:.3f}, {imu_msg.linear_acceleration.y:.3f}, {imu_msg.linear_acceleration.z:.3f}]")
        
        # 验证数据
        is_valid = imu_sim.validate_imu_data(imu_msg)
        print(f"  数据有效性: {'✅' if is_valid else '❌'}")
    
    print("\n🎉 IMU仿真器测试完成！")