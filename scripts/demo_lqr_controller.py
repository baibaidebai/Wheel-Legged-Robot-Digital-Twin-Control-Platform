#!/usr/bin/env python3
"""
LQR控制器演示脚本

演示LQR控制器的功能和使用方法。

注意：此脚本需要安装SciPy：
sudo apt install python3-scipy
或
pip install scipy
"""

import os
import sys
import logging
import argparse
import numpy as np
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src/wheel_legged_control'))

def check_dependencies():
    """检查依赖项"""
    missing_deps = []
    
    try:
        import numpy
        print(f"✅ NumPy版本: {numpy.__version__}")
    except ImportError:
        missing_deps.append("numpy")
    
    try:
        import scipy
        print(f"✅ SciPy版本: {scipy.__version__}")
    except ImportError:
        missing_deps.append("scipy")
        print("❌ SciPy未安装")
        print("请安装SciPy：")
        print("  sudo apt install python3-scipy")
        print("  或")
        print("  pip install scipy")
    
    try:
        import matplotlib
        print(f"✅ Matplotlib版本: {matplotlib.__version__}")
    except ImportError:
        print("⚠️  Matplotlib未安装，无法绘制图表")
        print("可选安装：pip install matplotlib")
    
    return len(missing_deps) == 0, missing_deps

def create_simple_system():
    """创建简单的测试系统（不依赖LQR模块）"""
    # 双积分器系统：位置和速度
    # 状态: [x, y, vx, vy]
    # 控制: [ax, ay] (加速度)
    
    A = np.array([
        [0, 0, 1, 0],
        [0, 0, 0, 1],
        [0, 0, 0, 0],
        [0, 0, 0, 0]
    ])
    
    B = np.array([
        [0, 0],
        [0, 0],
        [1, 0],
        [0, 1]
    ])
    
    return A, B

def simple_lqr_demo():
    """简单的LQR演示（不依赖SciPy）"""
    print("🎮 简单LQR控制演示（无SciPy依赖）")
    print("-" * 50)
    
    # 创建简单系统
    A, B = create_simple_system()
    dt = 0.1
    
    # 简化的离散化
    I = np.eye(4)
    A_d = I + A * dt
    B_d = B * dt
    
    print(f"📊 系统信息:")
    print(f"   状态维度: {A.shape[0]}")
    print(f"   控制维度: {B.shape[1]}")
    print(f"   采样时间: {dt}s")
    
    # 权重矩阵
    Q = np.diag([10.0, 10.0, 1.0, 1.0])  # 位置权重高，速度权重低
    R = np.diag([0.1, 0.1])               # 控制权重
    
    print(f"\n⚙️  控制参数:")
    print(f"   Q权重: {np.diag(Q)}")
    print(f"   R权重: {np.diag(R)}")
    
    # 简化的控制器（比例控制）
    # 这不是真正的LQR，但可以演示控制概念
    K_simple = np.array([
        [5.0, 0.0, 2.0, 0.0],  # x方向控制增益
        [0.0, 5.0, 0.0, 2.0]   # y方向控制增益
    ])
    
    print(f"   简化增益矩阵K: \n{K_simple}")
    
    # 仿真参数
    target_state = np.array([2.0, 1.0, 0.0, 0.0])  # 目标：位置(2,1)，速度(0,0)
    current_state = np.array([0.0, 0.0, 0.0, 0.0])  # 初始：原点，静止
    
    print(f"\n🎯 控制目标:")
    print(f"   目标位置: ({target_state[0]}, {target_state[1]})")
    print(f"   初始位置: ({current_state[0]}, {current_state[1]})")
    
    # 仿真循环
    states = [current_state.copy()]
    controls = []
    costs = []
    
    print(f"\n🔄 开始仿真...")
    
    for step in range(50):
        # 计算状态误差
        error = current_state - target_state
        
        # 简化控制律：u = -K * error
        control = -K_simple @ error
        
        # 控制限制
        control = np.clip(control, -5.0, 5.0)
        
        # 计算代价
        cost = error.T @ Q @ error + control.T @ R @ control
        
        # 更新状态
        current_state = A_d @ current_state + B_d @ control
        
        # 记录数据
        states.append(current_state.copy())
        controls.append(control.copy())
        costs.append(cost)
        
        # 每10步输出一次
        if step % 10 == 0:
            pos_error = np.linalg.norm(current_state[:2] - target_state[:2])
            print(f"   步骤 {step:2d}: 位置误差={pos_error:.4f}, 代价={cost:.4f}")
    
    # 分析结果
    states = np.array(states)
    controls = np.array(controls)
    costs = np.array(costs)
    
    final_error = np.linalg.norm(states[-1][:2] - target_state[:2])
    avg_cost = np.mean(costs)
    max_control = np.max(np.abs(controls))
    
    print(f"\n📈 仿真结果:")
    print(f"   最终位置误差: {final_error:.4f}")
    print(f"   平均代价: {avg_cost:.4f}")
    print(f"   最大控制力: {max_control:.4f}")
    
    if final_error < 0.1:
        print("✅ 控制成功收敛到目标！")
    else:
        print("⚠️  控制未完全收敛")
    
    # 尝试绘制结果
    try:
        import matplotlib.pyplot as plt
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        
        # 轨迹图
        axes[0, 0].plot(states[:, 0], states[:, 1], 'b-', linewidth=2, label='实际轨迹')
        axes[0, 0].plot(target_state[0], target_state[1], 'r*', markersize=15, label='目标')
        axes[0, 0].plot(states[0, 0], states[0, 1], 'go', markersize=8, label='起点')
        axes[0, 0].set_xlabel('X位置')
        axes[0, 0].set_ylabel('Y位置')
        axes[0, 0].set_title('机器人轨迹')
        axes[0, 0].legend()
        axes[0, 0].grid(True)
        
        # 位置误差
        time_steps = np.arange(len(states))
        position_errors = np.linalg.norm(states[:, :2] - target_state[:2], axis=1)
        axes[0, 1].plot(time_steps, position_errors, 'r-', linewidth=2)
        axes[0, 1].set_xlabel('时间步')
        axes[0, 1].set_ylabel('位置误差')
        axes[0, 1].set_title('位置误差收敛')
        axes[0, 1].grid(True)
        
        # 控制输入
        time_steps_control = np.arange(len(controls))
        axes[1, 0].plot(time_steps_control, controls[:, 0], 'b-', label='X控制')
        axes[1, 0].plot(time_steps_control, controls[:, 1], 'r-', label='Y控制')
        axes[1, 0].set_xlabel('时间步')
        axes[1, 0].set_ylabel('控制输入')
        axes[1, 0].set_title('控制输入历史')
        axes[1, 0].legend()
        axes[1, 0].grid(True)
        
        # 代价函数
        axes[1, 1].plot(time_steps_control, costs, 'g-', linewidth=2)
        axes[1, 1].set_xlabel('时间步')
        axes[1, 1].set_ylabel('代价')
        axes[1, 1].set_title('代价函数变化')
        axes[1, 1].grid(True)
        
        plt.tight_layout()
        plt.savefig('lqr_demo_results.png', dpi=300, bbox_inches='tight')
        print(f"📊 结果图表已保存: lqr_demo_results.png")
        
        try:
            plt.show()
        except:
            print("无法显示图表，但已保存到文件")
            
    except ImportError:
        print("📊 Matplotlib未安装，跳过图表绘制")
    
    return states, controls, costs

def full_lqr_demo():
    """完整的LQR演示（需要SciPy）"""
    print("🚀 完整LQR控制器演示")
    print("-" * 50)
    
    try:
        from wheel_legged_control.algorithms.lqr_controller import (
            LQRController, LQRConfig, LinearSystemModel, create_wheel_legged_robot_model
        )
        
        # 创建配置
        config = LQRConfig(
            state_dim=4,
            control_dim=2,
            Q_weights=[10.0, 10.0, 1.0, 1.0],
            R_weights=[0.1, 0.1],
            dt=0.1
        )
        
        print(f"📊 LQR配置:")
        print(f"   状态维度: {config.state_dim}")
        print(f"   控制维度: {config.control_dim}")
        print(f"   Q权重: {config.Q_weights}")
        print(f"   R权重: {config.R_weights}")
        
        # 创建系统模型
        A, B = create_simple_system()
        system_model = LinearSystemModel(A, B, config.dt)
        
        # 创建LQR控制器
        lqr = LQRController(config, system_model)
        
        print(f"✅ LQR控制器创建成功")
        print(f"📊 增益矩阵形状: {lqr.K_gain.shape}")
        
        # 设置参考状态
        reference_state = np.array([2.0, 1.0, 0.0, 0.0])
        lqr.set_reference(reference_state)
        
        print(f"🎯 参考状态: {reference_state}")
        
        # 仿真测试
        current_state = np.array([0.0, 0.0, 0.0, 0.0])
        states = [current_state.copy()]
        controls = []
        
        print(f"\n🔄 开始LQR仿真...")
        
        for step in range(50):
            # 计算控制输入
            control = lqr.compute_control(current_state)
            controls.append(control.copy())
            
            # 更新状态
            current_state = system_model.predict(current_state, control)
            states.append(current_state.copy())
            
            # 每10步输出一次
            if step % 10 == 0:
                pos_error = np.linalg.norm(current_state[:2] - reference_state[:2])
                cost = lqr.cost_history[-1] if lqr.cost_history else 0
                print(f"   步骤 {step:2d}: 位置误差={pos_error:.4f}, 代价={cost:.4f}")
        
        # 获取性能指标
        metrics = lqr.get_performance_metrics()
        
        print(f"\n📈 LQR性能指标:")
        for key, value in metrics.items():
            if isinstance(value, float):
                print(f"   {key}: {value:.4f}")
            else:
                print(f"   {key}: {value}")
        
        return states, controls, lqr
        
    except ImportError as e:
        print(f"❌ LQR模块导入失败: {e}")
        print("请确保SciPy已正确安装")
        return None, None, None

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='LQR控制器演示')
    parser.add_argument('--mode', type=str, default='simple', 
                       choices=['simple', 'full'], help='演示模式')
    parser.add_argument('--check-deps', action='store_true', help='检查依赖项')
    
    args = parser.parse_args()
    
    print("🎛️  LQR控制器演示")
    print("=" * 60)
    print(f"📅 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎮 模式: {args.mode}")
    
    # 检查依赖项
    deps_ok, missing = check_dependencies()
    
    if args.check_deps:
        if deps_ok:
            print("\n✅ 所有依赖项都已安装")
        else:
            print(f"\n❌ 缺少依赖项: {missing}")
        return 0
    
    try:
        if args.mode == 'simple':
            # 简单演示（不需要SciPy）
            states, controls, costs = simple_lqr_demo()
            
        elif args.mode == 'full':
            # 完整演示（需要SciPy）
            if not deps_ok:
                print(f"\n❌ 完整模式需要所有依赖项，缺少: {missing}")
                print("使用简单模式：python3 demo_lqr_controller.py --mode simple")
                return 1
            
            states, controls, lqr = full_lqr_demo()
            if states is None:
                print("回退到简单模式...")
                states, controls, costs = simple_lqr_demo()
        
        print(f"\n🎉 LQR演示完成！")
        
        return 0
        
    except KeyboardInterrupt:
        print(f"\n⏹️  演示被用户中断")
        return 0
    
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)