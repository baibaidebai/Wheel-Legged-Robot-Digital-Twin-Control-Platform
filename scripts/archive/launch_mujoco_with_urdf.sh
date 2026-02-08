#!/bin/bash
# 使用修复后的URDF启动MuJoCo

echo "🚀 MuJoCo + 真实URDF模型"
echo "======================================"

# 1. 修复URDF
echo "🔧 步骤1: 修复URDF mesh路径..."
python3 fix_urdf_for_mujoco.py <<< "1"

if [ $? -ne 0 ]; then
    echo "❌ URDF修复失败"
    exit 1
fi

echo ""
echo "======================================"
echo "🎨 步骤2: 启动MuJoCo..."
echo "======================================"

# 2. 使用修复后的URDF启动MuJoCo
export URDF_PATH="src/model/RM_Serial_Wheeled-leg_Robot/urdf/RM_Serial_Wheeled-leg_Robot_mujoco_fixed.urdf"

python3 << 'EOF'
import sys
import os

# 设置路径
venv_site_packages = os.path.join(os.getcwd(), 'venv/lib/python3.12/site-packages')
sys.path.insert(0, venv_site_packages)

import mujoco
import mujoco.viewer
import numpy as np

urdf_path = os.environ.get('URDF_PATH')

print(f"\n📥 加载URDF: {urdf_path}")

try:
    # 加载模型
    model = mujoco.MjModel.from_xml_path(urdf_path)
    data = mujoco.MjData(model)
    
    print(f"✅ 模型加载成功!")
    print(f"   关节数: {model.njnt}")
    print(f"   体数: {model.nbody}")
    print(f"   网格数: {model.nmesh}")
    
    if model.nmesh > 0:
        print(f"   ✅ 成功加载 {model.nmesh} 个STL网格文件!")
    
    print("\n🎨 启动MuJoCo查看器...")
    print("=" * 60)
    print("💡 控制说明:")
    print("   - 鼠标左键拖动: 旋转视角")
    print("   - 鼠标右键拖动: 平移视角")
    print("   - 鼠标滚轮: 缩放")
    print("   - 空格键: 暂停/继续")
    print("   - Esc: 退出")
    print("=" * 60)
    
    # 启动查看器
    with mujoco.viewer.launch_passive(model, data) as viewer:
        viewer.cam.distance = 2.0
        viewer.cam.elevation = -20
        viewer.cam.azimuth = 45
        
        step_count = 0
        while viewer.is_running():
            mujoco.mj_step(model, data)
            
            # 简单控制
            if model.nu > 0:
                for i in range(min(4, model.nu)):
                    data.ctrl[i] = 0.3 * np.sin(data.time * 1.5 + i * np.pi / 2)
            
            viewer.sync()
            step_count += 1
            
            if step_count % 1000 == 0:
                print(f"⏱️  时间: {data.time:.2f}s")

except KeyboardInterrupt:
    print("\n⏹️  用户中断")
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print("\n👋 感谢使用!")
EOF
