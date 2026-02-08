#!/usr/bin/env python3
"""
状态同步器集成测试

测试状态同步器的核心功能，包括：
- 状态更新和同步
- 网络延迟和丢包模拟
- 同步质量评估
- 数据导出功能
"""

import unittest
import time
import tempfile
import os
import json
import numpy as np
from unittest.mock import Mock, patch

# 导入被测试的模块
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/wheel_legged_control'))

from wheel_legged_control.core.state_synchronizer import (
    StateSynchronizer, SyncConfig, RobotStateSnapshot, 
    NetworkSimulator, SyncState
)


class TestStateSynchronizer(unittest.TestCase):
    """状态同步器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.config = SyncConfig(
            network_delay_mean=0.01,
            network_delay_std=0.002,
            packet_loss_rate=0.05,
            sync_frequency=50.0,
            max_sync_error=0.05
        )
        self.synchronizer = StateSynchronizer(self.config)
    
    def tearDown(self):
        """测试后清理"""
        self.synchronizer.reset_synchronizer()
    
    def create_test_state(self, timestamp=None, joint_offset=0.0):
        """创建测试状态快照"""
        if timestamp is None:
            timestamp = time.time()
        
        return RobotStateSnapshot(
            timestamp=timestamp,
            joint_positions={
                "lf0_Joint": 0.1 + joint_offset,
                "lf1_Joint": 0.2 + joint_offset,
                "rf0_Joint": -0.1 + joint_offset,
                "rf1_Joint": -0.2 + joint_offset
            },
            joint_velocities={
                "lf0_Joint": 0.01,
                "lf1_Joint": 0.02,
                "rf0_Joint": -0.01,
                "rf1_Joint": -0.02
            },
            joint_efforts={
                "lf0_Joint": 0.0,
                "lf1_Joint": 0.0,
                "rf0_Joint": 0.0,
                "rf1_Joint": 0.0
            },
            imu_orientation=(0.0, 0.0, 0.0, 1.0),
            imu_angular_velocity=(0.0, 0.0, 0.1),
            imu_linear_acceleration=(0.0, 0.0, -9.81)
        )
    
    def test_synchronizer_initialization(self):
        """测试同步器初始化"""
        self.assertIsNotNone(self.synchronizer)
        self.assertEqual(self.synchronizer.sync_state, SyncState.SYNCHRONIZED)
        self.assertEqual(len(self.synchronizer.virtual_state_history), 0)
        self.assertEqual(len(self.synchronizer.physical_state_history), 0)
    
    def test_state_update(self):
        """测试状态更新"""
        # 创建测试状态
        virtual_state = self.create_test_state()
        
        # 更新虚拟状态
        self.synchronizer.update_virtual_state(virtual_state)
        
        # 验证状态已添加到历史记录
        self.assertEqual(len(self.synchronizer.virtual_state_history), 1)
        
        # 更新物理状态
        self.synchronizer.update_physical_state(virtual_state)
        
        # 验证物理状态已添加
        self.assertEqual(len(self.synchronizer.physical_state_history), 1)
    
    def test_sync_error_calculation(self):
        """测试同步误差计算"""
        # 创建两个略有差异的状态
        virtual_state = self.create_test_state(joint_offset=0.0)
        physical_state = self.create_test_state(joint_offset=0.01)  # 小偏差
        
        # 计算同步误差
        errors = self.synchronizer.compute_sync_error(virtual_state, physical_state)
        
        # 验证误差计算
        self.assertIn("avg_joint_error", errors)
        self.assertIn("max_joint_error", errors)
        self.assertIn("imu_angular_error", errors)
        self.assertIn("imu_accel_error", errors)
        
        # 验证误差值合理
        self.assertGreater(errors["avg_joint_error"], 0.0)
        self.assertLess(errors["avg_joint_error"], 0.1)
    
    def test_synchronization_process(self):
        """测试同步过程"""
        # 添加多个状态
        for i in range(5):
            virtual_state = self.create_test_state(joint_offset=i * 0.001)
            self.synchronizer.update_virtual_state(virtual_state)
            self.synchronizer.update_physical_state(virtual_state)
        
        # 执行同步
        sync_success = self.synchronizer.perform_synchronization()
        
        # 验证同步结果
        self.assertTrue(sync_success)
        self.assertIn(self.synchronizer.sync_state, [SyncState.SYNCHRONIZED, SyncState.SYNCHRONIZING])
    
    def test_quality_metrics(self):
        """测试质量指标"""
        # 添加状态并执行同步
        for i in range(10):
            virtual_state = self.create_test_state(joint_offset=i * 0.002)
            self.synchronizer.update_virtual_state(virtual_state)
            self.synchronizer.update_physical_state(virtual_state)
            self.synchronizer.perform_synchronization()
        
        # 获取质量报告
        quality_report = self.synchronizer.get_sync_quality_report()
        
        # 验证质量报告结构
        self.assertIn("sync_state", quality_report)
        self.assertIn("quality_metrics", quality_report)
        self.assertIn("history_stats", quality_report)
        self.assertIn("config", quality_report)
        
        # 验证质量指标
        metrics = quality_report["quality_metrics"]
        self.assertIn("avg_sync_error", metrics)
        self.assertIn("sync_success_rate", metrics)
        self.assertGreaterEqual(metrics["sync_success_rate"], 0.0)
        self.assertLessEqual(metrics["sync_success_rate"], 1.0)
    
    def test_data_export(self):
        """测试数据导出"""
        # 添加一些测试数据
        for i in range(5):
            virtual_state = self.create_test_state(joint_offset=i * 0.001)
            self.synchronizer.update_virtual_state(virtual_state)
            self.synchronizer.update_physical_state(virtual_state)
        
        # 导出数据到临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_filename = f.name
        
        try:
            # 执行导出
            export_success = self.synchronizer.export_sync_data(temp_filename)
            self.assertTrue(export_success)
            
            # 验证文件存在
            self.assertTrue(os.path.exists(temp_filename))
            
            # 验证文件内容
            with open(temp_filename, 'r') as f:
                exported_data = json.load(f)
            
            self.assertIn("export_timestamp", exported_data)
            self.assertIn("sync_quality_report", exported_data)
            self.assertIn("virtual_state_history", exported_data)
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)
    
    def test_reset_functionality(self):
        """测试重置功能"""
        # 添加一些数据
        virtual_state = self.create_test_state()
        self.synchronizer.update_virtual_state(virtual_state)
        self.synchronizer.update_physical_state(virtual_state)
        
        # 验证数据已添加
        self.assertGreater(len(self.synchronizer.virtual_state_history), 0)
        
        # 重置同步器
        self.synchronizer.reset_synchronizer()
        
        # 验证数据已清空
        self.assertEqual(len(self.synchronizer.virtual_state_history), 0)
        self.assertEqual(len(self.synchronizer.physical_state_history), 0)
        self.assertEqual(self.synchronizer.sync_state, SyncState.SYNCHRONIZED)


class TestNetworkSimulator(unittest.TestCase):
    """网络模拟器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.config = SyncConfig(
            network_delay_mean=0.05,
            network_delay_std=0.01,
            packet_loss_rate=0.1
        )
        self.network_sim = NetworkSimulator(self.config)
    
    def test_network_delay_simulation(self):
        """测试网络延迟模拟"""
        delays = []
        for _ in range(100):
            delay = self.network_sim.simulate_network_delay()
            delays.append(delay)
            self.assertGreaterEqual(delay, 0.0)  # 延迟应该非负
        
        # 验证延迟分布合理
        mean_delay = np.mean(delays)
        self.assertAlmostEqual(mean_delay, self.config.network_delay_mean, delta=0.02)
    
    def test_packet_loss_simulation(self):
        """测试丢包模拟"""
        losses = []
        for _ in range(1000):
            loss = self.network_sim.simulate_packet_loss()
            losses.append(loss)
        
        # 验证丢包率
        loss_rate = sum(losses) / len(losses)
        self.assertAlmostEqual(loss_rate, self.config.packet_loss_rate, delta=0.02)
    
    def test_network_effects(self):
        """测试网络效应"""
        test_data = {"test": "data"}
        timestamp = time.time()
        
        # 多次测试网络效应
        results = []
        for _ in range(100):
            result = self.network_sim.add_network_effects(test_data, timestamp)
            results.append(result)
        
        # 统计结果
        successful_transmissions = [r for r in results if r is not None]
        packet_losses = [r for r in results if r is None]
        
        # 验证有成功传输和丢包
        self.assertGreater(len(successful_transmissions), 0)
        self.assertGreater(len(packet_losses), 0)
        
        # 验证延迟效应
        for data, delayed_timestamp in successful_transmissions:
            self.assertEqual(data, test_data)
            self.assertGreaterEqual(delayed_timestamp, timestamp)


def run_performance_test():
    """运行性能测试"""
    print("\n=== 状态同步器性能测试 ===")
    
    config = SyncConfig(sync_frequency=100.0)  # 高频率测试
    synchronizer = StateSynchronizer(config)
    
    # 性能测试
    start_time = time.time()
    num_operations = 1000
    
    for i in range(num_operations):
        virtual_state = RobotStateSnapshot(
            timestamp=time.time(),
            joint_positions={"joint1": np.sin(i * 0.01)},
            joint_velocities={"joint1": 0.01 * np.cos(i * 0.01)},
            joint_efforts={"joint1": 0.0},
            imu_orientation=(0.0, 0.0, 0.0, 1.0),
            imu_angular_velocity=(0.0, 0.0, 0.0),
            imu_linear_acceleration=(0.0, 0.0, -9.81)
        )
        
        synchronizer.update_virtual_state(virtual_state)
        synchronizer.update_physical_state(virtual_state)
        
        if i % 10 == 0:  # 每10次执行一次同步
            synchronizer.perform_synchronization()
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"处理 {num_operations} 个状态更新用时: {duration:.3f} 秒")
    print(f"平均处理速度: {num_operations/duration:.1f} 操作/秒")
    
    # 获取最终质量报告
    quality_report = synchronizer.get_sync_quality_report()
    print(f"最终同步成功率: {quality_report['quality_metrics']['sync_success_rate']:.2%}")
    print(f"平均同步误差: {quality_report['quality_metrics']['avg_sync_error']:.6f}")


if __name__ == '__main__':
    # 运行单元测试
    print("🚀 运行状态同步器单元测试")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # 运行性能测试
    run_performance_test()
    
    print("\n🎉 所有测试完成！")