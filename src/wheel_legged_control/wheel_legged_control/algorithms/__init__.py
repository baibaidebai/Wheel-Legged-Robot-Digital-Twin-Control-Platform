"""
控制算法模块

包含强化学习、LQR和自定义控制算法的实现。
"""

from .algorithm_manager import AlgorithmManager, BaseAlgorithm
from .lqr_controller import LQRController, LQRConfig, LinearSystemModel
from .ppo_trainer import PPOTrainer, PPOConfig
from .rl_environment import create_wheel_legged_environment, EnvironmentConfig, RewardType

# MuJoCo环境（可选导入）
try:
    from .mujoco_rl_environment import (
        create_mujoco_wheel_legged_environment, 
        MuJoCoEnvironmentConfig,
        MuJoCoWheelLeggedEnvironment
    )
    MUJOCO_ENV_AVAILABLE = True
except ImportError:
    MUJOCO_ENV_AVAILABLE = False

__all__ = [
    'AlgorithmManager',
    'BaseAlgorithm',
    'LQRController', 
    'LQRConfig',
    'LinearSystemModel',
    'PPOTrainer',
    'PPOConfig',
    'create_wheel_legged_environment',
    'EnvironmentConfig',
    'RewardType'
]

# 添加MuJoCo相关导出（如果可用）
if MUJOCO_ENV_AVAILABLE:
    __all__.extend([
        'create_mujoco_wheel_legged_environment',
        'MuJoCoEnvironmentConfig', 
        'MuJoCoWheelLeggedEnvironment'
    ])