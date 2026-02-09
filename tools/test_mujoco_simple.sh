#!/bin/bash
# 简单测试MuJoCo启动

echo "🧪 测试MuJoCo启动"
echo "======================================"
echo ""

# 检查MuJoCo
if ! python3 -c "import mujoco" 2>/dev/null; then
    echo "❌ MuJoCo未安装"
    echo "   pip install mujoco"
    exit 1
fi

echo "✅ MuJoCo已安装"
echo ""

# 查找MJCF文件
MJCF_FILE="src/model/RM_Serial_Wheeled-leg_Robot/mjcf/RM_Serial_Wheeled-leg_Robot_wiki.xml"

if [ ! -f "$MJCF_FILE" ]; then
    echo "❌ MJCF文件不存在: $MJCF_FILE"
    exit 1
fi

echo "✅ MJCF文件存在: $MJCF_FILE"
echo ""

echo "🚀 启动MuJoCo Viewer..."
echo "   (窗口将打开，按ESC或关闭窗口退出)"
echo ""

# 启动MuJoCo
python3 -m mujoco.viewer --mjcf="$MJCF_FILE"

echo ""
echo "👋 MuJoCo已关闭"
