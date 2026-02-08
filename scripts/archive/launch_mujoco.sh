#!/bin/bash
# 直接启动MuJoCo查看器 - 避免GUI问题

echo "🚀 启动MuJoCo直接查看器"
echo "======================================"

# 设置Python路径
export PYTHONPATH="$PWD/src/wheel_legged_control:$PWD/venv/lib/python3.12/site-packages:$PYTHONPATH"

# 检查MuJoCo
python3 -c "import mujoco; print('✅ MuJoCo v' + mujoco.__version__)" || {
    echo "❌ MuJoCo不可用"
    exit 1
}

echo ""
echo "启动MuJoCo交互式查看器..."
echo "======================================"

python3 launch_mujoco_direct.py
