#!/bin/bash
# 主启动脚本 - GUI版本

echo "🚀 启动Gazebo仿真器（GUI版本）"
echo "======================================"
echo ""

# 检查Python和tkinter
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未安装"
    echo "   sudo apt-get install python3"
    exit 1
fi

# 检查tkinter
if ! python3 -c "import tkinter" &> /dev/null; then
    echo "❌ tkinter未安装"
    echo ""
    echo "安装命令:"
    echo "   sudo apt-get install python3-tk"
    echo ""
    read -p "是否现在安装? (y/n): " install
    if [ "$install" = "y" ] || [ "$install" = "Y" ]; then
        sudo apt-get update
        sudo apt-get install -y python3-tk
    else
        exit 1
    fi
fi

# 启动GUI
python3 tools/launch_gazebo_gui.py
