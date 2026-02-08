#!/usr/bin/env python3
"""
简单的MuJoCo集成测试

验证MuJoCo安装和基本功能。
"""

import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_mujoco_installation():
    """测试MuJoCo安装"""
    print("🧪 测试MuJoCo安装...")
    
    try:
        import mujoco
        print(f"✅ MuJoCo版本: {mujoco.__version__}")
        return True
    except ImportError as e:
        print(f"❌ MuJoCo导入失败: {e}")
        return False

def test_simulation_modules():
    """测试仿真模块"""
    print("\n🧪 测试仿真模块...")
    
    try:
        from wheel_legged_control.simulation import (
            SimulationManager, SimulationBackend, SimulationConfig
        )
        print("✅ 仿真管理器导入成功")
        
        # 创建仿真管理器
        config = SimulationConfig(
            backend=SimulationBackend.MUJOCO,
            enable_rendering=False
        )
        sim_manager = SimulationManager(config)
        
        available_backends = sim_manager.get_available_backends()
        print(f"📊 可用后端: {[b.value for b in available_backends]}")
        
        if SimulationBackend.MUJOCO in available_backends:
            print("✅ MuJoCo后端可用")
        else:
            print("⚠️  MuJoCo后端不可用")
        
        sim_manager.close()
        return True
        
    except ImportError as e:
        print(f"❌ 仿真模块导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 仿真模块测试失败: {e}")
        return False

def test_urdf_converter():
    """测试URDF转换器"""
    print("\n🧪 测试URDF转换器...")
    
    try:
        from wheel_legged_control.simulation.mujoco_backend import URDFToMJCFConverter
        
        converter = URDFToMJCFConverter()
        
        # 创建简单MJCF文件
        test_file = "test_simple_robot.xml"
        result_path = converter._create_simple_mjcf(test_file)
        
        if os.path.exists(result_path):
            print("✅ MJCF文件创建成功")
            
            # 检查文件内容
            with open(result_path, 'r') as f:
                content = f.read()
                if '<mujoco' in content and 'wheel_legged_robot' in content:
                    print("✅ MJCF文件内容正确")
                else:
                    print("⚠️  MJCF文件内容可能有问题")
            
            # 清理测试文件
            os.remove(result_path)
            return True
        else:
            print("❌ MJCF文件创建失败")
            return False
            
    except ImportError as e:
        print(f"❌ URDF转换器导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ URDF转换器测试失败: {e}")
        return False

def test_mujoco_backend():
    """测试MuJoCo后端"""
    print("\n🧪 测试MuJoCo后端...")
    
    try:
        from wheel_legged_control.simulation.mujoco_backend import (
            MuJoCoSimulationBackend, URDFToMJCFConverter
        )
        from wheel_legged_control.simulation import SimulationConfig, SimulationBackend
        
        # 创建配置
        config = SimulationConfig(
            backend=SimulationBackend.MUJOCO,
            enable_rendering=False,
            dt=0.001
        )
        
        # 创建后端
        backend = MuJoCoSimulationBackend(config)
        print("✅ MuJoCo后端创建成功")
        
        # 创建测试模型
        converter = URDFToMJCFConverter()
        test_model = "test_mujoco_model.xml"
        converter._create_simple_mjcf(test_model)
        
        # 初始化后端
        success = backend.initialize(test_model)
        if success:
            print("✅ MuJoCo后端初始化成功")
            
            # 重置
            backend.reset()
            print("✅ 仿真重置成功")
            
            # 执行几步仿真
            for i in range(5):
                backend.step()
            
            # 获取状态
            state = backend.get_state()
            print(f"✅ 状态获取成功，关节数量: {len(state['joint_positions'])}")
            
            backend.close()
        else:
            print("❌ MuJoCo后端初始化失败")
        
        # 清理测试文件
        if os.path.exists(test_model):
            os.remove(test_model)
        
        return success
        
    except ImportError as e:
        print(f"❌ MuJoCo后端导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ MuJoCo后端测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mujoco_rl_environment():
    """测试MuJoCo强化学习环境"""
    print("\n🧪 测试MuJoCo强化学习环境...")
    
    try:
        from wheel_legged_control.algorithms.mujoco_rl_environment import (
            create_mujoco_wheel_legged_environment, MuJoCoEnvironmentConfig, RewardType
        )
        
        # 创建环境配置
        config = MuJoCoEnvironmentConfig(
            max_episode_steps=50,
            reward_type=RewardType.SHAPED,
            action_type="continuous",
            enable_rendering=False,
            simulation_dt=0.001,
            control_dt=0.02
        )
        
        # 创建环境
        env = create_mujoco_wheel_legged_environment(config)
        print("✅ MuJoCo强化学习环境创建成功")
        print(f"📊 观测空间: {env.observation_space.shape}")
        print(f"🎮 动作空间: {env.action_space.shape}")
        
        # 测试环境
        obs = env.reset()
        print(f"✅ 环境重置成功，观测维度: {obs.shape}")
        
        # 执行几步
        total_reward = 0
        for step in range(5):
            action = env.action_space.sample()
            obs, reward, done, info = env.step(action)
            total_reward += reward
            
            print(f"   步骤 {step+1}: 奖励={reward:.3f}, 累计={total_reward:.3f}")
            
            if done:
                break
        
        # 性能统计
        stats = env.get_performance_stats()
        print(f"✅ 性能统计: {stats.get('steps_per_second', 0):.1f} steps/s")
        
        env.close()
        return True
        
    except ImportError as e:
        print(f"❌ MuJoCo强化学习环境导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ MuJoCo强化学习环境测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 MuJoCo集成简单测试")
    print("=" * 50)
    
    tests = [
        ("MuJoCo安装", test_mujoco_installation),
        ("仿真模块", test_simulation_modules),
        ("URDF转换器", test_urdf_converter),
        ("MuJoCo后端", test_mujoco_backend),
        ("MuJoCo强化学习环境", test_mujoco_rl_environment)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"💥 {test_name} 测试出错: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 测试完成")
    print(f"📊 通过: {passed}/{total}")
    
    if passed == total:
        print("✅ 所有测试都通过！MuJoCo集成成功！")
        return True
    else:
        print("⚠️  部分测试失败，请检查配置")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)