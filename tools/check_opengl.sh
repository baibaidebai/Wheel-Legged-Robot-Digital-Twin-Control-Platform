#!/bin/bash
# OpenGL和渲染环境检查脚本

echo "🔍 OpenGL和渲染环境检查"
echo "======================================"
echo ""

# 检查glxinfo
echo "1️⃣ 检查glxinfo工具..."
if ! command -v glxinfo &> /dev/null; then
    echo "   ❌ glxinfo未安装"
    echo ""
    echo "   安装命令:"
    echo "   sudo apt-get install mesa-utils"
    echo ""
    GLXINFO_AVAILABLE=false
else
    echo "   ✅ glxinfo已安装"
    GLXINFO_AVAILABLE=true
fi
echo ""

# 检查OpenGL版本
if [ "$GLXINFO_AVAILABLE" = true ]; then
    echo "2️⃣ 检查OpenGL版本..."
    OPENGL_VERSION=$(glxinfo | grep "OpenGL version" | head -1)
    if [ -z "$OPENGL_VERSION" ]; then
        echo "   ❌ 无法获取OpenGL版本"
    else
        echo "   $OPENGL_VERSION"
        
        # 检查版本是否足够
        VERSION_NUM=$(echo "$OPENGL_VERSION" | grep -oP '\d+\.\d+' | head -1)
        if [ -n "$VERSION_NUM" ]; then
            MAJOR=$(echo "$VERSION_NUM" | cut -d. -f1)
            MINOR=$(echo "$VERSION_NUM" | cut -d. -f2)
            
            if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 3 ]; then
                echo "   ✅ OpenGL版本足够（需要3.3+）"
            else
                echo "   ⚠️  OpenGL版本较低（建议3.3+）"
            fi
        fi
    fi
    echo ""
    
    # 检查渲染器
    echo "3️⃣ 检查OpenGL渲染器..."
    RENDERER=$(glxinfo | grep "OpenGL renderer" | head -1)
    if [ -z "$RENDERER" ]; then
        echo "   ❌ 无法获取渲染器信息"
    else
        echo "   $RENDERER"
        
        # 检查是否是软件渲染
        if echo "$RENDERER" | grep -qi "llvmpipe\|software\|swrast"; then
            echo "   ⚠️  使用软件渲染（性能较低但稳定）"
        elif echo "$RENDERER" | grep -qi "vmware\|virtualbox"; then
            echo "   ⚠️  虚拟机渲染器（可能需要软件渲染模式）"
        else
            echo "   ✅ 硬件渲染器"
        fi
    fi
    echo ""
    
    # 检查直接渲染
    echo "4️⃣ 检查直接渲染..."
    DIRECT_RENDERING=$(glxinfo | grep "direct rendering" | head -1)
    if [ -z "$DIRECT_RENDERING" ]; then
        echo "   ❌ 无法获取直接渲染信息"
    else
        echo "   $DIRECT_RENDERING"
    fi
    echo ""
fi

# 检查环境变量
echo "5️⃣ 检查渲染相关环境变量..."
if [ -n "$LIBGL_ALWAYS_SOFTWARE" ]; then
    echo "   LIBGL_ALWAYS_SOFTWARE=$LIBGL_ALWAYS_SOFTWARE"
    echo "   ✅ 软件渲染已启用"
else
    echo "   LIBGL_ALWAYS_SOFTWARE未设置"
    echo "   ⚠️  使用硬件渲染（虚拟机中可能闪屏）"
fi

if [ -n "$MESA_GL_VERSION_OVERRIDE" ]; then
    echo "   MESA_GL_VERSION_OVERRIDE=$MESA_GL_VERSION_OVERRIDE"
fi

if [ -n "$GALLIUM_DRIVER" ]; then
    echo "   GALLIUM_DRIVER=$GALLIUM_DRIVER"
fi
echo ""

# 检查显示服务器
echo "6️⃣ 检查显示服务器..."
if [ -n "$WAYLAND_DISPLAY" ]; then
    echo "   ✅ Wayland显示服务器"
    echo "   Display: $WAYLAND_DISPLAY"
elif [ -n "$DISPLAY" ]; then
    echo "   ✅ X11显示服务器"
    echo "   Display: $DISPLAY"
else
    echo "   ❌ 没有检测到显示服务器"
fi
echo ""

# 检查虚拟机环境
echo "7️⃣ 检查虚拟机环境..."
if command -v systemd-detect-virt &> /dev/null; then
    VIRT=$(systemd-detect-virt)
    if [ "$VIRT" = "none" ]; then
        echo "   ✅ 物理机环境"
    else
        echo "   ⚠️  虚拟机环境: $VIRT"
        echo "   建议使用软件渲染模式"
    fi
else
    # 备用检测方法
    if grep -qi "vmware\|virtualbox\|qemu\|kvm" /proc/cpuinfo 2>/dev/null; then
        echo "   ⚠️  可能是虚拟机环境"
        echo "   建议使用软件渲染模式"
    else
        echo "   ✅ 可能是物理机环境"
    fi
fi
echo ""

# 诊断结果和建议
echo "======================================"
echo "📊 诊断结果和建议"
echo "======================================"
echo ""

# 判断是否需要软件渲染
NEED_SOFTWARE_RENDERING=false

if [ "$GLXINFO_AVAILABLE" = true ]; then
    if echo "$RENDERER" | grep -qi "vmware\|virtualbox\|llvmpipe"; then
        NEED_SOFTWARE_RENDERING=true
    fi
fi

if systemd-detect-virt &> /dev/null && [ "$(systemd-detect-virt)" != "none" ]; then
    NEED_SOFTWARE_RENDERING=true
fi

if [ "$NEED_SOFTWARE_RENDERING" = true ]; then
    echo "⚠️  检测到虚拟机环境或软件渲染"
    echo ""
    echo "🔧 建议使用软件渲染模式启动Gazebo："
    echo ""
    echo "   方法1（推荐）："
    echo "   ./launch_gazebo_safe.sh"
    echo ""
    echo "   方法2："
    echo "   ./launch_gazebo_simple.sh"
    echo ""
    echo "   方法3（手动设置）："
    echo "   export LIBGL_ALWAYS_SOFTWARE=1"
    echo "   ./launch_gazebo.sh"
    echo ""
    echo "📚 详细说明："
    echo "   查看 GAZEBO_FLICKERING_FIX.md"
else
    echo "✅ 渲染环境良好"
    echo ""
    echo "可以直接使用标准模式："
    echo "   ./launch_gazebo.sh"
    echo ""
    echo "如果遇到闪屏问题，使用安全模式："
    echo "   ./launch_gazebo_safe.sh"
fi

echo ""
echo "======================================"
