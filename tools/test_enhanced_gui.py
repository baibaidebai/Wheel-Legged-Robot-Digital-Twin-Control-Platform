#!/usr/bin/env python3
"""
增强版GUI测试脚本
验证所有功能是否正常工作
"""

import sys
import os
from pathlib import Path

def test_imports():
    """测试必要的导入"""
    print("🧪 测试1: 检查Python模块...")
    
    try:
        import tkinter
        print("  ✅ tkinter 可用")
    except ImportError:
        print("  ❌ tkinter 不可用")
        print("     安装: sudo apt-get install python3-tk")
        return False
    
    try:
        from tkinter import ttk, messagebox, filedialog
        print("  ✅ tkinter子模块 可用")
    except ImportError:
        print("  ❌ tkinter子模块 不可用")
        return False
    
    return True

def test_project_structure():
    """测试项目结构"""
    print("\n🧪 测试2: 检查项目结构...")
    
    project_root = Path(__file__).parent.parent
    
    # 检查关键目录
    required_dirs = [
        "src/model",
        "src/wheel_legged_control/worlds",
        "tools"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"  ✅ {dir_path} 存在")
        else:
            print(f"  ❌ {dir_path} 不存在")
            all_exist = False
    
    return all_exist

def test_model_folders():
    """测试模型文件夹"""
    print("\n🧪 测试3: 扫描模型文件夹...")
    
    project_root = Path(__file__).parent.parent
    model_base = project_root / "src" / "model"
    
    if not model_base.exists():
        print("  ❌ 模型目录不存在")
        return False
    
    model_folders = [f for f in model_base.iterdir() if f.is_dir() and not f.name.startswith('.')]
    
    if not model_folders:
        print("  ❌ 没有找到模型文件夹")
        return False
    
    print(f"  ✅ 找到 {len(model_folders)} 个模型文件夹:")
    for folder in model_folders:
        print(f"     - {folder.name}")
        
        # 检查子目录
        urdf_dir = folder / "urdf"
        mjcf_dir = folder / "mjcf"
        meshes_dir = folder / "meshes"
        
        if urdf_dir.exists():
            urdf_files = list(urdf_dir.glob("*.urdf"))
            print(f"       URDF: {len(urdf_files)} 个文件")
        
        if mjcf_dir.exists():
            mjcf_files = list(mjcf_dir.glob("*.xml"))
            print(f"       MJCF: {len(mjcf_files)} 个文件")
        
        if meshes_dir.exists():
            mesh_files = list(meshes_dir.glob("*.STL"))
            print(f"       Meshes: {len(mesh_files)} 个文件")
    
    return True

def test_world_files():
    """测试世界文件"""
    print("\n🧪 测试4: 扫描世界文件...")
    
    project_root = Path(__file__).parent.parent
    world_base = project_root / "src" / "wheel_legged_control" / "worlds"
    
    if not world_base.exists():
        print("  ⚠️  世界文件目录不存在")
        return True  # 不是必需的
    
    world_files = list(world_base.glob("*.world"))
    
    if not world_files:
        print("  ⚠️  没有找到世界文件")
        return True  # 不是必需的
    
    print(f"  ✅ 找到 {len(world_files)} 个世界文件:")
    for file in world_files:
        print(f"     - {file.name}")
    
    return True

def test_launch_scripts():
    """测试启动脚本"""
    print("\n🧪 测试5: 检查启动脚本...")
    
    project_root = Path(__file__).parent.parent
    
    scripts = [
        "launch.sh",
        "launch_enhanced.sh",
        "tools/launch_gazebo_safe.sh",
        "tools/launch_gazebo_simple.sh",
        "tools/launch_gazebo.sh",
        "tools/launch_mujoco.sh",
        "tools/launch_mujoco.py",
        "tools/launch_gazebo_gui.py",
        "tools/launch_gui_enhanced.py"
    ]
    
    all_exist = True
    for script in scripts:
        script_path = project_root / script
        if script_path.exists():
            # 检查是否可执行
            if script.endswith('.sh'):
                if os.access(script_path, os.X_OK):
                    print(f"  ✅ {script} (可执行)")
                else:
                    print(f"  ⚠️  {script} (不可执行)")
            else:
                print(f"  ✅ {script}")
        else:
            print(f"  ❌ {script} 不存在")
            all_exist = False
    
    return all_exist

def test_mujoco():
    """测试MuJoCo"""
    print("\n🧪 测试6: 检查MuJoCo...")
    
    try:
        import mujoco
        print(f"  ✅ MuJoCo {mujoco.__version__} 已安装")
        return True
    except ImportError:
        print("  ⚠️  MuJoCo 未安装")
        print("     安装: pip install mujoco")
        return True  # 不是必需的

def test_gui_launch():
    """测试GUI启动（不实际启动）"""
    print("\n🧪 测试7: 验证GUI代码...")
    
    project_root = Path(__file__).parent.parent
    gui_file = project_root / "tools" / "launch_gui_enhanced.py"
    
    if not gui_file.exists():
        print("  ❌ GUI文件不存在")
        return False
    
    try:
        # 尝试编译Python文件
        with open(gui_file, 'r', encoding='utf-8') as f:
            code = f.read()
        
        compile(code, str(gui_file), 'exec')
        print("  ✅ GUI代码语法正确")
        return True
    except SyntaxError as e:
        print(f"  ❌ GUI代码语法错误: {e}")
        return False

def print_summary(results):
    """打印测试总结"""
    print("\n" + "="*50)
    print("📊 测试总结")
    print("="*50)
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\n总测试数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {total - passed}")
    
    if passed == total:
        print("\n✅ 所有测试通过！增强版GUI可以正常使用。")
        print("\n启动命令:")
        print("  ./launch_enhanced.sh")
        return True
    else:
        print("\n⚠️  部分测试失败，请检查上述错误。")
        print("\n失败的测试:")
        for test_name, result in results.items():
            if not result:
                print(f"  ❌ {test_name}")
        return False

def main():
    print("="*50)
    print("🧪 增强版GUI测试")
    print("="*50)
    
    results = {}
    
    # 运行所有测试
    results["导入测试"] = test_imports()
    results["项目结构"] = test_project_structure()
    results["模型文件夹"] = test_model_folders()
    results["世界文件"] = test_world_files()
    results["启动脚本"] = test_launch_scripts()
    results["MuJoCo"] = test_mujoco()
    results["GUI代码"] = test_gui_launch()
    
    # 打印总结
    success = print_summary(results)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
