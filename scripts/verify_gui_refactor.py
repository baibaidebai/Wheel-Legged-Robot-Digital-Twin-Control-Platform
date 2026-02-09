#!/usr/bin/env python3
"""
验证GUI重构完整性

检查主应用程序是否完全移除了假的可视化组件，并集成了真实的MuJoCo渲染
"""

import sys
import os
import re

def check_file_content(filepath, patterns_to_find, patterns_to_avoid):
    """检查文件内容"""
    print(f"\n📄 检查文件: {filepath}")
    
    if not os.path.exists(filepath):
        print(f"  ❌ 文件不存在")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查应该存在的模式
    all_found = True
    for pattern, description in patterns_to_find:
        if re.search(pattern, content):
            print(f"  ✅ {description}")
        else:
            print(f"  ❌ 缺失: {description}")
            all_found = False
    
    # 检查应该避免的模式
    all_avoided = True
    for pattern, description in patterns_to_avoid:
        if re.search(pattern, content):
            print(f"  ❌ 仍然存在: {description}")
            all_avoided = False
        else:
            print(f"  ✅ 已移除: {description}")
    
    return all_found and all_avoided

def main():
    """主验证函数"""
    print("🔍 验证GUI重构完整性")
    print("=" * 60)
    
    base_path = "Wheel-Legged Robot Digital Twin Control Platform/src/wheel_legged_control/wheel_legged_control/gui"
    main_app_path = os.path.join(base_path, "main_application.py")
    
    # 定义检查模式
    patterns_to_find = [
        (r'self\.render_label', "MuJoCo渲染标签"),
        (r'def update_rendering\(self\)', "渲染更新函数"),
        (r'def step_simulation\(self\)', "仿真步进函数"),
        (r'simulation_manager\.render\(mode=[\'"]rgb_array[\'"]\)', "调用仿真管理器渲染"),
        (r'QImage.*rgb_array', "RGB数组转换为QImage"),
        (r'self\.render_timer', "渲染定时器"),
        (r'self\.sim_timer', "仿真定时器"),
        (r'def toggle_rendering\(self\)', "切换渲染函数"),
        (r'MuJoCo物理仿真', "MuJoCo标题"),
    ]
    
    patterns_to_avoid = [
        (r'from.*RobotVisualizationWidget', "导入假的可视化组件"),
        (r'self\.robot_viz\s*=\s*RobotVisualizationWidget', "创建假的可视化组件"),
        (r'robot_viz\.update_joint_angles', "调用假的可视化更新"),
    ]
    
    # 执行检查
    success = check_file_content(main_app_path, patterns_to_find, patterns_to_avoid)
    
    print("\n" + "=" * 60)
    if success:
        print("✅ GUI重构验证通过！")
        print("\n📋 重构完成的功能:")
        print("  1. ✅ 移除了假的RobotVisualizationWidget")
        print("  2. ✅ 添加了MuJoCo渲染标签")
        print("  3. ✅ 实现了真实物理仿真渲染")
        print("  4. ✅ 添加了渲染和仿真定时器")
        print("  5. ✅ 实现了渲染控制功能")
        print("\n🎯 下一步:")
        print("  - 运行 python scripts/test_mujoco_gui.py 测试GUI")
        print("  - 选择MuJoCo后端启动仿真")
        print("  - 验证物理仿真渲染是否正常显示")
        return 0
    else:
        print("❌ GUI重构验证失败！")
        print("\n⚠️  请检查上述缺失或残留的内容")
        return 1

if __name__ == "__main__":
    sys.exit(main())
