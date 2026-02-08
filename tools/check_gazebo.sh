#!/bin/bash
# Gazebo安装检查脚本

echo "🔍 Gazebo安装检查"
echo "======================================"
echo ""

# 检查ROS2
echo "1️⃣ 检查ROS2..."
if [ -f "/opt/ros/jazzy/setup.bash" ]; then
    source /opt/ros/jazzy/setup.bash
    echo "   ✅ ROS2 Jazzy已安装"
else
    echo "   ❌ ROS2 Jazzy未安装"
fi
echo ""

# 检查gz命令
echo "2️⃣ 检查gz命令..."
if command -v gz &> /dev/null; then
    echo "   ✅ gz命令存在"
    gz --version 2>/dev/null || echo "   版本: $(gz --version 2>&1 | head -1)"
else
    echo "   ❌ gz命令不存在"
fi
echo ""

# 检查gz sim
echo "3️⃣ 检查gz sim..."
if gz sim --help &> /dev/null; then
    echo "   ✅ gz sim可用"
    gz sim --version 2>/dev/null || echo "   Gazebo仿真器已安装"
else
    echo "   ❌ gz sim不可用"
    echo "   ⚠️  这是问题所在！"
fi
echo ""

# 检查已安装的Gazebo包
echo "4️⃣ 检查已安装的Gazebo包..."
GAZEBO_PACKAGES=$(dpkg -l | grep -E "gz-|gazebo" | grep "^ii" | awk '{print $2}')
if [ -z "$GAZEBO_PACKAGES" ]; then
    echo "   ❌ 没有安装Gazebo包"
else
    echo "   已安装的包:"
    echo "$GAZEBO_PACKAGES" | while read pkg; do
        echo "   - $pkg"
    done
fi
echo ""

# 检查ROS2 Gazebo包
echo "5️⃣ 检查ROS2 Gazebo集成包..."
ROS_GZ_PACKAGES=$(dpkg -l | grep "ros-jazzy-.*gz" | grep "^ii" | awk '{print $2}')
if [ -z "$ROS_GZ_PACKAGES" ]; then
    echo "   ❌ 没有安装ROS2 Gazebo包"
else
    echo "   已安装的包:"
    echo "$ROS_GZ_PACKAGES" | while read pkg; do
        echo "   - $pkg"
    done
fi
echo ""

# 诊断结果
echo "======================================"
echo "📊 诊断结果"
echo "======================================"
echo ""

if gz sim --help &> /dev/null; then
    echo "✅ Gazebo已正确安装，可以使用！"
    echo ""
    echo "运行以下命令启动仿真:"
    echo "   ./launch_gazebo.sh"
else
    echo "❌ Gazebo未正确安装"
    echo ""
    echo "🔧 解决方案："
    echo ""
    echo "方法1（推荐）- 自动安装:"
    echo "   ./install_gazebo.sh"
    echo ""
    echo "方法2 - 手动安装:"
    echo "   sudo apt-get update"
    echo "   sudo apt-get install ros-jazzy-ros-gz-sim"
    echo ""
    echo "方法3 - 安装完整版:"
    echo "   sudo apt-get install ros-jazzy-ros-gz"
    echo ""
    echo "详细说明请查看: INSTALL_GAZEBO.md"
fi
echo ""
echo "======================================"
