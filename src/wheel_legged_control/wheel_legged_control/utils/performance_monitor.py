#!/usr/bin/env python3
"""
性能监控工具

提供实时性能监控、性能分析和优化建议。
"""

import logging
import time
import functools
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
import threading


@dataclass
class PerformanceMetric:
    """性能指标"""
    name: str
    call_count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    avg_time: float = 0.0
    last_call_time: Optional[datetime] = None
    
    def update(self, execution_time: float):
        """更新指标"""
        self.call_count += 1
        self.total_time += execution_time
        self.min_time = min(self.min_time, execution_time)
        self.max_time = max(self.max_time, execution_time)
        self.avg_time = self.total_time / self.call_count
        self.last_call_time = datetime.now()


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics: Dict[str, PerformanceMetric] = {}
        self.lock = threading.Lock()
        
        # 性能阈值
        self.thresholds = {
            'slow_function': 0.1,  # 100ms
            'very_slow_function': 1.0,  # 1s
            'high_frequency': 100,  # calls/second
        }
        
        self.logger.info("性能监控器初始化完成")
    
    def measure(self, func: Callable) -> Callable:
        """
        性能测量装饰器
        
        用法:
            @performance_monitor.measure
            def my_function():
                pass
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                execution_time = time.time() - start_time
                self.record(func.__name__, execution_time)
        
        return wrapper
    
    def record(self, name: str, execution_time: float):
        """记录性能数据"""
        with self.lock:
            if name not in self.metrics:
                self.metrics[name] = PerformanceMetric(name=name)
            
            self.metrics[name].update(execution_time)
            
            # 检查性能问题
            if execution_time > self.thresholds['very_slow_function']:
                self.logger.warning(
                    f"⚠️  非常慢的函数调用: {name} 耗时 {execution_time:.3f}s"
                )
            elif execution_time > self.thresholds['slow_function']:
                self.logger.debug(
                    f"慢函数调用: {name} 耗时 {execution_time:.3f}s"
                )
    
    def get_metric(self, name: str) -> Optional[PerformanceMetric]:
        """获取指标"""
        return self.metrics.get(name)
    
    def get_all_metrics(self) -> Dict[str, PerformanceMetric]:
        """获取所有指标"""
        return self.metrics.copy()
    
    def get_slow_functions(self, threshold: float = None) -> List[PerformanceMetric]:
        """获取慢函数列表"""
        if threshold is None:
            threshold = self.thresholds['slow_function']
        
        return [
            metric for metric in self.metrics.values()
            if metric.avg_time > threshold
        ]
    
    def get_high_frequency_functions(self, threshold: int = None) -> List[PerformanceMetric]:
        """获取高频调用函数"""
        if threshold is None:
            threshold = self.thresholds['high_frequency']
        
        return [
            metric for metric in self.metrics.values()
            if metric.call_count > threshold
        ]
    
    def generate_report(self) -> str:
        """生成性能报告"""
        report = []
        report.append("=" * 80)
        report.append("性能监控报告")
        report.append("=" * 80)
        report.append(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"监控函数数量: {len(self.metrics)}")
        report.append("")
        
        # 按平均时间排序
        sorted_metrics = sorted(
            self.metrics.values(),
            key=lambda m: m.avg_time,
            reverse=True
        )
        
        # Top 10 最慢函数
        report.append("🐌 Top 10 最慢函数 (按平均时间):")
        report.append(f"{'函数名':<40} {'调用次数':<12} {'平均时间':<12} {'总时间':<12}")
        report.append("-" * 80)
        
        for metric in sorted_metrics[:10]:
            report.append(
                f"{metric.name:<40} {metric.call_count:<12} "
                f"{metric.avg_time*1000:<11.2f}ms {metric.total_time:<11.2f}s"
            )
        
        report.append("")
        
        # Top 10 最频繁调用
        sorted_by_count = sorted(
            self.metrics.values(),
            key=lambda m: m.call_count,
            reverse=True
        )
        
        report.append("🔥 Top 10 最频繁调用:")
        report.append(f"{'函数名':<40} {'调用次数':<12} {'总时间':<12}")
        report.append("-" * 80)
        
        for metric in sorted_by_count[:10]:
            report.append(
                f"{metric.name:<40} {metric.call_count:<12} {metric.total_time:<11.2f}s"
            )
        
        report.append("")
        
        # 性能问题
        slow_functions = self.get_slow_functions()
        if slow_functions:
            report.append(f"⚠️  发现 {len(slow_functions)} 个慢函数:")
            for metric in slow_functions[:5]:
                report.append(f"   - {metric.name}: 平均 {metric.avg_time*1000:.2f}ms")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def reset(self):
        """重置所有指标"""
        with self.lock:
            self.metrics.clear()
        self.logger.info("性能指标已重置")
    
    def reset_metric(self, name: str):
        """重置特定指标"""
        with self.lock:
            if name in self.metrics:
                del self.metrics[name]
                self.logger.info(f"指标 {name} 已重置")


# 全局性能监控器实例
_global_monitor = None

def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控器"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor


def measure_performance(func: Callable) -> Callable:
    """
    性能测量装饰器（使用全局监控器）
    
    用法:
        @measure_performance
        def my_function():
            pass
    """
    monitor = get_performance_monitor()
    return monitor.measure(func)


class PerformanceContext:
    """性能测量上下文管理器"""
    
    def __init__(self, name: str, monitor: Optional[PerformanceMonitor] = None):
        self.name = name
        self.monitor = monitor or get_performance_monitor()
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        execution_time = time.time() - self.start_time
        self.monitor.record(self.name, execution_time)


if __name__ == "__main__":
    # 测试性能监控器
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 测试性能监控器")
    print("=" * 60)
    
    monitor = PerformanceMonitor()
    
    # 测试装饰器
    @monitor.measure
    def fast_function():
        time.sleep(0.01)
    
    @monitor.measure
    def slow_function():
        time.sleep(0.15)
    
    # 执行测试
    print("\n执行测试函数...")
    for i in range(10):
        fast_function()
    
    for i in range(5):
        slow_function()
    
    # 测试上下文管理器
    print("\n测试上下文管理器...")
    for i in range(3):
        with PerformanceContext('context_test', monitor):
            time.sleep(0.05)
    
    # 生成报告
    print("\n" + monitor.generate_report())
    
    # 获取慢函数
    print("\n慢函数列表:")
    for metric in monitor.get_slow_functions(0.1):
        print(f"  - {metric.name}: {metric.avg_time*1000:.2f}ms")
    
    print("\n🎉 测试完成")
