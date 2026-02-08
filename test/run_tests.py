#!/usr/bin/env python3
"""
轮腿机器人孪生控制系统 - 测试运行器

统一的测试运行脚本，用于执行各种类型的测试
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

def run_integration_tests():
    """运行集成测试"""
    print("🧪 运行集成测试...")
    
    test_files = [
        "integration/test_ros2_gui_integration.py",
        "integration/test_imu_system.py", 
        "integration/test_imu_publisher_basic.py",
        "integration/test_joint_controller_basic.py",
        "integration/test_ros2_interface_basic.py"
    ]
    
    for test_file in test_files:
        test_path = Path(__file__).parent / test_file
        if test_path.exists():
            print(f"  运行: {test_file}")
            try:
                result = subprocess.run([sys.executable, str(test_path)], 
                                      capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    print(f"  ✅ {test_file} 通过")
                else:
                    print(f"  ❌ {test_file} 失败")
                    print(f"     错误: {result.stderr}")
            except subprocess.TimeoutExpired:
                print(f"  ⏰ {test_file} 超时")
            except Exception as e:
                print(f"  ❌ {test_file} 异常: {e}")
        else:
            print(f"  ⚠️  {test_file} 不存在")

def run_gui_tests():
    """运行GUI测试"""
    print("🎮 运行GUI测试...")
    
    test_files = [
        "gui/test_gui_launch.py"
    ]
    
    for test_file in test_files:
        test_path = Path(__file__).parent / test_file
        if test_path.exists():
            print(f"  运行: {test_file}")
            try:
                result = subprocess.run([sys.executable, str(test_path)], 
                                      capture_output=True, text=True, timeout=15)
                if result.returncode == 0:
                    print(f"  ✅ {test_file} 通过")
                else:
                    print(f"  ❌ {test_file} 失败")
                    print(f"     错误: {result.stderr}")
            except subprocess.TimeoutExpired:
                print(f"  ⏰ {test_file} 超时")
            except Exception as e:
                print(f"  ❌ {test_file} 异常: {e}")
        else:
            print(f"  ⚠️  {test_file} 不存在")

def run_python_tests():
    """运行Python单元测试"""
    print("🐍 运行Python单元测试...")
    
    # 运行pytest
    test_dir = Path(__file__).parent.parent / "test" / "python"
    if test_dir.exists():
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                str(test_dir), "-v"
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print("  ✅ Python单元测试通过")
            else:
                print("  ❌ Python单元测试失败")
                print(f"     输出: {result.stdout}")
                print(f"     错误: {result.stderr}")
        except subprocess.TimeoutExpired:
            print("  ⏰ Python单元测试超时")
        except Exception as e:
            print(f"  ❌ Python单元测试异常: {e}")
    else:
        print("  ⚠️  Python测试目录不存在")

def run_cpp_tests():
    """运行C++测试"""
    print("⚙️  运行C++测试...")
    
    # 运行colcon test
    project_root = Path(__file__).parent.parent
    try:
        result = subprocess.run([
            "colcon", "test", "--packages-select", "wheel_legged_control"
        ], cwd=project_root, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("  ✅ C++测试通过")
        else:
            print("  ❌ C++测试失败")
            print(f"     输出: {result.stdout}")
            print(f"     错误: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("  ⏰ C++测试超时")
    except Exception as e:
        print(f"  ❌ C++测试异常: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="轮腿机器人孪生控制系统测试运行器")
    parser.add_argument("--integration", action="store_true", help="运行集成测试")
    parser.add_argument("--gui", action="store_true", help="运行GUI测试")
    parser.add_argument("--python", action="store_true", help="运行Python单元测试")
    parser.add_argument("--cpp", action="store_true", help="运行C++测试")
    parser.add_argument("--all", action="store_true", help="运行所有测试")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("轮腿机器人孪生控制系统 - 测试运行器")
    print("=" * 60)
    
    if args.all or (not any([args.integration, args.gui, args.python, args.cpp])):
        # 默认运行所有测试
        run_gui_tests()
        run_integration_tests()
        run_python_tests()
        run_cpp_tests()
    else:
        if args.gui:
            run_gui_tests()
        if args.integration:
            run_integration_tests()
        if args.python:
            run_python_tests()
        if args.cpp:
            run_cpp_tests()
    
    print("\n🎉 测试运行完成！")

if __name__ == "__main__":
    main()