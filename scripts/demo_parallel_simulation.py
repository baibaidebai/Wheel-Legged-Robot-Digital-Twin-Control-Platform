#!/usr/bin/env python3
"""
并行仿真演示

展示并行MuJoCo仿真的性能优势，用于强化学习训练加速。
"""

import sys
import os
import numpy as np
import time
import logging

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'wheel_legged_control'))

from wheel_legged_control.simulation.simulation_manager import SimulationManager, SimulationConfig, SimulationBackend
from wheel_legged_control.simulation.parallel_mujoco_backend import ParallelMuJoCoBackend, VectorizedMuJoCoEnvironment
from wheel_legged_control.simulation.benchmark import SimulationBenchmark


def demo_basic_parallel():
    """演示基本并行仿真"""
    print("\n" + "=" * 80)
    print("演示 1: 基本并行仿真")
    print("=" * 80)
    
    # 创建配置
    config = SimulationConfig(
        backend=SimulationBackend.MUJOCO,
        enable_rendering=False,
        dt=0.001
    )
    
    # 创建测试模型
    from wheel_legged_control.simulation.mujoco_backend import URDFToMJCFConverter
    converter = URDFToMJCFConverter()
    model_path = converter._create_simple_mjcf("demo_parallel_model.xml")
    
    # 创建并行后端
    num_envs = 4
    print(f"\n创建 {num_envs} 个并行环境...")
    parallel_backend = ParallelMuJoCoBackend(config, num_envs=num_envs)
    
    if not parallel_backend.initialize(model_path):
        print("❌ 初始化失败")
        return
    
    print("✅ 并行环境初始化成功")
    
    # 重置所有环境
    print("\n重置所有环境...")
    states = parallel_backend.reset()
    print(f"✅ {len(states)} 个环境已重置")
    
    # 执行并行仿真
    print(f"\n执行 100 步并行仿真...")
    start_time = time.time()
    
    for step in range(100):
        # 为每个环境生成随机动作
        actions = []
        for _ in range(num_envs):
            action = {
                'lf0_motor': np.random.uniform(-1, 1),
                'rf0_motor': np.random.uniform(-1, 1),
                'l_wheel_motor': np.random.uniform(-1, 1),
                'r_wheel_motor': np.random.uniform(-1, 1)
            }
            actions.append(action)
        
        # 并行执行
        states, dones = parallel_backend.step(actions)
        
        if (step + 1) % 25 == 0:
            print(f"  步骤 {step + 1}/100 完成")
    
    elapsed = time.time() - start_time
    
    # 显示性能统计
    print(f"\n⏱️  总时间: {elapsed:.3f}秒")
    print(f"📊 总步数: {num_envs * 100} ({num_envs} 环境 × 100 步)")
    print(f"⚡ 吞吐量: {num_envs * 100 / elapsed:.2f} 步/秒")
    
    stats = parallel_backend.get_performance_stats()
    print(f"\n性能统计:")
    for key, value in stats.items():
        print(f"  {key}: {value:.4f}")
    
    parallel_backend.close()
    
    # 清理
    if os.path.exists(model_path):
        os.remove(model_path)
    
    print("\n✅ 演示 1 完成")


def demo_vectorized_environment():
    """演示向量化环境接口"""
    print("\n" + "=" * 80)
    print("演示 2: 向量化环境接口（用于强化学习）")
    print("=" * 80)
    
    # 创建配置
    config = SimulationConfig(
        backend=SimulationBackend.MUJOCO,
        enable_rendering=False,
        dt=0.001
    )
    
    # 创建测试模型
    from wheel_legged_control.simulation.mujoco_backend import URDFToMJCFConverter
    converter = URDFToMJCFConverter()
    model_path = converter._create_simple_mjcf("demo_vec_model.xml")
    
    # 创建向量化环境
    num_envs = 8
    print(f"\n创建向量化环境: {num_envs} 个并行实例...")
    vec_env = VectorizedMuJoCoEnvironment(config, num_envs=num_envs, model_path=model_path)
    
    print("✅ 向量化环境创建成功")
    
    # 重置环境
    print("\n重置环境...")
    observations = vec_env.reset()
    print(f"✅ 观测形状: {observations.shape}")
    
    # 模拟强化学习训练循环
    print(f"\n模拟强化学习训练循环 (50 步)...")
    total_rewards = np.zeros(num_envs)
    
    start_time = time.time()
    
    for step in range(50):
        # 生成随机动作（实际训练中会使用策略网络）
        actions = np.random.uniform(-1, 1, size=(num_envs, 6))
        
        # 执行步进
        observations, rewards, dones, infos = vec_env.step(actions)
        
        # 累积奖励
        total_rewards += rewards
        
        # 重置完成的环境
        if np.any(dones):
            done_envs = np.where(dones)[0]
            print(f"  步骤 {step + 1}: {len(done_envs)} 个环境完成")
            vec_env.reset(done_envs)
        
        if (step + 1) % 10 == 0:
            print(f"  步骤 {step + 1}/50: 平均奖励 = {rewards.mean():.3f}")
    
    elapsed = time.time() - start_time
    
    # 显示结果
    print(f"\n⏱️  总时间: {elapsed:.3f}秒")
    print(f"📊 总步数: {num_envs * 50} ({num_envs} 环境 × 50 步)")
    print(f"⚡ 吞吐量: {num_envs * 50 / elapsed:.2f} 步/秒")
    print(f"🎯 平均累积奖励: {total_rewards.mean():.3f}")
    
    stats = vec_env.get_performance_stats()
    print(f"\n性能统计:")
    for key, value in stats.items():
        print(f"  {key}: {value:.4f}")
    
    vec_env.close()
    
    # 清理
    if os.path.exists(model_path):
        os.remove(model_path)
    
    print("\n✅ 演示 2 完成")


def demo_performance_comparison():
    """演示性能对比"""
    print("\n" + "=" * 80)
    print("演示 3: 单环境 vs 并行环境性能对比")
    print("=" * 80)
    
    # 创建测试模型
    from wheel_legged_control.simulation.mujoco_backend import URDFToMJCFConverter
    converter = URDFToMJCFConverter()
    model_path = converter._create_simple_mjcf("demo_compare_model.xml")
    
    # 测试配置
    num_steps = 500
    env_counts = [1, 2, 4, 8]
    
    print(f"\n测试配置: 每个环境 {num_steps} 步")
    print(f"环境数量: {env_counts}")
    
    # 运行基准测试
    benchmark = SimulationBenchmark()
    results = benchmark.benchmark_parallel_performance(
        SimulationBackend.MUJOCO,
        model_path,
        env_counts=env_counts,
        steps_per_env=num_steps
    )
    
    # 清理
    if os.path.exists(model_path):
        os.remove(model_path)
    
    print("\n✅ 演示 3 完成")


def demo_rl_training_speedup():
    """演示强化学习训练加速"""
    print("\n" + "=" * 80)
    print("演示 4: 强化学习训练加速效果")
    print("=" * 80)
    
    # 创建测试模型
    from wheel_legged_control.simulation.mujoco_backend import URDFToMJCFConverter
    converter = URDFToMJCFConverter()
    model_path = converter._create_simple_mjcf("demo_rl_model.xml")
    
    config = SimulationConfig(
        backend=SimulationBackend.MUJOCO,
        enable_rendering=False,
        dt=0.001
    )
    
    # 模拟训练参数
    total_timesteps = 10000  # 总训练步数
    
    print(f"\n模拟训练参数:")
    print(f"  总训练步数: {total_timesteps}")
    
    # 测试不同并行度
    for num_envs in [1, 4, 8]:
        print(f"\n{'=' * 60}")
        print(f"测试 {num_envs} 个并行环境")
        print(f"{'=' * 60}")
        
        vec_env = VectorizedMuJoCoEnvironment(config, num_envs=num_envs, model_path=model_path)
        
        # 计算需要的步数
        steps_needed = total_timesteps // num_envs
        
        print(f"  每个环境需要: {steps_needed} 步")
        
        # 执行训练
        start_time = time.time()
        
        observations = vec_env.reset()
        
        for step in range(steps_needed):
            actions = np.random.uniform(-1, 1, size=(num_envs, 6))
            observations, rewards, dones, infos = vec_env.step(actions)
            
            # 重置完成的环境
            if np.any(dones):
                done_envs = np.where(dones)[0]
                vec_env.reset(done_envs)
        
        elapsed = time.time() - start_time
        
        # 显示结果
        print(f"\n  ⏱️  训练时间: {elapsed:.2f}秒")
        print(f"  ⚡ 吞吐量: {total_timesteps / elapsed:.2f} 步/秒")
        
        if num_envs == 1:
            baseline_time = elapsed
            print(f"  📊 基准时间")
        else:
            speedup = baseline_time / elapsed
            print(f"  🚀 加速比: {speedup:.2f}x")
        
        vec_env.close()
    
    # 清理
    if os.path.exists(model_path):
        os.remove(model_path)
    
    print("\n✅ 演示 4 完成")


def main():
    """主函数"""
    print("🚀 并行仿真演示程序")
    print("=" * 80)
    print("展示MuJoCo并行仿真的性能优势")
    print("=" * 80)
    
    # 检查MuJoCo可用性
    try:
        import mujoco
        print(f"✅ MuJoCo 版本: {mujoco.__version__}")
    except ImportError:
        print("❌ MuJoCo不可用，请安装: pip install mujoco")
        return
    
    try:
        # 运行演示
        demo_basic_parallel()
        demo_vectorized_environment()
        demo_performance_comparison()
        demo_rl_training_speedup()
        
        print("\n" + "=" * 80)
        print("🎉 所有演示完成！")
        print("=" * 80)
        print("\n总结:")
        print("  ✅ 并行仿真可以显著提高强化学习训练速度")
        print("  ✅ 向量化环境接口简化了批量操作")
        print("  ✅ MuJoCo后端提供了高性能物理仿真")
        print("  ✅ 多环境并行可以实现近线性加速")
        
    except Exception as e:
        print(f"\n❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()
