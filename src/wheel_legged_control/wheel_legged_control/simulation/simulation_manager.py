#!/usr/bin/env python3
"""
仿真管理器

提供统一的仿真接口，支持多种物理引擎后端的动态切换。
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
    """仿真管理器"""
    
    def __init__(self, config: SimulationConfig = None):
        self.config = config or SimulationConfig()
        self.logger = logging.getLogger(__name__)
        
        self.backend = None
        self.current_backend_type = None
        
        # 注册的后端
        self._backends = {}
        self._register_backends()
        
        self.logger.info(f"仿真管理器初始化完成，默认后端: {self.config.backend.value}")
    
    def _register_backends(self):
        """注册可用的仿真后端"""
        try:
            from .mujoco_backend import MuJoCoSimulationBackend
            self._backends[SimulationBackend.MUJOCO] = MuJoCoSimulationBackend
            self.logger.info("✅ MuJoCo后端已注册")
        except ImportError as e:
            self.logger.warning(f"⚠️  MuJoCo后端不可用: {e}")
        
        try:
            from .gazebo_backend import GazeboSimulationBackend
            self._backends[SimulationBackend.GAZEBO] = GazeboSimulationBackend
            self.logger.info("✅ Gazebo后端已注册")
        except ImportError as e:
            self.logger.warning(f"⚠️  Gazebo后端不可用: {e}")
    
    def initialize(self, model_path: str, backend: SimulationBackend = None) -> bool:
        """初始化仿真环境"""
        backend = backend or self.config.backend
        
        if backend not in self._backends:
            self.logger.error(f"❌ 不支持的仿真后端: {backend.value}")
            return False
        
        # 切换后端
        if self.current_backend_type != backend:
            if self.backend:
                self.backend.close()
            
            backend_class = self._backends[backend]
            self.backend = backend_class(self.config)
            self.current_backend_type = backend
            
            self.logger.info(f"🔄 切换到仿真后端: {backend.value}")
        
        # 初始化后端
        success = self.backend.initialize(model_path)
        if success:
            self.logger.info(f"✅ 仿真环境初始化成功")
        else:
            self.logger.error(f"❌ 仿真环境初始化失败")
        
        return success
    
    def reset(self) -> bool:
        """重置仿真状态"""
        if not self.backend:
            self.logger.error("❌ 仿真后端未初始化")
            return False
        
        return self.backend.reset()
    
    def step(self, action: Dict[str, float] = None) -> bool:
        """执行一步仿真"""
        if not self.backend:
            self.logger.error("❌ 仿真后端未初始化")
            return False
        
        return self.backend.step(action)
    
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
    
    def switch_backend(self, backend: SimulationBackend, model_path: str = None) -> bool:
        """切换仿真后端"""
        if backend == self.current_backend_type:
            self.logger.info(f"已经在使用 {backend.value} 后端")
            return True
        
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
        return list(self._backends.keys())
    
    def get_current_backend(self) -> Optional[SimulationBackend]:
        """获取当前使用的仿真后端"""
        return self.current_backend_type
    
    def close(self):
        """关闭仿真管理器"""
        if self.backend:
            self.backend.close()
            self.backend = None
            self.current_backend_type = None
        
        self.logger.info("仿真管理器已关闭")


def create_simulation_manager(backend: SimulationBackend = SimulationBackend.MUJOCO, **kwargs) -> SimulationManager:
    """创建仿真管理器的工厂函数"""
    config = SimulationConfig(backend=backend, **kwargs)
    return SimulationManager(config)


if __name__ == "__main__":
    # 测试仿真管理器
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 测试仿真管理器")
    
    # 创建仿真管理器
    sim_manager = create_simulation_manager(SimulationBackend.MUJOCO)
    
    print(f"📊 可用后端: {[b.value for b in sim_manager.get_available_backends()]}")
    print(f"🎯 当前后端: {sim_manager.get_current_backend()}")
    
    # 关闭
    sim_manager.close()
    print("🎉 测试完成")