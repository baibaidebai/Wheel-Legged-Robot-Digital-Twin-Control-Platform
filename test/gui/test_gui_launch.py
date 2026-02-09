#!/usr/bin/env python3
"""
简单的GUI启动测试

测试ROS2集成控制面板是否可以正常启动
"""

import sys
import os
import subprocess
import time

# 添加源码路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src/wheel_legged_control'))

def test_gui_import():
    """测试GUI模块导入"""
    print("🧪 测试GUI模块导入...")
    
    try:
        # 测试PyQt5
        from PyQt5.QtWidgets import QApplication
        print("✅ PyQt5导入成功")
        
        # 测试控制面板模块
        from wheel_legged_control.gui.ros2_control_panel import ROS2ControlPanelMainWindow
        print("✅ ROS2控制面板模块导入成功")
        
        # 测试ROS2模块
        import rclpy
        print("✅ ROS2模块导入成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_gui_creation():
    """测试GUI创建"""
    print("🧪 测试GUI创建...")
    
    try:
        from PyQt5.QtWidgets import QApplication
        from wheel_legged_control.gui.ros2_control_panel import ROS2ControlPanelMainWindow
        
        # 创建应用
        app = QApplication([])
        
        # 创建主窗口（不启动ROS2）
        window = ROS2ControlPanelMainWindow()
        
        print("✅ GUI窗口创建成功")
        
        # 立即关闭
        window.close()
        app.quit()
        
        return True
        
    except Exception as e:
        print(f"❌ GUI创建失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("轮腿机器人孪生控制系统 - GUI启动测试")
    print("=" * 60)
    
    # 测试导入
    if not test_gui_import():
        print("❌ 模块导入测试失败")
        return 1
    
    # 测试GUI创建
    if not test_gui_creation():
        print("❌ GUI创建测试失败")
        return 1
    
    print("\n🎉 所有测试通过！")
    print("💡 GUI可以正常启动")
    
    print("\n📋 使用说明:")
    print("1. 启动测试发布器:")
    print("   python3 test_ros2_gui_integration.py")
    print("2. 在另一个终端启动GUI:")
    print("   source install/setup.bash")
    print("   python3 src/wheel_legged_control/wheel_legged_control/gui/ros2_control_panel.py")
    print("3. 或使用launch文件:")
    print("   ros2 launch wheel_legged_control ros2_control_panel.launch.py")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())