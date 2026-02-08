#!/usr/bin/env python3
"""
仿真后端注册表

管理和注册可用的仿真后端，支持动态加载和插件系统。
"""

import logging
import importlib
from typing import Dict, List, Type, Optional, Any, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from .simulation_manager import BaseSimulationBackend, SimulationBackend, SimulationConfig


@dataclass
class BackendInfo:
    """后端信息"""
    name: str
    backend_type: SimulationBackend
    backend_class: Type[BaseSimulationBackend]
    description: str
    version: str
    dependencies: List[str]
    is_available: bool = False
    error_message: str = None


class BackendRegistry:
    """仿真后端注册表"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._backends: Dict[SimulationBackend, BackendInfo] = {}
        self._initialized = False
        
        # 自动注册内置后端
        self._register_builtin_backends()
    
    def _register_builtin_backends(self):
        """注册内置后端"""
        # MuJoCo后端
        try:
            from .mujoco_backend import MuJoCoSimulationBackend
            import mujoco
            
            self._backends[SimulationBackend.MUJOCO] = BackendInfo(
                name="MuJoCo",
                backend_type=SimulationBackend.MUJOCO,
                backend_class=MuJoCoSimulationBackend,
                description="高性能物理仿真引擎，适合强化学习和精确控制",
                version=getattr(mujoco, '__version__', 'unknown'),
                dependencies=['mujoco'],
                is_available=True
            )
            self.logger.info("✅ MuJoCo后端注册成功")
            
        except ImportError as e:
            self._backends[SimulationBackend.MUJOCO] = BackendInfo(
                name="MuJoCo",
                backend_type=SimulationBackend.MUJOCO,
                backend_class=None,
                description="高性能物理仿真引擎（未安装）",
                version="N/A",
                dependencies=['mujoco'],
                is_available=False,
                error_message=str(e)
            )
            self.logger.warning(f"⚠️  MuJoCo后端不可用: {e}")
        
        # Gazebo后端
        try:
            from .gazebo_backend import GazeboSimulationBackend
            
            # 检查ROS2依赖
            try:
                import rclpy
                ros_available = True
                ros_version = "ROS2"
            except ImportError:
                ros_available = False
                ros_version = "N/A"
            
            self._backends[SimulationBackend.GAZEBO] = BackendInfo(
                name="Gazebo",
                backend_type=SimulationBackend.GAZEBO,
                backend_class=GazeboSimulationBackend,
                description="机器人仿真平台，与ROS2深度集成",
                version=ros_version,
                dependencies=['rclpy', 'gazebo'],
                is_available=True,  # Gazebo后端有模拟模式
                error_message=None if ros_available else "ROS2不可用，使用模拟模式"
            )
            self.logger.info("✅ Gazebo后端注册成功")
            
        except ImportError as e:
            self._backends[SimulationBackend.GAZEBO] = BackendInfo(
                name="Gazebo",
                backend_type=SimulationBackend.GAZEBO,
                backend_class=None,
                description="机器人仿真平台（未安装）",
                version="N/A",
                dependencies=['rclpy', 'gazebo'],
                is_available=False,
                error_message=str(e)
            )
            self.logger.warning(f"⚠️  Gazebo后端不可用: {e}")
    
    def register_backend(self, 
                        backend_type: SimulationBackend,
                        backend_class: Type[BaseSimulationBackend],
                        name: str,
                        description: str = "",
                        version: str = "1.0.0",
                        dependencies: List[str] = None) -> bool:
        """注册自定义后端"""
        try:
            # 验证后端类
            if not issubclass(backend_class, BaseSimulationBackend):
                raise ValueError(f"后端类必须继承自BaseSimulationBackend")
            
            # 检查依赖
            is_available = True
            error_message = None
            
            if dependencies:
                for dep in dependencies:
                    try:
                        importlib.import_module(dep)
                    except ImportError as e:
                        is_available = False
                        error_message = f"缺少依赖: {dep}"
                        break
            
            # 注册后端
            self._backends[backend_type] = BackendInfo(
                name=name,
                backend_type=backend_type,
                backend_class=backend_class,
                description=description,
                version=version,
                dependencies=dependencies or [],
                is_available=is_available,
                error_message=error_message
            )
            
            self.logger.info(f"✅ 自定义后端 {name} 注册成功")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 后端注册失败: {e}")
            return False
    
    def get_available_backends(self) -> List[SimulationBackend]:
        """获取可用的后端列表"""
        return [backend_type for backend_type, info in self._backends.items() 
                if info.is_available]
    
    def get_all_backends(self) -> List[SimulationBackend]:
        """获取所有后端列表（包括不可用的）"""
        return list(self._backends.keys())
    
    def get_backend_info(self, backend_type: SimulationBackend) -> Optional[BackendInfo]:
        """获取后端信息"""
        return self._backends.get(backend_type)
    
    def is_backend_available(self, backend_type: SimulationBackend) -> bool:
        """检查后端是否可用"""
        info = self._backends.get(backend_type)
        return info is not None and info.is_available
    
    def create_backend(self, backend_type: SimulationBackend, config: SimulationConfig) -> Optional[BaseSimulationBackend]:
        """创建后端实例"""
        info = self._backends.get(backend_type)
        
        if not info:
            self.logger.error(f"❌ 未知的后端类型: {backend_type}")
            return None
        
        if not info.is_available:
            self.logger.error(f"❌ 后端不可用: {info.error_message}")
            return None
        
        try:
            backend_instance = info.backend_class(config)
            self.logger.info(f"✅ 后端实例创建成功: {info.name}")
            return backend_instance
            
        except Exception as e:
            self.logger.error(f"❌ 后端实例创建失败: {e}")
            return None
    
    def get_backend_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有后端的状态信息"""
        status = {}
        
        for backend_type, info in self._backends.items():
            status[backend_type.value] = {
                'name': info.name,
                'description': info.description,
                'version': info.version,
                'dependencies': info.dependencies,
                'is_available': info.is_available,
                'error_message': info.error_message
            }
        
        return status
    
    def validate_config(self, backend_type: SimulationBackend, config: SimulationConfig) -> Tuple[bool, str]:
        """验证配置是否适用于指定后端"""
        info = self._backends.get(backend_type)
        
        if not info:
            return False, f"未知的后端类型: {backend_type}"
        
        if not info.is_available:
            return False, f"后端不可用: {info.error_message}"
        
        # 基本配置验证
        if config.dt <= 0:
            return False, "时间步长必须大于0"
        
        if config.max_steps <= 0:
            return False, "最大步数必须大于0"
        
        # 后端特定验证
        if backend_type == SimulationBackend.MUJOCO:
            if config.mujoco_iterations <= 0:
                return False, "MuJoCo迭代次数必须大于0"
            
            if config.mujoco_solver not in ["Newton", "CG", "PGS"]:
                return False, f"不支持的MuJoCo求解器: {config.mujoco_solver}"
        
        return True, "配置验证通过"


# 全局后端注册表实例
_backend_registry = None

def get_backend_registry() -> BackendRegistry:
    """获取全局后端注册表实例"""
    global _backend_registry
    if _backend_registry is None:
        _backend_registry = BackendRegistry()
    return _backend_registry


def register_custom_backend(backend_type: SimulationBackend,
                          backend_class: Type[BaseSimulationBackend],
                          name: str,
                          description: str = "",
                          version: str = "1.0.0",
                          dependencies: List[str] = None) -> bool:
    """注册自定义后端的便捷函数"""
    registry = get_backend_registry()
    return registry.register_backend(
        backend_type, backend_class, name, description, version, dependencies
    )


if __name__ == "__main__":
    # 测试后端注册表
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 测试仿真后端注册表")
    print("=" * 50)
    
    registry = get_backend_registry()
    
    # 显示所有后端状态
    print("📊 后端状态:")
    status = registry.get_backend_status()
    for backend_name, info in status.items():
        print(f"\n🎯 {info['name']} ({backend_name}):")
        print(f"   描述: {info['description']}")
        print(f"   版本: {info['version']}")
        print(f"   依赖: {info['dependencies']}")
        print(f"   可用: {'✅' if info['is_available'] else '❌'}")
        if info['error_message']:
            print(f"   错误: {info['error_message']}")
    
    # 测试可用后端
    available = registry.get_available_backends()
    print(f"\n✅ 可用后端: {[b.value for b in available]}")
    
    # 测试配置验证
    config = SimulationConfig()
    for backend_type in registry.get_all_backends():
        valid, message = registry.validate_config(backend_type, config)
        print(f"🔍 {backend_type.value} 配置验证: {'✅' if valid else '❌'} {message}")
    
    print("\n🎉 测试完成")