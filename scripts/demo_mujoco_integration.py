#!/usr/bin/env python3
"""
MuJoCo集成演示脚本

展示如何使用MuJoCo物理引擎进行轮腿机器人仿真，包括：
1. 仿真管理器的使用
2. MuJoCo后端的初始化和控制
3. 与强化学习环境的集成
4. 性能对比测试
"""

import numpy as np
import time
import logging
import os
import sys
import matplotlib.pyplot as plt

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from wheel_legged_control.simulation import (
    SimulationManager, SimulationBackend, SimulationConfig
)


def demo_basic_mujoco_usage():
    """演示基本的MuJoCo使用"""
    print("🚀 演示1: 基本MuJoCo使用")
    print("=" * 50)
    
    # 创建仿真配置
    config = SimulationConfig(
        backend=SimulationBackend.MUJOCO,
        dt=0.001,
        enable_rendering=False,  # 先关闭渲染进行测试
        gravity=[0, 0, -9.81]
    )
    
    # 创建仿真管理器
    sim_manager = SimulationManager(config)
    
    print(f"📊 可用后端: {[b.value for b in sim_manager.get_available_backends()]}")
    
    # 检查MuJoCo是否可用
    if SimulationBackend.MUJOCO not in sim_manager.get_available_backends():
        print("⚠️  MuJoCo后端不可用，请安装: pip install mujoco")
        return False
    
    # 使用简化模型进行测试
    model_path = "test_wheel_legged_robot.xml"
    
    # 初始化仿真
    success = sim_manager.initialize(model_path)
    if not success:
        print("❌ 仿真初始化失败")
        return False
    
    print(f"✅ 仿真初始化成功，当前后端: {sim_manager.get_current_backend().value}")
    
    # 重置仿真
    sim_manager.reset()
    print("✅ 仿真重置完成")
    
    # 获取初始状态
    initial_state = sim_manager.get_state()
    print(f"📊 初始状态:")
    print(f"   关节数量: {len(initial_state['joint_positions'])}")
    print(f"   基座位置: {initial_state['base_position']}")
    
    # 执行仿真步骤
    print("\n🔄 执行仿真步骤...")
    
    states_history = []
    control_history = []
    
    for step in range(100):
        # 生成控制指令
        action = {}
        joint_states = sim_manager.get_joint_states()
        
        for joint_name in joint_states.keys():
            if 'wheel' in joint_name:
                # 轮子：正弦波速度
                action[joint_name + '_motor'] = 2.0 * np.sin(step * 0.1)
            else:
                # 腿部关节：小幅摆动
                action[joint_name + '_motor'] = 0.5 * np.sin(step * 0.05 + np.random.random())
        
        # 执行仿真步
        sim_manager.step(action)
        
        # 记录状态
        current_state = sim_manager.get_state()
        states_history.append(current_state)
        control_history.append(action.copy())
        
        # 定期输出状态
        if step % 20 == 0:
            print(f"   步骤 {step:3d}: 时间={current_state['time']:.3f}s, "
                  f"基座位置={current_state['base_position']}")
    
    print("✅ 仿真执行完成")
    
    # 分析结果
    print("\n📈 仿真结果分析:")
    final_state = states_history[-1]
    print(f"   最终时间: {final_state['time']:.3f}s")
    print(f"   最终基座位置: {final_state['base_position']}")
    print(f"   基座移动距离: {np.linalg.norm(final_state['base_position'] - initial_state['base_position']):.3f}m")
    
    # 清理
    sim_manager.close()
    
    # 清理测试文件
    if os.path.exists(model_path):
        os.remove(model_path)
    
    return True, states_history, control_history


def demo_backend_switching():
    """演示后端切换功能"""
    print("\n🔄 演示2: 仿真后端切换")
    print("=" * 50)
    
    # 创建仿真管理器
    sim_manager = SimulationManager()
    
    available_backends = sim_manager.get_available_backends()
    print(f"📊 可用后端: {[b.value for b in available_backends]}")
    
    if len(available_backends) < 2:
        print("⚠️  需要至少2个后端才能演示切换功能")
        return False
    
    model_path = "test_wheel_legged_robot.xml"
    
    # 测试每个后端
    for backend in available_backends:
        print(f"\n🎯 测试后端: {backend.value}")
        
        # 切换后端
        success = sim_manager.switch_backend(backend, model_path)
        if success:
            print(f"✅ 切换到 {backend.value} 成功")
            
            # 执行简单测试
            sim_manager.reset()
            
            for i in range(5):
                action = {'l_wheel_motor': 1.0, 'r_wheel_motor': 1.0}
                sim_manager.step(action)
            
            state = sim_manager.get_state()
            print(f"   测试结果: 基座位置={state['base_position']}")
        else:
            print(f"❌ 切换到 {backend.value} 失败")
    
    sim_manager.close()
    
    # 清理测试文件
    if os.path.exists(model_path):
        os.remove(model_path)
    
    return True


def demo_performance_comparison():
    """演示性能对比"""
    print("\n⚡ 演示3: 性能对比测试")
    print("=" * 50)
    
    results = {}
    
    # 测试配置
    test_steps = 1000
    
    for backend_type in [SimulationBackend.MUJOCO, SimulationBackend.GAZEBO]:
        print(f"\n🧪 测试 {backend_type.value} 性能...")
        
        try:
            config = SimulationConfig(
                backend=backend_type,
                dt=0.001,
                enable_rendering=False
            )
            
            sim_manager = SimulationManager(config)
            
            if backend_type not in sim_manager.get_available_backends():
                print(f"⚠️  {backend_type.value} 不可用，跳过测试")
                continue
            
            model_path = "test_wheel_legged_robot.xml"
            
            # 初始化
            init_start = time.time()
            success = sim_manager.initialize(model_path)
            init_time = time.time() - init_start
            
            if not success:
                print(f"❌ {backend_type.value} 初始化失败")
                continue
            
            # 性能测试
            sim_manager.reset()
            
            step_times = []
            start_time = time.time()
            
            for step in range(test_steps):
                step_start = time.time()
                
                # 随机控制输入
                action = {
                    'lf0_motor': np.random.uniform(-1, 1),
                    'rf0_motor': np.random.uniform(-1, 1),
                    'l_wheel_motor': np.random.uniform(-2, 2),
                    'r_wheel_motor': np.random.uniform(-2, 2)
                }
                
                sim_manager.step(action)
                
                step_time = time.time() - step_start
                step_times.append(step_time)
            
            total_time = time.time() - start_time
            
            # 统计结果
            results[backend_type.value] = {
                'init_time': init_time,
                'total_time': total_time,
                'avg_step_time': np.mean(step_times),
                'std_step_time': np.std(step_times),
                'steps_per_second': test_steps / total_time
            }
            
            print(f"✅ {backend_type.value} 测试完成:")
            print(f"   初始化时间: {init_time:.3f}s")
            print(f"   总仿真时间: {total_time:.3f}s")
            print(f"   平均步时间: {np.mean(step_times)*1000:.2f}ms")
            print(f"   仿真频率: {test_steps/total_time:.1f} steps/s")
            
            sim_manager.close()
            
            # 清理测试文件
            if os.path.exists(model_path):
                os.remove(model_path)
                
        except Exception as e:
            print(f"❌ {backend_type.value} 测试失败: {e}")
    
    # 性能对比
    if len(results) > 1:
        print("\n📊 性能对比结果:")
        print("-" * 60)
        print(f"{'后端':<10} {'初始化(s)':<10} {'步时间(ms)':<12} {'频率(Hz)':<10}")
        print("-" * 60)
        
        for backend_name, result in results.items():
            print(f"{backend_name:<10} {result['init_time']:<10.3f} "
                  f"{result['avg_step_time']*1000:<12.2f} {result['steps_per_second']:<10.1f}")
    
    return results


def demo_rl_integration():
    """演示与强化学习的集成"""
    print("\n🤖 演示4: 强化学习集成")
    print("=" * 50)
    
    try:
        # 导入强化学习环境
        from wheel_legged_control.algorithms.rl_environment import (
            create_wheel_legged_environment, EnvironmentConfig, RewardType
        )
        
        print("✅ 强化学习模块导入成功")
        
        # 创建环境配置
        env_config = EnvironmentConfig(
            max_episode_steps=200,
            dt=0.01,
            reward_type=RewardType.SHAPED,
            action_type="continuous",
            randomize_initial_state=True,
            target_position=[1.0, 0.0, 0.1]
        )
        
        # 创建环境
        env = create_wheel_legged_environment(env_config)
        print(f"✅ 强化学习环境创建成功")
        print(f"📊 观测空间: {env.observation_space.shape}")
        print(f"🎮 动作空间: {env.action_space.shape}")
        
        # 运行一个回合
        obs = env.reset()
        total_reward = 0
        
        print("\n🎮 运行强化学习回合...")
        
        for step in range(50):
            # 随机策略
            action = env.action_space.sample()
            
            obs, reward, done, info = env.step(action)
            total_reward += reward
            
            if step % 10 == 0:
                print(f"   步骤 {step:2d}: 奖励={reward:6.3f}, 累计={total_reward:6.3f}, "
                      f"距离={info.get('distance_to_target', 0):.3f}")
            
            if done:
                print(f"🏁 回合结束于步骤 {step}")
                break
        
        print(f"✅ 回合完成，总奖励: {total_reward:.3f}")
        
        env.close()
        
        return True
        
    except ImportError as e:
        print(f"⚠️  强化学习模块不可用: {e}")
        return False
    except Exception as e:
        print(f"❌ 强化学习集成测试失败: {e}")
        return False


def plot_simulation_results(states_history, control_history):
    """绘制仿真结果"""
    if not states_history:
        return
    
    print("\n📈 绘制仿真结果...")
    
    try:
        # 提取数据
        times = [state['time'] for state in states_history]
        base_positions = np.array([state['base_position'] for state in states_history])
        
        # 创建图表
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        
        # 基座位置
        axes[0, 0].plot(times, base_positions[:, 0], label='X')
        axes[0, 0].plot(times, base_positions[:, 1], label='Y')
        axes[0, 0].plot(times, base_positions[:, 2], label='Z')
        axes[0, 0].set_title('基座位置')
        axes[0, 0].set_xlabel('时间 (s)')
        axes[0, 0].set_ylabel('位置 (m)')
        axes[0, 0].legend()
        axes[0, 0].grid(True)
        
        # 基座轨迹
        axes[0, 1].plot(base_positions[:, 0], base_positions[:, 1])
        axes[0, 1].set_title('基座轨迹 (俯视图)')
        axes[0, 1].set_xlabel('X (m)')
        axes[0, 1].set_ylabel('Y (m)')
        axes[0, 1].grid(True)
        axes[0, 1].axis('equal')
        
        # 关节位置（选择几个关节）
        joint_names = list(states_history[0]['joint_positions'].keys())[:4]
        for i, joint_name in enumerate(joint_names):
            joint_positions = [state['joint_positions'][joint_name] for state in states_history]
            axes[1, 0].plot(times, joint_positions, label=joint_name)
        
        axes[1, 0].set_title('关节位置')
        axes[1, 0].set_xlabel('时间 (s)')
        axes[1, 0].set_ylabel('角度 (rad)')
        axes[1, 0].legend()
        axes[1, 0].grid(True)
        
        # 控制输入
        if control_history:
            control_names = list(control_history[0].keys())[:4]
            for control_name in control_names:
                control_values = [ctrl.get(control_name, 0) for ctrl in control_history]
                axes[1, 1].plot(times, control_values, label=control_name)
            
            axes[1, 1].set_title('控制输入')
            axes[1, 1].set_xlabel('时间 (s)')
            axes[1, 1].set_ylabel('控制值')
            axes[1, 1].legend()
            axes[1, 1].grid(True)
        
        plt.tight_layout()
        plt.savefig('mujoco_simulation_results.png', dpi=300, bbox_inches='tight')
        print("✅ 仿真结果图表已保存: mujoco_simulation_results.png")
        
        try:
            plt.show()
        except:
            print("💡 无法显示图表，但已保存到文件")
        
    except Exception as e:
        print(f"⚠️  绘图失败: {e}")


def main():
    """主函数"""
    print("🚀 MuJoCo集成演示")
    print("=" * 60)
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 检查依赖
    try:
        import mujoco
        print(f"✅ MuJoCo版本: {mujoco.__version__}")
    except ImportError:
        print("❌ MuJoCo未安装，请运行: pip install mujoco")
        return
    
    success_count = 0
    total_demos = 4
    
    # 演示1: 基本使用
    try:
        result = demo_basic_mujoco_usage()
        if isinstance(result, tuple) and result[0]:
            success_count += 1
            # 绘制结果
            plot_simulation_results(result[1], result[2])
        elif result:
            success_count += 1
    except Exception as e:
        print(f"❌ 演示1失败: {e}")
    
    # 演示2: 后端切换
    try:
        if demo_backend_switching():
            success_count += 1
    except Exception as e:
        print(f"❌ 演示2失败: {e}")
    
    # 演示3: 性能对比
    try:
        demo_performance_comparison()
        success_count += 1
    except Exception as e:
        print(f"❌ 演示3失败: {e}")
    
    # 演示4: 强化学习集成
    try:
        if demo_rl_integration():
            success_count += 1
    except Exception as e:
        print(f"❌ 演示4失败: {e}")
    
    # 总结
    print("\n" + "=" * 60)
    print("🎉 MuJoCo集成演示完成")
    print(f"📊 成功演示: {success_count}/{total_demos}")
    
    if success_count == total_demos:
        print("✅ 所有演示都成功完成！")
        print("💡 MuJoCo物理引擎已成功集成到轮腿机器人系统中")
    else:
        print("⚠️  部分演示失败，请检查依赖和配置")
    
    print("\n📚 使用说明:")
    print("1. 安装MuJoCo: pip install mujoco")
    print("2. 使用SimulationManager创建仿真环境")
    print("3. 支持URDF自动转换为MJCF格式")
    print("4. 可与现有PPO训练器无缝集成")
    print("5. 支持Gazebo和MuJoCo后端动态切换")


if __name__ == "__main__":
    main()