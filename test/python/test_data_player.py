#!/usr/bin/env python3
"""
数据回放器单元测试

测试DataPlayer类的各种功能，包括数据加载、回放控制、回调机制等。
"""

import unittest
import tempfile
import os
import json
import csv
import time
import threading
from unittest.mock import Mock, patch

# 添加项目路径
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'wheel_legged_control'))

from wheel_legged_control.data.data_player import (
    DataPlayer, PlaybackConfig, PlaybackState, PlaybackMode, PlaybackStatus,
    create_default_player
)
from wheel_legged_control.data.data_recorder import DataPoint


class TestPlaybackConfig(unittest.TestCase):
    """测试回放配置类"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = PlaybackConfig()
        
        self.assertEqual(config.playback_speed, 1.0)
        self.assertFalse(config.loop_playback)
        self.assertFalse(config.auto_start)
        self.assertEqual(config.data_types_filter, [])
        self.assertIsNone(config.time_range_filter)
        self.assertFalse(config.sync_with_simulation)
        self.assertEqual(config.sync_tolerance, 0.01)
        self.assertEqual(config.buffer_size, 1000)
        self.assertTrue(config.preload_data)
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = PlaybackConfig(
            playback_speed=2.0,
            loop_playback=True,
            auto_start=True,
            data_types_filter=['joint_state', 'imu_data'],
            time_range_filter=(0.0, 10.0),
            sync_with_simulation=True,
            sync_tolerance=0.05,
            buffer_size=2000,
            preload_data=False
        )
        
        self.assertEqual(config.playback_speed, 2.0)
        self.assertTrue(config.loop_playback)
        self.assertTrue(config.auto_start)
        self.assertEqual(config.data_types_filter, ['joint_state', 'imu_data'])
        self.assertEqual(config.time_range_filter, (0.0, 10.0))
        self.assertTrue(config.sync_with_simulation)
        self.assertEqual(config.sync_tolerance, 0.05)
        self.assertEqual(config.buffer_size, 2000)
        self.assertFalse(config.preload_data)


class TestPlaybackStatus(unittest.TestCase):
    """测试回放状态类"""
    
    def test_default_status(self):
        """测试默认状态"""
        status = PlaybackStatus()
        
        self.assertEqual(status.state, PlaybackState.STOPPED)
        self.assertEqual(status.current_time, 0.0)
        self.assertEqual(status.total_duration, 0.0)
        self.assertEqual(status.current_index, 0)
        self.assertEqual(status.total_points, 0)
        self.assertEqual(status.playback_speed, 1.0)
        self.assertEqual(status.loop_count, 0)
        self.assertIsNone(status.data_file)


class TestDataPlayer(unittest.TestCase):
    """测试数据回放器核心功能"""
    
    def setUp(self):
        """测试前准备"""
        self.config = PlaybackConfig(
            playback_speed=1.0,
            loop_playback=False,
            auto_start=False
        )
        self.player = DataPlayer(self.config)
        
        # 创建测试数据
        self.test_data = self._create_test_data()
    
    def tearDown(self):
        """测试后清理"""
        self.player.cleanup()
    
    def _create_test_data(self):
        """创建测试数据"""
        base_time = time.time()
        data = []
        
        for i in range(5):
            # 关节状态数据
            joint_data = {
                'timestamp': base_time + i * 0.1,
                'data_type': 'joint_state',
                'data': {
                    'joint_names': ['joint1', 'joint2'],
                    'positions': [0.1 * i, 0.2 * i],
                    'velocities': [0.01 * i, 0.02 * i],
                    'efforts': [0.5 * i, 0.6 * i]
                }
            }
            data.append(joint_data)
            
            # IMU数据
            imu_data = {
                'timestamp': base_time + i * 0.1 + 0.05,
                'data_type': 'imu_data',
                'data': {
                    'orientation': [0.0, 0.0, 0.0, 1.0],
                    'angular_velocity': [0.1 * i, 0.0, 0.0],
                    'linear_acceleration': [0.0, 0.0, 9.81]
                }
            }
            data.append(imu_data)
        
        return data
    
    def test_player_initialization(self):
        """测试回放器初始化"""
        self.assertIsNotNone(self.player)
        self.assertEqual(self.player.status.state, PlaybackState.STOPPED)
        self.assertEqual(len(self.player.data_points), 0)
        self.assertEqual(len(self.player.filtered_data), 0)
        self.assertIsNone(self.player.playback_thread)
    
    def test_load_data_from_json(self):
        """测试从JSON文件加载数据"""
        # 创建临时JSON文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_data, f, indent=2)
            json_file = f.name
        
        try:
            # 加载数据
            success = self.player.load_data_from_json(json_file)
            self.assertTrue(success)
            
            # 验证数据
            self.assertEqual(len(self.player.data_points), 10)
            self.assertEqual(len(self.player.filtered_data), 10)
            self.assertEqual(self.player.status.total_points, 10)
            self.assertGreater(self.player.status.total_duration, 0)
            
        finally:
            os.unlink(json_file)
    
    def test_load_data_from_nonexistent_file(self):
        """测试加载不存在的文件"""
        success = self.player.load_data_from_json('/nonexistent/file.json')
        self.assertFalse(success)
        self.assertEqual(len(self.player.data_points), 0)
    
    def test_load_data_from_csv_directory(self):
        """测试从CSV目录加载数据"""
        # 创建临时目录和CSV文件
        with tempfile.TemporaryDirectory() as temp_dir:
            base_filename = 'test_recording'
            
            # 创建关节状态CSV文件
            joint_csv = os.path.join(temp_dir, f'{base_filename}_joint_state.csv')
            with open(joint_csv, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'joint_name', 'position', 'velocity', 'effort'])
                base_time = time.time()
                for i in range(3):
                    writer.writerow([base_time + i * 0.1, 'joint1', 0.1 * i, 0.01 * i, 0.5 * i])
                    writer.writerow([base_time + i * 0.1, 'joint2', 0.2 * i, 0.02 * i, 0.6 * i])
            
            # 创建IMU数据CSV文件
            imu_csv = os.path.join(temp_dir, f'{base_filename}_imu_data.csv')
            with open(imu_csv, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'orientation_x', 'orientation_y', 'orientation_z', 'orientation_w',
                               'angular_velocity_x', 'angular_velocity_y', 'angular_velocity_z',
                               'linear_acceleration_x', 'linear_acceleration_y', 'linear_acceleration_z'])
                for i in range(3):
                    writer.writerow([base_time + i * 0.1 + 0.05, 0.0, 0.0, 0.0, 1.0,
                                   0.1 * i, 0.0, 0.0, 0.0, 0.0, 9.81])
            
            # 加载数据
            success = self.player.load_data_from_csv_directory(temp_dir, base_filename)
            self.assertTrue(success)
            
            # 验证数据
            self.assertGreater(len(self.player.data_points), 0)
            self.assertEqual(len(self.player.filtered_data), len(self.player.data_points))
    
    def test_data_filtering(self):
        """测试数据过滤功能"""
        # 加载测试数据
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_data, f, indent=2)
            json_file = f.name
        
        try:
            # 设置数据类型过滤器
            self.player.config.data_types_filter = ['joint_state']
            success = self.player.load_data_from_json(json_file)
            self.assertTrue(success)
            
            # 验证过滤结果
            self.assertEqual(len(self.player.data_points), 10)  # 原始数据
            self.assertEqual(len(self.player.filtered_data), 5)  # 过滤后只有关节状态数据
            
            # 验证所有过滤后的数据都是关节状态
            for dp in self.player.filtered_data:
                self.assertEqual(dp.data_type, 'joint_state')
                
        finally:
            os.unlink(json_file)
    
    def test_callback_registration(self):
        """测试回调函数注册"""
        # 创建模拟回调函数
        joint_callback = Mock()
        imu_callback = Mock()
        status_callback = Mock()
        
        # 注册回调
        self.player.register_data_callback('joint_state', joint_callback)
        self.player.register_data_callback('imu_data', imu_callback)
        self.player.register_status_callback(status_callback)
        
        # 验证回调已注册
        self.assertIn('joint_state', self.player.data_callbacks)
        self.assertIn('imu_data', self.player.data_callbacks)
        self.assertEqual(len(self.player.data_callbacks['joint_state']), 1)
        self.assertEqual(len(self.player.data_callbacks['imu_data']), 1)
        self.assertEqual(len(self.player.status_callbacks), 1)
    
    def test_playback_control(self):
        """测试回放控制功能"""
        # 加载测试数据
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_data, f, indent=2)
            json_file = f.name
        
        try:
            self.player.load_data_from_json(json_file)
            
            # 测试开始回放
            success = self.player.start_playback()
            self.assertTrue(success)
            self.assertEqual(self.player.status.state, PlaybackState.PLAYING)
            
            # 等待一小段时间
            time.sleep(0.1)
            
            # 测试暂停回放
            success = self.player.pause_playback()
            self.assertTrue(success)
            self.assertEqual(self.player.status.state, PlaybackState.PAUSED)
            
            # 测试恢复回放
            success = self.player.resume_playback()
            self.assertTrue(success)
            self.assertEqual(self.player.status.state, PlaybackState.PLAYING)
            
            # 测试停止回放
            success = self.player.stop_playback()
            self.assertTrue(success)
            self.assertEqual(self.player.status.state, PlaybackState.STOPPED)
            
        finally:
            os.unlink(json_file)
    
    def test_seek_functionality(self):
        """测试跳转功能"""
        # 加载测试数据
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_data, f, indent=2)
            json_file = f.name
        
        try:
            self.player.load_data_from_json(json_file)
            
            # 测试跳转到索引
            success = self.player.seek_to_index(5)
            self.assertTrue(success)
            self.assertEqual(self.player.status.current_index, 5)
            
            # 测试跳转到时间
            success = self.player.seek_to_time(0.2)
            self.assertTrue(success)
            self.assertGreaterEqual(self.player.status.current_time, 0.2)
            
            # 测试无效跳转
            success = self.player.seek_to_index(-1)
            self.assertFalse(success)
            
            success = self.player.seek_to_index(1000)
            self.assertFalse(success)
            
        finally:
            os.unlink(json_file)
    
    def test_playback_speed_control(self):
        """测试回放速度控制"""
        # 测试设置有效速度
        success = self.player.set_playback_speed(2.0)
        self.assertTrue(success)
        self.assertEqual(self.player.status.playback_speed, 2.0)
        self.assertEqual(self.player.config.playback_speed, 2.0)
        
        # 测试设置无效速度
        success = self.player.set_playback_speed(0.0)
        self.assertFalse(success)
        
        success = self.player.set_playback_speed(-1.0)
        self.assertFalse(success)
    
    def test_get_status(self):
        """测试获取状态"""
        status = self.player.get_status()
        self.assertIsInstance(status, PlaybackStatus)
        self.assertEqual(status.state, PlaybackState.STOPPED)
        self.assertEqual(status.current_time, 0.0)
        self.assertEqual(status.total_duration, 0.0)
        self.assertEqual(status.current_index, 0)
        self.assertEqual(status.total_points, 0)
    
    def test_get_stats(self):
        """测试获取统计信息"""
        stats = self.player.get_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn('total_played_points', stats)
        self.assertIn('playback_start_time', stats)
        self.assertIn('actual_playback_duration', stats)
        self.assertIn('sync_errors', stats)
        self.assertIn('callback_errors', stats)
    
    def test_get_data_summary(self):
        """测试获取数据摘要"""
        # 空数据时的摘要
        summary = self.player.get_data_summary()
        self.assertEqual(summary, {})
        
        # 加载数据后的摘要
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_data, f, indent=2)
            json_file = f.name
        
        try:
            self.player.load_data_from_json(json_file)
            summary = self.player.get_data_summary()
            
            self.assertIn('total_points', summary)
            self.assertIn('data_types', summary)
            self.assertIn('time_range', summary)
            self.assertIn('loaded_from', summary)
            
            self.assertEqual(summary['total_points'], 10)
            self.assertIn('joint_state', summary['data_types'])
            self.assertIn('imu_data', summary['data_types'])
            
        finally:
            os.unlink(json_file)
    
    def test_cleanup(self):
        """测试清理功能"""
        # 加载一些数据
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_data, f, indent=2)
            json_file = f.name
        
        try:
            self.player.load_data_from_json(json_file)
            self.player.register_data_callback('joint_state', lambda x: None)
            self.player.register_status_callback(lambda x: None)
            
            # 执行清理
            self.player.cleanup()
            
            # 验证清理结果
            self.assertEqual(len(self.player.data_points), 0)
            self.assertEqual(len(self.player.filtered_data), 0)
            self.assertEqual(len(self.player.data_callbacks), 0)
            self.assertEqual(len(self.player.status_callbacks), 0)
            
        finally:
            os.unlink(json_file)


class TestDataPlayerIntegration(unittest.TestCase):
    """测试数据回放器集成功能"""
    
    def test_complete_playback_workflow(self):
        """测试完整的回放工作流程"""
        # 创建配置
        config = PlaybackConfig(
            playback_speed=10.0,  # 快速回放以减少测试时间
            loop_playback=False,
            auto_start=False
        )
        player = DataPlayer(config)
        
        try:
            # 创建测试数据
            test_data = []
            base_time = time.time()
            for i in range(5):
                data_point = {
                    'timestamp': base_time + i * 0.01,  # 10ms间隔
                    'data_type': 'test_data',
                    'data': {'value': i}
                }
                test_data.append(data_point)
            
            # 保存到临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(test_data, f, indent=2)
                json_file = f.name
            
            # 加载数据
            success = player.load_data_from_json(json_file)
            self.assertTrue(success)
            
            # 注册回调函数
            received_data = []
            status_updates = []
            
            def data_callback(data_point):
                received_data.append(data_point.data['value'])
            
            def status_callback(status):
                status_updates.append(status.state)
            
            player.register_data_callback('test_data', data_callback)
            player.register_status_callback(status_callback)
            
            # 开始回放
            success = player.start_playback()
            self.assertTrue(success)
            
            # 等待回放完成
            timeout = 5.0  # 5秒超时
            start_time = time.time()
            while (player.get_status().state in [PlaybackState.PLAYING, PlaybackState.PAUSED] and 
                   time.time() - start_time < timeout):
                time.sleep(0.01)
            
            # 验证回放结果
            final_status = player.get_status()
            self.assertIn(final_status.state, [PlaybackState.FINISHED, PlaybackState.STOPPED])
            
            # 验证接收到的数据
            self.assertEqual(len(received_data), 5)
            self.assertEqual(received_data, [0, 1, 2, 3, 4])
            
            # 验证状态更新
            self.assertIn(PlaybackState.PLAYING, status_updates)
            
            # 清理
            os.unlink(json_file)
            
        finally:
            player.cleanup()
    
    def test_loop_playback(self):
        """测试循环回放功能"""
        config = PlaybackConfig(
            playback_speed=50.0,  # 非常快的回放速度
            loop_playback=True,
            auto_start=False
        )
        player = DataPlayer(config)
        
        try:
            # 创建简单的测试数据
            test_data = []
            base_time = time.time()
            for i in range(2):  # 只有2个数据点
                data_point = {
                    'timestamp': base_time + i * 0.01,
                    'data_type': 'test_data',
                    'data': {'value': i}
                }
                test_data.append(data_point)
            
            # 保存到临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(test_data, f, indent=2)
                json_file = f.name
            
            # 加载数据
            player.load_data_from_json(json_file)
            
            # 注册回调函数
            received_data = []
            
            def data_callback(data_point):
                received_data.append(data_point.data['value'])
            
            player.register_data_callback('test_data', data_callback)
            
            # 开始回放
            player.start_playback()
            
            # 等待至少一次循环完成
            time.sleep(0.5)
            
            # 停止回放
            player.stop_playback()
            
            # 验证循环回放（应该接收到多于2个数据点）
            self.assertGreater(len(received_data), 2)
            
            # 验证循环计数
            status = player.get_status()
            self.assertGreaterEqual(status.loop_count, 0)
            
            # 清理
            os.unlink(json_file)
            
        finally:
            player.cleanup()


class TestCreateDefaultPlayer(unittest.TestCase):
    """测试默认回放器创建函数"""
    
    def test_create_default_player_without_file(self):
        """测试创建默认回放器（无数据文件）"""
        player = create_default_player()
        
        self.assertIsInstance(player, DataPlayer)
        self.assertEqual(player.config.playback_speed, 1.0)
        self.assertFalse(player.config.loop_playback)
        self.assertFalse(player.config.auto_start)
        self.assertEqual(len(player.data_points), 0)
        
        player.cleanup()
    
    def test_create_default_player_with_json_file(self):
        """测试创建默认回放器（带JSON文件）"""
        # 创建测试数据文件
        test_data = [
            {
                'timestamp': time.time(),
                'data_type': 'test_data',
                'data': {'value': 1}
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f, indent=2)
            json_file = f.name
        
        try:
            player = create_default_player(json_file)
            
            self.assertIsInstance(player, DataPlayer)
            self.assertEqual(len(player.data_points), 1)
            self.assertEqual(player.status.total_points, 1)
            
            player.cleanup()
            
        finally:
            os.unlink(json_file)


if __name__ == '__main__':
    print("🧪 开始数据回放器测试")
    print("=" * 50)
    
    # 运行测试
    unittest.main(verbosity=2)