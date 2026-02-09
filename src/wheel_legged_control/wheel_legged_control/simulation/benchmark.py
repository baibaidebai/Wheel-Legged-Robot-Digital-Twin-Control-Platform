#!/usr/bin/env python3
"""
仿真性能基准测试工具

提供仿真后端性能对比和优化分析工具。
"""

import numpy as np
import time
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
import json

from .simulation_manager import SimulationManager, SimulationConfig, SimulationBackend


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    backend_name: str
    num_steps: int
    total_time: float
    avg_step_time: float
    steps_per_second: float
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    additional_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'backend_name': self.backend_name,
            'num_steps': self.num_steps,
            'total_time': self.total_time,
            'avg_step_time': self.avg_step_time,
            'steps_per_second': self.steps_per_second,
            'memory_usage_mb': self.memory_usage_mb,
            'cpu_usage_percent': self.cpu_usage_percent,
            'additional_metrics': self.additional_metrics
        }


class SimulationBenchmark:
    """仿真性能基准测试"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.results: List[BenchmarkResult] = []
    
    def benchmark_backend(self, 
                         backend: SimulationBackend,
                         model_path: str,
                         num_steps: int = 1000,
                         config: SimulationConfig = None,
                         warmup_steps: int = 100) -> BenchmarkResult:
        """
        对单个后端进行基准测试
        
        Args:
            backend: 仿真后端类型
            model_path: 模型文件路径
            num_steps: 测试步数
            config: 仿真配置
            warmup_steps: 预热步数
            
        Returns:
            基准测试结果
        """
        self.logger.info(f"开始基准测试: {backend.value}")
        
        if config is None:
            config = SimulationConfig(backend=backend, enable_rendering=False)
        else:
            config.backend = backend
            config.enable_rendering = False
        
        try:
            # 创建仿真管理器
            sim_manager = SimulationManager(config)
            
            # 初始化
            if not sim_manager.initialize(model_path):
                self.logger.error(f"后端 {backend.value} 初始化失败")
                return None
            
            # 预热
            self.logger.info(f"预热 {warmup_steps} 步...")
            for _ in range(warmup_steps):
                sim_manager.step()
            
            # 重置计时器
            sim_manager.reset()
            
            # 获取初始资源使用
            memory_start = self._get_memory_usage()
            cpu_start = self._get_cpu_usage()
            
            # 执行基准测试
            self.logger.info(f"执行 {num_steps} 步基准测试...")
            start_time = time.time()
            
            for step in range(num_steps):
                # 随机动作
                action = self._generate_random_action(sim_manager)
                sim_manager.step(action)
                
                # 定期输出进度
                if (step + 1) % (num_steps // 10) == 0:
                    progress = (step + 1) / num_steps * 100
                    self.logger.info(f"进度: {progress:.1f}%")
            
            end_time = time.time()
            
            # 获取最终资源使用
            memory_end = self._get_memory_usage()
            cpu_end = self._get_cpu_usage()
            
            # 计算统计
            total_time = end_time - start_time
            avg_step_time = total_time / num_steps
            steps_per_second = num_steps / total_time
            memory_usage = memory_end - memory_start
            cpu_usage = (cpu_start + cpu_end) / 2  # 平均CPU使用率
            
            # 获取额外指标
            perf_stats = sim_manager.get_performance_stats()
            
            # 创建结果
            result = BenchmarkResult(
                backend_name=backend.value,
                num_steps=num_steps,
                total_time=total_time,
                avg_step_time=avg_step_time,
                steps_per_second=steps_per_second,
                memory_usage_mb=memory_usage,
                cpu_usage_percent=cpu_usage,
                additional_metrics=perf_stats
            )
            
            # 清理
            sim_manager.close()
            
            self.results.append(result)
            self.logger.info(f"✅ {backend.value} 基准测试完成")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 基准测试失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def compare_backends(self,
                        backends: List[SimulationBackend],
                        model_path: str,
                        num_steps: int = 1000,
                        config: SimulationConfig = None) -> Dict[str, BenchmarkResult]:
        """
        对比多个后端的性能
        
        Args:
            backends: 后端列表
            model_path: 模型文件路径
            num_steps: 测试步数
            config: 仿真配置
            
        Returns:
            后端名称到结果的映射
        """
        self.logger.info(f"开始对比 {len(backends)} 个后端")
        
        results = {}
        
        for backend in backends:
            result = self.benchmark_backend(backend, model_path, num_steps, config)
            if result:
                results[backend.value] = result
        
        # 打印对比结果
        self._print_comparison(results)
        
        return results
    
    def benchmark_parallel_performance(self,
                                      backend: SimulationBackend,
                                      model_path: str,
                                      env_counts: List[int] = [1, 2, 4, 8],
                                      steps_per_env: int = 1000) -> Dict[int, BenchmarkResult]:
        """
        测试并行性能扩展性
        
        Args:
            backend: 仿真后端
            model_path: 模型文件路径
            env_counts: 环境数量列表
            steps_per_env: 每个环境的步数
            
        Returns:
            环境数量到结果的映射
        """
        self.logger.info(f"测试并行性能扩展性: {backend.value}")
        
        results = {}
        
        try:
            from .parallel_mujoco_backend import ParallelMuJoCoBackend
            
            for num_envs in env_counts:
                self.logger.info(f"测试 {num_envs} 个并行环境...")
                
                config = SimulationConfig(backend=backend, enable_rendering=False)
                parallel_backend = ParallelMuJoCoBackend(config, num_envs=num_envs)
                
                if not parallel_backend.initialize(model_path):
                    self.logger.error(f"初始化失败: {num_envs} 个环境")
                    continue
                
                # 重置
                parallel_backend.reset()
                
                # 执行测试
                start_time = time.time()
                
                for step in range(steps_per_env):
                    actions = [self._generate_random_action_dict() for _ in range(num_envs)]
                    parallel_backend.step(actions)
                
                end_time = time.time()
                
                # 计算统计
                total_time = end_time - start_time
                total_steps = num_envs * steps_per_env
                avg_step_time = total_time / total_steps
                steps_per_second = total_steps / total_time
                
                result = BenchmarkResult(
                    backend_name=f"{backend.value}_parallel_{num_envs}",
                    num_steps=total_steps,
                    total_time=total_time,
                    avg_step_time=avg_step_time,
                    steps_per_second=steps_per_second,
                    additional_metrics={'num_envs': num_envs}
                )
                
                results[num_envs] = result
                parallel_backend.close()
                
                self.logger.info(f"✅ {num_envs} 个环境: {steps_per_second:.2f} steps/s")
            
            # 打印扩展性分析
            self._print_scalability_analysis(results)
            
        except ImportError:
            self.logger.error("并行后端不可用")
        except Exception as e:
            self.logger.error(f"并行性能测试失败: {e}")
        
        return results
    
    def _generate_random_action(self, sim_manager: SimulationManager) -> Dict[str, float]:
        """生成随机动作"""
        joint_states = sim_manager.get_joint_states()
        action = {}
        
        for joint_name in joint_states.keys():
            action[joint_name] = np.random.uniform(-1.0, 1.0)
        
        return action
    
    def _generate_random_action_dict(self) -> Dict[str, float]:
        """生成随机动作字典"""
        return {
            'lf0_motor': np.random.uniform(-1, 1),
            'lf1_motor': np.random.uniform(-1, 1),
            'rf0_motor': np.random.uniform(-1, 1),
            'rf1_motor': np.random.uniform(-1, 1),
            'l_wheel_motor': np.random.uniform(-1, 1),
            'r_wheel_motor': np.random.uniform(-1, 1)
        }
    
    def _get_memory_usage(self) -> float:
        """获取当前内存使用（MB）"""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            return 0.0
    
    def _get_cpu_usage(self) -> float:
        """获取当前CPU使用率（%）"""
        try:
            import psutil
            return psutil.cpu_percent(interval=0.1)
        except ImportError:
            return 0.0
    
    def _print_comparison(self, results: Dict[str, BenchmarkResult]):
        """打印对比结果"""
        print("\n" + "=" * 80)
        print("仿真后端性能对比")
        print("=" * 80)
        
        # 表头
        print(f"{'后端':<20} {'步数':<10} {'总时间(s)':<12} {'平均步时(ms)':<15} {'步/秒':<12}")
        print("-" * 80)
        
        # 数据行
        for backend_name, result in results.items():
            print(f"{backend_name:<20} {result.num_steps:<10} "
                  f"{result.total_time:<12.3f} {result.avg_step_time*1000:<15.3f} "
                  f"{result.steps_per_second:<12.2f}")
        
        print("=" * 80)
        
        # 找出最快的后端
        if results:
            fastest = max(results.values(), key=lambda r: r.steps_per_second)
            print(f"\n🏆 最快后端: {fastest.backend_name} ({fastest.steps_per_second:.2f} steps/s)")
    
    def _print_scalability_analysis(self, results: Dict[int, BenchmarkResult]):
        """打印扩展性分析"""
        print("\n" + "=" * 80)
        print("并行性能扩展性分析")
        print("=" * 80)
        
        # 表头
        print(f"{'环境数':<10} {'总步数':<12} {'总时间(s)':<12} {'步/秒':<12} {'加速比':<10}")
        print("-" * 80)
        
        # 基准（单环境）
        baseline_sps = results[1].steps_per_second if 1 in results else 1.0
        
        # 数据行
        for num_envs, result in sorted(results.items()):
            speedup = result.steps_per_second / baseline_sps
            print(f"{num_envs:<10} {result.num_steps:<12} "
                  f"{result.total_time:<12.3f} {result.steps_per_second:<12.2f} "
                  f"{speedup:<10.2f}x")
        
        print("=" * 80)
        
        # 计算并行效率
        if len(results) > 1:
            max_envs = max(results.keys())
            max_result = results[max_envs]
            ideal_speedup = max_envs
            actual_speedup = max_result.steps_per_second / baseline_sps
            efficiency = (actual_speedup / ideal_speedup) * 100
            
            print(f"\n📊 并行效率: {efficiency:.1f}% (理想: {ideal_speedup}x, 实际: {actual_speedup:.2f}x)")
    
    def save_results(self, filename: str):
        """保存结果到JSON文件"""
        try:
            data = {
                'results': [r.to_dict() for r in self.results],
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"✅ 结果已保存到: {filename}")
            
        except Exception as e:
            self.logger.error(f"❌ 保存结果失败: {e}")
    
    def load_results(self, filename: str) -> List[BenchmarkResult]:
        """从JSON文件加载结果"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            results = []
            for r in data['results']:
                result = BenchmarkResult(
                    backend_name=r['backend_name'],
                    num_steps=r['num_steps'],
                    total_time=r['total_time'],
                    avg_step_time=r['avg_step_time'],
                    steps_per_second=r['steps_per_second'],
                    memory_usage_mb=r.get('memory_usage_mb', 0.0),
                    cpu_usage_percent=r.get('cpu_usage_percent', 0.0),
                    additional_metrics=r.get('additional_metrics', {})
                )
                results.append(result)
            
            self.results = results
            self.logger.info(f"✅ 从 {filename} 加载了 {len(results)} 个结果")
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ 加载结果失败: {e}")
            return []


def run_quick_benchmark(model_path: str, num_steps: int = 1000):
    """运行快速基准测试"""
    print("🚀 运行快速基准测试")
    print("=" * 80)
    
    benchmark = SimulationBenchmark()
    
    # 获取可用后端
    from .backend_registry import get_backend_registry
    registry = get_backend_registry()
    available_backends = registry.get_available_backends()
    
    print(f"可用后端: {[b.value for b in available_backends]}")
    
    # 对比后端
    results = benchmark.compare_backends(available_backends, model_path, num_steps)
    
    # 保存结果
    benchmark.save_results('benchmark_results.json')
    
    return results


if __name__ == "__main__":
    # 测试基准测试工具
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 测试仿真性能基准测试工具")
    print("=" * 80)
    
    try:
        # 创建测试模型
        from .mujoco_backend import URDFToMJCFConverter
        converter = URDFToMJCFConverter()
        test_mjcf = converter._create_simple_mjcf("test_benchmark_model.xml")
        
        # 运行快速基准测试
        results = run_quick_benchmark(test_mjcf, num_steps=500)
        
        # 测试并行性能
        if SimulationBackend.MUJOCO in [r for r in results.keys()]:
            print("\n🔄 测试并行性能扩展性...")
            benchmark = SimulationBenchmark()
            parallel_results = benchmark.benchmark_parallel_performance(
                SimulationBackend.MUJOCO,
                test_mjcf,
                env_counts=[1, 2, 4],
                steps_per_env=200
            )
        
        # 清理
        import os
        if os.path.exists("test_benchmark_model.xml"):
            os.remove("test_benchmark_model.xml")
        
        print("\n🎉 基准测试工具测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
