#!/usr/bin/env python3
"""
URDF加载器演示脚本

展示当前实现的URDF解析功能，无需完整的ROS2环境。
"""

import sys
import os
from pathlib import Path

# 添加源码路径
sys.path.insert(0, 'src/wheel_legged_control')

from wheel_legged_control.core.urdf_loader import URDFLoader, load_robot_from_directory

def main():
    """主演示函数"""
    print("=" * 60)
    print("轮腿机器人孪生控制系统 - URDF加载器演示")
    print("=" * 60)
    
    # 检查机器人模型目录
    robot_dir = "src/robot/urdf/RM_Serial_Wheeled-leg_Robot"
    
    if not Path(robot_dir).exists():
        print(f"❌ 机器人模型目录不存在: {robot_dir}")
        return
    
    try:
        print(f"📁 正在加载机器人模型: {robot_dir}")
        print("-" * 40)
        
        # 加载机器人模型
        robot_model = load_robot_from_directory(robot_dir)
        
        # 创建URDF加载器实例
        loader = URDFLoader()
        loader.robot_model = robot_model
        
        print("✅ 机器人模型加载成功！")
        print()
        
        # 显示机器人基本信息
        print("🤖 机器人基本信息:")
        info = loader.get_robot_info()
        print(f"   名称: {info['name']}")
        print(f"   总质量: {info['total_mass']:.2f} kg")
        print(f"   链接数量: {info['num_links']}")
        print(f"   关节数量: {info['num_joints']}")
        print(f"   基座链接: {info['base_link']}")
        print()
        
        # 显示关节分类
        print("🔧 关节分类:")
        print(f"   轮子关节: {info['wheel_joints']}")
        print(f"   腿部关节: {info['leg_joints']}")
        print()
        
        # 显示关节限制
        print("⚙️  关节限制:")
        for joint_name, (lower, upper) in info['joint_limits'].items():
            effort = info['joint_efforts'][joint_name]
            velocity = info['joint_velocities'][joint_name]
            print(f"   {joint_name}:")
            print(f"     位置范围: [{lower:.4f}, {upper:.4f}] rad")
            print(f"     最大力矩: {effort:.1f} N·m")
            print(f"     最大速度: {velocity:.1f} rad/s")
        print()
        
        # 显示链接信息
        print("🔗 链接信息:")
        for link_name, link_info in robot_model.links.items():
            print(f"   {link_name}:")
            print(f"     质量: {link_info.mass:.3f} kg")
            print(f"     质心: ({link_info.center_of_mass[0]:.3f}, "
                  f"{link_info.center_of_mass[1]:.3f}, "
                  f"{link_info.center_of_mass[2]:.3f})")
            if link_info.mesh_filename:
                print(f"     网格文件: {link_info.mesh_filename}")
        print()
        
        # 验证URDF
        print("🔍 URDF验证:")
        errors = loader.validate_urdf()
        if errors:
            print("   ⚠️  发现以下问题:")
            for error in errors:
                print(f"     - {error}")
        else:
            print("   ✅ URDF验证通过，模型结构完整")
        print()
        
        # 显示运动学链
        print("🔄 运动学链结构:")
        print("   base_link")
        for joint_name, joint_info in robot_model.joints.items():
            indent = "     " if joint_info.parent_link == "base_link" else "       "
            print(f"{indent}├── {joint_name} ({joint_info.joint_type})")
            print(f"{indent}│   └── {joint_info.child_link}")
        print()
        
        print("=" * 60)
        print("🎉 演示完成！")
        print()
        print("📋 功能总结:")
        print("   ✅ URDF文件解析和验证")
        print("   ✅ 关节和链接信息提取")
        print("   ✅ 轮腿机器人结构识别")
        print("   ✅ 运动学约束分析")
        print("   ✅ 错误检测和处理")
        print()
        print("🚀 下一步: 启动Gazebo仿真环境（需要安装ROS2）")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()