#!/usr/bin/env python3
"""
修复 DM 机器人的 STL 文件
将 ASCII STL 转换为 Binary STL，或修复损坏的 STL 文件
"""

import os
import sys
from pathlib import Path

try:
    from stl import mesh
    import numpy as np
except ImportError:
    print("❌ numpy-stl 未安装")
    print("请运行: pip install numpy-stl")
    sys.exit(1)

def check_and_fix_stl(stl_path):
    """检查并修复 STL 文件"""
    
    print(f"🔍 检查文件: {os.path.basename(stl_path)}")
    
    try:
        # 尝试加载 STL 文件
        stl_mesh = mesh.Mesh.from_file(stl_path)
        
        # 检查是否有效
        if len(stl_mesh.vectors) == 0:
            print(f"   ⚠️  文件为空或损坏")
            return False
        
        # 保存为 Binary 格式
        backup_path = stl_path + ".backup"
        if not os.path.exists(backup_path):
            os.rename(stl_path, backup_path)
            print(f"   💾 备份原文件: {os.path.basename(backup_path)}")
        
        # 保存为 Binary STL（默认就是 Binary）
        stl_mesh.save(stl_path)
        print(f"   ✅ 转换为 Binary STL")
        print(f"   📊 三角面数: {len(stl_mesh.vectors)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 处理失败: {e}")
        return False

def main():
    # 获取项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # DM 机器人 mesh 目录
    dm_mesh_dir = project_root / "src/model/DM_Wheel_leg_robot/meshes"
    
    print("🔧 修复 DM 机器人 STL 文件")
    print("=" * 60)
    print(f"Mesh 目录: {dm_mesh_dir}")
    print()
    
    if not dm_mesh_dir.exists():
        print(f"❌ 目录不存在: {dm_mesh_dir}")
        return 1
    
    # 获取所有 STL 文件
    stl_files = list(dm_mesh_dir.glob("*.STL"))
    
    if not stl_files:
        print("❌ 未找到 STL 文件")
        return 1
    
    print(f"找到 {len(stl_files)} 个 STL 文件")
    print()
    
    # 处理每个文件
    success_count = 0
    for stl_file in stl_files:
        if check_and_fix_stl(str(stl_file)):
            success_count += 1
        print()
    
    print("=" * 60)
    print(f"✅ 成功处理 {success_count}/{len(stl_files)} 个文件")
    
    if success_count == len(stl_files):
        print()
        print("💡 现在可以重新运行转换:")
        print("   python3 tools/test_wiki_mjcf.py")
    
    return 0 if success_count == len(stl_files) else 1

if __name__ == "__main__":
    sys.exit(main())
