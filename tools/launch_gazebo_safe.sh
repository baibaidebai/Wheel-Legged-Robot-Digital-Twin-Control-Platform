#!/bin/bash
# Gazebo仿真启动脚本 - 虚拟机安全模式（解决闪屏问题）

echo "🚀 轮腿机器人Gazebo仿真（虚拟机模式）"
echo "======================================"

# Source ROS2环境
if [ -f "/opt/ros/jazzy/setup.bash" ]; then
    source /opt/ros/jazzy/setup.bash
    echo "✅ ROS2 Jazzy环境已加载"
fi

# 检查gz sim命令
if ! command -v gz &> /dev/null; then
    echo "❌ Gazebo未安装"
    exit 1
fi

if ! gz sim --help &> /dev/null; then
    echo "❌ Gazebo仿真器(gz-sim)未安装"
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

# 创建包含机器人的SDF world文件
echo ""
echo "🔧 创建Gazebo world（包含机器人）..."

cat > robot_world_with_model.sdf << EOF
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
      <cast_shadows>false</cast_shadows>
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
    
    <!-- 包含机器人模型 -->
    <include>
      <uri>file://$URDF_FULL_PATH</uri>
      <name>robot</name>
      <pose>0 0 0.5 0 0 0</pose>
    </include>
  </world>
</sdf>
EOF

echo "✅ World文件创建完成"

# 设置环境变量 - 虚拟机优化
export GZ_SIM_RESOURCE_PATH="$MODEL_DIR:$GZ_SIM_RESOURCE_PATH"

# 虚拟机环境优化设置
echo ""
echo "🔧 配置虚拟机渲染优化..."

# 使用软件渲染（解决闪屏问题）
export LIBGL_ALWAYS_SOFTWARE=1
export MESA_GL_VERSION_OVERRIDE=3.3

# 禁用硬件加速
export GALLIUM_DRIVER=llvmpipe

# Gazebo渲染引擎设置
export OGRE_RTT_MODE=Copy

echo "✅ 渲染优化已配置"

# 启动Gazebo
echo ""
echo "======================================"
echo "🎨 启动Gazebo（虚拟机安全模式）..."
echo "======================================"
echo ""
echo "💡 虚拟机优化说明:"
echo "   - 使用软件渲染（解决闪屏）"
echo "   - 禁用阴影（提高性能）"
echo "   - 机器人已自动加载"
echo ""
echo "   视角控制:"
echo "   - 鼠标左键: 旋转"
echo "   - 鼠标滚轮: 缩放"
echo "   - Shift+左键: 平移"
echo ""
echo "⚠️  注意："
echo "   - 软件渲染模式下性能较低"
echo "   - 如果仍然闪屏，尝试增加虚拟机显存"
echo ""
echo "按 Ctrl+C 退出"
echo "======================================"

# 启动Gazebo（使用软件渲染）
gz sim robot_world_with_model.sdf -v 4 --render-engine ogre

# 清理
rm -f robot_world_with_model.sdf
echo ""
echo "🧹 清理完成"
echo "👋 感谢使用!"
