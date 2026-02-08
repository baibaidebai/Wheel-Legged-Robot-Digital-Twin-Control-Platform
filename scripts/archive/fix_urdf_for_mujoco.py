#!/usr/bin/env python3
"""
修复URDF文件以便MuJoCo可以正确加载

将相对mesh路径转换为绝对路径
"""

import os
import re
import sys
from pathlib import Path

print("🔧 URDF修复工具 - 为MuJoCo准备")
print("=" * 60)

# 选择模型
print("\n📦 可用的机器人模型:")
models = {
    '1': {
        'name': 'RM_Serial_Wheeled-leg_Robot',
        'urdf_path': 'src/model/RM_Serial_Wheeled-leg_Robot/urdf/RM_Serial_Wheeled-leg_Robot.urdf',
    },
    '2': {
        'name': 'DM_Wheel_leg_robot',
        'urdf_path': 'src/model/DM_Wheel_leg_robot/urdf/wheel_legged_urdf_pkg.urdf',
    }
}

for key, model in models.items():
    status = "✅" if Path(model['urdf_path']).exists() else "❌"
    print(f"  {key}. {status} {model['name']}")

choice = input("\n请选择模型 (1-2) [默认: 1]: ").strip() or '1'

if choice not in models:
    print(f"❌ 无效选择")
    sys.exit(1)

selected_model = models[choice]
urdf_path = selected_model['urdf_path']

print(f"\n✅ 已选择: {selected_model['name']}")
print(f"   原始URDF: {urdf_path}")

if not os.path.exists(urdf_path):
    print(f"❌ 文件不存在")
    sys.exit(1)

# 读取URDF
with open(urdf_path, 'r', encoding='utf-8') as f:
    urdf_content = f.read()

# 获取mesh目录的绝对路径
model_dir = os.path.dirname(os.path.dirname(os.path.abspath(urdf_path)))
meshes_dir = os.path.join(model_dir, 'meshes')

print(f"   Mesh目录: {meshes_dir}")

# 检查mesh文件是否存在
if not os.path.exists(meshes_dir):
    print(f"❌ Mesh目录不存在: {meshes_dir}")
    sys.exit(1)

mesh_files = list(Path(meshes_dir).glob('*.STL'))
print(f"   找到 {len(mesh_files)} 个mesh文件")

# 修复mesh路径
print("\n🔧 修复mesh路径...")

# 方法1: 替换../meshes/为绝对路径
modified_content = re.sub(
    r'filename="\.\.\/meshes\/',
    f'filename="{meshes_dir}/',
    urdf_content
)

# 方法2: 替换package://路径
modified_content = re.sub(
    r'filename="package://[^/]+/meshes/',
    f'filename="{meshes_dir}/',
    modified_content
)

# 统计修改
original_matches = len(re.findall(r'filename="[^"]*meshes/', urdf_content))
print(f"   修改了 {original_matches} 个mesh引用")

# 保存修复后的URDF
output_path = urdf_path.replace('.urdf', '_mujoco_fixed.urdf')
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(modified_content)

print(f"\n✅ 修复完成!")
print(f"   输出文件: {output_path}")

# 显示前几个mesh路径作为示例
print("\n📋 示例mesh路径:")
mesh_refs = re.findall(r'filename="([^"]+\.STL)"', modified_content)
for i, ref in enumerate(mesh_refs[:3]):
    print(f"   {i+1}. {ref}")
    # 检查文件是否存在
    if os.path.exists(ref):
        print(f"      ✅ 文件存在")
    else:
        print(f"      ❌ 文件不存在")

if len(mesh_refs) > 3:
    print(f"   ... 还有 {len(mesh_refs) - 3} 个")

print("\n" + "=" * 60)
print("🎉 现在可以使用修复后的URDF启动MuJoCo了!")
print(f"\n💡 使用方法:")
print(f"   python3 launch_mujoco_with_fixed_urdf.py")
print("=" * 60)
