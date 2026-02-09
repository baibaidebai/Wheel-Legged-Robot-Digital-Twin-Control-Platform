#!/usr/bin/env python3
"""
测试 Wiki-GRx-MJCF 转换工具
"""

import os
import sys
from pathlib import Path
from xml.etree.ElementTree import tostring, indent

# 导入 urdf2mjcf
try:
    from urdf2mjcf.core import parse_element
    from urdf2mjcf.app import full_pipeline
except ImportError:
    print("❌ urdf2mjcf 未安装")
    print("请先安装: pip install -e ~/workspace/Wiki-GRx-MJCF")
    sys.exit(1)

def test_conversion(urdf_path, output_path):
    """测试 URDF 到 MJCF 的转换"""
    
    print(f"🔄 测试 Wiki-GRx-MJCF 转换工具")
    print(f"=" * 60)
    print(f"输入 URDF: {urdf_path}")
    print(f"输出 MJCF: {output_path}")
    print()
    
    # 检查文件
    if not os.path.exists(urdf_path):
        print(f"❌ URDF 文件不存在: {urdf_path}")
        return False
    
    try:
        # 解析 URDF
        print("📖 解析 URDF 文件...")
        urdf = parse_element(urdf_path)
        
        # 转换
        print("🔧 转换为 MJCF...")
        mjcf = full_pipeline(
            urdf_file_path=urdf_path,
            urdf=urdf,
            mujoco_node=None,
            sensor_config=None,
            default_ground=True,
            default_lighting=True
        )
        
        # 格式化并保存
        print("💾 保存 MJCF 文件...")
        indent(mjcf, space="  ")
        mjcf_str = tostring(mjcf, encoding='unicode')
        
        with open(output_path, 'w') as f:
            f.write('<?xml version="1.0" encoding="utf-8"?>\n')
            f.write(mjcf_str)
        
        print()
        print(f"✅ 转换成功!")
        print(f"📝 MJCF 文件: {output_path}")
        print()
        
        return True
        
    except Exception as e:
        print(f"\n❌ 转换失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    # 获取项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # RM 机器人
    print("=" * 60)
    print("测试 RM 机器人转换")
    print("=" * 60)
    print()
    
    rm_urdf = project_root / "src/model/RM_Serial_Wheeled-leg_Robot/urdf/RM_Serial_Wheeled-leg_Robot.urdf"
    rm_output = project_root / "src/model/RM_Serial_Wheeled-leg_Robot/mjcf/RM_Serial_Wheeled-leg_Robot_wiki.xml"
    
    rm_success = test_conversion(str(rm_urdf), str(rm_output))
    
    print()
    print("=" * 60)
    print("测试 DM 机器人转换")
    print("=" * 60)
    print()
    
    # DM 机器人
    dm_urdf = project_root / "src/model/DM_Wheel_leg_robot/urdf/wheel_legged_urdf_pkg.urdf"
    dm_output = project_root / "src/model/DM_Wheel_leg_robot/mjcf/wheel_legged_urdf_pkg_wiki.xml"
    
    dm_success = test_conversion(str(dm_urdf), str(dm_output))
    
    print()
    print("=" * 60)
    if rm_success and dm_success:
        print("✅ 所有转换成功!")
    else:
        print("⚠️  部分转换失败")
    print("=" * 60)
    
    return 0 if (rm_success and dm_success) else 1

if __name__ == "__main__":
    sys.exit(main())
