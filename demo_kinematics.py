#!/usr/bin/env python3
"""
轮腿机器人运动学演示

展示轮腿机器人的运动学结构和关节运动范围。
"""

import sys
import os
import math
from pathlib import Path

# 添加源码路径
sys.path.insert(0, 'src/wheel_legged_control')

from wheel_legged_control.core.urdf_loader import load_robot_from_directory

def print_robot_kinematics():
    """打印机器人运动学信息"""
    print("=" * 70)
    print("🔄 轮腿机器人运动学分析")
    print("=" * 70)
    
    # 加载机器人模型
    robot_dir = "src/robot/urdf/RM_Serial_Wheeled-leg_Robot"
    if not Path(robot_dir).exists():
        print("❌ 机器人模型目录不存在")
        return
    
    robot_model = load_robot_from_directory(robot_dir)
    
    print(f"机器人名称: {robot_model.name}")
    print(f"基座链接: {robot_model.base_link}")
    print()
    
    # 分析运动学链
    print("🔗 运动学链结构:")
    print("-" * 50)
    
    # 构建运动学树
    joint_tree = {}
    for joint_name, joint_info in robot_model.joints.items():
        parent = joint_info.parent_link
        if parent not in joint_tree:
            joint_tree[parent] = []
        joint_tree[parent].append((joint_name, joint_info))
    
    def print_tree(link_name, level=0):
        """递归打印运动学树"""
        indent = "  " * level
        if level == 0:
            print(f"{indent}📦 {link_name} (基座)")
        else:
            print(f"{indent}└── 🔗 {link_name}")
        
        if link_name in joint_tree:
            for joint_name, joint_info in joint_tree[link_name]:
                joint_indent = "  " * (level + 1)
                joint_type_icon = "🔄" if joint_info.joint_type == "revolute" else "↔️"
                print(f"{joint_indent}├── {joint_type_icon} {joint_name} ({joint_info.joint_type})")
                print_tree(joint_info.child_link, level + 2)
    
    print_tree(robot_model.base_link)
    print()
    
    # 关节运动范围分析
    print("⚙️  关节运动范围分析:")
    print("-" * 50)
    
    for joint_name, joint_info in robot_model.joints.items():
        print(f"🔧 {joint_name}:")
        print(f"   类型: {joint_info.joint_type}")
        print(f"   父链接: {joint_info.parent_link}")
        print(f"   子链接: {joint_info.child_link}")
        
        if joint_info.limit_lower is not None and joint_info.limit_upper is not None:
            lower_deg = math.degrees(joint_info.limit_lower)
            upper_deg = math.degrees(joint_info.limit_upper)
            range_deg = upper_deg - lower_deg
            print(f"   运动范围: {lower_deg:.1f}° 到 {upper_deg:.1f}° (总计 {range_deg:.1f}°)")
        else:
            print(f"   运动范围: 无限制 (连续旋转)")
        
        if joint_info.limit_effort:
            print(f"   最大力矩: {joint_info.limit_effort} N·m")
        
        if joint_info.limit_velocity:
            print(f"   最大速度: {joint_info.limit_velocity} rad/s")
        
        # 轴向量
        axis = joint_info.axis_xyz
        print(f"   旋转轴: ({axis[0]}, {axis[1]}, {axis[2]})")
        print()
    
    # 轮腿协调分析
    print("🚶 轮腿协调运动分析:")
    print("-" * 50)
    
    print("左侧运动链:")
    print("  base_link → lf0_Joint → lf0_Link → lf1_Joint → lf1_Link → l_wheel_Joint → l_wheel_Link")
    print("  基座 → 髋关节 → 大腿 → 膝关节 → 小腿 → 轮子关节 → 轮子")
    print()
    
    print("右侧运动链:")
    print("  base_link → rf0_Joint → rf0_Link → rf1_Joint → rf1_Link → r_wheel_Joint → r_wheel_Link")
    print("  基座 → 髋关节 → 大腿 → 膝关节 → 小腿 → 轮子关节 → 轮子")
    print()
    
    # 运动模式分析
    print("🎯 运动模式分析:")
    print("-" * 50)
    
    modes = [
        ("轮式模式", "腿部关节锁定，仅轮子旋转", "平地高速移动"),
        ("腿式模式", "轮子锁定，腿部关节运动", "复杂地形通过"),
        ("轮腿协调", "轮子和腿部同时运动", "最优移动效率"),
        ("站立模式", "腿部支撑，轮子离地", "静态操作任务"),
    ]
    
    for mode, description, application in modes:
        print(f"🔸 {mode}:")
        print(f"   描述: {description}")
        print(f"   应用: {application}")
        print()
    
    # 控制挑战
    print("⚠️  控制挑战:")
    print("-" * 50)
    
    challenges = [
        "轮腿耦合约束处理",
        "动态平衡控制",
        "地形适应性",
        "能耗优化",
        "模式切换平滑性",
        "奇异位形避免"
    ]
    
    for i, challenge in enumerate(challenges, 1):
        print(f"   {i}. {challenge}")
    
    print()
    
    # 数字孪生映射器的作用
    print("🧠 数字孪生映射器的作用:")
    print("-" * 50)
    
    mapper_functions = [
        "解析URDF中的轮腿约束关系",
        "建立运动学正逆解算法",
        "处理轮腿耦合约束",
        "检测和处理奇异位形",
        "验证运动一致性",
        "提供任务空间映射"
    ]
    
    for i, function in enumerate(mapper_functions, 1):
        print(f"   {i}. {function}")
    
    print()
    print("=" * 70)
    print("🎯 运动学分析完成！")
    print("💡 这些信息将用于数字孪生映射器的设计和实现。")
    print("=" * 70)

def simulate_joint_motion():
    """模拟关节运动"""
    print("\n🎬 关节运动仿真演示:")
    print("-" * 50)
    
    # 模拟一个简单的步态
    print("模拟轮腿机器人步态序列...")
    print()
    
    # 定义步态阶段
    gait_phases = [
        ("初始站立", {"lf0": 0, "lf1": 0, "rf0": 0, "rf1": 0, "l_wheel": 0, "r_wheel": 0}),
        ("左腿抬起", {"lf0": 30, "lf1": -45, "rf0": 0, "rf1": 0, "l_wheel": 0, "r_wheel": 0}),
        ("左腿前摆", {"lf0": -15, "lf1": -30, "rf0": 0, "rf1": 0, "l_wheel": 0, "r_wheel": 0}),
        ("左腿着地", {"lf0": 0, "lf1": 0, "rf0": 0, "rf1": 0, "l_wheel": 0, "r_wheel": 0}),
        ("右腿抬起", {"lf0": 0, "lf1": 0, "rf0": -30, "rf1": 45, "l_wheel": 0, "r_wheel": 0}),
        ("右腿前摆", {"lf0": 0, "lf1": 0, "rf0": 15, "rf1": 30, "l_wheel": 0, "r_wheel": 0}),
        ("右腿着地", {"lf0": 0, "lf1": 0, "rf0": 0, "rf1": 0, "l_wheel": 0, "r_wheel": 0}),
        ("轮式滚动", {"lf0": 0, "lf1": 0, "rf0": 0, "rf1": 0, "l_wheel": 180, "r_wheel": 180}),
    ]
    
    for i, (phase_name, joint_angles) in enumerate(gait_phases):
        print(f"阶段 {i+1}: {phase_name}")
        print("   关节角度 (度):")
        for joint, angle in joint_angles.items():
            bar_length = int(abs(angle) / 10)
            bar = "█" * bar_length
            direction = "+" if angle >= 0 else "-"
            print(f"     {joint:8}: {angle:6.1f}° {direction}{bar}")
        print()
        
        # 模拟时间延迟
        import time
        time.sleep(0.5)
    
    print("✅ 步态仿真完成！")

def main():
    """主函数"""
    try:
        print_robot_kinematics()
        simulate_joint_motion()
    except Exception as e:
        print(f"❌ 运动学分析失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()