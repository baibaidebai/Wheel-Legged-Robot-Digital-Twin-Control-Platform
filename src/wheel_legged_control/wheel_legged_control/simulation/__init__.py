#!/usr/bin/env python3
"""
仿真模块

提供统一的仿真接口，支持多种物理引擎后端。
"""

from .simulation_manager import SimulationManager, SimulationBackend, SimulationConfig

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

__all__ = [
    'SimulationManager',
    'SimulationBackend', 
    'SimulationConfig'
]

# 添加可用的后端
if MUJOCO_BACKEND_AVAILABLE:
    __all__.append('MuJoCoSimulationBackend')

if GAZEBO_BACKEND_AVAILABLE:
    __all__.append('GazeboSimulationBackend')