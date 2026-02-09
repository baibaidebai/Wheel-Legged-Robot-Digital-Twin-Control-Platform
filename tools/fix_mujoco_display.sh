#!/bin/bash
# MuJoCo显示问题快速修复脚本

echo "🔧 MuJoCo显示问题修复工具"
echo "======================================"
echo ""

# 检查是否在虚拟机中
echo "📋 系统信息:"
echo "  会话类型: $XDG_SESSION_TYPE"
echo "  显示: $DISPLAY"
echo ""

# 安装必要的库
echo "📦 安装必要的库..."
sudo apt-get update
sudo apt-get install -y libglfw3 libglew-dev mesa-utils

echo ""
echo "✅ 库安装完成"
echo ""

# 检查会话类型
if [ "$XDG_SESSION_TYPE" = "wayland" ]; then
    echo "⚠️  检测到Wayland会话"
    echo ""
    echo "MuJoCo在Wayland下可能无法正常显示。"
    echo ""
    echo "解决方案："
    echo ""
    echo "方案1: 切换到X11（推荐）"
    echo "  1. 注销当前会话"
    echo "  2. 在登录界面点击右下角齿轮图标"
    echo "  3. 选择 'Ubuntu on Xorg'"
    echo "  4. 重新登录"
    echo ""
    echo "方案2: 使用软件渲染（临时）"
    echo "  export MUJOCO_GL=osmesa"
    echo "  python3 tools/launch_mujoco.py --model rm --render osmesa"
    echo ""
    
    read -p "是否现在注销切换到X11? (y/n): " switch
    if [ "$switch" = "y" ] || [ "$switch" = "Y" ]; then
        echo "正在注销..."
        gnome-session-quit --logout --no-prompt
    fi
else
    echo "✅ 使用X11会话"
    echo ""
    echo "尝试启动MuJoCo:"
    echo "  python3 tools/launch_mujoco.py --model rm"
fi

echo ""
echo "======================================"
echo "💡 其他建议（虚拟机用户）:"
echo "======================================"
echo ""
echo "1. VMware设置:"
echo "   - 虚拟机 → 设置 → 显示"
echo "   - 启用 '加速3D图形'"
echo "   - 图形内存设置为 2GB 或更高"
echo ""
echo "2. 安装VMware Tools:"
echo "   - 虚拟机 → 安装VMware Tools"
echo "   - 按照提示完成安装"
echo ""
echo "3. 测试命令:"
echo "   python3 tools/diagnose_mujoco.py  # 诊断"
echo "   python3 tools/launch_mujoco.py --model rm  # 启动"
echo ""
