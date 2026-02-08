#!/usr/bin/env python3
"""
算法管理器

支持多算法动态切换、性能监控和记录功能的核心管理模块。
为轮腿机器人提供灵活的控制算法管理能力。
"""

import time
import threading
import logging
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from collections import deque, defaultdict


class AlgorithmType(Enum):
    """算法类型枚举"""
    CONTROL = "control"
    PLANNING = "planning"
    ESTIMATION = "estimation"
    OPTIMIZATION = "optimization"


class AlgorithmStatus(Enum):
    """算法状态枚举"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class AlgorithmMetrics:
    """算法性能指标"""
    execution_time: float = 0.0  # 执行时间 (ms)
    success_rate: float = 1.0    # 成功率
    error_count: int = 0         # 错误次数
    total_calls: int = 0         # 总调用次数
    avg_execution_time: float = 0.0  # 平均执行时间
    max_execution_time: float = 0.0  # 最大执行时间
    min_execution_time: float = float('inf')  # 最小执行时间
    last_update_time: float = field(default_factory=time.time)


@dataclass
class AlgorithmConfig:
    """算法配置"""
    name: str
    algorithm_type: AlgorithmType
    parameters: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    priority: int = 1  # 优先级，数字越大优先级越高
    timeout: float = 1.0  # 超时时间 (秒)
    max_retries: int = 3  # 最大重试次数


class BaseAlgorithm(ABC):
    """算法基类"""
    
    def __init__(self, config: AlgorithmConfig):
        self.config = config
        self.status = AlgorithmStatus.IDLE
        self.metrics = AlgorithmMetrics()
        self.logger = logging.getLogger(f"{__name__}.{config.name}")
        self._lock = threading.RLock()
        
    @abstractmethod
    def initialize(self) -> bool:
        """
        初始化算法
        
        Returns:
            初始化是否成功
        """
        pass
    
    @abstractmethod
    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行算法
        
        Args:
            inputs: 输入数据
            
        Returns:
            输出结果
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> bool:
        """
        清理算法资源
        
        Returns:
            清理是否成功
        """
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """获取算法信息"""
        return {
            'name': self.config.name,
            'type': self.config.algorithm_type.value,
            'status': self.status.value,
            'enabled': self.config.enabled,
            'priority': self.config.priority,
            'metrics': {
                'execution_time': self.metrics.execution_time,
                'success_rate': self.metrics.success_rate,
                'error_count': self.metrics.error_count,
                'total_calls': self.metrics.total_calls,
                'avg_execution_time': self.metrics.avg_execution_time
            }
        }
    
    def update_metrics(self, execution_time: float, success: bool):
        """更新性能指标"""
        with self._lock:
            self.metrics.total_calls += 1
            self.metrics.execution_time = execution_time
            
            if success:
                # 更新执行时间统计
                if execution_time < self.metrics.min_execution_time:
                    self.metrics.min_execution_time = execution_time
                if execution_time > self.metrics.max_execution_time:
                    self.metrics.max_execution_time = execution_time
                
                # 更新平均执行时间
                if self.metrics.total_calls == 1:
                    self.metrics.avg_execution_time = execution_time
                else:
                    self.metrics.avg_execution_time = (
                        (self.metrics.avg_execution_time * (self.metrics.total_calls - 1) + execution_time) 
                        / self.metrics.total_calls
                    )
            else:
                self.metrics.error_count += 1
            
            # 更新成功率
            self.metrics.success_rate = (
                (self.metrics.total_calls - self.metrics.error_count) / self.metrics.total_calls
            )
            
            self.metrics.last_update_time = time.time()


class PIDControlAlgorithm(BaseAlgorithm):
    """PID控制算法实现"""
    
    def __init__(self, config: AlgorithmConfig):
        super().__init__(config)
        self.kp = config.parameters.get('kp', 1.0)
        self.ki = config.parameters.get('ki', 0.0)
        self.kd = config.parameters.get('kd', 0.0)
        self.integral = 0.0
        self.prev_error = 0.0
        self.prev_time = None
        
    def initialize(self) -> bool:
        """初始化PID控制器"""
        try:
            self.integral = 0.0
            self.prev_error = 0.0
            self.prev_time = None
            self.status = AlgorithmStatus.IDLE
            self.logger.info(f"PID控制器初始化成功: kp={self.kp}, ki={self.ki}, kd={self.kd}")
            return True
        except Exception as e:
            self.logger.error(f"PID控制器初始化失败: {e}")
            self.status = AlgorithmStatus.ERROR
            return False
    
    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """执行PID控制"""
        try:
            setpoint = inputs.get('setpoint', 0.0)
            current_value = inputs.get('current_value', 0.0)
            dt = inputs.get('dt', 0.01)
            
            # 计算误差
            error = setpoint - current_value
            
            # 比例项
            proportional = self.kp * error
            
            # 积分项
            self.integral += error * dt
            integral = self.ki * self.integral
            
            # 微分项
            if self.prev_time is not None:
                derivative = self.kd * (error - self.prev_error) / dt
            else:
                derivative = 0.0
            
            # 控制输出
            output = proportional + integral + derivative
            
            # 更新历史值
            self.prev_error = error
            self.prev_time = time.time()
            
            return {
                'output': output,
                'error': error,
                'proportional': proportional,
                'integral': integral,
                'derivative': derivative
            }
            
        except Exception as e:
            self.logger.error(f"PID控制执行失败: {e}")
            raise
    
    def cleanup(self) -> bool:
        """清理PID控制器"""
        try:
            self.integral = 0.0
            self.prev_error = 0.0
            self.prev_time = None
            self.status = AlgorithmStatus.STOPPED
            return True
        except Exception as e:
            self.logger.error(f"PID控制器清理失败: {e}")
            return False


class SimpleTrajectoryPlanner(BaseAlgorithm):
    """简单轨迹规划算法"""
    
    def __init__(self, config: AlgorithmConfig):
        super().__init__(config)
        self.max_velocity = config.parameters.get('max_velocity', 1.0)
        self.max_acceleration = config.parameters.get('max_acceleration', 1.0)
        
    def initialize(self) -> bool:
        """初始化轨迹规划器"""
        try:
            self.status = AlgorithmStatus.IDLE
            self.logger.info(f"轨迹规划器初始化成功: max_vel={self.max_velocity}, max_acc={self.max_acceleration}")
            return True
        except Exception as e:
            self.logger.error(f"轨迹规划器初始化失败: {e}")
            self.status = AlgorithmStatus.ERROR
            return False
    
    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """执行轨迹规划"""
        try:
            start_pos = np.array(inputs.get('start_position', [0.0]))
            end_pos = np.array(inputs.get('end_position', [1.0]))
            duration = inputs.get('duration', 1.0)
            num_points = inputs.get('num_points', 50)
            
            # 生成时间序列
            t = np.linspace(0, duration, num_points)
            
            # 简单的三次多项式轨迹
            trajectory = []
            for time_point in t:
                # 归一化时间
                s = time_point / duration
                # 三次多项式插值
                pos = start_pos + (end_pos - start_pos) * (3*s**2 - 2*s**3)
                trajectory.append(pos.tolist())
            
            return {
                'trajectory': trajectory,
                'time_points': t.tolist(),
                'duration': duration,
                'num_points': num_points
            }
            
        except Exception as e:
            self.logger.error(f"轨迹规划执行失败: {e}")
            raise
    
    def cleanup(self) -> bool:
        """清理轨迹规划器"""
        try:
            self.status = AlgorithmStatus.STOPPED
            return True
        except Exception as e:
            self.logger.error(f"轨迹规划器清理失败: {e}")
            return False


class AlgorithmManager:
    """算法管理器核心类"""
    
    def __init__(self, max_history_size: int = 1000):
        self.algorithms: Dict[str, BaseAlgorithm] = {}
        self.active_algorithms: Dict[AlgorithmType, str] = {}
        self.performance_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history_size))
        self.execution_history: deque = deque(maxlen=max_history_size)
        
        # 线程安全
        self._lock = threading.RLock()
        
        # 日志
        self.logger = logging.getLogger(__name__)
        
        # 性能监控
        self.monitoring_enabled = True
        self.monitoring_thread = None
        self.monitoring_interval = 1.0  # 秒
        
        # 算法工厂
        self.algorithm_factories = {
            'pid_control': PIDControlAlgorithm,
            'trajectory_planner': SimpleTrajectoryPlanner,
        }
        
    def register_algorithm_factory(self, name: str, factory: Callable[[AlgorithmConfig], BaseAlgorithm]):
        """注册算法工厂"""
        self.algorithm_factories[name] = factory
        self.logger.info(f"算法工厂已注册: {name}")
    
    def create_algorithm(self, algorithm_id: str, factory_name: str, config: AlgorithmConfig) -> bool:
        """
        创建算法实例
        
        Args:
            algorithm_id: 算法唯一标识
            factory_name: 工厂名称
            config: 算法配置
            
        Returns:
            创建是否成功
        """
        try:
            with self._lock:
                if algorithm_id in self.algorithms:
                    self.logger.warning(f"算法已存在: {algorithm_id}")
                    return False
                
                if factory_name not in self.algorithm_factories:
                    self.logger.error(f"未知的算法工厂: {factory_name}")
                    return False
                
                # 创建算法实例
                factory = self.algorithm_factories[factory_name]
                algorithm = factory(config)
                
                # 初始化算法
                if algorithm.initialize():
                    self.algorithms[algorithm_id] = algorithm
                    self.performance_history[algorithm_id] = deque(maxlen=1000)
                    self.logger.info(f"算法创建成功: {algorithm_id}")
                    return True
                else:
                    self.logger.error(f"算法初始化失败: {algorithm_id}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"创建算法失败: {e}")
            return False
    
    def remove_algorithm(self, algorithm_id: str) -> bool:
        """
        移除算法
        
        Args:
            algorithm_id: 算法标识
            
        Returns:
            移除是否成功
        """
        try:
            with self._lock:
                if algorithm_id not in self.algorithms:
                    self.logger.warning(f"算法不存在: {algorithm_id}")
                    return False
                
                algorithm = self.algorithms[algorithm_id]
                
                # 清理算法
                algorithm.cleanup()
                
                # 从活跃算法中移除
                for alg_type, active_id in list(self.active_algorithms.items()):
                    if active_id == algorithm_id:
                        del self.active_algorithms[alg_type]
                
                # 移除算法
                del self.algorithms[algorithm_id]
                if algorithm_id in self.performance_history:
                    del self.performance_history[algorithm_id]
                
                self.logger.info(f"算法已移除: {algorithm_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"移除算法失败: {e}")
            return False
    
    def set_active_algorithm(self, algorithm_type: AlgorithmType, algorithm_id: str) -> bool:
        """
        设置活跃算法
        
        Args:
            algorithm_type: 算法类型
            algorithm_id: 算法标识
            
        Returns:
            设置是否成功
        """
        try:
            with self._lock:
                if algorithm_id not in self.algorithms:
                    self.logger.error(f"算法不存在: {algorithm_id}")
                    return False
                
                algorithm = self.algorithms[algorithm_id]
                if algorithm.config.algorithm_type != algorithm_type:
                    self.logger.error(f"算法类型不匹配: {algorithm_id}")
                    return False
                
                if not algorithm.config.enabled:
                    self.logger.error(f"算法未启用: {algorithm_id}")
                    return False
                
                # 设置为活跃算法
                self.active_algorithms[algorithm_type] = algorithm_id
                self.logger.info(f"活跃算法已设置: {algorithm_type.value} -> {algorithm_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"设置活跃算法失败: {e}")
            return False
    
    def execute_algorithm(self, algorithm_type: AlgorithmType, inputs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        执行指定类型的活跃算法
        
        Args:
            algorithm_type: 算法类型
            inputs: 输入数据
            
        Returns:
            算法输出结果
        """
        start_time = time.time()
        
        try:
            with self._lock:
                if algorithm_type not in self.active_algorithms:
                    self.logger.error(f"没有活跃的{algorithm_type.value}算法")
                    return None
                
                algorithm_id = self.active_algorithms[algorithm_type]
                algorithm = self.algorithms[algorithm_id]
                
                if algorithm.status == AlgorithmStatus.ERROR:
                    self.logger.error(f"算法处于错误状态: {algorithm_id}")
                    return None
                
                # 设置算法状态为运行中
                algorithm.status = AlgorithmStatus.RUNNING
                
            # 执行算法（在锁外执行以避免阻塞）
            result = algorithm.execute(inputs)
            
            # 计算执行时间
            execution_time = (time.time() - start_time) * 1000  # 转换为毫秒
            
            with self._lock:
                # 更新算法状态和指标
                algorithm.status = AlgorithmStatus.IDLE
                algorithm.update_metrics(execution_time, True)
                
                # 记录性能历史
                self.performance_history[algorithm_id].append({
                    'timestamp': time.time(),
                    'execution_time': execution_time,
                    'success': True
                })
                
                # 记录执行历史
                self.execution_history.append({
                    'timestamp': time.time(),
                    'algorithm_id': algorithm_id,
                    'algorithm_type': algorithm_type.value,
                    'execution_time': execution_time,
                    'success': True
                })
            
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            
            with self._lock:
                if algorithm_type in self.active_algorithms:
                    algorithm_id = self.active_algorithms[algorithm_type]
                    if algorithm_id in self.algorithms:
                        algorithm = self.algorithms[algorithm_id]
                        algorithm.status = AlgorithmStatus.ERROR
                        algorithm.update_metrics(execution_time, False)
                        
                        # 记录失败历史
                        self.performance_history[algorithm_id].append({
                            'timestamp': time.time(),
                            'execution_time': execution_time,
                            'success': False,
                            'error': str(e)
                        })
            
            self.logger.error(f"算法执行失败: {e}")
            return None
    
    def get_algorithm_info(self, algorithm_id: str) -> Optional[Dict[str, Any]]:
        """获取算法信息"""
        with self._lock:
            if algorithm_id not in self.algorithms:
                return None
            return self.algorithms[algorithm_id].get_info()
    
    def get_all_algorithms_info(self) -> Dict[str, Dict[str, Any]]:
        """获取所有算法信息"""
        with self._lock:
            return {
                algorithm_id: algorithm.get_info()
                for algorithm_id, algorithm in self.algorithms.items()
            }
    
    def get_active_algorithms(self) -> Dict[str, str]:
        """获取活跃算法列表"""
        with self._lock:
            return {
                alg_type.value: algorithm_id
                for alg_type, algorithm_id in self.active_algorithms.items()
            }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        with self._lock:
            report = {
                'timestamp': time.time(),
                'total_algorithms': len(self.algorithms),
                'active_algorithms': len(self.active_algorithms),
                'total_executions': len(self.execution_history),
                'algorithms': {}
            }
            
            for algorithm_id, algorithm in self.algorithms.items():
                metrics = algorithm.metrics
                report['algorithms'][algorithm_id] = {
                    'name': algorithm.config.name,
                    'type': algorithm.config.algorithm_type.value,
                    'status': algorithm.status.value,
                    'total_calls': metrics.total_calls,
                    'success_rate': metrics.success_rate,
                    'avg_execution_time': metrics.avg_execution_time,
                    'min_execution_time': metrics.min_execution_time if metrics.min_execution_time != float('inf') else 0,
                    'max_execution_time': metrics.max_execution_time,
                    'error_count': metrics.error_count
                }
            
            return report
    
    def enable_algorithm(self, algorithm_id: str) -> bool:
        """启用算法"""
        with self._lock:
            if algorithm_id not in self.algorithms:
                return False
            self.algorithms[algorithm_id].config.enabled = True
            self.logger.info(f"算法已启用: {algorithm_id}")
            return True
    
    def disable_algorithm(self, algorithm_id: str) -> bool:
        """禁用算法"""
        with self._lock:
            if algorithm_id not in self.algorithms:
                return False
            
            algorithm = self.algorithms[algorithm_id]
            algorithm.config.enabled = False
            
            # 如果是活跃算法，则移除
            for alg_type, active_id in list(self.active_algorithms.items()):
                if active_id == algorithm_id:
                    del self.active_algorithms[alg_type]
                    self.logger.info(f"活跃算法已移除: {alg_type.value}")
            
            self.logger.info(f"算法已禁用: {algorithm_id}")
            return True
    
    def start_monitoring(self):
        """启动性能监控"""
        if self.monitoring_thread is None or not self.monitoring_thread.is_alive():
            self.monitoring_enabled = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            self.logger.info("性能监控已启动")
    
    def stop_monitoring(self):
        """停止性能监控"""
        self.monitoring_enabled = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=2.0)
        self.logger.info("性能监控已停止")
    
    def _monitoring_loop(self):
        """监控循环"""
        while self.monitoring_enabled:
            try:
                # 生成性能报告
                report = self.get_performance_report()
                
                # 检查异常情况
                for algorithm_id, info in report['algorithms'].items():
                    if info['success_rate'] < 0.8:  # 成功率低于80%
                        self.logger.warning(f"算法成功率过低: {algorithm_id} ({info['success_rate']:.2%})")
                    
                    if info['avg_execution_time'] > 100:  # 平均执行时间超过100ms
                        self.logger.warning(f"算法执行时间过长: {algorithm_id} ({info['avg_execution_time']:.2f}ms)")
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"监控循环错误: {e}")
                time.sleep(self.monitoring_interval)
    
    def export_performance_data(self, filename: str) -> bool:
        """导出性能数据"""
        try:
            with self._lock:
                data = {
                    'export_timestamp': time.time(),
                    'performance_report': self.get_performance_report(),
                    'execution_history': list(self.execution_history),
                    'performance_history': {
                        algorithm_id: list(history)
                        for algorithm_id, history in self.performance_history.items()
                    }
                }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"性能数据已导出: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出性能数据失败: {e}")
            return False
    
    def cleanup(self):
        """清理算法管理器"""
        self.stop_monitoring()
        
        with self._lock:
            # 清理所有算法
            for algorithm_id in list(self.algorithms.keys()):
                self.remove_algorithm(algorithm_id)
            
            # 清理历史数据
            self.performance_history.clear()
            self.execution_history.clear()
            self.active_algorithms.clear()
        
        self.logger.info("算法管理器已清理")


def create_default_algorithms(manager: AlgorithmManager) -> bool:
    """创建默认算法集合"""
    try:
        # 创建PID控制算法
        pid_config = AlgorithmConfig(
            name="默认PID控制器",
            algorithm_type=AlgorithmType.CONTROL,
            parameters={'kp': 1.0, 'ki': 0.1, 'kd': 0.05},
            priority=1
        )
        
        if not manager.create_algorithm('default_pid', 'pid_control', pid_config):
            return False
        
        # 创建轨迹规划算法
        planner_config = AlgorithmConfig(
            name="简单轨迹规划器",
            algorithm_type=AlgorithmType.PLANNING,
            parameters={'max_velocity': 1.0, 'max_acceleration': 2.0},
            priority=1
        )
        
        if not manager.create_algorithm('default_planner', 'trajectory_planner', planner_config):
            return False
        
        # 设置为活跃算法
        manager.set_active_algorithm(AlgorithmType.CONTROL, 'default_pid')
        manager.set_active_algorithm(AlgorithmType.PLANNING, 'default_planner')
        
        return True
        
    except Exception as e:
        logging.error(f"创建默认算法失败: {e}")
        return False


if __name__ == "__main__":
    # 测试算法管理器
    print("🚀 测试算法管理器")
    
    # 创建算法管理器
    manager = AlgorithmManager()
    
    # 创建默认算法
    if create_default_algorithms(manager):
        print("✅ 默认算法创建成功")
    else:
        print("❌ 默认算法创建失败")
        exit(1)
    
    # 启动监控
    manager.start_monitoring()
    
    # 测试PID控制算法
    print("\n=== 测试PID控制算法 ===")
    for i in range(5):
        inputs = {
            'setpoint': 1.0,
            'current_value': 0.1 * i,
            'dt': 0.01
        }
        
        result = manager.execute_algorithm(AlgorithmType.CONTROL, inputs)
        if result:
            print(f"PID输出: {result['output']:.3f}, 误差: {result['error']:.3f}")
        else:
            print("PID执行失败")
    
    # 测试轨迹规划算法
    print("\n=== 测试轨迹规划算法 ===")
    planner_inputs = {
        'start_position': [0.0, 0.0],
        'end_position': [1.0, 1.0],
        'duration': 2.0,
        'num_points': 10
    }
    
    result = manager.execute_algorithm(AlgorithmType.PLANNING, planner_inputs)
    if result:
        print(f"轨迹点数: {len(result['trajectory'])}")
        print(f"轨迹持续时间: {result['duration']}s")
    else:
        print("轨迹规划执行失败")
    
    # 获取性能报告
    print("\n=== 性能报告 ===")
    report = manager.get_performance_report()
    print(f"总算法数: {report['total_algorithms']}")
    print(f"活跃算法数: {report['active_algorithms']}")
    print(f"总执行次数: {report['total_executions']}")
    
    for alg_id, info in report['algorithms'].items():
        print(f"算法 {alg_id}:")
        print(f"  - 调用次数: {info['total_calls']}")
        print(f"  - 成功率: {info['success_rate']:.2%}")
        print(f"  - 平均执行时间: {info['avg_execution_time']:.2f}ms")
    
    # 导出性能数据
    if manager.export_performance_data('/tmp/algorithm_performance.json'):
        print("\n✅ 性能数据已导出")
    
    # 清理
    manager.cleanup()
    print("\n🎉 算法管理器测试完成！")