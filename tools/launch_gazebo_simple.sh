#!/bin/bash
# Gazebo简单启动脚本 - 直接加载机器人

echo "🚀 轮腿机器人Gazebo仿真（简单模式）"
echo "======================================"

# Source ROS2环境
if [ -f "/opt/ros/jazzy/setup.bash" ]; then
    source /opt/ros/jazzy/setup.bash
    echo "✅ ROS2 Jazzy环境已加载"
fi

echo ""
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

echo ""
echo "======================================"
echo "🎨 启动Gazebo..."
echo "======================================"
echo ""
echo "💡 使用说明:"
echo "   - 窗口打开后，机器人会自动加载"
echo "   - 如果看不到机器人，按数字键 '2' 切换到正交视图"
echo "   - 或者用鼠标滚轮缩小视角"
echo ""
echo "按 Ctrl+C 退出"
echo "======================================"

# 虚拟机环境优化
export LIBGL_ALWAYS_SOFTWARE=1
export MESA_GL_VERSION_OVERRIDE=3.3
export GALLIUM_DRIVER=llvmpipe

# 直接启动Gazebo并加载URDF
gz sim -r "$URDF_FULL_PATH" -v 4

echo ""
echo "👋 感谢使用!"
