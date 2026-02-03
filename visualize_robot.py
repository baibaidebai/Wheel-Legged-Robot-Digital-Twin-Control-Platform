#!/usr/bin/env python3
"""
机器人结构可视化脚本

使用matplotlib创建轮腿机器人的结构图和关节分布图。
"""

import sys
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from pathlib import Path

# 添加源码路径
sys.path.insert(0, 'src/wheel_legged_control')

from wheel_legged_control.core.urdf_loader import load_robot_from_directory

def create_robot_visualization():
    """创建机器人可视化图"""
    
    # 加载机器人模型
    robot_dir = "src/robot/urdf/RM_Serial_Wheeled-leg_Robot"
    if not Path(robot_dir).exists():
        print("❌ 机器人模型目录不存在")
        return
    
    robot_model = load_robot_from_directory(robot_dir)
    
    # 创建图形
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('轮腿机器人孪生控制系统 - 机器人结构分析', fontsize=16, fontweight='bold')
    
    # 图1: 机器人结构示意图
    ax1.set_title('机器人结构示意图', fontsize=14, fontweight='bold')
    ax1.set_xlim(-0.5, 0.5)
    ax1.set_ylim(-0.4, 0.4)
    ax1.set_aspect('equal')
    
    # 绘制基座
    base = patches.Rectangle((-0.15, -0.1), 0.3, 0.2, 
                           linewidth=2, edgecolor='blue', facecolor='lightblue', alpha=0.7)
    ax1.add_patch(base)
    ax1.text(0, 0, 'base_link\n8.8kg', ha='center', va='center', fontweight='bold')
    
    # 绘制左腿
    # lf0关节
    lf0_x, lf0_y = -0.05, 0.17
    ax1.plot([0, lf0_x], [0.1, lf0_y], 'r-', linewidth=3)
    ax1.plot(lf0_x, lf0_y, 'ro', markersize=8)
    ax1.text(lf0_x-0.05, lf0_y+0.02, 'lf0_Joint', ha='center', fontsize=8)
    
    # lf1关节和左轮
    lf1_x, lf1_y = lf0_x + 0.15, lf0_y + 0.15
    wheel_l_x, wheel_l_y = lf1_x, lf1_y + 0.08
    
    ax1.plot([lf0_x, lf1_x], [lf0_y, lf1_y], 'r-', linewidth=3)
    ax1.plot(lf1_x, lf1_y, 'ro', markersize=8)
    ax1.text(lf1_x+0.02, lf1_y, 'lf1_Joint', ha='left', fontsize=8)
    
    ax1.plot([lf1_x, wheel_l_x], [lf1_y, wheel_l_y], 'g-', linewidth=3)
    wheel_l = patches.Circle((wheel_l_x, wheel_l_y), 0.03, 
                           linewidth=2, edgecolor='green', facecolor='lightgreen')
    ax1.add_patch(wheel_l)
    ax1.text(wheel_l_x, wheel_l_y-0.06, '左轮\n1.22kg', ha='center', fontsize=8)
    
    # 绘制右腿（镜像）
    rf0_x, rf0_y = 0.05, -0.17
    ax1.plot([0, rf0_x], [-0.1, rf0_y], 'r-', linewidth=3)
    ax1.plot(rf0_x, rf0_y, 'ro', markersize=8)
    ax1.text(rf0_x+0.05, rf0_y-0.02, 'rf0_Joint', ha='center', fontsize=8)
    
    rf1_x, rf1_y = rf0_x + 0.15, rf0_y - 0.15
    wheel_r_x, wheel_r_y = rf1_x, rf1_y - 0.08
    
    ax1.plot([rf0_x, rf1_x], [rf0_y, rf1_y], 'r-', linewidth=3)
    ax1.plot(rf1_x, rf1_y, 'ro', markersize=8)
    ax1.text(rf1_x+0.02, rf1_y, 'rf1_Joint', ha='left', fontsize=8)
    
    ax1.plot([rf1_x, wheel_r_x], [rf1_y, wheel_r_y], 'g-', linewidth=3)
    wheel_r = patches.Circle((wheel_r_x, wheel_r_y), 0.03, 
                           linewidth=2, edgecolor='green', facecolor='lightgreen')
    ax1.add_patch(wheel_r)
    ax1.text(wheel_r_x, wheel_r_y+0.06, '右轮\n1.22kg', ha='center', fontsize=8)
    
    ax1.grid(True, alpha=0.3)
    ax1.set_xlabel('X (m)')
    ax1.set_ylabel('Y (m)')
    
    # 图2: 关节限制分析
    ax2.set_title('关节限制分析', fontsize=14, fontweight='bold')
    
    joint_names = []
    lower_limits = []
    upper_limits = []
    efforts = []
    
    for joint_name, joint_info in robot_model.joints.items():
        joint_names.append(joint_name.replace('_Joint', ''))
        lower_limits.append(joint_info.limit_lower if joint_info.limit_lower else -np.pi)
        upper_limits.append(joint_info.limit_upper if joint_info.limit_upper else np.pi)
        efforts.append(joint_info.limit_effort if joint_info.limit_effort else 0)
    
    x_pos = np.arange(len(joint_names))
    
    # 绘制关节限制范围
    ax2.barh(x_pos, np.array(upper_limits) - np.array(lower_limits), 
             left=lower_limits, alpha=0.6, color='skyblue', label='运动范围')
    
    # 添加力矩信息
    ax2_twin = ax2.twinx()
    ax2_twin.plot(efforts, x_pos, 'ro-', linewidth=2, markersize=6, label='最大力矩')
    ax2_twin.set_ylabel('最大力矩 (N·m)', color='red')
    ax2_twin.tick_params(axis='y', labelcolor='red')
    
    ax2.set_yticks(x_pos)
    ax2.set_yticklabels(joint_names)
    ax2.set_xlabel('关节角度 (rad)')
    ax2.set_ylabel('关节')
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper left')
    ax2_twin.legend(loc='upper right')
    
    # 图3: 质量分布
    ax3.set_title('链接质量分布', fontsize=14, fontweight='bold')
    
    link_names = []
    masses = []
    colors = []
    
    for link_name, link_info in robot_model.links.items():
        link_names.append(link_name.replace('_Link', '').replace('_link', ''))
        masses.append(link_info.mass)
        
        if 'base' in link_name:
            colors.append('blue')
        elif 'wheel' in link_name:
            colors.append('green')
        else:
            colors.append('orange')
    
    bars = ax3.bar(link_names, masses, color=colors, alpha=0.7)
    ax3.set_ylabel('质量 (kg)')
    ax3.set_xlabel('链接')
    ax3.grid(True, alpha=0.3, axis='y')
    
    # 添加数值标签
    for bar, mass in zip(bars, masses):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{mass:.2f}kg', ha='center', va='bottom', fontsize=9)
    
    plt.setp(ax3.get_xticklabels(), rotation=45, ha='right')
    
    # 图4: 系统信息总览
    ax4.axis('off')
    ax4.set_title('系统信息总览', fontsize=14, fontweight='bold')
    
    info_text = f"""
机器人名称: {robot_model.name}
总质量: {sum(link.mass for link in robot_model.links.values()):.2f} kg
链接数量: {len(robot_model.links)}
关节数量: {len(robot_model.joints)}

关节分类:
• 轮子关节: {len(robot_model.wheel_joints)} 个
  {', '.join(robot_model.wheel_joints)}
  
• 腿部关节: {len(robot_model.leg_joints)} 个  
  {', '.join(robot_model.leg_joints)}

技术特点:
✓ 轮腿混合移动机构
✓ 串联关节链结构  
✓ 位置控制模式
✓ 支持强化学习集成
✓ 数字孪生映射能力

开发状态:
✅ URDF解析完成
✅ Gazebo集成就绪
🔄 控制器开发中
🔄 GUI界面开发中
    """
    
    ax4.text(0.05, 0.95, info_text, transform=ax4.transAxes, fontsize=11,
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.8))
    
    plt.tight_layout()
    
    # 保存图片
    output_file = 'robot_analysis.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"📊 机器人分析图已保存: {output_file}")
    
    # 显示图片
    plt.show()

def main():
    """主函数"""
    print("🎨 正在生成机器人结构可视化图...")
    
    try:
        create_robot_visualization()
        print("✅ 可视化完成！")
    except ImportError:
        print("❌ 需要安装matplotlib: pip3 install matplotlib")
    except Exception as e:
        print(f"❌ 可视化失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()