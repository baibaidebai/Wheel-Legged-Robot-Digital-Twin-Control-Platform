#!/usr/bin/env python3
"""
Gazebo仿真启动器 - 直接使用URDF模型

Gazebo对URDF有完美支持，可以直接加载你的机器人模型
"""

import sys
import os
import subprocess
from pathlib import Path

print("🚀 Gazebo仿真启动器")
print("=" * 60)

# 1. 选择机器人模型
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
    }
}

for key, model in models.items():
    full_path = Path(model['urdf_path'])
    status = "✅" if full_path.exists() else "❌"
    print(f"  {key}. {status} {model['name']} - {model['description']}")

choice = input("\n请选择模型 (1-2) [默认: 1]: ").strip() or '1'

if choice not in models:
    print(f"❌ 无效选择: {choice}")
    sys.exit(1)

selected_model = models[choice]
print(f"\n✅ 已选择: {selected_model['name']}")

urdf_path = os.path.abspath(selected_model['urdf_path'])

if not os.path.exists(urdf_path):
    print(f"❌ URDF文件不存在: {urdf_path}")
    sys.exit(1)

# 2. 检查Gazebo
print("\n🔍 检查Gazebo...")
try:
    result = subprocess.run(['which', 'gazebo'], capture_output=True, text=True)
    if result.returncode != 0:
        raise FileNotFoundError("Gazebo not found")
    gazebo_path = result.stdout.strip()
    print(f"✅ Gazebo已安装: {gazebo_path}")
except:
    print("❌ Gazebo未安装")
    print("\n💡 安装Gazebo:")
    print("   Ubuntu 20.04/22.04:")
    print("   sudo apt-get update")
    print("   sudo apt-get install gazebo11 libgazebo11-dev")
    print("\n   或者使用ROS2:")
    print("   sudo apt-get install ros-<distro>-gazebo-ros-pkgs")
    sys.exit(1)

# 3. 创建Gazebo world文件
print("\n🔧 准备Gazebo world...")

model_dir = os.path.dirname(os.path.dirname(urdf_path))
model_name = os.path.basename(model_dir)

# 创建SDF world文件
world_content = f'''<?xml version="1.0"?>
<sdf version="1.6">
  <world name="robot_world">
    <!-- 地面 -->
    <include>
      <uri>model://ground_plane</uri>
    </include>
    
    <!-- 太阳光 -->
    <include>
      <uri>model://sun</uri>
    </include>
    
    <!-- 物理引擎设置 -->
    <physics type="ode">
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1</real_time_factor>
      <real_time_update_rate>1000</real_time_update_rate>
      <gravity>0 0 -9.81</gravity>
    </physics>
    
    <!-- 场景设置 -->
    <scene>
      <ambient>0.4 0.4 0.4 1</ambient>
      <background>0.7 0.7 0.7 1</background>
      <shadows>true</shadows>
    </scene>
    
    <!-- 相机 -->
    <gui>
      <camera name="user_camera">
        <pose>2.0 -2.0 1.5 0 0.3 2.35</pose>
      </camera>
    </gui>
  </world>
</sdf>
'''

world_path = "robot_simulation.world"
with open(world_path, 'w') as f:
    f.write(world_content)

print(f"✅ 创建world文件: {world_path}")

# 4. 启动Gazebo
print("\n" + "=" * 60)
print("🎨 启动Gazebo...")
print("=" * 60)
print("\n💡 使用说明:")
print("   1. Gazebo窗口会打开，显示空白世界")
print("   2. 点击左侧 'Insert' 标签")
print("   3. 点击 'Add Path' 按钮")
print(f"   4. 添加路径: {model_dir}")
print(f"   5. 在列表中找到并拖动 '{model_name}' 到场景中")
print("\n   或者使用命令行spawn模型（在另一个终端）:")
print(f"   gz model --spawn-file={urdf_path} --model-name=robot -x 0 -y 0 -z 0.5")
print("\n   视角控制:")
print("   - 鼠标左键拖动: 旋转视角")
print("   - 鼠标滚轮: 缩放")
print("   - Shift+鼠标左键: 平移")
print("\n按 Ctrl+C 退出")
print("=" * 60)

try:
    # 设置环境变量
    env = os.environ.copy()
    
    # 添加模型路径
    if 'GAZEBO_MODEL_PATH' in env:
        env['GAZEBO_MODEL_PATH'] = f"{model_dir}:{env['GAZEBO_MODEL_PATH']}"
    else:
        env['GAZEBO_MODEL_PATH'] = model_dir
    
    # 启动Gazebo
    print(f"\n🚀 启动Gazebo world...")
    subprocess.run(['gazebo', world_path, '--verbose'], env=env)
    
except KeyboardInterrupt:
    print("\n\n⏹️  用户中断")
except Exception as e:
    print(f"\n❌ 启动失败: {e}")
    print("\n💡 故障排除:")
    print("   1. 确认Gazebo已正确安装: gazebo --version")
    print("   2. 尝试手动启动: gazebo")
    print("   3. 检查URDF文件格式是否正确")
    import traceback
    traceback.print_exc()
finally:
    # 清理临时文件
    if os.path.exists(world_path):
        os.remove(world_path)
        print(f"\n🧹 清理临时文件: {world_path}")

print("\n👋 感谢使用！")
