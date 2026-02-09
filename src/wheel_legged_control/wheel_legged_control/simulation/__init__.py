#!/usr/bin/env python3
"""
仿真模块

提供统一的仿真接口，支持多种物理引擎后端。
集成后端注册表和配置管理器，提供完善的仿真架构。
"""

from .simulation_manager import SimulationManager, SimulationBackend, SimulationConfig, BaseSimulationBackend, create_simulation_manager
from .backend_registry import BackendRegistry, get_backend_registry, register_custom_backend

# 尝试导入配置管理器（需要PyYAML）
try:
    from .config_manager import ConfigManager
    CONFIG_MANAGER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  ConfigManager不可用 (缺少PyYAML): {e}")
    ConfigManager = None
    CONFIG_MANAGER_AVAILABLE = False

# 尝试导入后端（可选）
try:
    from .mujoco_backend import MuJoCoSimulationBackend
    MUJOCO_BACKEND_AVAILABLE = True
except ImportError:
    MuJoCoSimulationBackend = None
    MUJOCO_BACKEND_AVAILABLE = False

try:
    from .gazebo_backend import GazeboSimulationBackend
    GAZEBO_BACKEND_AVAILABLE = True
except ImportError:
    GazeboSimulationBackend = None
    GAZEBO_BACKEND_AVAILABLE = False

# 尝试导入并行后端（可选）
try:
    from .parallel_mujoco_backend import ParallelMuJoCoBackend, VectorizedMuJoCoEnvironment
    PARALLEL_BACKEND_AVAILABLE = True
except ImportError:
    ParallelMuJoCoBackend = None
    VectorizedMuJoCoEnvironment = None
    PARALLEL_BACKEND_AVAILABLE = False

# 尝试导入基准测试工具（可选）
try:
    from .benchmark import SimulationBenchmark, BenchmarkResult, run_quick_benchmark
    BENCHMARK_AVAILABLE = True
except ImportError:
    SimulationBenchmark = None
    BenchmarkResult = None
    run_quick_benchmark = None
    BENCHMARK_AVAILABLE = False

__all__ = [
    'SimulationManager',
    'SimulationBackend', 
    'SimulationConfig',
    'BaseSimulationBackend',
    'BackendRegistry',
    'get_backend_registry',
    'register_custom_backend',
    'ConfigManager',
    'create_simulation_manager'
]

# 添加可用的后端
if MUJOCO_BACKEND_AVAILABLE:
    __all__.append('MuJoCoSimulationBackend')

if GAZEBO_BACKEND_AVAILABLE:
    __all__.append('GazeboSimulationBackend')

if PARALLEL_BACKEND_AVAILABLE:
    __all__.extend(['ParallelMuJoCoBackend', 'VectorizedMuJoCoEnvironment'])

if BENCHMARK_AVAILABLE:
    __all__.extend(['SimulationBenchmark', 'BenchmarkResult', 'run_quick_benchmark'])