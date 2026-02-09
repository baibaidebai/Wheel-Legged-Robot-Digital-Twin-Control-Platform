#!/usr/bin/env python3
"""
Gazebo Harmonic (gz) 仿真启动器 - Ubuntu 24.04

使用新版Gazebo (gz命令) 直接加载URDF模型
"""

import sys
import os
import subprocess
from pathlib import Path

print("🚀 Gazebo Harmonic 仿真启动器")
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
    result = subprocess.run(['which', 'gz'], capture_output=True, text=True)
    if result.returncode != 0:
        raise FileNotFoundError("gz command not found")
    gz_path = result.stdout.strip()
    print(f"✅ Gazebo已安装: {gz_path}")
    
    # 检查版本
    version_result = subprocess.run(['gz', 'sim', '--version'], capture_output=True, text=True)
    print(f"   版本: {version_result.stdout.strip()}")
except:
    print("❌ Gazebo未安装或配置不正确")
    print("\n💡 安装Gazebo Harmonic:")
    print("   sudo apt-get update")
    print("   sudo apt-get install ros-jazzy-ros-gz")
    sys.exit(1)

# 3. 创建SDF world文件
print("\n🔧 准备Gazebo world...")

# 创建SDF world文件（新版Gazebo使用SDF 1.9+）
world_content = f'''<?xml version="1.0"?>
<sdf version="1.9">
  <world name="robot_world">
    <!-- 物理引擎 -->
    <physics name="1ms" type="ignored">
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1.0</real_time_factor>
    </physics>
    
    <!-- 插件 -->
    <plugin
      filename="gz-sim-physics-system"
      name="gz::sim::systems::Physics">
    </plugin>
    <plugin
      filename="gz-sim-user-commands-system"
      name="gz::sim::systems::UserCommands">
    </plugin>
    <plugin
      filename="gz-sim-scene-broadcaster-system"
      name="gz::sim::systems::SceneBroadcaster">
    </plugin>
    
    <!-- 光照 -->
    <light type="directional" name="sun">
      <cast_shadows>true</cast_shadows>
      <pose>0 0 10 0 0 0</pose>
      <diffuse>0.8 0.8 0.8 1</diffuse>
      <specular>0.2 0.2 0.2 1</specular>
      <attenuation>
        <range>1000</range>
        <constant>0.9</constant>
        <linear>0.01</linear>
        <quadratic>0.001</quadratic>
      </attenuation>
      <direction>-0.5 0.1 -0.9</direction>
    </light>
    
    <!-- 地面 -->
    <model name="ground_plane">
      <static>true</static>
      <link name="link">
        <collision name="collision">
          <geometry>
            <plane>
              <normal>0 0 1</normal>
              <size>100 100</size>
            </plane>
          </geometry>
        </collision>
        <visual name="visual">
          <geometry>
            <plane>
              <normal>0 0 1</normal>
              <size>100 100</size>
            </plane>
          </geometry>
          <material>
            <ambient>0.8 0.8 0.8 1</ambient>
            <diffuse>0.8 0.8 0.8 1</diffuse>
            <specular>0.8 0.8 0.8 1</specular>
          </material>
        </visual>
      </link>
    </model>
  </world>
</sdf>
'''

world_path = "robot_gz.sdf"
with open(world_path, 'w') as f:
    f.write(world_content)

print(f"✅ 创建world文件: {world_path}")

# 4. 启动Gazebo
print("\n" + "=" * 60)
print("🎨 启动Gazebo Harmonic...")
print("=" * 60)
print("\n💡 使用说明:")
print("   1. Gazebo窗口会打开")
print("   2. 在另一个终端运行以下命令加载机器人:")
print(f"      gz model --spawn-file={urdf_path} --model-name=robot -x 0 -y 0 -z 0.5")
print("\n   视角控制:")
print("   - 鼠标左键拖动: 旋转视角")
print("   - 鼠标滚轮: 缩放")
print("   - Shift+鼠标左键: 平移")
print("\n按 Ctrl+C 退出")
print("=" * 60)

try:
    # 启动Gazebo
    print(f"\n🚀 启动Gazebo world...")
    subprocess.run(['gz', 'sim', world_path, '-v', '4'])
    
except KeyboardInterrupt:
    print("\n\n⏹️  用户中断")
except Exception as e:
    print(f"\n❌ 启动失败: {e}")
    print("\n💡 故障排除:")
    print("   1. 确认Gazebo已正确安装: gz sim --version")
    print("   2. 尝试手动启动: gz sim")
    print("   3. 检查ROS2环境: source /opt/ros/jazzy/setup.bash")
    import traceback
    traceback.print_exc()
finally:
    # 清理临时文件
    if os.path.exists(world_path):
        os.remove(world_path)
        print(f"\n🧹 清理临时文件: {world_path}")

print("\n👋 感谢使用！")
