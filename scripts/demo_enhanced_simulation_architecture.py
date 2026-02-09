#!/usr/bin/env python3
"""
增强版仿真架构演示

展示仿真管理器、后端注册表和配置管理器的集成功能。
"""

import sys
import os
import logging
import time

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from wheel_legged_control.simulation import (
    SimulationManager, SimulationBackend, SimulationConfig,
    BackendRegistry, get_backend_registry, ConfigManager,
    create_simulation_manager
)


def demo_backend_registry():
    """演示后端注册表功能"""
    print("🔧 后端注册表演示")
    print("=" * 50)
    
    registry = get_backend_registry()
    
    # 显示所有后端状态
    print("📊 后端状态:")
    status = registry.get_backend_status()
    for backend_name, info in status.items():
        availability = "✅ 可用" if info['is_available'] else "❌ 不可用"
        print(f"\n🎯 {info['name']} ({backend_name}):")
        print(f"   状态: {availability}")
        print(f"   描述: {info['description']}")
        print(f"   版本: {info['version']}")
        print(f"   依赖: {', '.join(info['dependencies'])}")
        if info['error_message']:
            print(f"   错误: {info['error_message']}")
    
    # 显示可用后端
    available = registry.get_available_backends()
    print(f"\n✅ 可用后端: {[b.value for b in available]}")
    
    return registry


def demo_config_manager():
    """演示配置管理器功能"""
    print("\n📁 配置管理器演示")
    print("=" * 50)
    
    config_manager = ConfigManager()
    
    # 显示默认配置档案
    print("📋 默认配置档案:")
    default_profiles = config_manager.list_default_profiles()
    for profile in default_profiles:
        print(f"   - {profile}")
    
    # 演示配置加载
    print("\n💾 配置加载演示:")
    config = config_manager.get_default_config('mujoco_high_performance')
    print(f"✅ 加载配置: {config.backend.value}")
    print(f"   时间步长: {config.dt}")
    print(f"   最大步数: {config.max_steps}")
    print(f"   渲染: {'开启' if config.enable_rendering else '关闭'}")
    
    # 演示配置验证
    print("\n🔍 配置验证演示:")
    valid, errors = config_manager.validate_config(config)
    print(f"配置验证: {'✅ 通过' if valid else '❌ 失败'}")
    if errors:
        for error in errors:
            print(f"   - {error}")
    
    # 演示配置模板
    print("\n📝 配置模板演示:")
    mujoco_template = config_manager.create_config_template(SimulationBackend.MUJOCO)
    print(f"MuJoCo模板字段: {list(mujoco_template.keys())}")
    
    # 演示配置档案保存和加载
    print("\n💿 配置档案演示:")
    
    # 创建自定义配置
    custom_config = SimulationConfig(
        backend=SimulationBackend.MUJOCO,
        dt=0.005,
        max_steps=5000,
        enable_rendering=True,
        render_width=1280,
        render_height=720
    )
    
    # 保存档案
    success = config_manager.save_profile(custom_config, 'demo_profile')
    print(f"保存档案: {'✅' if success else '❌'}")
    
    # 加载档案
    loaded_config = config_manager.load_profile('demo_profile')
    if loaded_config:
        print(f"✅ 加载档案成功")
        print(f"   后端: {loaded_config.backend.value}")
        print(f"   分辨率: {loaded_config.render_width}x{loaded_config.render_height}")
    
    # 列出所有档案
    profiles = config_manager.list_profiles()
    print(f"\n📂 所有配置档案:")
    print(f"   默认档案: {profiles['default']}")
    print(f"   用户档案: {profiles['user']}")
    
    return config_manager


def demo_enhanced_simulation_manager(config_manager, registry):
    """演示增强版仿真管理器功能"""
    print("\n🚀 增强版仿真管理器演示")
    print("=" * 50)
    
    # 创建仿真管理器
    sim_manager = SimulationManager(
        config_manager=config_manager,
        backend_registry=registry
    )
    
    # 显示系统状态
    print("📈 系统状态:")
    status = sim_manager.get_system_status()
    print(f"   当前后端: {status['current_backend']}")
    print(f"   后端已初始化: {status['backend_initialized']}")
    print(f"   可用后端: {status['available_backends']}")
    print(f"   配置有效: {status['config_valid']}")
    
    # 显示性能统计
    print("\n⚡ 性能统计:")
    perf_stats = sim_manager.get_performance_stats()
    for key, value in perf_stats.items():
        print(f"   {key}: {value}")
    
    # 演示配置档案集成
    print("\n🔗 配置档案集成演示:")
    
    # 加载不同的配置档案
    profiles_to_test = ['mujoco_high_performance', 'mujoco_visualization', 'debug']
    
    for profile in profiles_to_test:
        success = sim_manager.load_config_profile(profile)
        if success:
            print(f"✅ 加载配置档案: {profile}")
            print(f"   后端: {sim_manager.config.backend.value}")
            print(f"   时间步长: {sim_manager.config.dt}")
            print(f"   渲染: {'开启' if sim_manager.config.enable_rendering else '关闭'}")
        else:
            print(f"❌ 配置档案加载失败: {profile}")
    
    # 演示后端信息获取
    print("\n🔍 后端信息演示:")
    for backend in [SimulationBackend.MUJOCO, SimulationBackend.GAZEBO]:
        info = sim_manager.get_backend_info(backend)
        if info:
            print(f"\n{backend.value.upper()}:")
            print(f"   名称: {info['name']}")
            print(f"   版本: {info['version']}")
            print(f"   可用: {'✅' if info['is_available'] else '❌'}")
    
    # 演示配置保存
    print("\n💾 配置保存演示:")
    success = sim_manager.save_current_config('demo_saved_config')
    print(f"保存当前配置: {'✅' if success else '❌'}")
    
    # 模拟一些仿真步骤（不需要真实后端）
    print("\n🎮 模拟仿真步骤:")
    print("模拟执行仿真步骤...")
    
    # 更新性能统计（模拟）
    sim_manager.performance_stats['total_steps'] = 100
    sim_manager.performance_stats['total_time'] = 0.1
    sim_manager.performance_stats['average_step_time'] = 0.001
    
    updated_stats = sim_manager.get_performance_stats()
    print(f"✅ 模拟完成")
    print(f"   总步数: {updated_stats['total_steps']}")
    print(f"   总时间: {updated_stats['total_time']:.3f}s")
    print(f"   平均步时: {updated_stats['average_step_time']:.6f}s")
    print(f"   仿真频率: {updated_stats['simulation_frequency']:.1f} Hz")
    
    # 关闭管理器
    sim_manager.close()
    print("✅ 仿真管理器已关闭")


def demo_factory_function():
    """演示工厂函数功能"""
    print("\n🏭 工厂函数演示")
    print("=" * 50)
    
    # 使用默认配置创建
    print("📦 使用默认配置创建:")
    sim_manager1 = create_simulation_manager(SimulationBackend.MUJOCO)
    print(f"✅ 创建成功，后端: {sim_manager1.config.backend.value}")
    sim_manager1.close()
    
    # 使用配置档案创建
    print("\n📦 使用配置档案创建:")
    sim_manager2 = create_simulation_manager(
        backend=SimulationBackend.MUJOCO,
        config_profile='mujoco_visualization'
    )
    print(f"✅ 创建成功，配置档案: mujoco_visualization")
    print(f"   渲染: {'开启' if sim_manager2.config.enable_rendering else '关闭'}")
    print(f"   分辨率: {sim_manager2.config.render_width}x{sim_manager2.config.render_height}")
    sim_manager2.close()
    
    # 使用自定义参数创建
    print("\n📦 使用自定义参数创建:")
    sim_manager3 = create_simulation_manager(
        backend=SimulationBackend.MUJOCO,
        dt=0.002,
        max_steps=50000,
        enable_rendering=False
    )
    print(f"✅ 创建成功，自定义参数")
    print(f"   时间步长: {sim_manager3.config.dt}")
    print(f"   最大步数: {sim_manager3.config.max_steps}")
    sim_manager3.close()


def main():
    """主演示函数"""
    print("🎯 增强版仿真架构完整演示")
    print("=" * 60)
    print("展示仿真管理器、后端注册表和配置管理器的集成功能")
    print("=" * 60)
    
    # 设置日志
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    try:
        # 演示各个组件
        registry = demo_backend_registry()
        config_manager = demo_config_manager()
        demo_enhanced_simulation_manager(config_manager, registry)
        demo_factory_function()
        
        print("\n🎉 演示完成！")
        print("\n📋 功能总结:")
        print("✅ 后端注册表 - 动态后端管理和状态监控")
        print("✅ 配置管理器 - 配置档案管理和验证")
        print("✅ 增强仿真管理器 - 集成架构和性能监控")
        print("✅ 工厂函数 - 便捷的实例创建")
        print("✅ 完整集成 - 所有组件协同工作")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)