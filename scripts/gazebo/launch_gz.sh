#!/bin/bash
# Gazebo Harmonic (gz) 启动脚本 - Ubuntu 24.04

echo "🚀 启动Gazebo Harmonic (gz)"
echo "======================================"

# Source ROS2环境
if [ -f "/opt/ros/jazzy/setup.bash" ]; then
    source /opt/ros/jazzy/setup.bash
    echo "✅ ROS2 Jazzy环境已加载"
else
    echo "⚠️  ROS2环境未找到"
fi

# 检查gz命令
if ! command -v gz &> /dev/null; then
    echo "❌ Gazebo (gz) 未安装"
    echo ""
    echo "💡 安装Gazebo:"
    echo "   sudo apt-get update"
    echo "   sudo apt-get install ros-jazzy-ros-gz"
    exit 1
fi

echo "✅ Gazebo已安装"
echo ""

# 运行Python启动脚本
python3 launch_gz.py
