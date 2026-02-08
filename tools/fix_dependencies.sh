#!/bin/bash
# 修复GUI依赖问题

echo "🔧 修复轮腿机器人孪生控制系统依赖"
echo "======================================"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先创建: python3 -m venv venv"
    exit 1
fi

echo "📦 激活虚拟环境..."
source venv/bin/activate

echo ""
echo "📥 安装PyYAML..."
pip install --default-timeout=100 pyyaml || {
    echo "⚠️  PyPI安装失败，尝试使用国内镜像..."
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pyyaml
}

echo ""
echo "📥 安装PyQt5..."
pip install --default-timeout=100 PyQt5 || {
    echo "⚠️  PyPI安装失败，尝试使用国内镜像..."
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple PyQt5
}

echo ""
echo "✅ 验证MuJoCo..."
python -c "import mujoco; print(f'✅ MuJoCo v{mujoco.__version__} 可用')" || {
    echo "❌ MuJoCo未安装，正在安装..."
    pip install mujoco
}

echo ""
echo "🧪 验证所有依赖..."
python -c "
import sys
errors = []

try:
    import PyQt5
    print('✅ PyQt5 可用')
except ImportError as e:
    errors.append(f'PyQt5: {e}')
    print('❌ PyQt5 不可用')

try:
    import yaml
    print('✅ PyYAML 可用')
except ImportError as e:
    errors.append(f'PyYAML: {e}')
    print('❌ PyYAML 不可用')

try:
    import mujoco
    print(f'✅ MuJoCo v{mujoco.__version__} 可用')
except ImportError as e:
    errors.append(f'MuJoCo: {e}')
    print('❌ MuJoCo 不可用')

try:
    import numpy
    print(f'✅ NumPy v{numpy.__version__} 可用')
except ImportError as e:
    errors.append(f'NumPy: {e}')
    print('❌ NumPy 不可用')

if errors:
    print('\n❌ 存在依赖问题:')
    for error in errors:
        print(f'  - {error}')
    sys.exit(1)
else:
    print('\n🎉 所有依赖已正确安装!')
"

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================"
    echo "✅ 依赖修复完成!"
    echo ""
    echo "现在可以启动GUI:"
    echo "  python scripts/launch_main_application.py"
    echo ""
    echo "或运行测试:"
    echo "  python test_mujoco_simple.py"
else
    echo ""
    echo "❌ 依赖修复失败，请查看上面的错误信息"
    exit 1
fi
