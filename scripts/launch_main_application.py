#!/usr/bin/env python3
"""
轮腿机器人孪生控制系统 - 主应用程序启动脚本

启动完整的用户界面流程：配置选择页面 → 可视化仿真界面
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src" / "wheel_legged_control"))

def main():
    """主函数"""
    print("🚀 启动轮腿机器人孪生控制系统")
    print("=" * 50)
    
    try:
        # 检查依赖
        print("📦 检查依赖...")
        
        try:
            from PyQt5.QtWidgets import QApplication
            print("✅ PyQt5 可用")
        except ImportError:
            print("❌ PyQt5 未安装，请运行: pip install PyQt5")
            return 1
            
        try:
            from wheel_legged_control.gui.main_application import MainApplication
            print("✅ 主应用程序模块可用")
        except ImportError as e:
            print(f"❌ 导入主应用程序失败: {e}")
            return 1
            
        # 检查模型文件
        print("\n🤖 检查机器人模型...")
        model_dirs = [
            project_root / "src" / "model" / "RM_Serial_Wheeled-leg_Robot",
            project_root / "src" / "model" / "DM_Wheel_leg_robot"
        ]
        
        model_found = False
        for model_dir in model_dirs:
            if model_dir.exists():
                urdf_files = list(model_dir.glob("**/*.urdf"))
                if urdf_files:
                    print(f"✅ 找到模型: {model_dir.name}")
                    model_found = True
                    
        if not model_found:
            print("⚠️  未找到机器人模型文件，某些功能可能不可用")
            
        # 启动应用程序
        print("\n🎯 启动用户界面...")
        
        app = QApplication(sys.argv)
        
        # 设置应用信息
        app.setApplicationName("轮腿机器人孪生控制系统")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("轮腿机器人项目团队")
        
        # 创建主应用程序
        main_app = MainApplication()
        main_app.show()
        
        print("✅ 应用程序已启动")
        print("\n📋 使用说明:")
        print("1. 在配置页面选择机器人模型、仿真后端、配置档案和控制算法")
        print("2. 调整高级参数（可选）")
        print("3. 点击'开始仿真'进入可视化仿真界面")
        print("4. 在仿真界面中控制机器人或运行算法")
        print("5. 可随时返回配置页面重新配置")
        
        # 启动事件循环
        return app.exec_()
        
    except KeyboardInterrupt:
        print("\n👋 用户中断，程序退出")
        return 0
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)