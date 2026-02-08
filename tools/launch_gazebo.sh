#!/bin/bash
# Gazebo仿真启动脚本 - Ubuntu 24.04

echo "🚀 轮腿机器人Gazebo仿真"
echo "======================================"

# Source ROS2环境
if [ -f "/opt/ros/jazzy/setup.bash" ]; then
    source /opt/ros/jazzy/setup.bash
    echo "✅ ROS2 Jazzy环境已加载"
fi

# 检查gz sim命令
if ! command -v gz &> /dev/null; then
    echo "❌ Gazebo未安装"
    echo ""
    echo "💡 请查看安装指南: INSTALL_GAZEBO.md"
    echo ""
    echo "快速安装命令:"
    echo "   sudo apt-get update"
    echo "   sudo apt-get install ros-jazzy-ros-gz-sim"
    exit 1
fi

# 检查gz sim是否可用
if ! gz sim --help &> /dev/null; then
    echo "❌ Gazebo仿真器(gz-sim)未安装"
    echo ""
    echo "💡 你只安装了部分Gazebo组件"
    echo ""
    echo "请运行以下命令安装完整的Gazebo:"
    echo "   sudo apt-get update"
    echo "   sudo apt-get install ros-jazzy-ros-gz-sim"
    echo ""
    echo "详细说明请查看: INSTALL_GAZEBO.md"
    exit 1
fi

echo "✅ Gazebo已安装"
echo ""

# 选择模型
echo "📦 选择机器人模型:"
echo "  1. RM_Serial_Wheeled-leg_Robot"
echo "  2. DM_Wheel_leg_robot"
echo ""
read -p "请选择 (1-2) [默认: 1]: " choice
choice=${choice:-1}

case $choice in
    1)
        MODEL_NAME="RM_Serial_Wheeled-leg_Robot"
        URDF_PATH="src/model/RM_Serial_Wheeled-leg_Robot/urdf/RM_Serial_Wheeled-leg_Robot.urdf"
        ;;
    2)
        MODEL_NAME="DM_Wheel_leg_robot"
        URDF_PATH="src/model/DM_Wheel_leg_robot/urdf/wheel_legged_urdf_pkg.urdf"
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo "✅ 已选择: $MODEL_NAME"

# 检查URDF文件
if [ ! -f "$URDF_PATH" ]; then
    echo "❌ URDF文件不存在: $URDF_PATH"
    exit 1
fi

URDF_FULL_PATH=$(realpath "$URDF_PATH")
MODEL_DIR=$(dirname $(dirname "$URDF_FULL_PATH"))

echo "   URDF: $URDF_FULL_PATH"
echo "   模型目录: $MODEL_DIR"

# 创建SDF world文件
echo ""
echo "🔧 创建Gazebo world..."

cat > robot_world.sdf << EOF
<?xml version="1.0"?>
<sdf version="1.9">
  <world name="robot_world">
    <!-- 物理引擎 -->
    <physics name="1ms" type="ignored">
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1.0</real_time_factor>
    </physics>
    
    <!-- 插件 -->
    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
    
    <!-- 光照 -->
    <light type="directional" name="sun">
      <cast_shadows>true</cast_shadows>
      <pose>0 0 10 0 0 0</pose>
      <diffuse>0.8 0.8 0.8 1</diffuse>
      <specular>0.2 0.2 0.2 1</specular>
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
          </material>
        </visual>
      </link>
    </model>
  </world>
</sdf>
EOF

echo "✅ World文件创建完成"

# 设置环境变量
export GZ_SIM_RESOURCE_PATH="$MODEL_DIR:$GZ_SIM_RESOURCE_PATH"

# 启动Gazebo
echo ""
echo "======================================"
echo "🎨 启动Gazebo..."
echo "======================================"
echo ""
echo "💡 使用说明:"
echo "   1. Gazebo窗口会打开"
echo "   2. 在另一个终端运行以下命令加载机器人:"
echo "      gz service -s /world/robot_world/create \\"
echo "        --reqtype gz.msgs.EntityFactory \\"
echo "        --reptype gz.msgs.Boolean \\"
echo "        --timeout 1000 \\"
echo "        --req 'sdf_filename: \"$URDF_FULL_PATH\", name: \"robot\"'"
echo ""
echo "   视角控制:"
echo "   - 鼠标左键: 旋转"
echo "   - 鼠标滚轮: 缩放"
echo "   - Shift+左键: 平移"
echo ""
echo "按 Ctrl+C 退出"
echo "======================================"

# 启动Gazebo
gz sim robot_world.sdf -v 4

# 清理
rm -f robot_world.sdf
echo ""
echo "🧹 清理完成"
echo "👋 感谢使用!"
