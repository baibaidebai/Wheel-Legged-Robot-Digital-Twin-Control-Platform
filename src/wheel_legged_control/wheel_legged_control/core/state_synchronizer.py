#!/usr/bin/env python3
"""
状态同步器

模拟虚实状态同步功能，为未来硬件集成做准备。
包括状态历史记录、网络延迟模拟、同步误差计算和校正机制。
"""

import time
import threading
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import deque
import json
import logging
from enum import Enum

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from sensor_msgs.msg import JointState, Imu
from std_msgs.msg import Header, Float64MultiArray
from geometry_msgs.msg import Twist, Vector3, Quaternion


class SyncState(Enum):
    """同步状态枚举"""
    SYNCHRONIZED = "synchronized"
    SYNCHRONIZING = "synchronizing"
    DESYNCHRONIZED = "desynchronized"
    ERROR = "error"


@dataclass
class RobotStateSnapshot:
    """机器人状态快照"""
    timestamp: float
    joint_positions: Dict[str, float]
    joint_velocities: Dict[str, float]
    joint_efforts: Dict[str, float]
    imu_orientation: Tuple[float, float, float, float]  # x, y, z, w
    imu_angular_velocity: Tuple[float, float, float]
    imu_linear_acceleration: Tuple[float, float, float]
    base_position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    base_velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)


@dataclass
class SyncConfig:
    """同步配置参数"""
    # 网络延迟模拟
    network_delay_mean: float = 0.05  # 平均延迟 50ms
    network_delay_std: float = 0.01   # 延迟标准差 10ms
    packet_loss_rate: float = 0.01    # 丢包率 1%
    
    # 同步参数
    sync_frequency: float = 20.0       # 同步频率 20Hz
    max_sync_error: float = 0.1        # 最大同步误差阈值
    correction_gain: float = 0.5       # 校正增益
    
    # 历史记录
    max_history_length: int = 1000     # 最大历史记录长度
    state_buffer_size: int = 100       # 状态缓冲区大小
    
    # 质量评估
    quality_window_size: int = 100     # 质量评估窗口大小


@dataclass
class SyncQualityMetrics:
    """同步质量指标"""
    avg_sync_error: float = 0.0
    max_sync_error: float = 0.0
    sync_success_rate: float = 1.0
    avg_network_delay: float = 0.0
    packet_loss_count: int = 0
    correction_count: int = 0
    last_update_time: float = field(default_factory=time.time)


class NetworkSimulator:
    """网络延迟和丢包模拟器"""
    
    def __init__(self, config: SyncConfig):
        self.config = config
        self.rng = np.random.RandomState(42)
        
    def simulate_network_delay(self) -> float:
        """模拟网络延迟"""
        delay = self.rng.normal(
            self.config.network_delay_mean,
            self.config.network_delay_std
        )
        return max(0.0, delay)  # 确保延迟非负
    
    def simulate_packet_loss(self) -> bool:
        """模拟丢包"""
        return self.rng.random() < self.config.packet_loss_rate
    
    def add_network_effects(self, data: Any, timestamp: float) -> Optional[Tuple[Any, float]]:
        """添加网络效应（延迟和丢包）"""
        # 模拟丢包
        if self.simulate_packet_loss():
            return None
        
        # 模拟延迟
        delay = self.simulate_network_delay()
        delayed_timestamp = timestamp + delay
        
        return data, delayed_timestamp


class StateSynchronizer:
    """状态同步器核心类"""
    
    def __init__(self, config: Optional[SyncConfig] = None):
        self.config = config if config is not None else SyncConfig()
        
        # 状态存储
        self.virtual_state_history: deque = deque(maxlen=self.config.max_history_length)
        self.physical_state_history: deque = deque(maxlen=self.config.max_history_length)
        self.sync_error_history: deque = deque(maxlen=self.config.quality_window_size)
        
        # 状态缓冲区
        self.virtual_state_buffer: deque = deque(maxlen=self.config.state_buffer_size)
        self.physical_state_buffer: deque = deque(maxlen=self.config.state_buffer_size)
        
        # 网络模拟器
        self.network_sim = NetworkSimulator(self.config)
        
        # 同步状态
        self.sync_state = SyncState.SYNCHRONIZED
        self.quality_metrics = SyncQualityMetrics()
        
        # 线程安全
        self.lock = threading.RLock()
        
        # 日志
        self.logger = logging.getLogger(__name__)
        
    def update_virtual_state(self, state: RobotStateSnapshot):
        """更新虚拟状态"""
        with self.lock:
            # 添加到历史记录
            self.virtual_state_history.append(state)
            
            # 模拟网络传输到物理端
            network_result = self.network_sim.add_network_effects(
                state, state.timestamp
            )
            
            if network_result is not None:
                delayed_state, delayed_timestamp = network_result
                # 创建延迟后的状态快照
                delayed_state_copy = RobotStateSnapshot(
                    timestamp=delayed_timestamp,
                    joint_positions=delayed_state.joint_positions.copy(),
                    joint_velocities=delayed_state.joint_velocities.copy(),
                    joint_efforts=delayed_state.joint_efforts.copy(),
                    imu_orientation=delayed_state.imu_orientation,
                    imu_angular_velocity=delayed_state.imu_angular_velocity,
                    imu_linear_acceleration=delayed_state.imu_linear_acceleration,
                    base_position=delayed_state.base_position,
                    base_velocity=delayed_state.base_velocity
                )
                self.virtual_state_buffer.append(delayed_state_copy)
            else:
                # 记录丢包
                self.quality_metrics.packet_loss_count += 1
    
    def update_physical_state(self, state: RobotStateSnapshot):
        """更新物理状态（模拟）"""
        with self.lock:
            # 在实际应用中，这里会接收真实硬件的状态
            # 现在我们模拟一个略有差异的物理状态
            simulated_physical_state = self._simulate_physical_state(state)
            
            # 添加到历史记录
            self.physical_state_history.append(simulated_physical_state)
            self.physical_state_buffer.append(simulated_physical_state)
    
    def _simulate_physical_state(self, virtual_state: RobotStateSnapshot) -> RobotStateSnapshot:
        """模拟物理状态（添加噪声和延迟）"""
        # 添加小幅度噪声来模拟物理系统的差异
        noise_scale = 0.01
        
        # 关节位置噪声
        noisy_positions = {}
        for name, pos in virtual_state.joint_positions.items():
            noise = np.random.normal(0, noise_scale)
            noisy_positions[name] = pos + noise
        
        # 关节速度噪声
        noisy_velocities = {}
        for name, vel in virtual_state.joint_velocities.items():
            noise = np.random.normal(0, noise_scale * 0.1)
            noisy_velocities[name] = vel + noise
        
        # IMU数据噪声
        imu_noise = np.random.normal(0, 0.001, 3)
        noisy_angular_vel = tuple(
            virtual_state.imu_angular_velocity[i] + imu_noise[i] 
            for i in range(3)
        )
        
        accel_noise = np.random.normal(0, 0.01, 3)
        noisy_linear_accel = tuple(
            virtual_state.imu_linear_acceleration[i] + accel_noise[i] 
            for i in range(3)
        )
        
        return RobotStateSnapshot(
            timestamp=virtual_state.timestamp + 0.001,  # 小延迟
            joint_positions=noisy_positions,
            joint_velocities=noisy_velocities,
            joint_efforts=virtual_state.joint_efforts.copy(),
            imu_orientation=virtual_state.imu_orientation,
            imu_angular_velocity=noisy_angular_vel,
            imu_linear_acceleration=noisy_linear_accel,
            base_position=virtual_state.base_position,
            base_velocity=virtual_state.base_velocity
        )
    
    def compute_sync_error(self, virtual_state: RobotStateSnapshot, 
                          physical_state: RobotStateSnapshot) -> Dict[str, float]:
        """计算同步误差"""
        errors = {}
        
        # 关节位置误差
        joint_errors = []
        for joint_name in virtual_state.joint_positions:
            if joint_name in physical_state.joint_positions:
                error = abs(virtual_state.joint_positions[joint_name] - 
                           physical_state.joint_positions[joint_name])
                errors[f"joint_{joint_name}"] = error
                joint_errors.append(error)
        
        # 平均关节误差
        if joint_errors:
            errors["avg_joint_error"] = np.mean(joint_errors)
            errors["max_joint_error"] = np.max(joint_errors)
        
        # IMU误差
        imu_angular_error = np.linalg.norm(
            np.array(virtual_state.imu_angular_velocity) - 
            np.array(physical_state.imu_angular_velocity)
        )
        errors["imu_angular_error"] = imu_angular_error
        
        imu_accel_error = np.linalg.norm(
            np.array(virtual_state.imu_linear_acceleration) - 
            np.array(physical_state.imu_linear_acceleration)
        )
        errors["imu_accel_error"] = imu_accel_error
        
        # 时间戳误差
        errors["timestamp_error"] = abs(virtual_state.timestamp - physical_state.timestamp)
        
        return errors
    
    def perform_synchronization(self) -> bool:
        """执行状态同步"""
        with self.lock:
            if not self.virtual_state_buffer or not self.physical_state_buffer:
                return False
            
            # 获取最新状态
            virtual_state = self.virtual_state_buffer[-1]
            physical_state = self.physical_state_buffer[-1]
            
            # 计算同步误差
            sync_errors = self.compute_sync_error(virtual_state, physical_state)
            
            # 更新质量指标
            self._update_quality_metrics(sync_errors)
            
            # 检查是否需要校正
            max_error = sync_errors.get("max_joint_error", 0.0)
            if max_error > self.config.max_sync_error:
                self.sync_state = SyncState.DESYNCHRONIZED
                correction_applied = self._apply_state_correction(virtual_state, physical_state)
                if correction_applied:
                    self.quality_metrics.correction_count += 1
                    self.sync_state = SyncState.SYNCHRONIZING
                return correction_applied
            else:
                self.sync_state = SyncState.SYNCHRONIZED
                return True
    
    def _update_quality_metrics(self, sync_errors: Dict[str, float]):
        """更新同步质量指标"""
        # 记录同步误差
        avg_error = sync_errors.get("avg_joint_error", 0.0)
        max_error = sync_errors.get("max_joint_error", 0.0)
        
        self.sync_error_history.append(avg_error)
        
        # 计算质量指标
        if self.sync_error_history:
            self.quality_metrics.avg_sync_error = np.mean(self.sync_error_history)
            self.quality_metrics.max_sync_error = np.max(self.sync_error_history)
            
            # 成功率（误差小于阈值的比例）
            success_count = sum(1 for error in self.sync_error_history 
                              if error <= self.config.max_sync_error)
            self.quality_metrics.sync_success_rate = success_count / len(self.sync_error_history)
        
        # 更新网络延迟
        self.quality_metrics.avg_network_delay = self.config.network_delay_mean
        self.quality_metrics.last_update_time = time.time()
    
    def _apply_state_correction(self, virtual_state: RobotStateSnapshot, 
                               physical_state: RobotStateSnapshot) -> bool:
        """应用状态校正"""
        try:
            # 在实际应用中，这里会发送校正指令到物理系统
            # 现在我们只是记录校正动作
            self.logger.info(f"应用状态校正: 虚拟状态时间戳={virtual_state.timestamp}, "
                           f"物理状态时间戳={physical_state.timestamp}")
            
            # 模拟校正过程
            correction_delay = 0.1  # 100ms校正时间
            time.sleep(correction_delay)
            
            return True
        except Exception as e:
            self.logger.error(f"状态校正失败: {e}")
            self.sync_state = SyncState.ERROR
            return False
    
    def get_sync_quality_report(self) -> Dict[str, Any]:
        """获取同步质量报告"""
        with self.lock:
            return {
                "sync_state": self.sync_state.value,
                "quality_metrics": {
                    "avg_sync_error": self.quality_metrics.avg_sync_error,
                    "max_sync_error": self.quality_metrics.max_sync_error,
                    "sync_success_rate": self.quality_metrics.sync_success_rate,
                    "avg_network_delay": self.quality_metrics.avg_network_delay,
                    "packet_loss_count": self.quality_metrics.packet_loss_count,
                    "correction_count": self.quality_metrics.correction_count,
                    "last_update_time": self.quality_metrics.last_update_time
                },
                "history_stats": {
                    "virtual_states_count": len(self.virtual_state_history),
                    "physical_states_count": len(self.physical_state_history),
                    "sync_errors_count": len(self.sync_error_history)
                },
                "config": {
                    "network_delay_mean": self.config.network_delay_mean,
                    "network_delay_std": self.config.network_delay_std,
                    "packet_loss_rate": self.config.packet_loss_rate,
                    "sync_frequency": self.config.sync_frequency,
                    "max_sync_error": self.config.max_sync_error
                }
            }
    
    def reset_synchronizer(self):
        """重置同步器状态"""
        with self.lock:
            self.virtual_state_history.clear()
            self.physical_state_history.clear()
            self.sync_error_history.clear()
            self.virtual_state_buffer.clear()
            self.physical_state_buffer.clear()
            
            self.sync_state = SyncState.SYNCHRONIZED
            self.quality_metrics = SyncQualityMetrics()
            
            self.logger.info("状态同步器已重置")
    
    def export_sync_data(self, filename: str) -> bool:
        """导出同步数据到文件"""
        try:
            with self.lock:
                data = {
                    "export_timestamp": time.time(),
                    "sync_quality_report": self.get_sync_quality_report(),
                    "virtual_state_history": [
                        {
                            "timestamp": state.timestamp,
                            "joint_positions": state.joint_positions,
                            "joint_velocities": state.joint_velocities,
                            "imu_orientation": state.imu_orientation,
                            "imu_angular_velocity": state.imu_angular_velocity,
                            "imu_linear_acceleration": state.imu_linear_acceleration
                        }
                        for state in list(self.virtual_state_history)[-100:]  # 最近100个状态
                    ],
                    "sync_error_history": list(self.sync_error_history)
                }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"同步数据已导出到: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出同步数据失败: {e}")
            return False


def create_robot_state_from_joint_state(joint_state_msg: JointState, 
                                       imu_msg: Optional[Imu] = None) -> RobotStateSnapshot:
    """从ROS2消息创建机器人状态快照"""
    # 处理关节状态
    joint_positions = dict(zip(joint_state_msg.name, joint_state_msg.position))
    joint_velocities = dict(zip(joint_state_msg.name, joint_state_msg.velocity))
    joint_efforts = dict(zip(joint_state_msg.name, joint_state_msg.effort))
    
    # 处理IMU数据
    if imu_msg:
        imu_orientation = (
            imu_msg.orientation.x,
            imu_msg.orientation.y,
            imu_msg.orientation.z,
            imu_msg.orientation.w
        )
        imu_angular_velocity = (
            imu_msg.angular_velocity.x,
            imu_msg.angular_velocity.y,
            imu_msg.angular_velocity.z
        )
        imu_linear_acceleration = (
            imu_msg.linear_acceleration.x,
            imu_msg.linear_acceleration.y,
            imu_msg.linear_acceleration.z
        )
    else:
        # 默认IMU数据
        imu_orientation = (0.0, 0.0, 0.0, 1.0)
        imu_angular_velocity = (0.0, 0.0, 0.0)
        imu_linear_acceleration = (0.0, 0.0, -9.81)
    
    return RobotStateSnapshot(
        timestamp=time.time(),
        joint_positions=joint_positions,
        joint_velocities=joint_velocities,
        joint_efforts=joint_efforts,
        imu_orientation=imu_orientation,
        imu_angular_velocity=imu_angular_velocity,
        imu_linear_acceleration=imu_linear_acceleration
    )


if __name__ == "__main__":
    # 测试状态同步器
    print("🚀 测试状态同步器")
    
    # 创建配置
    config = SyncConfig(
        network_delay_mean=0.02,
        network_delay_std=0.005,
        packet_loss_rate=0.005,
        sync_frequency=50.0
    )
    
    # 创建同步器
    synchronizer = StateSynchronizer(config)
    
    # 模拟状态更新
    print("\n=== 模拟状态同步过程 ===")
    
    for i in range(10):
        # 创建虚拟状态
        virtual_state = RobotStateSnapshot(
            timestamp=time.time(),
            joint_positions={
                "lf0_Joint": 0.1 * np.sin(i * 0.1),
                "lf1_Joint": 0.2 * np.cos(i * 0.1),
                "rf0_Joint": 0.1 * np.sin(i * 0.1 + np.pi),
                "rf1_Joint": 0.2 * np.cos(i * 0.1 + np.pi)
            },
            joint_velocities={
                "lf0_Joint": 0.01 * np.cos(i * 0.1),
                "lf1_Joint": -0.02 * np.sin(i * 0.1),
                "rf0_Joint": 0.01 * np.cos(i * 0.1 + np.pi),
                "rf1_Joint": -0.02 * np.sin(i * 0.1 + np.pi)
            },
            joint_efforts={"lf0_Joint": 0.0, "lf1_Joint": 0.0, "rf0_Joint": 0.0, "rf1_Joint": 0.0},
            imu_orientation=(0.0, 0.0, 0.0, 1.0),
            imu_angular_velocity=(0.0, 0.0, 0.1),
            imu_linear_acceleration=(0.0, 0.0, -9.81)
        )
        
        # 更新状态
        synchronizer.update_virtual_state(virtual_state)
        synchronizer.update_physical_state(virtual_state)
        
        # 执行同步
        sync_success = synchronizer.perform_synchronization()
        
        print(f"步骤 {i+1}: 同步{'成功' if sync_success else '失败'}, "
              f"状态: {synchronizer.sync_state.value}")
        
        time.sleep(0.05)  # 50ms间隔
    
    # 获取质量报告
    print("\n=== 同步质量报告 ===")
    quality_report = synchronizer.get_sync_quality_report()
    
    print(f"平均同步误差: {quality_report['quality_metrics']['avg_sync_error']:.6f}")
    print(f"最大同步误差: {quality_report['quality_metrics']['max_sync_error']:.6f}")
    print(f"同步成功率: {quality_report['quality_metrics']['sync_success_rate']:.2%}")
    print(f"平均网络延迟: {quality_report['quality_metrics']['avg_network_delay']:.3f}s")
    print(f"丢包数量: {quality_report['quality_metrics']['packet_loss_count']}")
    print(f"校正次数: {quality_report['quality_metrics']['correction_count']}")
    
    # 导出数据
    export_file = "/tmp/sync_test_data.json"
    if synchronizer.export_sync_data(export_file):
        print(f"\n✅ 同步数据已导出到: {export_file}")
    
    print("\n🎉 状态同步器测试完成！")