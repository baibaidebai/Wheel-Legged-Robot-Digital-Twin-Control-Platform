#!/usr/bin/env python3
"""
数据回放器

实现数据回放功能，支持加载和回放历史记录的数据。
提供播放控制功能（播放、暂停、快进、倒退）和与仿真环境的同步。
"""

import os
import csv
import json
import time
import threading
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from pathlib import Path
import numpy as np
from enum import Enum

# 导入数据记录器的数据结构
try:
    from .data_recorder import DataPoint, RecordingConfig
except ImportError:
    # 用于独立测试时的导入
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from data_recorder import DataPoint, RecordingConfig


class PlaybackState(Enum):
    """回放状态枚举"""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    FINISHED = "finished"


class PlaybackMode(Enum):
    """回放模式枚举"""
    REALTIME = "realtime"      # 实时回放
    FAST = "fast"              # 快速回放
    SLOW = "slow"              # 慢速回放
    STEP = "step"              # 单步回放


@dataclass
class PlaybackConfig:
    """数据回放配置"""
    # 回放速度控制
    playback_speed: float = 1.0      # 回放速度倍数 (1.0 = 实时)
    loop_playback: bool = False      # 是否循环回放
    auto_start: bool = False         # 是否自动开始回放
    
    # 数据过滤
    data_types_filter: List[str] = field(default_factory=list)  # 数据类型过滤器
    time_range_filter: Optional[tuple] = None  # 时间范围过滤器 (start_time, end_time)
    
    # 同步设置
    sync_with_simulation: bool = False  # 是否与仿真同步
    sync_tolerance: float = 0.01        # 同步容差 (秒)
    
    # 缓冲设置
    buffer_size: int = 1000             # 预加载缓冲区大小
    preload_data: bool = True           # 是否预加载数据


@dataclass
class PlaybackStatus:
    """回放状态信息"""
    state: PlaybackState = PlaybackState.STOPPED
    current_time: float = 0.0
    total_duration: float = 0.0
    current_index: int = 0
    total_points: int = 0
    playback_speed: float = 1.0
    loop_count: int = 0
    data_file: Optional[str] = None


class DataPlayer:
    """数据回放器核心类"""
    
    def __init__(self, config: PlaybackConfig = None):
        self.config = config or PlaybackConfig()
        self.logger = logging.getLogger(__name__)
        
        # 回放状态
        self.status = PlaybackStatus()
        self.data_points: List[DataPoint] = []
        self.filtered_data: List[DataPoint] = []
        
        # 回放控制
        self.playback_thread: Optional[threading.Thread] = None
        self.playback_stop_event = threading.Event()
        self.playback_pause_event = threading.Event()
        
        # 线程安全
        self._lock = threading.RLock()
        
        # 回调函数
        self.data_callbacks: Dict[str, List[Callable]] = {}
        self.status_callbacks: List[Callable] = []
        
        # 性能统计
        self.stats = {
            'total_played_points': 0,
            'playback_start_time': 0.0,
            'actual_playback_duration': 0.0,
            'sync_errors': 0,
            'callback_errors': 0
        }
        
        self.logger.info("数据回放器初始化完成")
    
    def load_data_from_json(self, json_file: str) -> bool:
        """
        从JSON文件加载数据
        
        Args:
            json_file: JSON文件路径
            
        Returns:
            加载是否成功
        """
        try:
            if not os.path.exists(json_file):
                self.logger.error(f"JSON文件不存在: {json_file}")
                return False
            
            with open(json_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # 转换为DataPoint对象
            self.data_points = []
            for item in json_data:
                if isinstance(item, dict) and 'timestamp' in item:
                    data_point = DataPoint(
                        timestamp=item['timestamp'],
                        data_type=item.get('data_type', 'unknown'),
                        data=item.get('data', {}),
                        metadata=item.get('metadata')
                    )
                    self.data_points.append(data_point)
            
            # 按时间戳排序
            self.data_points.sort(key=lambda x: x.timestamp)
            
            # 应用过滤器
            self._apply_filters()
            
            # 更新状态
            self._update_status_after_load(json_file)
            
            self.logger.info(f"成功加载数据: {len(self.data_points)}个数据点，来自 {json_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"加载JSON数据失败: {e}")
            return False
    
    def load_data_from_csv_directory(self, csv_directory: str, base_filename: str) -> bool:
        """
        从CSV文件目录加载数据
        
        Args:
            csv_directory: CSV文件目录
            base_filename: 基础文件名（不含扩展名）
            
        Returns:
            加载是否成功
        """
        try:
            if not os.path.exists(csv_directory):
                self.logger.error(f"CSV目录不存在: {csv_directory}")
                return False
            
            self.data_points = []
            
            # 查找所有相关的CSV文件
            csv_files = []
            for file in os.listdir(csv_directory):
                if file.startswith(base_filename) and file.endswith('.csv'):
                    csv_files.append(os.path.join(csv_directory, file))
            
            if not csv_files:
                self.logger.error(f"未找到匹配的CSV文件: {base_filename}*.csv")
                return False
            
            # 加载每个CSV文件
            for csv_file in csv_files:
                data_type = self._extract_data_type_from_filename(csv_file, base_filename)
                if not self._load_csv_file(csv_file, data_type):
                    self.logger.warning(f"加载CSV文件失败: {csv_file}")
            
            # 按时间戳排序
            self.data_points.sort(key=lambda x: x.timestamp)
            
            # 应用过滤器
            self._apply_filters()
            
            # 更新状态
            self._update_status_after_load(csv_directory)
            
            self.logger.info(f"成功加载CSV数据: {len(self.data_points)}个数据点，来自 {len(csv_files)}个文件")
            return True
            
        except Exception as e:
            self.logger.error(f"加载CSV数据失败: {e}")
            return False
    
    def _extract_data_type_from_filename(self, filename: str, base_filename: str) -> str:
        """从文件名提取数据类型"""
        basename = os.path.basename(filename)
        if base_filename in basename:
            # 提取数据类型部分
            suffix = basename.replace(base_filename, '').replace('.csv', '')
            if suffix.startswith('_'):
                return suffix[1:]  # 移除前导下划线
        return 'unknown'
    
    def _load_csv_file(self, csv_file: str, data_type: str) -> bool:
        """加载单个CSV文件"""
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    timestamp = float(row.get('timestamp', 0.0))
                    
                    # 根据数据类型解析数据
                    data = self._parse_csv_row(row, data_type)
                    
                    data_point = DataPoint(
                        timestamp=timestamp,
                        data_type=data_type,
                        data=data,
                        metadata=None
                    )
                    self.data_points.append(data_point)
            
            return True
            
        except Exception as e:
            self.logger.error(f"加载CSV文件失败 {csv_file}: {e}")
            return False
    
    def _parse_csv_row(self, row: Dict[str, str], data_type: str) -> Dict[str, Any]:
        """解析CSV行数据"""
        data = {}
        
        if data_type == 'joint_state':
            data = {
                'joint_names': [row.get('joint_name', '')],
                'positions': [float(row.get('position', 0.0))],
                'velocities': [float(row.get('velocity', 0.0))],
                'efforts': [float(row.get('effort', 0.0))]
            }
        elif data_type == 'imu_data':
            data = {
                'orientation': [
                    float(row.get('orientation_x', 0.0)),
                    float(row.get('orientation_y', 0.0)),
                    float(row.get('orientation_z', 0.0)),
                    float(row.get('orientation_w', 1.0))
                ],
                'angular_velocity': [
                    float(row.get('angular_velocity_x', 0.0)),
                    float(row.get('angular_velocity_y', 0.0)),
                    float(row.get('angular_velocity_z', 0.0))
                ],
                'linear_acceleration': [
                    float(row.get('linear_acceleration_x', 0.0)),
                    float(row.get('linear_acceleration_y', 0.0)),
                    float(row.get('linear_acceleration_z', 0.0))
                ]
            }
        elif data_type == 'control_command':
            data = {
                'joint_names': [row.get('joint_name', '')],
                'commands': [float(row.get('command', 0.0))],
                'command_type': row.get('command_type', 'position')
            }
        else:
            # 通用解析
            data = {k: v for k, v in row.items() if k != 'timestamp'}
        
        return data
    
    def _apply_filters(self):
        """应用数据过滤器"""
        self.filtered_data = self.data_points.copy()
        
        # 数据类型过滤
        if self.config.data_types_filter:
            self.filtered_data = [
                dp for dp in self.filtered_data 
                if dp.data_type in self.config.data_types_filter
            ]
        
        # 时间范围过滤
        if self.config.time_range_filter:
            start_time, end_time = self.config.time_range_filter
            self.filtered_data = [
                dp for dp in self.filtered_data 
                if start_time <= dp.timestamp <= end_time
            ]
        
        self.logger.info(f"过滤后数据点数量: {len(self.filtered_data)}")
    
    def _update_status_after_load(self, data_file: str):
        """加载数据后更新状态"""
        with self._lock:
            self.status.data_file = data_file
            self.status.total_points = len(self.filtered_data)
            self.status.current_index = 0
            self.status.current_time = 0.0
            
            if self.filtered_data:
                start_time = self.filtered_data[0].timestamp
                end_time = self.filtered_data[-1].timestamp
                self.status.total_duration = end_time - start_time
            else:
                self.status.total_duration = 0.0
            
            self.status.state = PlaybackState.STOPPED
    
    def register_data_callback(self, data_type: str, callback: Callable[[DataPoint], None]):
        """
        注册数据回调函数
        
        Args:
            data_type: 数据类型
            callback: 回调函数
        """
        if data_type not in self.data_callbacks:
            self.data_callbacks[data_type] = []
        self.data_callbacks[data_type].append(callback)
        self.logger.info(f"注册数据回调: {data_type}")
    
    def register_status_callback(self, callback: Callable[[PlaybackStatus], None]):
        """
        注册状态回调函数
        
        Args:
            callback: 状态回调函数
        """
        self.status_callbacks.append(callback)
        self.logger.info("注册状态回调")
    
    def start_playback(self) -> bool:
        """
        开始回放
        
        Returns:
            是否成功开始回放
        """
        try:
            with self._lock:
                if self.status.state == PlaybackState.PLAYING:
                    self.logger.warning("回放已在进行中")
                    return False
                
                if not self.filtered_data:
                    self.logger.error("没有可回放的数据")
                    return False
                
                # 重置事件
                self.playback_stop_event.clear()
                self.playback_pause_event.clear()
                
                # 更新状态
                self.status.state = PlaybackState.PLAYING
                self.status.playback_speed = self.config.playback_speed
                self.stats['playback_start_time'] = time.time()
                
                # 启动回放线程
                self.playback_thread = threading.Thread(target=self._playback_loop, daemon=True)
                self.playback_thread.start()
                
                self.logger.info("开始数据回放")
                self._notify_status_callbacks()
                return True
                
        except Exception as e:
            self.logger.error(f"开始回放失败: {e}")
            return False
    
    def pause_playback(self) -> bool:
        """
        暂停回放
        
        Returns:
            是否成功暂停
        """
        try:
            with self._lock:
                if self.status.state != PlaybackState.PLAYING:
                    self.logger.warning("回放未在进行中")
                    return False
                
                self.playback_pause_event.set()
                self.status.state = PlaybackState.PAUSED
                
                self.logger.info("回放已暂停")
                self._notify_status_callbacks()
                return True
                
        except Exception as e:
            self.logger.error(f"暂停回放失败: {e}")
            return False
    
    def resume_playback(self) -> bool:
        """
        恢复回放
        
        Returns:
            是否成功恢复
        """
        try:
            with self._lock:
                if self.status.state != PlaybackState.PAUSED:
                    self.logger.warning("回放未处于暂停状态")
                    return False
                
                self.playback_pause_event.clear()
                self.status.state = PlaybackState.PLAYING
                
                self.logger.info("回放已恢复")
                self._notify_status_callbacks()
                return True
                
        except Exception as e:
            self.logger.error(f"恢复回放失败: {e}")
            return False
    
    def stop_playback(self) -> bool:
        """
        停止回放
        
        Returns:
            是否成功停止
        """
        try:
            with self._lock:
                if self.status.state == PlaybackState.STOPPED:
                    self.logger.warning("回放已停止")
                    return False
                
                # 设置停止事件
                self.playback_stop_event.set()
                self.playback_pause_event.clear()
                
                # 等待回放线程结束
                if self.playback_thread and self.playback_thread.is_alive():
                    self.playback_thread.join(timeout=2.0)
                
                # 更新状态
                self.status.state = PlaybackState.STOPPED
                self.status.current_index = 0
                self.status.current_time = 0.0
                
                # 更新统计
                self.stats['actual_playback_duration'] = time.time() - self.stats['playback_start_time']
                
                self.logger.info("回放已停止")
                self._notify_status_callbacks()
                return True
                
        except Exception as e:
            self.logger.error(f"停止回放失败: {e}")
            return False
    
    def seek_to_time(self, target_time: float) -> bool:
        """
        跳转到指定时间
        
        Args:
            target_time: 目标时间（相对于开始时间）
            
        Returns:
            是否成功跳转
        """
        try:
            with self._lock:
                if not self.filtered_data:
                    return False
                
                start_time = self.filtered_data[0].timestamp
                absolute_time = start_time + target_time
                
                # 查找最接近的数据点
                target_index = 0
                for i, dp in enumerate(self.filtered_data):
                    if dp.timestamp >= absolute_time:
                        target_index = i
                        break
                else:
                    target_index = len(self.filtered_data) - 1
                
                self.status.current_index = target_index
                self.status.current_time = target_time
                
                self.logger.info(f"跳转到时间: {target_time:.2f}s (索引: {target_index})")
                self._notify_status_callbacks()
                return True
                
        except Exception as e:
            self.logger.error(f"跳转失败: {e}")
            return False
    
    def seek_to_index(self, target_index: int) -> bool:
        """
        跳转到指定索引
        
        Args:
            target_index: 目标索引
            
        Returns:
            是否成功跳转
        """
        try:
            with self._lock:
                if not self.filtered_data or target_index < 0 or target_index >= len(self.filtered_data):
                    return False
                
                self.status.current_index = target_index
                
                # 计算相对时间
                if self.filtered_data:
                    start_time = self.filtered_data[0].timestamp
                    current_absolute_time = self.filtered_data[target_index].timestamp
                    self.status.current_time = current_absolute_time - start_time
                
                self.logger.info(f"跳转到索引: {target_index} (时间: {self.status.current_time:.2f}s)")
                self._notify_status_callbacks()
                return True
                
        except Exception as e:
            self.logger.error(f"跳转失败: {e}")
            return False
    
    def set_playback_speed(self, speed: float) -> bool:
        """
        设置回放速度
        
        Args:
            speed: 回放速度倍数
            
        Returns:
            是否成功设置
        """
        try:
            if speed <= 0:
                self.logger.error("回放速度必须大于0")
                return False
            
            with self._lock:
                self.config.playback_speed = speed
                self.status.playback_speed = speed
                
                self.logger.info(f"回放速度设置为: {speed}x")
                self._notify_status_callbacks()
                return True
                
        except Exception as e:
            self.logger.error(f"设置回放速度失败: {e}")
            return False
    
    def _playback_loop(self):
        """回放主循环"""
        try:
            while not self.playback_stop_event.is_set():
                # 检查暂停状态
                if self.playback_pause_event.is_set():
                    time.sleep(0.1)
                    continue
                
                # 检查是否到达结尾
                if self.status.current_index >= len(self.filtered_data):
                    if self.config.loop_playback:
                        # 循环回放
                        self.status.current_index = 0
                        self.status.current_time = 0.0
                        self.status.loop_count += 1
                        self.logger.info(f"开始第{self.status.loop_count + 1}次循环回放")
                    else:
                        # 回放结束
                        with self._lock:
                            self.status.state = PlaybackState.FINISHED
                        self.logger.info("回放完成")
                        self._notify_status_callbacks()
                        break
                
                # 获取当前数据点
                current_data = self.filtered_data[self.status.current_index]
                
                # 计算等待时间
                if self.status.current_index > 0:
                    prev_data = self.filtered_data[self.status.current_index - 1]
                    time_diff = current_data.timestamp - prev_data.timestamp
                    wait_time = time_diff / self.status.playback_speed
                    
                    if wait_time > 0:
                        time.sleep(wait_time)
                
                # 发送数据到回调函数
                self._send_data_to_callbacks(current_data)
                
                # 更新状态
                with self._lock:
                    self.status.current_index += 1
                    if self.filtered_data:
                        start_time = self.filtered_data[0].timestamp
                        self.status.current_time = current_data.timestamp - start_time
                    
                    self.stats['total_played_points'] += 1
                
                # 通知状态更新（每10个数据点通知一次以减少开销）
                if self.status.current_index % 10 == 0:
                    self._notify_status_callbacks()
            
        except Exception as e:
            self.logger.error(f"回放循环错误: {e}")
            with self._lock:
                self.status.state = PlaybackState.STOPPED
            self._notify_status_callbacks()
    
    def _send_data_to_callbacks(self, data_point: DataPoint):
        """发送数据到回调函数"""
        try:
            if data_point.data_type in self.data_callbacks:
                for callback in self.data_callbacks[data_point.data_type]:
                    try:
                        callback(data_point)
                    except Exception as e:
                        self.logger.error(f"数据回调错误: {e}")
                        self.stats['callback_errors'] += 1
        except Exception as e:
            self.logger.error(f"发送数据到回调失败: {e}")
    
    def _notify_status_callbacks(self):
        """通知状态回调函数"""
        try:
            for callback in self.status_callbacks:
                try:
                    callback(self.status)
                except Exception as e:
                    self.logger.error(f"状态回调错误: {e}")
        except Exception as e:
            self.logger.error(f"通知状态回调失败: {e}")
    
    def get_status(self) -> PlaybackStatus:
        """获取回放状态"""
        with self._lock:
            return PlaybackStatus(
                state=self.status.state,
                current_time=self.status.current_time,
                total_duration=self.status.total_duration,
                current_index=self.status.current_index,
                total_points=self.status.total_points,
                playback_speed=self.status.playback_speed,
                loop_count=self.status.loop_count,
                data_file=self.status.data_file
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()
    
    def get_data_summary(self) -> Dict[str, Any]:
        """获取数据摘要"""
        if not self.filtered_data:
            return {}
        
        # 统计数据类型
        data_type_counts = {}
        for dp in self.filtered_data:
            data_type_counts[dp.data_type] = data_type_counts.get(dp.data_type, 0) + 1
        
        return {
            'total_points': len(self.filtered_data),
            'data_types': data_type_counts,
            'time_range': {
                'start': self.filtered_data[0].timestamp,
                'end': self.filtered_data[-1].timestamp,
                'duration': self.filtered_data[-1].timestamp - self.filtered_data[0].timestamp
            },
            'loaded_from': self.status.data_file
        }
    
    def cleanup(self):
        """清理资源"""
        try:
            # 停止回放
            self.stop_playback()
            
            # 清理数据
            self.data_points.clear()
            self.filtered_data.clear()
            
            # 清理回调
            self.data_callbacks.clear()
            self.status_callbacks.clear()
            
            self.logger.info("数据回放器清理完成")
            
        except Exception as e:
            self.logger.error(f"数据回放器清理失败: {e}")


def create_default_player(data_file: str = None) -> DataPlayer:
    """创建默认配置的数据回放器"""
    config = PlaybackConfig(
        playback_speed=1.0,
        loop_playback=False,
        auto_start=False,
        sync_with_simulation=False,
        buffer_size=1000,
        preload_data=True
    )
    
    player = DataPlayer(config)
    
    # 如果提供了数据文件，尝试加载
    if data_file:
        if data_file.endswith('.json'):
            player.load_data_from_json(data_file)
        elif os.path.isdir(data_file):
            # 假设是CSV目录，需要基础文件名
            base_name = "robot_experiment"  # 默认基础名称
            player.load_data_from_csv_directory(data_file, base_name)
    
    return player


if __name__ == "__main__":
    # 测试数据回放器
    print("🎬 测试数据回放器")
    print("=" * 50)
    
    # 创建回放器
    config = PlaybackConfig(
        playback_speed=2.0,  # 2倍速回放
        loop_playback=False,
        auto_start=False
    )
    player = DataPlayer(config)
    
    # 创建测试数据
    test_data = []
    base_time = time.time()
    for i in range(10):
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
        test_data.append(joint_data)
        
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
        test_data.append(imu_data)
    
    # 保存测试数据到临时文件
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_data, f, indent=2)
        test_file = f.name
    
    try:
        # 加载测试数据
        print("📂 加载测试数据...")
        success = player.load_data_from_json(test_file)
        print(f"数据加载: {'成功' if success else '失败'}")
        
        if success:
            # 获取数据摘要
            summary = player.get_data_summary()
            print(f"\n📊 数据摘要:")
            print(f"   总数据点: {summary['total_points']}")
            print(f"   数据类型: {summary['data_types']}")
            print(f"   时间范围: {summary['time_range']['duration']:.2f}秒")
            
            # 注册回调函数
            def joint_callback(data_point):
                positions = data_point.data['positions']
                print(f"   关节位置: {positions}")
            
            def imu_callback(data_point):
                acc = data_point.data['linear_acceleration']
                print(f"   IMU加速度: {acc}")
            
            def status_callback(status):
                if status.current_index % 5 == 0:  # 每5个数据点打印一次
                    print(f"   回放进度: {status.current_index}/{status.total_points} "
                          f"({status.current_time:.2f}s/{status.total_duration:.2f}s)")
            
            player.register_data_callback('joint_state', joint_callback)
            player.register_data_callback('imu_data', imu_callback)
            player.register_status_callback(status_callback)
            
            # 开始回放
            print("\n▶️  开始回放...")
            success = player.start_playback()
            print(f"回放启动: {'成功' if success else '失败'}")
            
            if success:
                # 等待回放完成
                time.sleep(2.0)
                
                # 测试暂停和恢复
                print("\n⏸️  暂停回放...")
                player.pause_playback()
                time.sleep(1.0)
                
                print("▶️  恢复回放...")
                player.resume_playback()
                time.sleep(1.0)
                
                # 等待回放完成
                while player.get_status().state == PlaybackState.PLAYING:
                    time.sleep(0.1)
                
                # 获取最终状态
                final_status = player.get_status()
                stats = player.get_stats()
                
                print(f"\n📈 回放完成:")
                print(f"   最终状态: {final_status.state.value}")
                print(f"   播放数据点: {stats['total_played_points']}")
                print(f"   实际播放时长: {stats['actual_playback_duration']:.2f}秒")
                print(f"   回调错误: {stats['callback_errors']}")
    
    finally:
        # 清理
        player.cleanup()
        os.unlink(test_file)  # 删除临时文件
    
    print("\n🎉 数据回放器测试完成！")