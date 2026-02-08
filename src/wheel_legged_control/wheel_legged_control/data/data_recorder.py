#!/usr/bin/env python3
"""
数据记录器

实现数据记录与回放功能，支持ROS2 bag格式和CSV格式导出。
记录关节状态、IMU数据和控制指令，用于实验数据分析和算法验证。
"""

import os
import csv
import json
import time
import threading
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from pathlib import Path
import numpy as np

# ROS2相关导入
try:
    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import JointState, Imu
    from std_msgs.msg import Header
    from geometry_msgs.msg import Vector3, Quaternion
    ROS2_AVAILABLE = True
except ImportError:
    ROS2_AVAILABLE = False
    print("⚠️  ROS2未安装，数据记录器将以离线模式运行")


@dataclass
class RecordingConfig:
    """数据记录配置"""
    # 文件路径配置
    output_directory: str = "./data/recordings"
    filename_prefix: str = "robot_data"
    auto_timestamp: bool = True
    
    # 记录格式配置
    save_rosbag: bool = True
    save_csv: bool = True
    save_json: bool = True
    
    # 数据类型配置
    record_joint_states: bool = True
    record_imu_data: bool = True
    record_control_commands: bool = True
    record_system_states: bool = True
    
    # 性能配置
    max_buffer_size: int = 10000
    flush_interval: float = 1.0  # 秒
    compression: bool = True
    
    # 元数据配置
    include_metadata: bool = True
    metadata_fields: List[str] = field(default_factory=lambda: [
        'timestamp', 'session_id', 'robot_model', 'experiment_name'
    ])


@dataclass
class DataPoint:
    """单个数据点"""
    timestamp: float
    data_type: str
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class DataBuffer:
    """数据缓冲区"""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.buffer: List[DataPoint] = []
        self._lock = threading.RLock()
        
    def add(self, data_point: DataPoint):
        """添加数据点"""
        with self._lock:
            self.buffer.append(data_point)
            
            # 如果超过最大大小，移除最旧的数据
            if len(self.buffer) > self.max_size:
                self.buffer.pop(0)
    
    def get_all(self) -> List[DataPoint]:
        """获取所有数据点"""
        with self._lock:
            return self.buffer.copy()
    
    def clear(self):
        """清空缓冲区"""
        with self._lock:
            self.buffer.clear()
    
    def size(self) -> int:
        """获取缓冲区大小"""
        with self._lock:
            return len(self.buffer)


class DataRecorder:
    """数据记录器核心类"""
    
    def __init__(self, config: RecordingConfig = None):
        self.config = config or RecordingConfig()
        self.logger = logging.getLogger(__name__)
        
        # 记录状态
        self.is_recording = False
        self.session_id = None
        self.start_time = None
        self.current_filename = None
        
        # 数据缓冲区
        self.data_buffer = DataBuffer(self.config.max_buffer_size)
        
        # 线程安全
        self._lock = threading.RLock()
        
        # 定时刷新线程
        self.flush_thread = None
        self.flush_stop_event = threading.Event()
        
        # 统计信息
        self.stats = {
            'total_points': 0,
            'joint_states': 0,
            'imu_data': 0,
            'control_commands': 0,
            'system_states': 0,
            'recording_duration': 0.0
        }
        
        # 确保输出目录存在
        self._ensure_output_directory()
        
        self.logger.info("数据记录器初始化完成")
    
    def _ensure_output_directory(self):
        """确保输出目录存在"""
        output_path = Path(self.config.output_directory)
        output_path.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"输出目录: {output_path.absolute()}")
    
    def start_recording(self, experiment_name: str = None, metadata: Dict[str, Any] = None) -> bool:
        """
        开始记录数据
        
        Args:
            experiment_name: 实验名称
            metadata: 额外的元数据
            
        Returns:
            是否成功开始记录
        """
        try:
            with self._lock:
                if self.is_recording:
                    self.logger.warning("数据记录已在进行中")
                    return False
                
                # 生成会话ID和文件名
                self.session_id = self._generate_session_id()
                self.start_time = time.time()
                self.current_filename = self._generate_filename(experiment_name)
                
                # 清空缓冲区和统计
                self.data_buffer.clear()
                self._reset_stats()
                
                # 记录会话元数据
                session_metadata = {
                    'session_id': self.session_id,
                    'start_time': self.start_time,
                    'experiment_name': experiment_name or 'default',
                    'robot_model': 'wheel_legged_robot',
                    'config': self.config.__dict__.copy()
                }
                
                if metadata:
                    session_metadata.update(metadata)
                
                # 添加元数据记录
                self._add_data_point('metadata', session_metadata)
                
                # 设置记录状态
                self.is_recording = True
                
                # 启动定时刷新线程
                self._start_flush_thread()
                
                self.logger.info(f"开始数据记录: {self.current_filename}")
                self.logger.info(f"会话ID: {self.session_id}")
                
                return True
                
        except Exception as e:
            self.logger.error(f"启动数据记录失败: {e}")
            return False
    
    def stop_recording(self) -> bool:
        """
        停止记录数据
        
        Returns:
            是否成功停止记录
        """
        try:
            with self._lock:
                if not self.is_recording:
                    self.logger.warning("数据记录未在进行中")
                    return False
                
                # 停止记录
                self.is_recording = False
                
                # 停止刷新线程
                self._stop_flush_thread()
                
                # 最终刷新数据
                self._flush_data()
                
                # 更新统计信息
                if self.start_time:
                    self.stats['recording_duration'] = time.time() - self.start_time
                
                # 记录结束元数据
                end_metadata = {
                    'session_id': self.session_id,
                    'end_time': time.time(),
                    'duration': self.stats['recording_duration'],
                    'total_points': self.stats['total_points'],
                    'stats': self.stats.copy()
                }
                
                self._add_data_point('end_metadata', end_metadata)
                
                # 最终保存
                self._flush_data()
                
                self.logger.info(f"数据记录已停止: {self.current_filename}")
                self.logger.info(f"记录时长: {self.stats['recording_duration']:.2f}秒")
                self.logger.info(f"总数据点: {self.stats['total_points']}")
                
                return True
                
        except Exception as e:
            self.logger.error(f"停止数据记录失败: {e}")
            return False
    
    def record_joint_state(self, joint_names: List[str], positions: List[float], 
                          velocities: List[float] = None, efforts: List[float] = None):
        """
        记录关节状态数据
        
        Args:
            joint_names: 关节名称列表
            positions: 关节位置
            velocities: 关节速度（可选）
            efforts: 关节力矩（可选）
        """
        if not self.is_recording or not self.config.record_joint_states:
            return
        
        try:
            joint_data = {
                'joint_names': joint_names,
                'positions': positions,
                'velocities': velocities or [0.0] * len(joint_names),
                'efforts': efforts or [0.0] * len(joint_names)
            }
            
            self._add_data_point('joint_state', joint_data)
            self.stats['joint_states'] += 1
            
        except Exception as e:
            self.logger.error(f"记录关节状态失败: {e}")
    
    def record_imu_data(self, orientation: List[float], angular_velocity: List[float], 
                       linear_acceleration: List[float]):
        """
        记录IMU数据
        
        Args:
            orientation: 姿态四元数 [x, y, z, w]
            angular_velocity: 角速度 [x, y, z]
            linear_acceleration: 线性加速度 [x, y, z]
        """
        if not self.is_recording or not self.config.record_imu_data:
            return
        
        try:
            imu_data = {
                'orientation': orientation,
                'angular_velocity': angular_velocity,
                'linear_acceleration': linear_acceleration
            }
            
            self._add_data_point('imu_data', imu_data)
            self.stats['imu_data'] += 1
            
        except Exception as e:
            self.logger.error(f"记录IMU数据失败: {e}")
    
    def record_control_command(self, joint_names: List[str], commands: List[float], 
                              command_type: str = 'position'):
        """
        记录控制指令
        
        Args:
            joint_names: 关节名称列表
            commands: 控制指令
            command_type: 指令类型 ('position', 'velocity', 'effort')
        """
        if not self.is_recording or not self.config.record_control_commands:
            return
        
        try:
            control_data = {
                'joint_names': joint_names,
                'commands': commands,
                'command_type': command_type
            }
            
            self._add_data_point('control_command', control_data)
            self.stats['control_commands'] += 1
            
        except Exception as e:
            self.logger.error(f"记录控制指令失败: {e}")
    
    def record_system_state(self, state_data: Dict[str, Any]):
        """
        记录系统状态
        
        Args:
            state_data: 系统状态数据
        """
        if not self.is_recording or not self.config.record_system_states:
            return
        
        try:
            self._add_data_point('system_state', state_data)
            self.stats['system_states'] += 1
            
        except Exception as e:
            self.logger.error(f"记录系统状态失败: {e}")
    
    def _add_data_point(self, data_type: str, data: Dict[str, Any], metadata: Dict[str, Any] = None):
        """添加数据点到缓冲区"""
        data_point = DataPoint(
            timestamp=time.time(),
            data_type=data_type,
            data=data,
            metadata=metadata
        )
        
        self.data_buffer.add(data_point)
        self.stats['total_points'] += 1
    
    def _generate_session_id(self) -> str:
        """生成会话ID"""
        return f"session_{int(time.time())}_{os.getpid()}"
    
    def _generate_filename(self, experiment_name: str = None) -> str:
        """生成文件名"""
        if self.config.auto_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if experiment_name:
                return f"{self.config.filename_prefix}_{experiment_name}_{timestamp}"
            else:
                return f"{self.config.filename_prefix}_{timestamp}"
        else:
            if experiment_name:
                return f"{self.config.filename_prefix}_{experiment_name}"
            else:
                return self.config.filename_prefix
    
    def _start_flush_thread(self):
        """启动定时刷新线程"""
        if self.flush_thread and self.flush_thread.is_alive():
            return
        
        self.flush_stop_event.clear()
        self.flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
        self.flush_thread.start()
    
    def _stop_flush_thread(self):
        """停止定时刷新线程"""
        if self.flush_thread and self.flush_thread.is_alive():
            self.flush_stop_event.set()
            self.flush_thread.join(timeout=2.0)
    
    def _flush_loop(self):
        """定时刷新循环"""
        while not self.flush_stop_event.wait(self.config.flush_interval):
            try:
                self._flush_data()
            except Exception as e:
                self.logger.error(f"定时刷新失败: {e}")
    
    def _flush_data(self):
        """刷新数据到文件"""
        if not self.current_filename:
            return
        
        data_points = self.data_buffer.get_all()
        if not data_points:
            return
        
        try:
            # 保存为JSON格式
            if self.config.save_json:
                self._save_json(data_points)
            
            # 保存为CSV格式
            if self.config.save_csv:
                self._save_csv(data_points)
            
            # 保存为ROS2 bag格式（如果可用）
            if self.config.save_rosbag and ROS2_AVAILABLE:
                self._save_rosbag(data_points)
            
        except Exception as e:
            self.logger.error(f"刷新数据失败: {e}")
    
    def _save_json(self, data_points: List[DataPoint]):
        """保存为JSON格式"""
        json_file = os.path.join(self.config.output_directory, f"{self.current_filename}.json")
        
        # 转换数据点为可序列化格式
        json_data = []
        for point in data_points:
            json_point = {
                'timestamp': point.timestamp,
                'data_type': point.data_type,
                'data': point.data,
                'metadata': point.metadata
            }
            json_data.append(json_point)
        
        # 写入文件
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False, default=str)
    
    def _save_csv(self, data_points: List[DataPoint]):
        """保存为CSV格式"""
        # 按数据类型分组保存
        data_by_type = {}
        for point in data_points:
            if point.data_type not in data_by_type:
                data_by_type[point.data_type] = []
            data_by_type[point.data_type].append(point)
        
        # 为每种数据类型创建CSV文件
        for data_type, points in data_by_type.items():
            if data_type in ['metadata', 'end_metadata']:
                continue  # 跳过元数据
            
            csv_file = os.path.join(self.config.output_directory, 
                                   f"{self.current_filename}_{data_type}.csv")
            
            self._write_csv_file(csv_file, points, data_type)
    
    def _write_csv_file(self, filename: str, data_points: List[DataPoint], data_type: str):
        """写入CSV文件"""
        if not data_points:
            return
        
        # 确定CSV列
        columns = ['timestamp']
        sample_data = data_points[0].data
        
        if data_type == 'joint_state':
            columns.extend(['joint_name', 'position', 'velocity', 'effort'])
        elif data_type == 'imu_data':
            columns.extend(['orientation_x', 'orientation_y', 'orientation_z', 'orientation_w',
                           'angular_velocity_x', 'angular_velocity_y', 'angular_velocity_z',
                           'linear_acceleration_x', 'linear_acceleration_y', 'linear_acceleration_z'])
        elif data_type == 'control_command':
            columns.extend(['joint_name', 'command', 'command_type'])
        else:
            # 通用格式
            if isinstance(sample_data, dict):
                columns.extend(sample_data.keys())
        
        # 写入CSV文件
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            
            for point in data_points:
                self._write_csv_row(writer, point, data_type)
    
    def _write_csv_row(self, writer, data_point: DataPoint, data_type: str):
        """写入CSV行"""
        base_row = [data_point.timestamp]
        
        if data_type == 'joint_state':
            joint_names = data_point.data['joint_names']
            positions = data_point.data['positions']
            velocities = data_point.data['velocities']
            efforts = data_point.data['efforts']
            
            for i, name in enumerate(joint_names):
                row = base_row + [
                    name,
                    positions[i] if i < len(positions) else 0.0,
                    velocities[i] if i < len(velocities) else 0.0,
                    efforts[i] if i < len(efforts) else 0.0
                ]
                writer.writerow(row)
        
        elif data_type == 'imu_data':
            data = data_point.data
            row = base_row + [
                data['orientation'][0], data['orientation'][1], 
                data['orientation'][2], data['orientation'][3],
                data['angular_velocity'][0], data['angular_velocity'][1], data['angular_velocity'][2],
                data['linear_acceleration'][0], data['linear_acceleration'][1], data['linear_acceleration'][2]
            ]
            writer.writerow(row)
        
        elif data_type == 'control_command':
            joint_names = data_point.data['joint_names']
            commands = data_point.data['commands']
            command_type = data_point.data['command_type']
            
            for i, name in enumerate(joint_names):
                row = base_row + [
                    name,
                    commands[i] if i < len(commands) else 0.0,
                    command_type
                ]
                writer.writerow(row)
        
        else:
            # 通用格式
            if isinstance(data_point.data, dict):
                row = base_row + list(data_point.data.values())
                writer.writerow(row)
    
    def _save_rosbag(self, data_points: List[DataPoint]):
        """保存为ROS2 bag格式"""
        # 这里是ROS2 bag保存的占位符实现
        # 实际实现需要rosbag2_py库
        self.logger.info("ROS2 bag保存功能待实现")
    
    def _reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'total_points': 0,
            'joint_states': 0,
            'imu_data': 0,
            'control_commands': 0,
            'system_states': 0,
            'recording_duration': 0.0
        }
    
    def get_recording_status(self) -> Dict[str, Any]:
        """获取记录状态"""
        with self._lock:
            status = {
                'is_recording': self.is_recording,
                'session_id': self.session_id,
                'current_filename': self.current_filename,
                'buffer_size': self.data_buffer.size(),
                'stats': self.stats.copy()
            }
            
            if self.start_time:
                status['recording_duration'] = time.time() - self.start_time
            
            return status
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.is_recording:
                self.stop_recording()
            
            self._stop_flush_thread()
            self.data_buffer.clear()
            
            self.logger.info("数据记录器清理完成")
            
        except Exception as e:
            self.logger.error(f"数据记录器清理失败: {e}")


def create_default_recorder(output_dir: str = "./data/recordings") -> DataRecorder:
    """创建默认配置的数据记录器"""
    config = RecordingConfig(
        output_directory=output_dir,
        filename_prefix="robot_experiment",
        auto_timestamp=True,
        save_json=True,
        save_csv=True,
        save_rosbag=False,  # 默认关闭ROS2 bag
        record_joint_states=True,
        record_imu_data=True,
        record_control_commands=True,
        record_system_states=True,
        max_buffer_size=5000,
        flush_interval=2.0
    )
    
    return DataRecorder(config)


if __name__ == "__main__":
    # 测试数据记录器
    print("🎬 测试数据记录器")
    print("=" * 50)
    
    # 创建记录器
    recorder = create_default_recorder("./test_data")
    
    # 开始记录
    print("📹 开始记录...")
    success = recorder.start_recording("test_experiment", {"test_mode": True})
    print(f"记录启动: {'成功' if success else '失败'}")
    
    if success:
        # 模拟记录数据
        print("📊 模拟数据记录...")
        
        for i in range(10):
            # 记录关节状态
            joint_names = ['joint1', 'joint2', 'joint3']
            positions = [0.1 * i, 0.2 * i, 0.3 * i]
            velocities = [0.01 * i, 0.02 * i, 0.03 * i]
            recorder.record_joint_state(joint_names, positions, velocities)
            
            # 记录IMU数据
            orientation = [0.0, 0.0, 0.0, 1.0]
            angular_vel = [0.1 * i, 0.0, 0.0]
            linear_acc = [0.0, 0.0, 9.81]
            recorder.record_imu_data(orientation, angular_vel, linear_acc)
            
            # 记录控制指令
            commands = [0.5 * i, 0.6 * i, 0.7 * i]
            recorder.record_control_command(joint_names, commands, 'position')
            
            # 记录系统状态
            system_state = {
                'step': i,
                'battery_level': 100 - i * 2,
                'temperature': 25.0 + i * 0.5
            }
            recorder.record_system_state(system_state)
            
            time.sleep(0.1)
        
        # 获取状态
        status = recorder.get_recording_status()
        print(f"\n📊 记录状态:")
        print(f"   缓冲区大小: {status['buffer_size']}")
        print(f"   总数据点: {status['stats']['total_points']}")
        print(f"   关节状态: {status['stats']['joint_states']}")
        print(f"   IMU数据: {status['stats']['imu_data']}")
        print(f"   控制指令: {status['stats']['control_commands']}")
        print(f"   系统状态: {status['stats']['system_states']}")
        
        # 停止记录
        print("\n⏹️  停止记录...")
        success = recorder.stop_recording()
        print(f"记录停止: {'成功' if success else '失败'}")
        
        # 最终统计
        final_stats = recorder.get_stats()
        print(f"\n📈 最终统计:")
        for key, value in final_stats.items():
            print(f"   {key}: {value}")
    
    # 清理
    recorder.cleanup()
    print("\n🎉 数据记录器测试完成！")