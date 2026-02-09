#!/usr/bin/env python3
"""
测试MuJoCo GUI集成

验证主应用程序是否正确集成了MuJoCo物理仿真渲染
"""

import sys
import os

# 添加源码路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src/wheel_legged_control'))

from PyQt5.QtWidgets import QApplication

try:
    from wheel_legged_control.gui.main_application import MainApplication
    print("✅ 成功导入MainApplication")
except ImportError as e:
    print(f"❌ 导入MainApplication失败: {e}")
    sys.exit(1)

def test_gui():
    """测试GUI启动"""
    print("\n🧪 测试MuJoCo GUI集成")
    print("=" * 50)
    
    try:
        # 创建应用
        app = QApplication(sys.argv)
        
        # 创建主窗口
        main_window = MainApplication()
        
        print("✅ 主窗口创建成功")
        print("📋 检查点:")
        print("  1. 配置页面应该显示")
        print("  2. 选择机器人模型")
        print("  3. 选择MuJoCo后端")
        print("  4. 点击'开始仿真'")
        print("  5. 应该看到MuJoCo物理仿真渲染")
        print("\n💡 提示: 关闭窗口退出测试")
        
        # 显示窗口
        main_window.show()
        
        # 运行应用
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"❌ GUI测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_gui()
