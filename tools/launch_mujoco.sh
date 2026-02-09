#!/bin/bash
# MuJoCo启动脚本

echo "🚀 MuJoCo仿真启动器"
echo "======================================"
echo ""

# 检查MuJoCo
if ! python3 -c "import mujoco" 2>/dev/null; then
    echo "❌ MuJoCo未安装"
    echo ""
    echo "安装命令:"
    echo "   pip install mujoco"
    exit 1
fi

# 显示版本
MUJOCO_VERSION=$(python3 -c "import mujoco; print(mujoco.__version__)")
echo "✅ MuJoCo版本: $MUJOCO_VERSION"
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
        MODEL="rm"
        MODEL_NAME="RM串联轮腿机器人"
        ;;
    2)
        MODEL="dm"
        MODEL_NAME="DM轮腿机器人"
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo "✅ 已选择: $MODEL_NAME"
echo ""
echo "======================================"
echo "🎨 启动MuJoCo..."
echo "======================================"
echo ""

# 启动MuJoCo
python3 tools/launch_mujoco.py --model $MODEL

echo ""
echo "👋 感谢使用!"
