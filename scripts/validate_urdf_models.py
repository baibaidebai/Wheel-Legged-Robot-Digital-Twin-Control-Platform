#!/usr/bin/env python3
"""
URDF模型验证脚本

验证所有机器人模型的URDF文件是否正确
"""

import sys
import os
from pathlib import Path
import xml.etree.ElementTree as ET

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src" / "wheel_legged_control"))

def validate_xml_syntax(urdf_path):
    """验证XML语法"""
    try:
        ET.parse(urdf_path)
        return True, "XML语法正确"
    except ET.ParseError as e:
        return False, f"XML解析错误: {e}"
    except Exception as e:
        return False, f"文件读取错误: {e}"

def validate_urdf_structure(urdf_path):
    """验证URDF结构"""
    try:
        tree = ET.parse(urdf_path)
        root = tree.getroot()
        
        if root.tag != 'robot':
            return False, "根元素必须是 <robot>"
        
        if 'name' not in root.attrib:
            return False, "robot元素缺少name属性"
        
        # 检查基本元素
        links = root.findall('link')
        joints = root.findall('joint')
        
        if len(links) == 0:
            return False, "未找到link元素"
        
        # 检查base_link
        base_links = [link for link in links if link.get('name') == 'base_link']
        if len(base_links) == 0:
            return False, "未找到base_link"
        
        return True, f"URDF结构正确 - {len(links)}个链接, {len(joints)}个关节"
        
    except Exception as e:
        return False, f"结构验证失败: {e}"

def validate_urdf_with_loader(urdf_path):
    """使用URDF加载器验证"""
    try:
        from wheel_legged_control.core.urdf_loader import URDFLoader
        
        loader = URDFLoader()
        robot = loader.load_urdf(str(urdf_path))
        
        return True, f"加载成功 - {robot.name}: {len(robot.joints)}个关节, {len(robot.links)}个链接"
        
    except Exception as e:
        return False, f"URDF加载器验证失败: {e}"

def main():
    """主函数"""
    print("🔍 URDF模型验证")
    print("=" * 50)
    
    # 扫描模型目录
    model_dirs = [
        project_root / "src" / "model" / "RM_Serial_Wheeled-leg_Robot",
        project_root / "src" / "model" / "DM_Wheel_leg_robot"
    ]
    
    total_models = 0
    valid_models = 0
    
    for model_dir in model_dirs:
        if not model_dir.exists():
            print(f"⚠️  模型目录不存在: {model_dir}")
            continue
            
        print(f"\n📁 检查模型目录: {model_dir.name}")
        print("-" * 40)
        
        # 查找URDF文件
        urdf_files = list(model_dir.glob("**/*.urdf"))
        
        if not urdf_files:
            print("   ❌ 未找到URDF文件")
            continue
            
        for urdf_file in urdf_files:
            total_models += 1
            print(f"\n🤖 验证模型: {urdf_file.name}")
            
            # 1. XML语法验证
            xml_valid, xml_msg = validate_xml_syntax(urdf_file)
            print(f"   XML语法: {'✅' if xml_valid else '❌'} {xml_msg}")
            
            if not xml_valid:
                continue
                
            # 2. URDF结构验证
            struct_valid, struct_msg = validate_urdf_structure(urdf_file)
            print(f"   URDF结构: {'✅' if struct_valid else '❌'} {struct_msg}")
            
            if not struct_valid:
                continue
                
            # 3. 加载器验证
            loader_valid, loader_msg = validate_urdf_with_loader(urdf_file)
            print(f"   加载器验证: {'✅' if loader_valid else '❌'} {loader_msg}")
            
            if xml_valid and struct_valid and loader_valid:
                valid_models += 1
                print(f"   🎉 模型验证通过!")
    
    # 总结
    print(f"\n📊 验证结果")
    print("=" * 50)
    print(f"总模型数: {total_models}")
    print(f"有效模型: {valid_models}")
    print(f"成功率: {valid_models/total_models*100:.1f}%" if total_models > 0 else "无模型")
    
    if valid_models == total_models and total_models > 0:
        print("\n🎉 所有模型验证通过!")
        return 0
    else:
        print(f"\n⚠️  有 {total_models - valid_models} 个模型验证失败")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)