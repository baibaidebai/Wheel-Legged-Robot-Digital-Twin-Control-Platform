#!/usr/bin/env python3
"""
URDF到MJCF转换工具
将URDF机器人模型转换为MuJoCo的MJCF格式
"""

import os
import sys
import xml.etree.ElementTree as ET
import argparse

def convert_urdf_to_mjcf(urdf_path, output_dir=None):
    """
    将URDF文件转换为MJCF格式
    
    Args:
        urdf_path: URDF文件路径
        output_dir: 输出目录（默认为模型目录下的mjcf/）
    """
    
    print(f"🔄 URDF到MJCF转换工具")
    print(f"=" * 60)
    print(f"输入URDF: {urdf_path}")
    print()
    
    # 检查URDF文件
    if not os.path.exists(urdf_path):
        print(f"❌ URDF文件不存在: {urdf_path}")
        return False
    
    # 确定输出目录
    model_dir = os.path.dirname(os.path.dirname(urdf_path))
    if output_dir is None:
        output_dir = os.path.join(model_dir, 'mjcf')
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    print(f"📁 输出目录: {output_dir}")
    
    # 解析URDF
    print("📖 解析URDF文件...")
    tree = ET.parse(urdf_path)
    root = tree.getroot()
    robot_name = root.get('name', 'robot')
    
    # 创建MJCF根元素
    mjcf_root = ET.Element('mujoco', model=robot_name)
    
    # 添加编译器选项
    compiler = ET.SubElement(mjcf_root, 'compiler')
    compiler.set('angle', 'degree')
    compiler.set('meshdir', '../meshes')  # 指向mesh目录
    
    # 添加选项
    option = ET.SubElement(mjcf_root, 'option')
    option.set('timestep', '0.001')
    option.set('gravity', '0 0 -9.81')
    
    # 添加资产
    asset = ET.SubElement(mjcf_root, 'asset')
    texture = ET.SubElement(asset, 'texture')
    texture.set('name', 'grid')
    texture.set('type', '2d')
    texture.set('builtin', 'checker')
    texture.set('rgb1', '0.1 0.2 0.3')
    texture.set('rgb2', '0.2 0.3 0.4')
    texture.set('width', '300')
    texture.set('height', '300')
    
    material = ET.SubElement(asset, 'material')
    material.set('name', 'grid')
    material.set('texture', 'grid')
    material.set('texrepeat', '8 8')
    material.set('reflectance', '0.2')
    
    # 添加世界体
    worldbody = ET.SubElement(mjcf_root, 'worldbody')
    
    # 添加地面
    ground = ET.SubElement(worldbody, 'geom')
    ground.set('name', 'ground')
    ground.set('type', 'plane')
    ground.set('size', '10 10 0.1')
    ground.set('material', 'grid')
    
    # 添加光源
    light = ET.SubElement(worldbody, 'light')
    light.set('name', 'light')
    light.set('pos', '0 0 3')
    
    print("🔧 转换机器人结构...")
    
    # 转换链接和关节
    links = root.findall('link')
    joints = root.findall('joint')
    
    print(f"   找到 {len(links)} 个link")
    print(f"   找到 {len(joints)} 个joint")
    
    # 构建链接层次结构
    link_children = {}
    for joint in joints:
        parent = joint.find('parent').get('link')
        child = joint.find('child').get('link')
        if parent not in link_children:
            link_children[parent] = []
        link_children[parent].append((child, joint))
    
    # 找到根链接（没有父关节的链接）
    child_links = set()
    for joint in joints:
        child_links.add(joint.find('child').get('link'))
    
    root_link = None
    for link in links:
        link_name = link.get('name')
        if link_name not in child_links:
            root_link = link_name
            break
    
    if root_link:
        print(f"   根链接: {root_link}")
        _convert_link_recursive(root, worldbody, root_link, link_children, use_mesh=False)
    
    # 添加执行器
    actuator = ET.SubElement(mjcf_root, 'actuator')
    actuator_count = 0
    for joint in joints:
        joint_type = joint.get('type')
        if joint_type in ['revolute', 'continuous', 'prismatic']:
            motor = ET.SubElement(actuator, 'motor')
            motor.set('name', f"{joint.get('name')}_motor")
            motor.set('joint', joint.get('name'))
            motor.set('gear', '1')
            motor.set('ctrllimited', 'true')
            motor.set('ctrlrange', '-10 10')
            actuator_count += 1
    
    print(f"   添加了 {actuator_count} 个执行器")
    
    # 保存MJCF文件
    urdf_filename = os.path.basename(urdf_path)
    mjcf_filename = urdf_filename.replace('.urdf', '.xml')
    mjcf_path = os.path.join(output_dir, mjcf_filename)
    
    mjcf_tree = ET.ElementTree(mjcf_root)
    ET.indent(mjcf_tree, space="  ", level=0)
    mjcf_tree.write(mjcf_path, encoding='utf-8', xml_declaration=True)
    
    print()
    print(f"✅ 转换成功!")
    print(f"📝 MJCF文件: {mjcf_path}")
    print()
    print("💡 注意：")
    print("   - 使用简单几何体代替STL mesh（MuJoCo URDF mesh路径限制）")
    print("   - 可以手动编辑MJCF文件以调整几何体尺寸和外观")
    print("   - 关节结构和名称保持与URDF一致")
    
    return True

def _convert_link_recursive(urdf_root, parent_body, link_name, link_children, use_mesh=False):
    """递归转换链接"""
    # 查找链接
    link = None
    for l in urdf_root.findall('link'):
        if l.get('name') == link_name:
            link = l
            break
    
    if not link:
        return
    
    # 创建体
    body = ET.SubElement(parent_body, 'body')
    body.set('name', link_name)
    
    # 添加惯性
    inertial = link.find('inertial')
    if inertial is not None:
        inertial_elem = ET.SubElement(body, 'inertial')
        
        # 质量
        mass = inertial.find('mass')
        if mass is not None:
            inertial_elem.set('mass', mass.get('value', '1.0'))
        
        # 位置
        origin = inertial.find('origin')
        if origin is not None:
            xyz = origin.get('xyz', '0 0 0')
            inertial_elem.set('pos', xyz)
        
        # 惯性矩阵
        inertia = inertial.find('inertia')
        if inertia is not None:
            ixx = inertia.get('ixx', '0.1')
            iyy = inertia.get('iyy', '0.1')
            izz = inertia.get('izz', '0.1')
            inertial_elem.set('diaginertia', f'{ixx} {iyy} {izz}')
    
    # 添加几何体（使用简单形状代替mesh）
    for visual in link.findall('visual'):
        _add_simple_geom(body, visual, link_name)
    
    # 处理子链接
    if link_name in link_children:
        for child_link, joint in link_children[link_name]:
            # 添加关节
            _add_joint(body, joint)
            # 递归处理子链接
            _convert_link_recursive(urdf_root, body, child_link, link_children, use_mesh)

def _add_simple_geom(body, visual, link_name):
    """添加简单几何体（代替mesh）"""
    geometry = visual.find('geometry')
    if geometry is None:
        return
    
    geom = ET.SubElement(body, 'geom')
    geom.set('name', f"{link_name}_geom")
    
    # 位置和方向
    origin = visual.find('origin')
    if origin is not None:
        xyz = origin.get('xyz', '0 0 0')
        geom.set('pos', xyz)
    
    # 几何形状
    if geometry.find('box') is not None:
        box = geometry.find('box')
        size = box.get('size', '0.1 0.1 0.1')
        sizes = size.split()
        # MuJoCo box size是半尺寸
        half_sizes = [str(float(s)/2) for s in sizes]
        geom.set('type', 'box')
        geom.set('size', ' '.join(half_sizes))
    elif geometry.find('cylinder') is not None:
        cylinder = geometry.find('cylinder')
        radius = cylinder.get('radius', '0.05')
        length = cylinder.get('length', '0.1')
        geom.set('type', 'cylinder')
        geom.set('size', f'{radius} {float(length)/2}')
    elif geometry.find('sphere') is not None:
        sphere = geometry.find('sphere')
        radius = sphere.get('radius', '0.05')
        geom.set('type', 'sphere')
        geom.set('size', radius)
    elif geometry.find('mesh') is not None:
        # mesh用box代替
        geom.set('type', 'box')
        geom.set('size', '0.05 0.05 0.05')
    else:
        # 默认为盒子
        geom.set('type', 'box')
        geom.set('size', '0.05 0.05 0.05')
    
    # 颜色
    material = visual.find('material')
    if material is not None:
        color = material.find('color')
        if color is not None:
            rgba = color.get('rgba', '0.8 0.8 0.8 1')
            geom.set('rgba', rgba)
    else:
        geom.set('rgba', '0.7 0.7 0.7 1')

def _add_joint(body, joint):
    """添加关节"""
    joint_elem = ET.SubElement(body, 'joint')
    joint_elem.set('name', joint.get('name'))
    
    # 关节类型
    joint_type = joint.get('type', 'revolute')
    if joint_type == 'revolute':
        joint_elem.set('type', 'hinge')
    elif joint_type == 'prismatic':
        joint_elem.set('type', 'slide')
    elif joint_type == 'continuous':
        joint_elem.set('type', 'hinge')
    else:
        joint_elem.set('type', 'hinge')
    
    # 关节轴
    axis = joint.find('axis')
    if axis is not None:
        xyz = axis.get('xyz', '0 0 1')
        joint_elem.set('axis', xyz)
    
    # 关节限制
    limit = joint.find('limit')
    if limit is not None:
        lower = limit.get('lower', '-180')
        upper = limit.get('upper', '180')
        # 转换为度
        try:
            lower_deg = float(lower) * 180 / 3.14159
            upper_deg = float(upper) * 180 / 3.14159
            joint_elem.set('range', f'{lower_deg:.1f} {upper_deg:.1f}')
        except:
            joint_elem.set('range', f'{lower} {upper}')
    
    # 关节原点
    origin = joint.find('origin')
    if origin is not None:
        xyz = origin.get('xyz', '0 0 0')
        joint_elem.set('pos', xyz)
    
    # 添加阻尼
    joint_elem.set('damping', '0.1')

def main():
    parser = argparse.ArgumentParser(description="URDF到MJCF转换工具")
    parser.add_argument(
        "--model",
        type=str,
        choices=["rm", "dm", "both"],
        default="rm",
        help="选择要转换的模型: rm, dm, 或 both"
    )
    parser.add_argument(
        "--urdf",
        type=str,
        help="URDF文件路径（可选，覆盖默认路径）"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="输出目录（可选，默认为模型目录下的mjcf/）"
    )
    
    args = parser.parse_args()
    
    # 获取项目根目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    models_to_convert = []
    
    if args.urdf:
        # 使用指定的URDF文件
        models_to_convert.append((args.urdf, args.output))
    else:
        # 使用默认路径
        if args.model in ["rm", "both"]:
            rm_urdf = os.path.join(
                project_root,
                "src/model/RM_Serial_Wheeled-leg_Robot/urdf/RM_Serial_Wheeled-leg_Robot.urdf"
            )
            models_to_convert.append((rm_urdf, None))
        
        if args.model in ["dm", "both"]:
            dm_urdf = os.path.join(
                project_root,
                "src/model/DM_Wheel_leg_robot/urdf/wheel_legged_urdf_pkg.urdf"
            )
            models_to_convert.append((dm_urdf, None))
    
    # 转换所有模型
    success_count = 0
    for urdf_path, output_dir in models_to_convert:
        if convert_urdf_to_mjcf(urdf_path, output_dir):
            success_count += 1
        print()
    
    print("=" * 60)
    print(f"✅ 成功转换 {success_count}/{len(models_to_convert)} 个模型")
    
    return 0 if success_count == len(models_to_convert) else 1

if __name__ == "__main__":
    sys.exit(main())
