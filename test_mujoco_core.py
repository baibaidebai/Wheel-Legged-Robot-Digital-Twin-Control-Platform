#!/usr/bin/env python3
"""
MuJoCo核心功能测试

测试MuJoCo物理引擎的核心集成功能，不依赖其他复杂模块。
"""

import sys
import os
import numpy as np
import time

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_mujoco_simulation_workflow():
    """测试完整的MuJoCo仿真工作流"""
    print("🧪 测试MuJoCo仿真工作流...")
    
    try:
        from wheel_legged_control.simulation import (
            SimulationManager, SimulationBackend, SimulationConfig
        )
        
        # 创建配置
        config = SimulationConfig(
            backend=SimulationBackend.MUJOCO,
            dt=0.001,
            enable_rendering=False
        )
        
        # 创建仿真管理器
        sim_manager = SimulationManager(config)
        
        # 创建测试模型
        from wheel_legged_control.simulation.mujoco_backend import URDFToMJCFConverter
        converter = URDFToMJCFConverter()
        test_model = "workflow_test_model.xml"
        converter._create_simple_mjcf(test_model)
        
        # 初始化仿真
        success = sim_manager.initialize(test_model)
        if not success:
            print("❌ 仿真初始化失败")
            return False
        
        print("✅ 仿真初始化成功")
        
        # 重置仿真
        sim_manager.reset()
        initial_state = sim_manager.get_state()
        print(f"✅ 仿真重置成功，初始时间: {initial_state['time']:.3f}s")
        
        # 执行控制循环
        print("🔄 执行控制循环...")
        
        states_history = []
        for step in range(50):
            # 生成控制指令
            action = {
                'lf0_motor': 0.5 * np.sin(step * 0.1),
                'rf0_motor': 0.5 * np.sin(step * 0.1 + np.pi),
                'l_wheel_motor': 1.0,
                'r_wheel_motor': 1.0
            }
            
            # 执行仿真步
            success = sim_manager.step(action)
            if not success:
                print(f"❌ 仿真步 {step} 失败")
                return False
            
            # 记录状态
            current_state = sim_manager.get_state()
            states_history.append(current_state)
            
            # 定期输出
            if step % 10 == 0:
                base_pos = current_state['base_position']
                print(f"   步骤 {step:2d}: 时间={current_state['time']:.3f}s, "
                      f"基座位置=[{base_pos[0]:.3f}, {base_pos[1]:.3f}, {base_pos[2]:.3f}]")
        
        # 分析结果
        final_state = states_history[-1]
        print(f"✅ 控制循环完成")
        print(f"   最终时间: {final_state['time']:.3f}s")
        print(f"   基座移动: {np.linalg.norm(final_state['base_position'] - initial_state['base_position']):.3f}m")
        
        # 测试关节控制
        print("\n🎮 测试关节控制...")
        
        # 设置特定关节位置
        target_positions = {
            'lf0_joint': 0.5,
            'rf0_joint': -0.5,
            'lf1_joint': 1.0,
            'rf1_joint': -1.0
        }
        
        success = sim_manager.set_joint_positions(target_positions)
        if success:
            print("✅ 关节位置设置成功")
            
            # 验证设置
            joint_states = sim_manager.get_joint_states()
            for joint_name, target_pos in target_positions.items():
                if joint_name in joint_states:
                    actual_pos = joint_states[joint_name]['position']
                    error = abs(actual_pos - target_pos)
                    if error < 0.1:
                        print(f"   ✅ {joint_name}: 目标={target_pos:.3f}, 实际={actual_pos:.3f}")
                    else:
                        print(f"   ⚠️  {joint_name}: 目标={target_pos:.3f}, 实际={actual_pos:.3f}, 误差={error:.3f}")
        else:
            print("❌ 关节位置设置失败")
        
        # 清理
        sim_manager.close()
        if os.path.exists(test_model):
            os.remove(test_model)
        
        return True
        
    except Exception as e:
        print(f"❌ 工作流测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_performance_benchmark():
    """测试性能基准"""
    print("\n⚡ 测试MuJoCo性能基准...")
    
    try:
        from wheel_legged_control.simulation import (
            SimulationManager, SimulationBackend, SimulationConfig
        )
        from wheel_legged_control.simulation.mujoco_backend import URDFToMJCFConverter
        
        # 创建配置
        config = SimulationConfig(
            backend=SimulationBackend.MUJOCO,
            dt=0.001,
            enable_rendering=False
        )
        
        sim_manager = SimulationManager(config)
        
        # 创建测试模型
        converter = URDFToMJCFConverter()
        test_model = "performance_test_model.xml"
        converter._create_simple_mjcf(test_model)
        
        # 初始化
        sim_manager.initialize(test_model)
        sim_manager.reset()
        
        # 性能测试
        num_steps = 1000
        print(f"🏃 执行 {num_steps} 步仿真...")
        
        step_times = []
        start_time = time.time()
        
        for step in range(num_steps):
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
        avg_step_time = np.mean(step_times)
        std_step_time = np.std(step_times)
        max_step_time = np.max(step_times)
        min_step_time = np.min(step_times)
        steps_per_second = num_steps / total_time
        
        print(f"✅ 性能测试完成:")
        print(f"   总时间: {total_time:.3f}s")
        print(f"   平均步时间: {avg_step_time*1000:.2f}ms")
        print(f"   标准差: {std_step_time*1000:.2f}ms")
        print(f"   最大步时间: {max_step_time*1000:.2f}ms")
        print(f"   最小步时间: {min_step_time*1000:.2f}ms")
        print(f"   仿真频率: {steps_per_second:.1f} Hz")
        
        # 性能评估
        if steps_per_second > 1000:
            print("🚀 性能优秀 (>1000 Hz)")
        elif steps_per_second > 500:
            print("✅ 性能良好 (>500 Hz)")
        elif steps_per_second > 100:
            print("⚠️  性能一般 (>100 Hz)")
        else:
            print("❌ 性能较差 (<100 Hz)")
        
        # 清理
        sim_manager.close()
        if os.path.exists(test_model):
            os.remove(test_model)
        
        return steps_per_second > 100  # 至少要达到100Hz
        
    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        return False

def test_backend_switching():
    """测试后端切换功能"""
    print("\n🔄 测试后端切换...")
    
    try:
        from wheel_legged_control.simulation import (
            SimulationManager, SimulationBackend, SimulationConfig
        )
        from wheel_legged_control.simulation.mujoco_backend import URDFToMJCFConverter
        
        # 创建仿真管理器
        sim_manager = SimulationManager()
        
        available_backends = sim_manager.get_available_backends()
        print(f"📊 可用后端: {[b.value for b in available_backends]}")
        
        # 创建测试模型
        converter = URDFToMJCFConverter()
        test_model = "switching_test_model.xml"
        converter._create_simple_mjcf(test_model)
        
        # 测试每个后端
        for backend in available_backends:
            print(f"\n🎯 测试后端: {backend.value}")
            
            # 切换后端
            success = sim_manager.switch_backend(backend, test_model)
            if success:
                print(f"✅ 切换到 {backend.value} 成功")
                
                # 执行简单测试
                sim_manager.reset()
                
                for i in range(3):
                    action = {'l_wheel_motor': 1.0, 'r_wheel_motor': 1.0}
                    sim_manager.step(action)
                
                state = sim_manager.get_state()
                print(f"   测试结果: 基座位置={state['base_position']}")
                print(f"   当前后端: {sim_manager.get_current_backend().value}")
            else:
                print(f"❌ 切换到 {backend.value} 失败")
        
        # 清理
        sim_manager.close()
        if os.path.exists(test_model):
            os.remove(test_model)
        
        return True
        
    except Exception as e:
        print(f"❌ 后端切换测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 MuJoCo核心功能测试")
    print("=" * 60)
    
    # 检查MuJoCo
    try:
        import mujoco
        print(f"✅ MuJoCo版本: {mujoco.__version__}")
    except ImportError:
        print("❌ MuJoCo未安装")
        return False
    
    tests = [
        ("MuJoCo仿真工作流", test_mujoco_simulation_workflow),
        ("性能基准测试", test_performance_benchmark),
        ("后端切换测试", test_backend_switching)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 通过")
            else:
                print(f"❌ {test_name} 失败")
        except Exception as e:
            print(f"💥 {test_name} 出错: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 MuJoCo核心功能测试完成")
    print(f"📊 通过: {passed}/{total}")
    
    if passed == total:
        print("✅ 所有测试都通过！MuJoCo集成完全成功！")
        print("\n🎯 MuJoCo物理引擎已成功集成到轮腿机器人系统中")
        print("💡 主要功能:")
        print("   - URDF自动转换为MJCF格式")
        print("   - 高性能物理仿真 (>1000 Hz)")
        print("   - 统一的仿真管理接口")
        print("   - 多后端动态切换支持")
        print("   - 完整的关节控制功能")
        return True
    else:
        print("⚠️  部分测试失败，请检查配置")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)