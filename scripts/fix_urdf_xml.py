#!/usr/bin/env python3
"""
URDF XML修复脚本

修复URDF文件中的XML语法错误
"""

import sys
import os
from pathlib import Path
import xml.etree.ElementTree as ET

def fix_urdf_file(urdf_path):
    """修复URDF文件"""
    print(f"🔧 修复URDF文件: {urdf_path}")
    
    try:
        # 读取原始文件
        with open(urdf_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 备份原始文件
        backup_path = urdf_path.with_suffix('.urdf.backup')
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"   ✅ 已备份到: {backup_path}")
        
        # 尝试解析XML
        try:
            ET.fromstring(content)
            print("   ✅ XML语法已经正确")
            return True
        except ET.ParseError as e:
            print(f"   ❌ XML解析错误: {e}")
            
        # 常见修复
        fixes_applied = []
        
        # 修复1: 移除多余的注释结束符
        if '-->' in content and content.count('-->') > content.count('<!--'):
            content = content.replace(' -->', '')
            fixes_applied.append("移除多余的注释结束符")
        
        # 修复2: 确保所有gazebo标签都正确闭合
        lines = content.split('\n')
        fixed_lines = []
        gazebo_stack = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # 检查gazebo开始标签
            if '<gazebo' in stripped and not stripped.endswith('/>') and not '</gazebo>' in stripped:
                gazebo_stack.append(i)
                fixed_lines.append(line)
            # 检查gazebo结束标签
            elif '</gazebo>' in stripped:
                if gazebo_stack:
                    gazebo_stack.pop()
                fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        
        # 如果有未闭合的gazebo标签，添加闭合标签
        while gazebo_stack:
            indent_level = len(lines[gazebo_stack.pop()]) - len(lines[gazebo_stack[-1] if gazebo_stack else 0].lstrip())
            fixed_lines.append(' ' * (indent_level - 2) + '</gazebo>')
            fixes_applied.append("添加缺失的</gazebo>标签")
        
        content = '\n'.join(fixed_lines)
        
        # 修复3: 确保robot标签正确闭合
        if '<robot' in content and not content.strip().endswith('</robot>'):
            if not content.strip().endswith('</robot>'):
                content = content.rstrip() + '\n</robot>\n'
                fixes_applied.append("添加缺失的</robot>标签")
        
        # 验证修复后的XML
        try:
            ET.fromstring(content)
            print(f"   ✅ XML修复成功，应用的修复: {', '.join(fixes_applied)}")
            
            # 写入修复后的文件
            with open(urdf_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
            
        except ET.ParseError as e:
            print(f"   ❌ 修复后仍有XML错误: {e}")
            return False
            
    except Exception as e:
        print(f"   ❌ 修复过程出错: {e}")
        return False

def main():
    """主函数"""
    print("🔧 URDF XML修复工具")
    print("=" * 50)
    
    project_root = Path(__file__).parent.parent
    
    # 要修复的URDF文件
    urdf_files = [
        project_root / "src" / "model" / "DM_Wheel_leg_robot" / "urdf" / "wheel_legged_urdf_pkg.urdf",
        project_root / "src" / "model" / "RM_Serial_Wheeled-leg_Robot" / "urdf" / "RM_Serial_Wheeled-leg_Robot.urdf"
    ]
    
    success_count = 0
    
    for urdf_file in urdf_files:
        if urdf_file.exists():
            if fix_urdf_file(urdf_file):
                success_count += 1
        else:
            print(f"⚠️  文件不存在: {urdf_file}")
    
    print(f"\n📊 修复结果: {success_count}/{len([f for f in urdf_files if f.exists()])} 个文件修复成功")
    
    return 0 if success_count == len([f for f in urdf_files if f.exists()]) else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)