#!/usr/bin/env python3
"""
数据记录器单元测试

测试数据记录器的各项功能，包括数据记录、文件保存和配置管理。
"""

import unittest
import tempfile
import shutil
import os
import json
import csv
import time
from pathlib import Path

# 导入测试目标
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/wheel_legged_control'))

from wheel_legged_control.data import DataRecorder, RecordingConfig, DataPoint, create_default_recorder


class TestDataRecorder(unittest.TestCase):
    """数据记录器测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建测试配置
        self.config = RecordingConfig(
            output_directory=self.temp_dir,
            filename_prefix="test_recording",
            auto_timestamp=False,  # 便于测试
            save_json=True,
            save_csv=True,
            save_rosbag=False,
            max_buffer_size=100,
            flush_interval=0.1
        )
        
        self.recorder = DataRecorder(self.config)
    
    def tearDown(self):
        """测试后清理"""
        if hasattr(self, 'recorder'):
            self.recorder.cleanup()
        
        # 清理临时目录
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_recorder_initialization(self):
        """测试记录器初始化"""
        self.assertIsNotNone(self.recorder)
        self.assertEqual(self.recorder.config.output_directory, self.temp_dir)
        self.assertFalse(self.recorder.is_recording)
        self.assertIsNone(self.recorder.session_id)
        self.assertEqual(self.recorder.data_buffer.size(), 0)
    
    def test_start_stop_recording(self):
        """测试开始和停止记录"""
        # 测试开始记录
        success = self.recorder.start_recording("test_experiment")
        self.assertTrue(success)
        self.assertTrue(self.recorder.is_recording)
        self.assertIsNotNone(self.recorder.session_id)
        self.assertIsNotNone(self.recorder.start_time)
        
        # 测试重复开始记录
        success = self.recorder.start_recording("test_experiment2")
        self.assertFalse(success)  # 应该失败
        
        # 测试停止记录
        success = self.recorder.stop_recording()
        self.assertTrue(success)
        self.assertFalse(self.recorder.is_recording)
        
        # 测试重复停止记录
        success = self.recorder.stop_recording()
        self.assertFalse(success)  # 应该失败
    
    def test_record_joint_state(self):
        """测试关节状态记录"""
        self.recorder.start_recording("joint_test")
        
        joint_names = ['joint1', 'joint2', 'joint3']
        positions = [0.1, 0.2, 0.3]
        velocities = [0.01, 0.02, 0.03]
        efforts = [1.0, 2.0, 3.0]
        
        # 记录关节状态
        self.recorder.record_joint_state(joint_names, positions, velocities, efforts)
        
        # 检查缓冲区
        self.assertGreater(self.recorder.data_buffer.size(), 0)
        self.assertEqual(self.recorder.stats['joint_states'], 1)
        
        # 检查数据内容
        data_points = self.recorder.data_buffer.get_all()
        joint_data_points = [p for p in data_points if p.data_type == 'joint_state']
        self.assertEqual(len(joint_data_points), 1)
        
        joint_data = joint_data_points[0].data
        self.assertEqual(joint_data['joint_names'], joint_names)
        self.assertEqual(joint_data['positions'], positions)
        self.assertEqual(joint_data['velocities'], velocities)
        self.assertEqual(joint_data['efforts'], efforts)
        
        self.recorder.stop_recording()
    
    def test_record_imu_data(self):
        """测试IMU数据记录"""
        self.recorder.start_recording("imu_test")
        
        orientation = [0.0, 0.0, 0.0, 1.0]
        angular_velocity = [0.1, 0.2, 0.3]
        linear_acceleration = [0.0, 0.0, 9.81]
        
        # 记录IMU数据
        self.recorder.record_imu_data(orientation, angular_velocity, linear_acceleration)
        
        # 检查统计
        self.assertEqual(self.recorder.stats['imu_data'], 1)
        
        # 检查数据内容
        data_points = self.recorder.data_buffer.get_all()
        imu_data_points = [p for p in data_points if p.data_type == 'imu_data']
        self.assertEqual(len(imu_data_points), 1)
        
        imu_data = imu_data_points[0].data
        self.assertEqual(imu_data['orientation'], orientation)
        self.assertEqual(imu_data['angular_velocity'], angular_velocity)
        self.assertEqual(imu_data['linear_acceleration'], linear_acceleration)
        
        self.recorder.stop_recording()
    
    def test_record_control_command(self):
        """测试控制指令记录"""
        self.recorder.start_recording("control_test")
        
        joint_names = ['joint1', 'joint2']
        commands = [1.5, 2.5]
        command_type = 'position'
        
        # 记录控制指令
        self.recorder.record_control_command(joint_names, commands, command_type)
        
        # 检查统计
        self.assertEqual(self.recorder.stats['control_commands'], 1)
        
        # 检查数据内容
        data_points = self.recorder.data_buffer.get_all()
        control_data_points = [p for p in data_points if p.data_type == 'control_command']
        self.assertEqual(len(control_data_points), 1)
        
        control_data = control_data_points[0].data
        self.assertEqual(control_data['joint_names'], joint_names)
        self.assertEqual(control_data['commands'], commands)
        self.assertEqual(control_data['command_type'], command_type)
        
        self.recorder.stop_recording()
    
    def test_record_system_state(self):
        """测试系统状态记录"""
        self.recorder.start_recording("system_test")
        
        system_state = {
            'battery_level': 85.5,
            'temperature': 42.3,
            'cpu_usage': 65.2
        }
        
        # 记录系统状态
        self.recorder.record_system_state(system_state)
        
        # 检查统计
        self.assertEqual(self.recorder.stats['system_states'], 1)
        
        # 检查数据内容
        data_points = self.recorder.data_buffer.get_all()
        system_data_points = [p for p in data_points if p.data_type == 'system_state']
        self.assertEqual(len(system_data_points), 1)
        
        system_data = system_data_points[0].data
        self.assertEqual(system_data, system_state)
        
        self.recorder.stop_recording()
    
    def test_file_saving(self):
        """测试文件保存功能"""
        # 开始记录
        self.recorder.start_recording("file_test")
        
        # 添加一些测试数据
        self.recorder.record_joint_state(['joint1'], [0.5], [0.1], [1.0])
        self.recorder.record_imu_data([0, 0, 0, 1], [0, 0, 0], [0, 0, 9.81])
        self.recorder.record_control_command(['joint1'], [0.6], 'position')
        self.recorder.record_system_state({'test': 'value'})
        
        # 停止记录
        self.recorder.stop_recording()
        
        # 检查文件是否创建
        expected_files = [
            'test_recording_file_test.json',
            'test_recording_file_test_joint_state.csv',
            'test_recording_file_test_imu_data.csv',
            'test_recording_file_test_control_command.csv',
            'test_recording_file_test_system_state.csv'
        ]
        
        for filename in expected_files:
            filepath = os.path.join(self.temp_dir, filename)
            self.assertTrue(os.path.exists(filepath), f"文件不存在: {filename}")
            self.assertGreater(os.path.getsize(filepath), 0, f"文件为空: {filename}")
    
    def test_json_file_content(self):
        """测试JSON文件内容"""
        self.recorder.start_recording("json_test")
        
        # 添加测试数据
        self.recorder.record_joint_state(['test_joint'], [1.23], [0.45], [6.78])
        
        self.recorder.stop_recording()
        
        # 读取JSON文件
        json_file = os.path.join(self.temp_dir, 'test_recording_json_test.json')
        self.assertTrue(os.path.exists(json_file))
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查数据结构
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        
        # 查找关节状态数据
        joint_data = None
        for item in data:
            if item['data_type'] == 'joint_state':
                joint_data = item
                break
        
        self.assertIsNotNone(joint_data)
        self.assertEqual(joint_data['data']['joint_names'], ['test_joint'])
        self.assertEqual(joint_data['data']['positions'], [1.23])
    
    def test_csv_file_content(self):
        """测试CSV文件内容"""
        self.recorder.start_recording("csv_test")
        
        # 添加测试数据
        joint_names = ['joint1', 'joint2']
        positions = [1.1, 2.2]
        velocities = [0.1, 0.2]
        efforts = [10.0, 20.0]
        
        self.recorder.record_joint_state(joint_names, positions, velocities, efforts)
        
        self.recorder.stop_recording()
        
        # 读取CSV文件
        csv_file = os.path.join(self.temp_dir, 'test_recording_csv_test_joint_state.csv')
        self.assertTrue(os.path.exists(csv_file))
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        # 检查CSV结构
        self.assertGreater(len(rows), 1)  # 至少有标题行和数据行
        
        # 检查标题行
        header = rows[0]
        expected_header = ['timestamp', 'joint_name', 'position', 'velocity', 'effort']
        self.assertEqual(header, expected_header)
        
        # 检查数据行
        self.assertEqual(len(rows), 3)  # 标题行 + 2个关节数据行
        
        # 检查第一个关节数据
        row1 = rows[1]
        self.assertEqual(row1[1], 'joint1')  # joint_name
        self.assertEqual(float(row1[2]), 1.1)  # position
        self.assertEqual(float(row1[3]), 0.1)  # velocity
        self.assertEqual(float(row1[4]), 10.0)  # effort
    
    def test_recording_status(self):
        """测试记录状态获取"""
        # 初始状态
        status = self.recorder.get_recording_status()
        self.assertFalse(status['is_recording'])
        self.assertIsNone(status['session_id'])
        self.assertEqual(status['buffer_size'], 0)
        
        # 记录中状态
        self.recorder.start_recording("status_test")
        self.recorder.record_joint_state(['joint1'], [0.0], [0.0], [0.0])
        
        status = self.recorder.get_recording_status()
        self.assertTrue(status['is_recording'])
        self.assertIsNotNone(status['session_id'])
        self.assertGreater(status['buffer_size'], 0)
        self.assertIn('recording_duration', status)
        
        self.recorder.stop_recording()
        
        # 停止后状态
        status = self.recorder.get_recording_status()
        self.assertFalse(status['is_recording'])
    
    def test_stats(self):
        """测试统计信息"""
        self.recorder.start_recording("stats_test")
        
        # 添加不同类型的数据
        self.recorder.record_joint_state(['joint1'], [0.0], [0.0], [0.0])
        self.recorder.record_joint_state(['joint2'], [1.0], [0.1], [1.0])
        self.recorder.record_imu_data([0, 0, 0, 1], [0, 0, 0], [0, 0, 9.81])
        self.recorder.record_control_command(['joint1'], [0.5], 'position')
        self.recorder.record_system_state({'test': True})
        
        stats = self.recorder.get_stats()
        
        # 检查统计数据
        self.assertEqual(stats['joint_states'], 2)
        self.assertEqual(stats['imu_data'], 1)
        self.assertEqual(stats['control_commands'], 1)
        self.assertEqual(stats['system_states'], 1)
        self.assertGreater(stats['total_points'], 5)  # 包括元数据
        
        self.recorder.stop_recording()
    
    def test_config_validation(self):
        """测试配置验证"""
        # 测试默认配置
        default_config = RecordingConfig()
        self.assertEqual(default_config.output_directory, "./data/recordings")
        self.assertTrue(default_config.record_joint_states)
        self.assertTrue(default_config.save_csv)
        
        # 测试自定义配置
        custom_config = RecordingConfig(
            output_directory="/tmp/test",
            record_joint_states=False,
            save_csv=False
        )
        self.assertEqual(custom_config.output_directory, "/tmp/test")
        self.assertFalse(custom_config.record_joint_states)
        self.assertFalse(custom_config.save_csv)
    
    def test_create_default_recorder(self):
        """测试默认记录器创建"""
        temp_dir = tempfile.mkdtemp()
        try:
            recorder = create_default_recorder(temp_dir)
            self.assertIsNotNone(recorder)
            self.assertEqual(recorder.config.output_directory, temp_dir)
            self.assertTrue(recorder.config.save_json)
            self.assertTrue(recorder.config.save_csv)
            recorder.cleanup()
        finally:
            shutil.rmtree(temp_dir)
    
    def test_data_buffer(self):
        """测试数据缓冲区"""
        from wheel_legged_control.data.data_recorder import DataBuffer, DataPoint
        
        buffer = DataBuffer(max_size=3)
        
        # 添加数据点
        for i in range(5):
            point = DataPoint(
                timestamp=time.time(),
                data_type='test',
                data={'value': i}
            )
            buffer.add(point)
        
        # 检查缓冲区大小限制
        self.assertEqual(buffer.size(), 3)
        
        # 检查数据内容（应该保留最新的3个）
        points = buffer.get_all()
        values = [p.data['value'] for p in points]
        self.assertEqual(values, [2, 3, 4])
        
        # 测试清空
        buffer.clear()
        self.assertEqual(buffer.size(), 0)


class TestDataRecorderIntegration(unittest.TestCase):
    """数据记录器集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_complete_recording_workflow(self):
        """测试完整的记录工作流程"""
        recorder = create_default_recorder(self.temp_dir)
        
        try:
            # 开始记录
            success = recorder.start_recording("integration_test", {
                "test_type": "integration",
                "description": "完整工作流程测试"
            })
            self.assertTrue(success)
            
            # 模拟机器人运行数据
            for i in range(10):
                # 关节状态
                joint_names = ['hip', 'knee', 'wheel']
                positions = [0.1 * i, 0.2 * i, 1.0 * i]
                velocities = [0.01 * i, 0.02 * i, 0.1 * i]
                efforts = [1.0 * i, 2.0 * i, 0.5 * i]
                recorder.record_joint_state(joint_names, positions, velocities, efforts)
                
                # IMU数据
                orientation = [0.0, 0.0, 0.1 * i, 1.0]
                angular_vel = [0.01 * i, 0.02 * i, 0.03 * i]
                linear_acc = [0.1 * i, 0.0, 9.81]
                recorder.record_imu_data(orientation, angular_vel, linear_acc)
                
                # 控制指令
                commands = [p + 0.01 for p in positions]
                recorder.record_control_command(joint_names, commands, 'position')
                
                # 系统状态
                system_state = {
                    'step': i,
                    'battery': 100 - i,
                    'temperature': 25 + i * 0.5
                }
                recorder.record_system_state(system_state)
                
                time.sleep(0.01)  # 模拟时间间隔
            
            # 检查记录状态
            status = recorder.get_recording_status()
            self.assertTrue(status['is_recording'])
            self.assertGreater(status['stats']['total_points'], 40)
            
            # 停止记录
            success = recorder.stop_recording()
            self.assertTrue(success)
            
            # 验证文件生成
            files = os.listdir(self.temp_dir)
            self.assertGreater(len(files), 4)  # 至少有JSON和多个CSV文件
            
            # 验证JSON文件内容
            json_files = [f for f in files if f.endswith('.json')]
            self.assertEqual(len(json_files), 1)
            
            json_file = os.path.join(self.temp_dir, json_files[0])
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            self.assertIsInstance(data, list)
            self.assertGreater(len(data), 40)
            
            # 验证数据类型
            data_types = set(item['data_type'] for item in data)
            expected_types = {'metadata', 'joint_state', 'imu_data', 'control_command', 'system_state', 'end_metadata'}
            self.assertTrue(expected_types.issubset(data_types))
            
        finally:
            recorder.cleanup()


if __name__ == '__main__':
    # 设置日志级别
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # 运行测试
    unittest.main(verbosity=2)