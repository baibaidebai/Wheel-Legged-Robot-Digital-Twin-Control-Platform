#!/usr/bin/env python3
"""
项目精简脚本
删除非必要文件，整合重复文档
"""

import os
import shutil
from pathlib import Path

def cleanup_project():
    """精简项目"""
    
    project_root = Path(__file__).parent.parent
    
    print("🧹 开始精简项目")
    print("=" * 60)
    
    # 1. 删除备份文件
    print("\n📦 删除备份文件...")
    backup_patterns = ['*.backup', '*.original', '*_temp.urdf', '*_mujoco_temp.urdf']
    deleted_count = 0
    
    for pattern in backup_patterns:
        for file in project_root.rglob(pattern):
            print(f"   删除: {file.relative_to(project_root)}")
            file.unlink()
            deleted_count += 1
    
    print(f"   ✅ 删除了 {deleted_count} 个备份文件")
    
    # 2. 删除废弃的文档
    print("\n📄 删除废弃/重复的文档...")
    docs_to_remove = [
        'docs/archive',  # 归档文档
        'docs/gui_mujoco_refactor_summary.md',  # 已整合到新文档
        'docs/ppo_implementation_summary.md',  # 可选，如果不需要
        'docs/ppo_training_guide.md',  # 可选
        'docs/main_application_guide.md',  # 可选
        'docs/quick_start_mujoco_gui.md',  # 已整合
        'docs/ros2_gui_integration_guide.md',  # 可选
    ]
    
    for doc_path in docs_to_remove:
        full_path = project_root / doc_path
        if full_path.exists():
            if full_path.is_dir():
                shutil.rmtree(full_path)
                print(f"   删除目录: {doc_path}")
            else:
                full_path.unlink()
                print(f"   删除文件: {doc_path}")
    
    # 3. 删除废弃的脚本
    print("\n🔧 删除废弃的脚本...")
    scripts_to_remove = [
        'scripts/archive',  # 归档脚本
        'tools/launch_mujoco_simple.py',  # 简化版，不再需要
    ]
    
    for script_path in scripts_to_remove:
        full_path = project_root / script_path
        if full_path.exists():
            if full_path.is_dir():
                shutil.rmtree(full_path)
                print(f"   删除目录: {script_path}")
            else:
                full_path.unlink()
                print(f"   删除文件: {script_path}")
    
    # 4. 整合 MuJoCo 文档
    print("\n📚 整合 MuJoCo 文档...")
    
    # 创建统一的 MuJoCo 文档
    mujoco_doc = project_root / 'docs/MUJOCO_GUIDE.md'
    
    if not mujoco_doc.exists():
        print("   创建统一的 MuJoCo 指南...")
        # 这里可以整合多个文档的内容
        # 暂时保留原有文档
    
    # 5. 清理 Python 缓存
    print("\n🗑️  清理 Python 缓存...")
    cache_count = 0
    for pycache in project_root.rglob('__pycache__'):
        shutil.rmtree(pycache)
        cache_count += 1
    
    for pyc in project_root.rglob('*.pyc'):
        pyc.unlink()
        cache_count += 1
    
    print(f"   ✅ 清理了 {cache_count} 个缓存文件/目录")
    
    # 6. 清理测试数据（可选）
    print("\n📊 检查测试数据...")
    test_data_dir = project_root / 'test_data'
    if test_data_dir.exists():
        print(f"   保留测试数据目录: test_data/")
    
    # 7. 整合重复的 MJCF 文件
    print("\n🔄 检查重复的 MJCF 文件...")
    for model_dir in (project_root / 'src/model').iterdir():
        if model_dir.is_dir():
            mjcf_dir = model_dir / 'mjcf'
            if mjcf_dir.exists():
                mjcf_files = list(mjcf_dir.glob('*.xml'))
                if len(mjcf_files) > 1:
                    print(f"   {model_dir.name}: {len(mjcf_files)} 个 MJCF 文件")
                    for f in mjcf_files:
                        print(f"      - {f.name}")
    
    print("\n" + "=" * 60)
    print("✅ 项目精简完成!")
    print("\n💡 建议:")
    print("   1. 检查删除的文件是否正确")
    print("   2. 运行测试确保功能正常")
    print("   3. 提交精简后的版本")

if __name__ == "__main__":
    cleanup_project()
