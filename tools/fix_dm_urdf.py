#!/usr/bin/env python3
"""
修复DM机器人URDF文件的网格路径
将 package://wheel_leg_description/meshes/ 替换为相对路径
"""

import os
import sys

def fix_urdf(urdf_path):
    """修复URDF文件中的网格路径"""
    
    # 读取URDF文件
    with open(urdf_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 备份原文件
    backup_path = urdf_path + '.backup'
    if not os.path.exists(backup_path):
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 已备份原文件: {backup_path}")
    
    # 替换package://路径为相对路径
    # package://wheel_leg_description/meshes/xxx.STL -> ../meshes/xxx.STL
    content = content.replace(
        'package://wheel_leg_description/meshes/',
        '../meshes/'
    )
    
    # 写入修复后的文件
    with open(urdf_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 已修复URDF文件: {urdf_path}")
    print(f"   package://wheel_leg_description/meshes/ -> ../meshes/")
    
    return True

def main():
    # DM机器人URDF路径
    urdf_path = "src/model/DM_Wheel_leg_robot/urdf/wheel_legged_urdf_pkg.urdf"
    
    if not os.path.exists(urdf_path):
        print(f"❌ URDF文件不存在: {urdf_path}")
        return 1
    
    print("🔧 修复DM机器人URDF文件")
    print("=" * 50)
    print()
    
    # 检查meshes目录
    meshes_dir = "src/model/DM_Wheel_leg_robot/meshes"
    if not os.path.exists(meshes_dir):
        print(f"❌ Meshes目录不存在: {meshes_dir}")
        return 1
    
    # 列出STL文件
    stl_files = [f for f in os.listdir(meshes_dir) if f.endswith('.STL')]
    print(f"📦 找到 {len(stl_files)} 个STL文件:")
    for stl in sorted(stl_files):
        print(f"   - {stl}")
    print()
    
    # 修复URDF
    if fix_urdf(urdf_path):
        print()
        print("=" * 50)
        print("🎉 修复完成!")
        print()
        print("现在可以运行:")
        print("   ./launch_gazebo_safe.sh")
        print()
        print("选择模型 2 (DM_Wheel_leg_robot)")
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
