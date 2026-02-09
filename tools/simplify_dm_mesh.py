#!/usr/bin/env python3
"""
简化 DM 机器人的复杂 mesh 文件
将三角面数减少到 MuJoCo 的限制以下（200,000）
"""

import os
import sys
from pathlib import Path

try:
    import pymeshlab
    from stl import mesh
except ImportError:
    print("❌ 缺少依赖库")
    print("请运行: pip install pymeshlab numpy-stl")
    sys.exit(1)

def simplify_mesh(input_path, output_path, target_faces=150000):
    """简化 mesh 文件"""
    
    print(f"🔧 简化: {os.path.basename(input_path)}")
    
    try:
        # 加载原始 mesh
        original_mesh = mesh.Mesh.from_file(input_path)
        original_faces = len(original_mesh.vectors)
        print(f"   原始三角面数: {original_faces:,}")
        
        if original_faces <= 200000:
            print(f"   ✅ 无需简化（在限制内）")
            return True
        
        # 使用 PyMeshLab 简化
        ms = pymeshlab.MeshSet()
        ms.load_new_mesh(input_path)
        
        # 计算简化比例
        reduction_ratio = target_faces / original_faces
        print(f"   目标三角面数: {target_faces:,}")
        print(f"   简化比例: {reduction_ratio:.2%}")
        
        # 应用简化算法
        ms.meshing_decimation_quadric_edge_collapse(
            targetfacenum=target_faces,
            preserveboundary=True,
            preservenormal=True,
            preservetopology=True
        )
        
        # 保存简化后的 mesh
        ms.save_current_mesh(output_path)
        
        # 验证结果
        simplified_mesh = mesh.Mesh.from_file(output_path)
        simplified_faces = len(simplified_mesh.vectors)
        print(f"   简化后三角面数: {simplified_faces:,}")
        print(f"   ✅ 简化成功")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 简化失败: {e}")
        return False

def main():
    # 获取项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # DM 机器人 mesh 目录
    dm_mesh_dir = project_root / "src/model/DM_Wheel_leg_robot/meshes"
    
    print("🔧 简化 DM 机器人复杂 Mesh")
    print("=" * 60)
    print(f"Mesh 目录: {dm_mesh_dir}")
    print()
    
    if not dm_mesh_dir.exists():
        print(f"❌ 目录不存在: {dm_mesh_dir}")
        return 1
    
    # 需要简化的文件列表
    files_to_simplify = [
        ("base_link.STL", 150000),  # 从 573,210 减少到 150,000
    ]
    
    success_count = 0
    for filename, target_faces in files_to_simplify:
        input_path = dm_mesh_dir / filename
        
        if not input_path.exists():
            print(f"⚠️  文件不存在: {filename}")
            continue
        
        # 备份原文件
        backup_path = dm_mesh_dir / (filename + ".original")
        if not backup_path.exists():
            import shutil
            shutil.copy2(input_path, backup_path)
            print(f"💾 备份原文件: {backup_path.name}")
        
        # 简化并覆盖原文件
        if simplify_mesh(str(input_path), str(input_path), target_faces):
            success_count += 1
        print()
    
    print("=" * 60)
    print(f"✅ 成功简化 {success_count}/{len(files_to_simplify)} 个文件")
    
    if success_count == len(files_to_simplify):
        print()
        print("💡 现在可以重新运行转换:")
        print("   python3 tools/test_wiki_mjcf.py")
    
    return 0 if success_count == len(files_to_simplify) else 1

if __name__ == "__main__":
    sys.exit(main())
