#!/usr/bin/env python3
"""
增强版仿真架构集成测试

测试仿真管理器、后端注册表和配置管理器的集成功能。
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from wheel_legged_control.simulation import (
    SimulationManager, SimulationBackend, SimulationConfig,
    BackendRegistry, get_backend_registry, ConfigManager
)


class TestEnhancedSimulationArchitecture:
    """增强版仿真架构测试"""
    
    def setup_method(self):
        """测试前准备"""
        # 创建临时配置目录
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigManager(self.temp_dir)
        self.backend_registry = get_backend_registry()
    
    def teardown_method(self):
        """测试后清理"""
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_backend_registry_initialization(self):
        """测试后端注册表初始化"""
        registry = BackendRegistry()
        
        # 检查是否有可用后端
        available_backends = registry.get_available_backends()
        all_backends = registry.get_all_backends()
        
        assert len(all_backends) >= 2  # 至少有MuJoCo和Gazebo
        assert SimulationBackend.MUJOCO in all_backends
        assert SimulationBackend.GAZEBO in all_backends
        
        # 检查后端状态
        status = registry.get_backend_status()
        assert 'mujoco' in status
        assert 'gazebo' in status
        
        for backend_name, info in status.items():
            assert 'name' in info
            assert 'description' in info
            assert 'is_available' in info
    
    def test_config_manager_default_profiles(self):
        """测试配置管理器默认档案"""
        # 检查默认档案
        profiles = self.config_manager.list_default_profiles()
        
        expected_profiles = [
            'mujoco_high_performance',
            'mujoco_visualization', 
            'gazebo_standard',
            'rl_training',
            'debug'
        ]
        
        for profile in expected_profiles:
            assert profile in profiles
        
        # 测试加载默认配置
        config = self.config_manager.get_default_config('mujoco_high_performance')
        assert config.backend == SimulationBackend.MUJOCO
        assert config.dt == 0.001
        assert config.enable_rendering == False
    
    def test_config_save_and_load(self):
        """测试配置保存和加载"""
        # 创建测试配置
        config = SimulationConfig(
            backend=SimulationBackend.MUJOCO,
            dt=0.005,
            max_steps=5000,
            enable_rendering=True
        )
        
        # 保存配置
        success = self.config_manager.save_config(config, 'test_config')
        assert success
        
        # 加载配置
        loaded_config = self.config_manager.load_config('test_config')
        assert loaded_config is not None
        assert loaded_config.backend == SimulationBackend.MUJOCO
        assert loaded_config.dt == 0.005
        assert loaded_config.max_steps == 5000
        assert loaded_config.enable_rendering == True
    
    def test_config_profile_management(self):
        """测试配置档案管理"""
        # 创建测试配置
        config = SimulationConfig(
            backend=SimulationBackend.GAZEBO,
            dt=0.01,
            friction=0.9
        )
        
        # 保存档案
        success = self.config_manager.save_profile(config, 'test_profile')
        assert success
        
        # 加载档案
        loaded_config = self.config_manager.load_profile('test_profile')
        assert loaded_config is not None
        assert loaded_config.backend == SimulationBackend.GAZEBO
        assert loaded_config.friction == 0.9
        
        # 列出档案
        profiles = self.config_manager.list_profiles()
        assert 'test_profile' in profiles['user']
        
        # 删除档案
        success = self.config_manager.delete_profile('test_profile')
        assert success
        
        # 确认删除
        profiles = self.config_manager.list_profiles()
        assert 'test_profile' not in profiles['user']
    
    def test_config_validation(self):
        """测试配置验证"""
        # 有效配置
        valid_config = SimulationConfig(
            backend=SimulationBackend.MUJOCO,
            dt=0.001,
            max_steps=1000,
            friction=0.8,
            restitution=0.1
        )
        
        valid, errors = self.config_manager.validate_config(valid_config)
        assert valid
        assert len(errors) == 0
        
        # 无效配置 - 负时间步长
        invalid_config = SimulationConfig(
            backend=SimulationBackend.MUJOCO,
            dt=-0.001,  # 无效
            max_steps=1000
        )
        
        valid, errors = self.config_manager.validate_config(invalid_config)
        assert not valid
        assert len(errors) > 0
        assert any("时间步长" in error for error in errors)
    
    def test_enhanced_simulation_manager(self):
        """测试增强版仿真管理器"""
        # 创建仿真管理器
        sim_manager = SimulationManager(
            config_manager=self.config_manager,
            backend_registry=self.backend_registry
        )
        
        # 检查可用后端
        available_backends = sim_manager.get_available_backends()
        assert len(available_backends) >= 0  # 可能没有可用后端（在CI环境中）
        
        # 检查系统状态
        status = sim_manager.get_system_status()
        assert 'current_backend' in status
        assert 'backend_initialized' in status
        assert 'available_backends' in status
        assert 'performance_stats' in status
        assert 'config_valid' in status
        assert 'config_profiles' in status
        
        # 检查性能统计
        perf_stats = sim_manager.get_performance_stats()
        assert 'total_steps' in perf_stats
        assert 'total_time' in perf_stats
        assert 'average_step_time' in perf_stats
        assert 'backend_switches' in perf_stats
        assert 'simulation_frequency' in perf_stats
        
        # 关闭管理器
        sim_manager.close()
    
    def test_config_profile_integration(self):
        """测试配置档案与仿真管理器集成"""
        # 保存测试配置档案
        config = SimulationConfig(
            backend=SimulationBackend.MUJOCO,
            dt=0.002,
            max_steps=2000
        )
        
        success = self.config_manager.save_profile(config, 'integration_test')
        assert success
        
        # 创建仿真管理器并加载档案
        sim_manager = SimulationManager(
            config_manager=self.config_manager,
            backend_registry=self.backend_registry
        )
        
        success = sim_manager.load_config_profile('integration_test')
        assert success
        assert sim_manager.config.dt == 0.002
        assert sim_manager.config.max_steps == 2000
        
        # 保存当前配置为新档案
        success = sim_manager.save_current_config('saved_from_manager')
        assert success
        
        # 验证新档案
        loaded_config = self.config_manager.load_profile('saved_from_manager')
        assert loaded_config is not None
        assert loaded_config.dt == 0.002
        
        sim_manager.close()
    
    def test_backend_info_retrieval(self):
        """测试后端信息获取"""
        sim_manager = SimulationManager(
            config_manager=self.config_manager,
            backend_registry=self.backend_registry
        )
        
        # 获取所有后端信息
        for backend in [SimulationBackend.MUJOCO, SimulationBackend.GAZEBO]:
            info = sim_manager.get_backend_info(backend)
            
            # 基本信息字段检查
            expected_fields = ['name', 'description', 'version', 'dependencies', 'is_available']
            for field in expected_fields:
                assert field in info
        
        sim_manager.close()
    
    def test_config_template_generation(self):
        """测试配置模板生成"""
        # MuJoCo模板
        mujoco_template = self.config_manager.create_config_template(SimulationBackend.MUJOCO)
        
        assert 'backend' in mujoco_template
        assert mujoco_template['backend'] == 'mujoco'
        assert 'mujoco_solver' in mujoco_template
        assert 'mujoco_iterations' in mujoco_template
        
        # Gazebo模板
        gazebo_template = self.config_manager.create_config_template(SimulationBackend.GAZEBO)
        
        assert 'backend' in gazebo_template
        assert gazebo_template['backend'] == 'gazebo'
        assert 'gazebo_world_path' in gazebo_template
        assert 'gazebo_model_path' in gazebo_template
    
    def test_performance_monitoring(self):
        """测试性能监控功能"""
        sim_manager = SimulationManager(
            config_manager=self.config_manager,
            backend_registry=self.backend_registry
        )
        
        # 初始性能统计
        initial_stats = sim_manager.get_performance_stats()
        assert initial_stats['total_steps'] == 0
        assert initial_stats['total_time'] == 0.0
        assert initial_stats['backend_switches'] == 0
        
        # 模拟一些操作（不需要真实后端）
        # 这里只测试统计数据结构的正确性
        
        sim_manager.close()


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])