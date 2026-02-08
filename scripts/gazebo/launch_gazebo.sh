#!/bin/bash
# Gazebo仿真启动脚本

echo "🚀 启动Gazebo仿真"
echo "======================================"

# 检查Gazebo
if ! command -v gazebo &> /dev/null; then
    echo "❌ Gazebo未安装"
    echo ""
    echo "💡 安装Gazebo:"
    echo "   sudo apt-get update"
    echo "   sudo apt-get install gazebo11 libgazebo11-dev"
    exit 1
fi

echo "✅ Gazebo已安装"
echo ""

# 运行Python启动脚本
python3 launch_gazebo.py
