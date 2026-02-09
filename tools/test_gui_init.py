#!/usr/bin/env python3
"""
测试GUI初始化
不实际显示窗口，只测试初始化过程
"""

import sys
import os
from pathlib import Path

# 设置工作目录
project_root = Path(__file__).parent.parent
os.chdir(project_root)

def test_gui_init():
    """测试GUI初始化"""
    print("🧪 测试GUI初始化...")
    
    try:
        import tkinter as tk
        from tkinter import ttk
        
        # 创建隐藏的根窗口
        root = tk.Tk()
        root.withdraw()  # 隐藏窗口
        
        print("  ✅ Tkinter根窗口创建成功")
        
        # 导入GUI类
        sys.path.insert(0, str(project_root / "tools"))
        from launch_gui_enhanced import EnhancedSimulationLauncher
        
        print("  ✅ GUI类导入成功")
        
        # 尝试初始化（但不显示）
        try:
            app = EnhancedSimulationLauncher(root)
            print("  ✅ GUI初始化成功")
            
            # 检查关键属性
            assert hasattr(app, 'simulator_var'), "缺少 simulator_var"
            assert hasattr(app, 'model_folder_var'), "缺少 model_folder_var"
            assert hasattr(app, 'urdf_file_var'), "缺少 urdf_file_var"
            assert hasattr(app, 'mjcf_file_var'), "缺少 mjcf_file_var"
            assert hasattr(app, 'world_file_var'), "缺少 world_file_var"
            assert hasattr(app, 'model_folder_combo'), "缺少 model_folder_combo"
            assert hasattr(app, 'urdf_combo'), "缺少 urdf_combo"
            assert hasattr(app, 'mjcf_combo'), "缺少 mjcf_combo"
            assert hasattr(app, 'world_combo'), "缺少 world_combo"
            
            print("  ✅ 所有关键属性存在")
            
            # 检查扫描结果
            print(f"  ✅ 扫描到 {len(app.model_folders)} 个模型文件夹")
            print(f"  ✅ 扫描到 {len(app.world_files)} 个世界文件")
            
            # 清理
            root.destroy()
            
            return True
            
        except Exception as e:
            print(f"  ❌ GUI初始化失败: {e}")
            import traceback
            traceback.print_exc()
            root.destroy()
            return False
            
    except ImportError as e:
        print(f"  ❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("="*50)
    print("🧪 GUI初始化测试")
    print("="*50)
    print()
    
    success = test_gui_init()
    
    print()
    print("="*50)
    if success:
        print("✅ 测试通过！GUI可以正常初始化。")
        print()
        print("启动GUI:")
        print("  ./launch_enhanced.sh")
    else:
        print("❌ 测试失败！请检查错误信息。")
    print("="*50)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
