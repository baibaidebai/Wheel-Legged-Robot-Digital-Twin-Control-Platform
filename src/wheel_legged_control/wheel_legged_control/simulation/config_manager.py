#!/usr/bin/env python3
"""
仿真配置管理器

提供配置文件加载、验证、保存和模板生成功能。
"""

import os
import json
import yaml
import logging
import time
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict, fields
from pathlib import Path

from .simulation_manager import SimulationConfig, SimulationBackend


class ConfigManager:
    """仿真配置管理器"""
    
    def __init__(self, config_dir: str = None):
        self.logger = logging.getLogger(__name__)
        
        # 配置目录
        if config_dir is None:
            config_dir = os.path.join(os.path.expanduser("~"), ".wheel_legged_control", "simulation")
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置文件路径
        self.default_config_file = self.config_dir / "default_config.yaml"
        self.user_config_file = self.config_dir / "user_config.yaml"
        self.profiles_dir = self.config_dir / "profiles"
        self.profiles_dir.mkdir(exist_ok=True)
        
        # 默认配置
        self._default_configs = self._create_default_configs()
        
        self.logger.info(f"配置管理器初始化完成，配置目录: {self.config_dir}")
    
    def _create_default_configs(self) -> Dict[str, SimulationConfig]:
        """创建默认配置"""
        configs = {}
        
        # MuJoCo高性能配置
        configs['mujoco_high_performance'] = SimulationConfig(
            backend=SimulationBackend.MUJOCO,
            dt=0.001,
            max_steps=100000,
            gravity=[0, 0, -9.81],
            enable_rendering=False,
            mujoco_solver="Newton",
            mujoco_iterations=50
        )
        
        # MuJoCo可视化配置
        configs['mujoco_visualization'] = SimulationConfig(
            backend=SimulationBackend.MUJOCO,
            dt=0.002,
            max_steps=10000,
            gravity=[0, 0, -9.81],
            enable_rendering=True,
            render_width=1280,
            render_height=720,
            camera_distance=3.0,
            camera_elevation=-30.0,
            camera_azimuth=45.0,
            mujoco_solver="Newton",
            mujoco_iterations=100
        )
        
        # Gazebo标准配置
        configs['gazebo_standard'] = SimulationConfig(
            backend=SimulationBackend.GAZEBO,
            dt=0.01,
            max_steps=10000,
            gravity=[0, 0, -9.81],
            enable_rendering=True,
            friction=0.8,
            restitution=0.1
        )
        
        # 强化学习训练配置
        configs['rl_training'] = SimulationConfig(
            backend=SimulationBackend.MUJOCO,
            dt=0.001,
            max_steps=1000000,
            gravity=[0, 0, -9.81],
            enable_rendering=False,
            mujoco_solver="Newton",
            mujoco_iterations=50,
            friction=1.0,
            restitution=0.0
        )
        
        # 调试配置
        configs['debug'] = SimulationConfig(
            backend=SimulationBackend.MUJOCO,
            dt=0.01,
            max_steps=1000,
            gravity=[0, 0, -9.81],
            enable_rendering=True,
            render_width=800,
            render_height=600,
            mujoco_solver="Newton",
            mujoco_iterations=10
        )
        
        return configs
    
    def get_default_config(self, profile_name: str = 'mujoco_high_performance') -> SimulationConfig:
        """获取默认配置"""
        if profile_name in self._default_configs:
            return self._default_configs[profile_name]
        else:
            self.logger.warning(f"未知的配置档案: {profile_name}，使用默认配置")
            return self._default_configs['mujoco_high_performance']
    
    def list_default_profiles(self) -> List[str]:
        """列出所有默认配置档案"""
        return list(self._default_configs.keys())
    
    def save_config(self, config: SimulationConfig, filename: str, format: str = 'yaml') -> bool:
        """保存配置到文件"""
        try:
            file_path = self.config_dir / f"{filename}.{format}"
            
            # 转换为字典
            config_dict = asdict(config)
            
            # 处理枚举类型
            if 'backend' in config_dict:
                config_dict['backend'] = config_dict['backend'].value
            
            # 保存文件
            if format.lower() == 'yaml':
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
            elif format.lower() == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config_dict, f, indent=2, ensure_ascii=False)
            else:
                raise ValueError(f"不支持的格式: {format}")
            
            self.logger.info(f"✅ 配置已保存: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 配置保存失败: {e}")
            return False
    
    def load_config(self, filename: str, format: str = None) -> Optional[SimulationConfig]:
        """从文件加载配置"""
        try:
            # 自动检测格式
            if format is None:
                if filename.endswith('.yaml') or filename.endswith('.yml'):
                    format = 'yaml'
                elif filename.endswith('.json'):
                    format = 'json'
                else:
                    # 尝试两种格式
                    yaml_path = self.config_dir / f"{filename}.yaml"
                    json_path = self.config_dir / f"{filename}.json"
                    
                    if yaml_path.exists():
                        filename = f"{filename}.yaml"
                        format = 'yaml'
                    elif json_path.exists():
                        filename = f"{filename}.json"
                        format = 'json'
                    else:
                        raise FileNotFoundError(f"配置文件不存在: {filename}")
            
            file_path = self.config_dir / filename
            
            if not file_path.exists():
                raise FileNotFoundError(f"配置文件不存在: {file_path}")
            
            # 加载文件
            if format.lower() == 'yaml':
                with open(file_path, 'r', encoding='utf-8') as f:
                    config_dict = yaml.safe_load(f)
            elif format.lower() == 'json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    config_dict = json.load(f)
            else:
                raise ValueError(f"不支持的格式: {format}")
            
            # 处理枚举类型
            if 'backend' in config_dict:
                if isinstance(config_dict['backend'], str):
                    config_dict['backend'] = SimulationBackend(config_dict['backend'])
            
            # 创建配置对象
            config = SimulationConfig(**config_dict)
            
            self.logger.info(f"✅ 配置已加载: {file_path}")
            return config
            
        except Exception as e:
            self.logger.error(f"❌ 配置加载失败: {e}")
            return None
    
    def save_profile(self, config: SimulationConfig, profile_name: str) -> bool:
        """保存配置档案"""
        profile_path = self.profiles_dir / f"{profile_name}.yaml"
        
        try:
            config_dict = asdict(config)
            
            # 处理枚举类型
            if 'backend' in config_dict:
                config_dict['backend'] = config_dict['backend'].value
            
            # 添加元数据
            profile_data = {
                'metadata': {
                    'name': profile_name,
                    'description': f"用户配置档案: {profile_name}",
                    'created_at': str(profile_path.stat().st_ctime if profile_path.exists() else time.time()),
                    'version': '1.0'
                },
                'config': config_dict
            }
            
            with open(profile_path, 'w', encoding='utf-8') as f:
                yaml.dump(profile_data, f, default_flow_style=False, allow_unicode=True)
            
            self.logger.info(f"✅ 配置档案已保存: {profile_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 配置档案保存失败: {e}")
            return False
    
    def load_profile(self, profile_name: str) -> Optional[SimulationConfig]:
        """加载配置档案"""
        # 首先检查用户档案
        profile_path = self.profiles_dir / f"{profile_name}.yaml"
        
        if profile_path.exists():
            try:
                with open(profile_path, 'r', encoding='utf-8') as f:
                    profile_data = yaml.safe_load(f)
                
                config_dict = profile_data.get('config', profile_data)
                
                # 处理枚举类型
                if 'backend' in config_dict:
                    if isinstance(config_dict['backend'], str):
                        config_dict['backend'] = SimulationBackend(config_dict['backend'])
                
                config = SimulationConfig(**config_dict)
                self.logger.info(f"✅ 用户配置档案已加载: {profile_name}")
                return config
                
            except Exception as e:
                self.logger.error(f"❌ 用户配置档案加载失败: {e}")
        
        # 检查默认档案
        if profile_name in self._default_configs:
            self.logger.info(f"✅ 默认配置档案已加载: {profile_name}")
            return self._default_configs[profile_name]
        
        self.logger.error(f"❌ 配置档案不存在: {profile_name}")
        return None
    
    def list_profiles(self) -> Dict[str, List[str]]:
        """列出所有配置档案"""
        profiles = {
            'default': list(self._default_configs.keys()),
            'user': []
        }
        
        # 扫描用户档案
        for profile_file in self.profiles_dir.glob("*.yaml"):
            profile_name = profile_file.stem
            profiles['user'].append(profile_name)
        
        return profiles
    
    def delete_profile(self, profile_name: str) -> bool:
        """删除用户配置档案"""
        profile_path = self.profiles_dir / f"{profile_name}.yaml"
        
        if not profile_path.exists():
            self.logger.error(f"❌ 配置档案不存在: {profile_name}")
            return False
        
        try:
            profile_path.unlink()
            self.logger.info(f"✅ 配置档案已删除: {profile_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 配置档案删除失败: {e}")
            return False
    
    def validate_config(self, config: SimulationConfig) -> Tuple[bool, List[str]]:
        """验证配置"""
        errors = []
        
        # 基本验证
        if config.dt <= 0:
            errors.append("时间步长必须大于0")
        
        if config.max_steps <= 0:
            errors.append("最大步数必须大于0")
        
        if len(config.gravity) != 3:
            errors.append("重力向量必须是3维")
        
        if config.friction < 0:
            errors.append("摩擦系数不能为负")
        
        if config.restitution < 0 or config.restitution > 1:
            errors.append("恢复系数必须在0-1之间")
        
        # 渲染配置验证
        if config.enable_rendering:
            if config.render_width <= 0 or config.render_height <= 0:
                errors.append("渲染分辨率必须大于0")
            
            if config.camera_distance <= 0:
                errors.append("相机距离必须大于0")
        
        # 后端特定验证
        if config.backend == SimulationBackend.MUJOCO:
            if config.mujoco_iterations <= 0:
                errors.append("MuJoCo迭代次数必须大于0")
            
            if config.mujoco_solver not in ["Newton", "CG", "PGS"]:
                errors.append(f"不支持的MuJoCo求解器: {config.mujoco_solver}")
        
        return len(errors) == 0, errors
    
    def create_config_template(self, backend: SimulationBackend) -> Dict[str, Any]:
        """创建配置模板"""
        template = {
            'backend': backend.value,
            'dt': 0.001,
            'max_steps': 10000,
            'gravity': [0, 0, -9.81],
            'friction': 0.8,
            'restitution': 0.1,
            'enable_rendering': True,
            'render_width': 640,
            'render_height': 480,
            'camera_distance': 2.0,
            'camera_elevation': -20.0,
            'camera_azimuth': 45.0
        }
        
        if backend == SimulationBackend.MUJOCO:
            template.update({
                'mujoco_model_path': None,
                'mujoco_solver': 'Newton',
                'mujoco_iterations': 100
            })
        elif backend == SimulationBackend.GAZEBO:
            template.update({
                'gazebo_world_path': None,
                'gazebo_model_path': None
            })
        
        return template
    
    def export_all_defaults(self) -> bool:
        """导出所有默认配置到文件"""
        try:
            for profile_name, config in self._default_configs.items():
                self.save_config(config, f"default_{profile_name}")
            
            self.logger.info("✅ 所有默认配置已导出")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 默认配置导出失败: {e}")
            return False


if __name__ == "__main__":
    # 测试配置管理器
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 测试仿真配置管理器")
    print("=" * 50)
    
    # 创建配置管理器
    config_manager = ConfigManager()
    
    # 列出默认档案
    print("📋 默认配置档案:")
    for profile in config_manager.list_default_profiles():
        print(f"   - {profile}")
    
    # 测试配置加载和保存
    print("\n💾 测试配置保存和加载:")
    
    # 获取默认配置
    config = config_manager.get_default_config('mujoco_high_performance')
    print(f"✅ 加载默认配置: {config.backend.value}")
    
    # 保存配置
    success = config_manager.save_config(config, 'test_config')
    print(f"保存配置: {'✅' if success else '❌'}")
    
    # 加载配置
    loaded_config = config_manager.load_config('test_config')
    print(f"加载配置: {'✅' if loaded_config else '❌'}")
    
    # 验证配置
    if loaded_config:
        valid, errors = config_manager.validate_config(loaded_config)
        print(f"配置验证: {'✅' if valid else '❌'}")
        if errors:
            for error in errors:
                print(f"   - {error}")
    
    # 测试配置档案
    print("\n📁 测试配置档案:")
    
    # 保存档案
    success = config_manager.save_profile(config, 'my_test_profile')
    print(f"保存档案: {'✅' if success else '❌'}")
    
    # 列出所有档案
    profiles = config_manager.list_profiles()
    print(f"默认档案: {profiles['default']}")
    print(f"用户档案: {profiles['user']}")
    
    # 创建模板
    print("\n📝 配置模板:")
    template = config_manager.create_config_template(SimulationBackend.MUJOCO)
    print(f"MuJoCo模板字段: {list(template.keys())}")
    
    print("\n🎉 测试完成")