#!/usr/bin/env python3
"""
Gazebo集成验证脚本

验证Gazebo仿真环境是否正确配置和工作。
"""

import os
import sys
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path

def check_dependencies():
    """检查依赖项"""
    print("🔍 检查依赖项...")
    
    dependencies = {
        'python3': 'python3 --version',
        'gazebo': 'gazebo --version',
        'ros2': 'ros2 --version'
    }
    
    missing = []
    for name, cmd in dependencies.items():
        try:
            result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"  ✅ {name}: 已安装")
            else:
                print(f"  ❌ {name}: 未正确安装")
                missing.append(name)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(f"  ❌ {name}: 未找到")
            missing.append(name)
    
    return missing

def verify_urdf_files():
    """验证URDF文件"""
    print("\n📄 验证URDF文件...")
    
    urdf_files = [
        "src/wheel_legged_control/urdf/wheel_legged_robot.urdf",
        "src/wheel_legged_control/urdf/wheel_legged_robot_gazebo.urdf"
    ]
    
    for urdf_file in urdf_files:
        if not Path(urdf_file).exists():
            print(f"  ❌ 文件不存在: {urdf_file}")
            continue
            
        try:
            tree = ET.parse(urdf_file)
            root = tree.getroot()
            
            if root.tag == 'robot':
                robot_name = root.get('name', 'unknown')
                links = len(root.findall('link'))
                joints = len(root.findall('joint'))
                print(f"  ✅ {urdf_file}")
                print(f"     机器人: {robot_name}, 链接: {links}, 关节: {joints}")
            else:
                print(f"  ❌ 无效的URDF文件: {urdf_file}")
                
        except ET.ParseError as e:
            print(f"  ❌ XML解析错误: {urdf_file} - {e}")

def verify_world_file():
    """验证世界文件"""
    print("\n🌍 验证世界文件...")
    
    world_file = "src/wheel_legged_control/worlds/wheel_legged_robot.world"
    
    if not Path(world_file).exists():
        print(f"  ❌ 世界文件不存在: {world_file}")
        return
        
    try:
        tree = ET.parse(world_file)
        root = tree.getroot()
        
        if root.tag == 'sdf':
            world = root.find('world')
            if world is not None:
                world_name = world.get('name', 'unknown')
                models = len(world.findall('model'))
                print(f"  ✅ {world_file}")
                print(f"     世界: {world_name}, 模型数量: {models}")
            else:
                print(f"  ❌ 缺少world元素: {world_file}")
        else:
            print(f"  ❌ 无效的SDF文件: {world_file}")
            
    except ET.ParseError as e:
        print(f"  ❌ XML解析错误: {world_file} - {e}")

def verify_launch_files():
    """验证启动文件"""
    print("\n🚀 验证启动文件...")
    
    launch_files = [
        "src/wheel_legged_control/launch/simple_gazebo.launch.py",
        "src/wheel_legged_control/launch/gazebo_simulation.launch.py",
        "src/wheel_legged_control/launch/system_launch.py"
    ]
    
    for launch_file in launch_files:
        if not Path(launch_file).exists():
            print(f"  ❌ 启动文件不存在: {launch_file}")
            continue
            
        try:
            # 检查Python语法
            result = subprocess.run(
                ['python3', '-m', 'py_compile', launch_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print(f"  ✅ {launch_file}")
            else:
                print(f"  ❌ 语法错误: {launch_file}")
                print(f"     {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print(f"  ❌ 语法检查超时: {launch_file}")

def verify_config_files():
    """验证配置文件"""
    print("\n⚙️  验证配置文件...")
    
    config_file = "src/wheel_legged_control/config/wheel_legged_control.yaml"
    
    if not Path(config_file).exists():
        print(f"  ❌ 配置文件不存在: {config_file}")
        return
        
    try:
        import yaml
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        # 检查基本结构
        if 'joint_state_broadcaster' in config:
            joints = config['joint_state_broadcaster']['ros__parameters']['joints']
            print(f"  ✅ {config_file}")
            print(f"     配置的关节: {len(joints)} 个")
            print(f"     关节列表: {', '.join(joints)}")
        else:
            print(f"  ❌ 配置文件结构不完整: {config_file}")
            
    except yaml.YAMLError as e:
        print(f"  ❌ YAML解析错误: {config_file} - {e}")
    except ImportError:
        print(f"  ⚠️  PyYAML未安装，跳过YAML验证")

def test_urdf_loader():
    """测试URDF加载器"""
    print("\n🔧 测试URDF加载器...")
    
    try:
        sys.path.insert(0, 'src/wheel_legged_control')
        from wheel_legged_control.core.urdf_loader import URDFLoader
        
        loader = URDFLoader()
        urdf_file = "src/wheel_legged_control/urdf/wheel_legged_robot.urdf"
        
        robot_model = loader.load_urdf(urdf_file)
        
        print(f"  ✅ URDF加载成功")
        print(f"     机器人名称: {robot_model.name}")
        print(f"     链接数量: {len(robot_model.links)}")
        print(f"     关节数量: {len(robot_model.joints)}")
        print(f"     轮子关节: {robot_model.wheel_joints}")
        print(f"     腿部关节: {robot_model.leg_joints}")
        
        # 验证关节限制
        limits = loader.get_joint_limits()
        print(f"     关节限制: {len(limits)} 个关节有限制")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ 无法导入URDF加载器: {e}")
        return False
    except Exception as e:
        print(f"  ❌ URDF加载器测试失败: {e}")
        return False

def generate_summary():
    """生成验证摘要"""
    print("\n" + "="*60)
    print("📋 Gazebo集成验证摘要")
    print("="*60)
    
    # 检查关键文件
    key_files = [
        "src/wheel_legged_control/urdf/wheel_legged_robot.urdf",
        "src/wheel_legged_control/worlds/wheel_legged_robot.world",
        "src/wheel_legged_control/launch/simple_gazebo.launch.py",
        "src/wheel_legged_control/config/wheel_legged_control.yaml"
    ]
    
    all_files_exist = True
    for file_path in key_files:
        exists = Path(file_path).exists()
        status = "✅" if exists else "❌"
        print(f"{status} {file_path}")
        if not exists:
            all_files_exist = False
    
    print("\n📊 集成状态:")
    if all_files_exist:
        print("✅ 所有关键文件已创建")
        print("✅ Gazebo仿真环境已配置")
        print("✅ 可以开始下一步开发")
        
        print("\n🚀 下一步操作:")
        print("1. 安装ROS2和Gazebo (如果尚未安装)")
        print("2. 构建工作空间: colcon build --symlink-install")
        print("3. 启动仿真: ros2 launch wheel_legged_control simple_gazebo.launch.py")
        
    else:
        print("❌ 部分文件缺失，需要重新创建")
        
    print("="*60)

def main():
    """主函数"""
    print("🤖 轮腿机器人Gazebo集成验证")
    print("="*60)
    
    # 检查依赖项
    missing_deps = check_dependencies()
    
    # 验证文件
    verify_urdf_files()
    verify_world_file()
    verify_launch_files()
    verify_config_files()
    
    # 测试URDF加载器
    urdf_loader_ok = test_urdf_loader()
    
    # 生成摘要
    generate_summary()
    
    # 提供建议
    if missing_deps:
        print(f"\n⚠️  缺少依赖项: {', '.join(missing_deps)}")
        print("请安装缺少的依赖项后重新运行验证")
    
    if not urdf_loader_ok:
        print("\n⚠️  URDF加载器测试失败")
        print("请检查Python路径和模块导入")

if __name__ == "__main__":
    main()