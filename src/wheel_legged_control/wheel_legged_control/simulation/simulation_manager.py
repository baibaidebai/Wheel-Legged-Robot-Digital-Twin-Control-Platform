#!/usr/bin/env python3
"""
仿真管理器

提供统一的仿真接口，支持多种物理引擎后端的动态切换。
集成后端注册表和配置管理器，提供完善的仿真架构。
"""

import numpy as np
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum


class SimulationBackend(Enum):
    """仿真后端类型"""
    MUJOCO = "mujoco"
    GAZEBO = "gazebo"


@dataclass
class SimulationConfig:
    """仿真配置参数"""
    # 基本配置
    backend: SimulationBackend = SimulationBackend.MUJOCO
    dt: float = 0.001  # 时间步长
    max_steps: int = 10000
    
    # 物理参数
    gravity: List[float] = None  # [0, 0, -9.81]
    friction: float = 0.8
    restitution: float = 0.1
    
    # 渲染配置
    enable_rendering: bool = True
    render_width: int = 640
    render_height: int = 480
    camera_distance: float = 2.0
    camera_elevation: float = -20.0
    camera_azimuth: float = 45.0
    
    # MuJoCo特定配置
    mujoco_model_path: str = None
    mujoco_solver: str = "Newton"  # "Newton", "CG", "PGS"
    mujoco_iterations: int = 100
    
    # Gazebo特定配置
    gazebo_world_path: str = None
    gazebo_model_path: str = None
    
    def __post_init__(self):
        if self.gravity is None:
            self.gravity = [0, 0, -9.81]


class BaseSimulationBackend(ABC):
    """仿真后端基类"""
    
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.is_initialized = False
        self.current_step = 0
        
        # 机器人状态
        self.joint_positions = {}
        self.joint_velocities = {}
        self.joint_efforts = {}
        self.base_position = np.zeros(3)
        self.base_orientation = np.zeros(4)  # 四元数
        self.base_linear_velocity = np.zeros(3)
        self.base_angular_velocity = np.zeros(3)
    
    @abstractmethod
    def initialize(self, model_path: str) -> bool:
        """初始化仿真环境"""
        pass
    
    @abstractmethod
    def reset(self) -> bool:
        """重置仿真状态"""
        pass
    
    @abstractmethod
    def step(self, action: Dict[str, float] = None) -> bool:
        """执行一步仿真"""
        pass
    
    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """获取当前仿真状态"""
        pass
    
    @abstractmethod
    def set_joint_positions(self, positions: Dict[str, float]) -> bool:
        """设置关节位置"""
        pass
    
    @abstractmethod
    def set_joint_velocities(self, velocities: Dict[str, float]) -> bool:
        """设置关节速度"""
        pass
    
    @abstractmethod
    def set_joint_efforts(self, efforts: Dict[str, float]) -> bool:
        """设置关节力矩"""
        pass
    
    @abstractmethod
    def get_joint_states(self) -> Dict[str, Dict[str, float]]:
        """获取关节状态"""
        pass
    
    @abstractmethod
    def render(self, mode: str = 'human') -> Optional[np.ndarray]:
        """渲染仿真画面"""
        pass
    
    @abstractmethod
    def close(self):
        """关闭仿真环境"""
        pass
    
    def get_base_pose(self) -> Tuple[np.ndarray, np.ndarray]:
        """获取基座位姿"""
        return self.base_position.copy(), self.base_orientation.copy()
    
    def get_base_velocity(self) -> Tuple[np.ndarray, np.ndarray]:
        """获取基座速度"""
        return self.base_linear_velocity.copy(), self.base_angular_velocity.copy()


class SimulationManager:
    """仿真管理器 - 增强版本，集成后端注册表和配置管理器"""
    
    def __init__(self, config: SimulationConfig = None, config_manager=None, backend_registry=None):
        self.config = config or SimulationConfig()
        self.logger = logging.getLogger(__name__)
        
        # 集成配置管理器和后端注册表
        if config_manager is None:
            try:
                from .config_manager import ConfigManager
                self.config_manager = ConfigManager()
            except ImportError:
                # 如果相对导入失败，尝试绝对导入
                try:
                    from wheel_legged_control.simulation.config_manager import ConfigManager
                    self.config_manager = ConfigManager()
                except ImportError:
                    self.config_manager = None
                    self.logger.warning("⚠️  配置管理器不可用")
        else:
            self.config_manager = config_manager
        
        if backend_registry is None:
            try:
                from .backend_registry import get_backend_registry
                self.backend_registry = get_backend_registry()
            except ImportError:
                # 如果相对导入失败，尝试绝对导入
                try:
                    from wheel_legged_control.simulation.backend_registry import get_backend_registry
                    self.backend_registry = get_backend_registry()
                except ImportError:
                    self.backend_registry = None
                    self.logger.warning("⚠️  后端注册表不可用")
        else:
            self.backend_registry = backend_registry
        
        self.backend = None
        self.current_backend_type = None
        
        # 性能监控
        self.performance_stats = {
            'total_steps': 0,
            'total_time': 0.0,
            'average_step_time': 0.0,
            'backend_switches': 0
        }
        
        self.logger.info(f"仿真管理器初始化完成，默认后端: {self.config.backend.value}")
        self.logger.info(f"可用后端: {[b.value for b in self.backend_registry.get_available_backends()]}")
    
    def initialize(self, model_path: str, backend: SimulationBackend = None, config_profile: str = None) -> bool:
        """初始化仿真环境"""
        # 如果指定了配置档案，加载配置
        if config_profile:
            loaded_config = self.config_manager.load_profile(config_profile)
            if loaded_config:
                self.config = loaded_config
                self.logger.info(f"✅ 已加载配置档案: {config_profile}")
            else:
                self.logger.warning(f"⚠️  配置档案加载失败，使用当前配置: {config_profile}")
        
        backend = backend or self.config.backend
        
        # 验证后端可用性
        if not self.backend_registry.is_backend_available(backend):
            available_backends = self.backend_registry.get_available_backends()
            if available_backends:
                backend = available_backends[0]
                self.logger.warning(f"⚠️  指定后端不可用，切换到: {backend.value}")
            else:
                self.logger.error("❌ 没有可用的仿真后端")
                return False
        
        # 验证配置
        valid, message = self.backend_registry.validate_config(backend, self.config)
        if not valid:
            self.logger.error(f"❌ 配置验证失败: {message}")
            return False
        
        # 切换后端
        if self.current_backend_type != backend:
            if self.backend:
                self.backend.close()
            
            self.backend = self.backend_registry.create_backend(backend, self.config)
            if not self.backend:
                self.logger.error(f"❌ 后端创建失败: {backend.value}")
                return False
            
            self.current_backend_type = backend
            self.performance_stats['backend_switches'] += 1
            
            self.logger.info(f"🔄 切换到仿真后端: {backend.value}")
        
        # 初始化后端
        success = self.backend.initialize(model_path)
        if success:
            self._current_model_path = model_path  # 保存模型路径
            self.logger.info(f"✅ 仿真环境初始化成功")
        else:
            self.logger.error(f"❌ 仿真环境初始化失败")
        
        return success
    
    def reset(self) -> bool:
        """重置仿真状态"""
        if not self.backend:
            self.logger.error("❌ 仿真后端未初始化")
            return False
        
        success = self.backend.reset()
        if success:
            self.performance_stats['total_steps'] = 0
            self.performance_stats['total_time'] = 0.0
            self.performance_stats['average_step_time'] = 0.0
        
        return success
    
    def step(self, action: Dict[str, float] = None) -> bool:
        """执行一步仿真"""
        if not self.backend:
            self.logger.error("❌ 仿真后端未初始化")
            return False
        
        import time
        start_time = time.time()
        
        success = self.backend.step(action)
        
        if success:
            step_time = time.time() - start_time
            self.performance_stats['total_steps'] += 1
            self.performance_stats['total_time'] += step_time
            self.performance_stats['average_step_time'] = (
                self.performance_stats['total_time'] / self.performance_stats['total_steps']
            )
        
        return success
    
    def get_state(self) -> Dict[str, Any]:
        """获取当前仿真状态"""
        if not self.backend:
            self.logger.error("❌ 仿真后端未初始化")
            return {}
        
        return self.backend.get_state()
    
    def set_joint_positions(self, positions: Dict[str, float]) -> bool:
        """设置关节位置"""
        if not self.backend:
            self.logger.error("❌ 仿真后端未初始化")
            return False
        
        return self.backend.set_joint_positions(positions)
    
    def set_joint_velocities(self, velocities: Dict[str, float]) -> bool:
        """设置关节速度"""
        if not self.backend:
            self.logger.error("❌ 仿真后端未初始化")
            return False
        
        return self.backend.set_joint_velocities(velocities)
    
    def set_joint_efforts(self, efforts: Dict[str, float]) -> bool:
        """设置关节力矩"""
        if not self.backend:
            self.logger.error("❌ 仿真后端未初始化")
            return False
        
        return self.backend.set_joint_efforts(efforts)
    
    def get_joint_states(self) -> Dict[str, Dict[str, float]]:
        """获取关节状态"""
        if not self.backend:
            self.logger.error("❌ 仿真后端未初始化")
            return {}
        
        return self.backend.get_joint_states()
    
    def get_base_pose(self) -> Tuple[np.ndarray, np.ndarray]:
        """获取基座位姿"""
        if not self.backend:
            self.logger.error("❌ 仿真后端未初始化")
            return np.zeros(3), np.zeros(4)
        
        return self.backend.get_base_pose()
    
    def get_base_velocity(self) -> Tuple[np.ndarray, np.ndarray]:
        """获取基座速度"""
        if not self.backend:
            self.logger.error("❌ 仿真后端未初始化")
            return np.zeros(3), np.zeros(3)
        
        return self.backend.get_base_velocity()
    
    def render(self, mode: str = 'human') -> Optional[np.ndarray]:
        """渲染仿真画面"""
        if not self.backend:
            self.logger.error("❌ 仿真后端未初始化")
            return None
        
        return self.backend.render(mode)
    
    def switch_backend(self, backend: SimulationBackend, model_path: str = None, config_profile: str = None) -> bool:
        """切换仿真后端"""
        if backend == self.current_backend_type:
            self.logger.info(f"已经在使用 {backend.value} 后端")
            return True
        
        # 检查后端可用性
        if not self.backend_registry.is_backend_available(backend):
            self.logger.error(f"❌ 后端不可用: {backend.value}")
            return False
        
        # 加载新配置（如果指定）
        if config_profile:
            new_config = self.config_manager.load_profile(config_profile)
            if new_config:
                self.config = new_config
                self.logger.info(f"✅ 已加载新配置档案: {config_profile}")
        
        # 保存当前状态
        current_state = None
        if self.backend:
            current_state = self.backend.get_state()
            self.backend.close()
        
        # 切换后端
        self.config.backend = backend
        if model_path:
            success = self.initialize(model_path, backend)
        else:
            self.logger.error("❌ 切换后端需要提供模型路径")
            return False
        
        # 恢复状态（如果可能）
        if success and current_state:
            try:
                if 'joint_positions' in current_state:
                    self.set_joint_positions(current_state['joint_positions'])
                if 'joint_velocities' in current_state:
                    self.set_joint_velocities(current_state['joint_velocities'])
            except Exception as e:
                self.logger.warning(f"⚠️  状态恢复失败: {e}")
        
        return success
    
    def get_available_backends(self) -> List[SimulationBackend]:
        """获取可用的仿真后端"""
        return self.backend_registry.get_available_backends()
    
    def get_current_backend(self) -> Optional[SimulationBackend]:
        """获取当前使用的仿真后端"""
        return self.current_backend_type
    
    def get_backend_info(self, backend: SimulationBackend = None) -> Dict[str, Any]:
        """获取后端信息"""
        if backend is None:
            backend = self.current_backend_type
        
        if backend is None:
            return {}
        
        info = self.backend_registry.get_backend_info(backend)
        if info:
            return {
                'name': info.name,
                'description': info.description,
                'version': info.version,
                'dependencies': info.dependencies,
                'is_available': info.is_available,
                'error_message': info.error_message
            }
        return {}
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        stats = self.performance_stats.copy()
        
        if self.performance_stats['total_time'] > 0:
            stats['simulation_frequency'] = self.performance_stats['total_steps'] / self.performance_stats['total_time']
        else:
            stats['simulation_frequency'] = 0.0
        
        return stats
    
    def save_current_config(self, profile_name: str) -> bool:
        """保存当前配置为档案"""
        return self.config_manager.save_profile(self.config, profile_name)
    
    def load_config_profile(self, profile_name: str) -> bool:
        """加载配置档案"""
        config = self.config_manager.load_profile(profile_name)
        if config:
            self.config = config
            self.logger.info(f"✅ 配置档案已加载: {profile_name}")
            return True
        else:
            self.logger.error(f"❌ 配置档案加载失败: {profile_name}")
            return False
    
    def list_config_profiles(self) -> Dict[str, List[str]]:
        """列出所有配置档案"""
        return self.config_manager.list_profiles()
    
    def validate_current_config(self) -> Tuple[bool, List[str]]:
        """验证当前配置"""
        return self.config_manager.validate_config(self.config)
    
    def enable_parallel_simulation(self, num_envs: int, use_multiprocessing: bool = False) -> bool:
        """
        启用并行仿真模式
        
        Args:
            num_envs: 并行环境数量
            use_multiprocessing: 是否使用多进程（True）或多线程（False）
            
        Returns:
            是否成功启用
        """
        if self.current_backend_type != SimulationBackend.MUJOCO:
            self.logger.error("❌ 并行仿真目前仅支持MuJoCo后端")
            return False
        
        try:
            from .parallel_mujoco_backend import ParallelMuJoCoBackend
            
            # 保存当前模型路径（如果有）
            model_path = getattr(self, '_current_model_path', None)
            if not model_path:
                self.logger.error("❌ 需要先初始化模型才能启用并行仿真")
                return False
            
            # 关闭当前后端
            if self.backend:
                self.backend.close()
            
            # 创建并行后端
            self.backend = ParallelMuJoCoBackend(self.config, num_envs, use_multiprocessing)
            
            # 初始化
            if not self.backend.initialize(model_path):
                self.logger.error("❌ 并行后端初始化失败")
                return False
            
            self.logger.info(f"✅ 并行仿真已启用: {num_envs}个环境")
            return True
            
        except ImportError as e:
            self.logger.error(f"❌ 并行后端不可用: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ 启用并行仿真失败: {e}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'current_backend': self.current_backend_type.value if self.current_backend_type else None,
            'backend_initialized': self.backend is not None and self.backend.is_initialized,
            'available_backends': [b.value for b in self.get_available_backends()],
            'performance_stats': self.get_performance_stats(),
            'config_valid': self.validate_current_config()[0],
            'config_profiles': self.list_config_profiles()
        }
    
    def close(self):
        """关闭仿真管理器"""
        if self.backend:
            self.backend.close()
            self.backend = None
            self.current_backend_type = None
        
        self.logger.info("仿真管理器已关闭")


def create_simulation_manager(backend: SimulationBackend = SimulationBackend.MUJOCO, 
                            config_profile: str = None,
                            **kwargs) -> SimulationManager:
    """创建仿真管理器的工厂函数"""
    # 如果指定了配置档案，优先使用档案配置
    if config_profile:
        from .config_manager import ConfigManager
        config_manager = ConfigManager()
        config = config_manager.load_profile(config_profile)
        if config is None:
            # 如果档案不存在，使用默认配置
            config = SimulationConfig(backend=backend, **kwargs)
    else:
        config = SimulationConfig(backend=backend, **kwargs)
    
    return SimulationManager(config)


if __name__ == "__main__":
    # 测试增强版仿真管理器
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 测试增强版仿真管理器")
    print("=" * 50)
    
    # 直接创建配置，避免相对导入问题
    config = SimulationConfig(backend=SimulationBackend.MUJOCO)
    sim_manager = SimulationManager(config)
    
    print(f"📊 可用后端: {[b.value for b in sim_manager.get_available_backends()]}")
    print(f"🎯 当前后端: {sim_manager.get_current_backend()}")
    
    # 测试配置档案
    print("\n📁 配置档案:")
    profiles = sim_manager.list_config_profiles()
    print(f"默认档案: {profiles['default']}")
    print(f"用户档案: {profiles['user']}")
    
    # 测试后端信息
    print("\n🔍 后端信息:")
    for backend in sim_manager.get_available_backends():
        info = sim_manager.get_backend_info(backend)
        print(f"{backend.value}: {info.get('name', 'N/A')} v{info.get('version', 'N/A')}")
    
    # 测试系统状态
    print("\n📈 系统状态:")
    status = sim_manager.get_system_status()
    print(f"当前后端: {status['current_backend']}")
    print(f"后端已初始化: {status['backend_initialized']}")
    print(f"配置有效: {status['config_valid']}")
    
    # 测试性能统计
    print("\n⚡ 性能统计:")
    perf_stats = sim_manager.get_performance_stats()
    for key, value in perf_stats.items():
        print(f"{key}: {value}")
    
    # 关闭
    sim_manager.close()
    print("\n🎉 测试完成")