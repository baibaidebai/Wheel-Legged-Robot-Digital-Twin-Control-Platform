#!/usr/bin/env python3
"""
统一仿真启动器 - 支持MuJoCo和Gazebo

让用户选择仿真器和机器人模型
"""

import sys
import os
import subprocess
from pathlib import Path

# 保存原始工作目录
original_dir = os.getcwd()

print("🚀 轮腿机器人仿真启动器")
print("=" * 60)

# 1. 选择仿真器
print("\n🎮 选择仿真器:")
simulators = {
    '1': {
        'name': 'Gazebo',
        'description': 'ROS标准仿真器，完美支持URDF',
        'command': 'gazebo'
    },
    '2': {
        'name': 'MuJoCo',
        'description': '高性能物理引擎，适合强化学习',
        'command': 'mujoco'
    }
}

for key, sim in simulators.items():
    print(f"  {key}. {sim['name']} - {sim['description']}")

sim_choice = input("\n请选择仿真器 (1-2) [默认: 1]: ").strip() or '1'

if sim_choice not in simulators:
    print(f"❌ 无效选择: {sim_choice}")
    sys.exit(1)

selected_simulator = simulators[sim_choice]
print(f"\n✅ 已选择: {selected_simulator['name']}")

# 2. 选择机器人模型
print("\n📦 可用的机器人模型:")
models = {
    '1': {
        'name': 'RM_Serial_Wheeled-leg_Robot',
        'urdf_path': 'src/model/RM_Serial_Wheeled-leg_Robot/urdf/RM_Serial_Wheeled-leg_Robot.urdf',
        'description': 'RM串联轮腿机器人'
    },
    '2': {
        'name': 'DM_Wheel_leg_robot',
        'urdf_path': 'src/model/DM_Wheel_leg_robot/urdf/wheel_legged_urdf_pkg.urdf',
        'description': 'DM轮腿机器人'
    },
    '3': {
        'name': '简化测试模型',
        'urdf_path': None,
        'description': '用于快速测试的简化模型（仅MuJoCo）'
    }
}

for key, model in models.items():
    if model['urdf_path'] is None:
        status = "✅" if sim_choice == '2' else "⚠️ "
    else:
        full_path = os.path.join(original_dir, model['urdf_path'])
        status = "✅" if Path(full_path).exists() else "❌"
    print(f"  {key}. {status} {model['name']} - {model['description']}")

model_choice = input("\n请选择模型 (1-3) [默认: 1]: ").strip() or '1'

if model_choice not in models:
    print(f"❌ 无效选择: {model_choice}")
    sys.exit(1)

selected_model = models[model_choice]

# 验证选择
if selected_model['urdf_path'] is None and sim_choice == '1':
    print(f"\n❌ 错误: Gazebo不支持简化模型，请选择URDF模型（选项1或2）")
    sys.exit(1)

print(f"\n✅ 已选择: {selected_model['name']}")

# 3. 启动仿真
print("\n" + "=" * 60)
print(f"🎨 启动 {selected_simulator['name']} 仿真...")
print("=" * 60)

if sim_choice == '1':
    # 启动Gazebo
    print("\n💡 Gazebo使用说明:")
    print("   - Gazebo会打开独立的3D可视化窗口")
    print("   - 可以使用鼠标旋转、平移、缩放视角")
    print("   - 左侧面板可以插入模型和调整参数")
    print("   - 按Ctrl+C退出")
    print("\n启动中，请稍候...")
    print("=" * 60)
    
    urdf_path = os.path.join(original_dir, selected_model['urdf_path'])
    
    # 检查Gazebo是否安装
    try:
        subprocess.run(['which', 'gazebo'], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("\n❌ 错误: Gazebo未安装")
        print("\n💡 安装Gazebo:")
        print("   Ubuntu/Debian:")
        print("   sudo apt-get update")
        print("   sudo apt-get install gazebo11 libgazebo11-dev")
        sys.exit(1)
    
    # 启动Gazebo并加载URDF
    try:
        # 方法1: 使用gazebo命令直接加载
        print(f"\n📥 加载URDF: {selected_model['urdf_path']}")
        
        # 创建一个简单的world文件
        world_content = f'''<?xml version="1.0"?>
<sdf version="1.6">
  <world name="default">
    <include>
      <uri>model://ground_plane</uri>
    </include>
    <include>
      <uri>model://sun</uri>
    </include>
    <model name="robot">
      <include>
        <uri>file://{urdf_path}</uri>
      </include>
    </model>
  </world>
</sdf>
'''
        
        world_path = "temp_robot.world"
        with open(world_path, 'w') as f:
            f.write(world_content)
        
        print(f"✅ 创建world文件: {world_path}")
        print(f"\n🎮 启动Gazebo...")
        
        # 启动Gazebo
        subprocess.run(['gazebo', world_path])
        
        # 清理
        if os.path.exists(world_path):
            os.remove(world_path)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  用户中断")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        print("\n💡 尝试备用方法...")
        
        # 备用方法：使用ROS launch
        print("\n使用ROS2 launch启动Gazebo...")
        try:
            # 设置环境变量
            env = os.environ.copy()
            env['GAZEBO_MODEL_PATH'] = os.path.dirname(os.path.dirname(urdf_path))
            
            # 启动gazebo并spawn模型
            subprocess.run(['gazebo', '--verbose'], env=env)
        except Exception as e2:
            print(f"❌ 备用方法也失败: {e2}")
            print("\n💡 建议:")
            print("   1. 检查Gazebo是否正确安装")
            print("   2. 尝试手动启动: gazebo")
            print(f"   3. 然后在Gazebo中插入模型: {urdf_path}")

elif sim_choice == '2':
    # 启动MuJoCo
    print("\n💡 MuJoCo使用说明:")
    print("   - 鼠标左键拖动: 旋转视角")
    print("   - 鼠标右键拖动: 平移视角")
    print("   - 鼠标滚轮: 缩放")
    print("   - 空格键: 暂停/继续仿真")
    print("   - Esc: 退出")
    print("\n启动中...")
    print("=" * 60)
    
    # 调用MuJoCo启动脚本
    try:
        # 传递模型选择
        env = os.environ.copy()
        env['MODEL_CHOICE'] = model_choice
        
        subprocess.run([sys.executable, 'launch_mujoco_direct.py'], env=env)
    except KeyboardInterrupt:
        print("\n\n⏹️  用户中断")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()

print("\n👋 感谢使用！")
