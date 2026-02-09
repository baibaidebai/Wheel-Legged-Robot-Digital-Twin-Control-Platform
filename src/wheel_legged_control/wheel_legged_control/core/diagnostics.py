#!/usr/bin/env python3
"""
系统诊断工具

提供系统健康检查、性能监控和问题诊断功能。
"""

import logging
import psutil
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class HealthStatus(Enum):
    """健康状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class DiagnosticResult:
    """诊断结果"""
    component: str
    status: HealthStatus
    message: str
    details: Dict[str, Any]
    timestamp: datetime


class SystemDiagnostics:
    """系统诊断器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 阈值配置
        self.thresholds = {
            'cpu_usage': 80.0,  # %
            'memory_usage': 85.0,  # %
            'disk_usage': 90.0,  # %
            'response_time': 1.0,  # seconds
            'error_rate': 0.1  # 10%
        }
        
        # 组件健康状态
        self.component_health: Dict[str, HealthStatus] = {}
        
        # 性能指标
        self.performance_metrics: Dict[str, List[float]] = {}
        
        self.logger.info("系统诊断器初始化完成")
    
    def run_full_diagnostics(self) -> List[DiagnosticResult]:
        """运行完整诊断"""
        results = []
        
        self.logger.info("开始系统诊断...")
        
        # 系统资源检查
        results.append(self._check_cpu_usage())
        results.append(self._check_memory_usage())
        results.append(self._check_disk_usage())
        
        # 网络检查
        results.append(self._check_network())
        
        # 进程检查
        results.append(self._check_processes())
        
        self.logger.info(f"诊断完成，共 {len(results)} 项检查")
        
        return results
    
    def _check_cpu_usage(self) -> DiagnosticResult:
        """检查CPU使用率"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            if cpu_percent > self.thresholds['cpu_usage']:
                status = HealthStatus.UNHEALTHY
                message = f"CPU使用率过高: {cpu_percent:.1f}%"
            elif cpu_percent > self.thresholds['cpu_usage'] * 0.8:
                status = HealthStatus.DEGRADED
                message = f"CPU使用率较高: {cpu_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"CPU使用率正常: {cpu_percent:.1f}%"
            
            return DiagnosticResult(
                component='cpu',
                status=status,
                message=message,
                details={
                    'usage_percent': cpu_percent,
                    'cpu_count': cpu_count,
                    'per_cpu': psutil.cpu_percent(percpu=True)
                },
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"CPU检查失败: {e}")
            return DiagnosticResult(
                component='cpu',
                status=HealthStatus.UNKNOWN,
                message=f"检查失败: {e}",
                details={},
                timestamp=datetime.now()
            )
    
    def _check_memory_usage(self) -> DiagnosticResult:
        """检查内存使用"""
        try:
            memory = psutil.virtual_memory()
            
            if memory.percent > self.thresholds['memory_usage']:
                status = HealthStatus.UNHEALTHY
                message = f"内存使用率过高: {memory.percent:.1f}%"
            elif memory.percent > self.thresholds['memory_usage'] * 0.8:
                status = HealthStatus.DEGRADED
                message = f"内存使用率较高: {memory.percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"内存使用率正常: {memory.percent:.1f}%"
            
            return DiagnosticResult(
                component='memory',
                status=status,
                message=message,
                details={
                    'total_gb': memory.total / (1024**3),
                    'available_gb': memory.available / (1024**3),
                    'used_gb': memory.used / (1024**3),
                    'percent': memory.percent
                },
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"内存检查失败: {e}")
            return DiagnosticResult(
                component='memory',
                status=HealthStatus.UNKNOWN,
                message=f"检查失败: {e}",
                details={},
                timestamp=datetime.now()
            )
    
    def _check_disk_usage(self) -> DiagnosticResult:
        """检查磁盘使用"""
        try:
            disk = psutil.disk_usage('/')
            
            if disk.percent > self.thresholds['disk_usage']:
                status = HealthStatus.UNHEALTHY
                message = f"磁盘使用率过高: {disk.percent:.1f}%"
            elif disk.percent > self.thresholds['disk_usage'] * 0.8:
                status = HealthStatus.DEGRADED
                message = f"磁盘使用率较高: {disk.percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"磁盘使用率正常: {disk.percent:.1f}%"
            
            return DiagnosticResult(
                component='disk',
                status=status,
                message=message,
                details={
                    'total_gb': disk.total / (1024**3),
                    'used_gb': disk.used / (1024**3),
                    'free_gb': disk.free / (1024**3),
                    'percent': disk.percent
                },
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"磁盘检查失败: {e}")
            return DiagnosticResult(
                component='disk',
                status=HealthStatus.UNKNOWN,
                message=f"检查失败: {e}",
                details={},
                timestamp=datetime.now()
            )
    
    def _check_network(self) -> DiagnosticResult:
        """检查网络状态"""
        try:
            net_io = psutil.net_io_counters()
            
            status = HealthStatus.HEALTHY
            message = "网络连接正常"
            
            return DiagnosticResult(
                component='network',
                status=status,
                message=message,
                details={
                    'bytes_sent_mb': net_io.bytes_sent / (1024**2),
                    'bytes_recv_mb': net_io.bytes_recv / (1024**2),
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv,
                    'errors_in': net_io.errin,
                    'errors_out': net_io.errout
                },
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"网络检查失败: {e}")
            return DiagnosticResult(
                component='network',
                status=HealthStatus.UNKNOWN,
                message=f"检查失败: {e}",
                details={},
                timestamp=datetime.now()
            )
    
    def _check_processes(self) -> DiagnosticResult:
        """检查进程状态"""
        try:
            process_count = len(psutil.pids())
            
            # 查找ROS2相关进程
            ros_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    if 'ros' in proc.info['name'].lower():
                        ros_processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            status = HealthStatus.HEALTHY
            message = f"进程运行正常，共 {process_count} 个进程"
            
            return DiagnosticResult(
                component='processes',
                status=status,
                message=message,
                details={
                    'total_processes': process_count,
                    'ros_processes': len(ros_processes),
                    'ros_process_list': ros_processes[:10]  # 限制数量
                },
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"进程检查失败: {e}")
            return DiagnosticResult(
                component='processes',
                status=HealthStatus.UNKNOWN,
                message=f"检查失败: {e}",
                details={},
                timestamp=datetime.now()
            )
    
    def check_component_health(self, component: str, metrics: Dict[str, float]) -> HealthStatus:
        """检查组件健康状态"""
        # 简化的健康检查逻辑
        if 'error_rate' in metrics and metrics['error_rate'] > self.thresholds['error_rate']:
            return HealthStatus.UNHEALTHY
        
        if 'response_time' in metrics and metrics['response_time'] > self.thresholds['response_time']:
            return HealthStatus.DEGRADED
        
        return HealthStatus.HEALTHY
    
    def record_performance_metric(self, component: str, metric_name: str, value: float):
        """记录性能指标"""
        key = f"{component}.{metric_name}"
        
        if key not in self.performance_metrics:
            self.performance_metrics[key] = []
        
        self.performance_metrics[key].append(value)
        
        # 限制历史数据大小
        if len(self.performance_metrics[key]) > 1000:
            self.performance_metrics[key].pop(0)
    
    def get_performance_summary(self, component: str) -> Dict[str, Any]:
        """获取性能摘要"""
        summary = {}
        
        for key, values in self.performance_metrics.items():
            if key.startswith(f"{component}."):
                metric_name = key.split('.', 1)[1]
                if values:
                    summary[metric_name] = {
                        'current': values[-1],
                        'average': sum(values) / len(values),
                        'min': min(values),
                        'max': max(values),
                        'count': len(values)
                    }
        
        return summary
    
    def generate_report(self, results: List[DiagnosticResult]) -> str:
        """生成诊断报告"""
        report = []
        report.append("=" * 60)
        report.append("系统诊断报告")
        report.append("=" * 60)
        report.append(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 按状态分组
        healthy = [r for r in results if r.status == HealthStatus.HEALTHY]
        degraded = [r for r in results if r.status == HealthStatus.DEGRADED]
        unhealthy = [r for r in results if r.status == HealthStatus.UNHEALTHY]
        unknown = [r for r in results if r.status == HealthStatus.UNKNOWN]
        
        report.append(f"✅ 健康: {len(healthy)}")
        report.append(f"⚠️  降级: {len(degraded)}")
        report.append(f"❌ 不健康: {len(unhealthy)}")
        report.append(f"❓ 未知: {len(unknown)}")
        report.append("")
        
        # 详细信息
        for result in results:
            icon = {
                HealthStatus.HEALTHY: "✅",
                HealthStatus.DEGRADED: "⚠️ ",
                HealthStatus.UNHEALTHY: "❌",
                HealthStatus.UNKNOWN: "❓"
            }.get(result.status, "?")
            
            report.append(f"{icon} {result.component}: {result.message}")
            
            if result.details:
                for key, value in result.details.items():
                    if isinstance(value, float):
                        report.append(f"   {key}: {value:.2f}")
                    elif isinstance(value, list) and len(value) > 5:
                        report.append(f"   {key}: [{len(value)} items]")
                    else:
                        report.append(f"   {key}: {value}")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)


if __name__ == "__main__":
    # 测试诊断工具
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 测试系统诊断工具")
    print("=" * 60)
    
    diagnostics = SystemDiagnostics()
    
    # 运行完整诊断
    results = diagnostics.run_full_diagnostics()
    
    # 生成报告
    report = diagnostics.generate_report(results)
    print(report)
    
    # 测试性能指标记录
    print("\n📊 测试性能指标记录")
    for i in range(10):
        diagnostics.record_performance_metric('test_component', 'response_time', 0.1 + i * 0.01)
    
    summary = diagnostics.get_performance_summary('test_component')
    print(f"性能摘要: {summary}")
    
    print("\n🎉 测试完成")
