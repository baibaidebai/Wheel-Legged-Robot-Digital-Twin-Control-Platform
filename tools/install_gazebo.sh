#!/bin/bash
# Gazebo自动安装脚本

echo "🔧 Gazebo安装脚本"
echo "======================================"

# 检查是否已安装
if gz sim --version &> /dev/null; then
    echo "✅ Gazebo已经安装"
    gz sim --version
    echo ""
    echo "可以直接运行: ./launch_gazebo.sh"
    exit 0
fi

echo "📦 准备安装Gazebo..."
echo ""

# 提示用户
echo "将要安装: ros-jazzy-ros-gz-sim"
echo ""
read -p "是否继续? (y/n) [默认: y]: " confirm
confirm=${confirm:-y}

if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "❌ 安装已取消"
    exit 1
fi

echo ""
echo "🚀 开始安装..."
echo "======================================"

# 更新包列表
echo "📥 更新包列表..."
sudo apt-get update

# 安装Gazebo
echo ""
echo "📦 安装ros-jazzy-ros-gz-sim..."
sudo apt-get install -y ros-jazzy-ros-gz-sim

# 验证安装
echo ""
echo "======================================"
echo "✅ 验证安装..."

if gz sim --version &> /dev/null; then
    echo "✅ Gazebo安装成功!"
    echo ""
    gz sim --version
    echo ""
    echo "======================================"
    echo "🎉 安装完成!"
    echo ""
    echo "现在可以运行:"
    echo "   ./launch_gazebo.sh"
    echo "======================================"
else
    echo "❌ 安装可能失败"
    echo ""
    echo "请手动运行:"
    echo "   sudo apt-get install ros-jazzy-ros-gz-sim"
    echo ""
    echo "或查看详细说明: INSTALL_GAZEBO.md"
    exit 1
fi
