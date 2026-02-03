"""
URDF加载器模块

负责解析和加载轮腿机器人的URDF模型文件，提取关节信息、链接信息和约束关系。
"""

import os
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import numpy as np
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class JointInfo:
    """关节信息数据类"""
    name: str
    joint_type: str
    parent_link: str
    child_link: str
    origin_xyz: Tuple[float, float, float]
    origin_rpy: Tuple[float, float, float]
    axis_xyz: Tuple[float, float, float]
    limit_lower: Optional[float] = None
    limit_upper: Optional[float] = None
    limit_effort: Optional[float] = None
    limit_velocity: Optional[float] = None
    dynamics_damping: float = 0.0
    dynamics_friction: float = 0.0


@dataclass
class LinkInfo:
    """链接信息数据类"""
    name: str
    mass: float
    inertia_matrix: np.ndarray
    center_of_mass: Tuple[float, float, float]
    visual_geometry: Optional[str] = None
    collision_geometry: Optional[str] = None
    mesh_filename: Optional[str] = None


@dataclass
class RobotModel:
    """机器人模型数据类"""
    name: str
    links: Dict[str, LinkInfo]
    joints: Dict[str, JointInfo]
    joint_names: List[str]
    link_names: List[str]
    wheel_joints: List[str]
    leg_joints: List[str]
    base_link: str


class URDFParseError(Exception):
    """URDF解析错误异常"""
    pass


class URDFLoader:
    """
    URDF加载器类
    
    负责解析轮腿机器人URDF文件，提取机器人结构信息，
    为数字孪生映射器提供基础数据。
    """
    
    def __init__(self):
        """初始化URDF加载器"""
        self.robot_model: Optional[RobotModel] = None
        self._supported_joint_types = {'revolute', 'continuous', 'prismatic', 'fixed'}
        
    def load_urdf(self, urdf_path: str) -> RobotModel:
        """
        加载URDF文件
        
        Args:
            urdf_path: URDF文件路径
            
        Returns:
            RobotModel: 解析后的机器人模型
            
        Raises:
            URDFParseError: URDF解析失败
            FileNotFoundError: 文件不存在
        """
        if not os.path.exists(urdf_path):
            raise FileNotFoundError(f"URDF文件不存在: {urdf_path}")
            
        try:
            logger.info(f"开始加载URDF文件: {urdf_path}")
            
            # 解析XML文件
            tree = ET.parse(urdf_path)
            root = tree.getroot()
            
            if root.tag != 'robot':
                raise URDFParseError("URDF文件格式错误：根元素必须是'robot'")
                
            # 提取机器人名称
            robot_name = root.get('name', 'unknown_robot')
            
            # 解析链接和关节
            links = self._parse_links(root)
            joints = self._parse_joints(root)
            
            # 分析机器人结构
            joint_names = list(joints.keys())
            link_names = list(links.keys())
            wheel_joints, leg_joints = self._classify_joints(joints)
            base_link = self._find_base_link(links, joints)
            
            # 创建机器人模型
            self.robot_model = RobotModel(
                name=robot_name,
                links=links,
                joints=joints,
                joint_names=joint_names,
                link_names=link_names,
                wheel_joints=wheel_joints,
                leg_joints=leg_joints,
                base_link=base_link
            )
            
            logger.info(f"URDF加载成功: {robot_name}")
            logger.info(f"  - 链接数量: {len(links)}")
            logger.info(f"  - 关节数量: {len(joints)}")
            logger.info(f"  - 轮子关节: {wheel_joints}")
            logger.info(f"  - 腿部关节: {leg_joints}")
            
            return self.robot_model
            
        except ET.ParseError as e:
            raise URDFParseError(f"XML解析错误: {e}")
        except Exception as e:
            raise URDFParseError(f"URDF加载失败: {e}")
    
    def _parse_links(self, root: ET.Element) -> Dict[str, LinkInfo]:
        """解析链接信息"""
        links = {}
        
        for link_elem in root.findall('link'):
            link_name = link_elem.get('name')
            if not link_name:
                continue
                
            # 解析惯性信息
            inertial_elem = link_elem.find('inertial')
            if inertial_elem is not None:
                mass_elem = inertial_elem.find('mass')
                mass = float(mass_elem.get('value', 0.0)) if mass_elem is not None else 0.0
                
                origin_elem = inertial_elem.find('origin')
                if origin_elem is not None:
                    xyz_str = origin_elem.get('xyz', '0 0 0')
                    center_of_mass = tuple(map(float, xyz_str.split()))
                else:
                    center_of_mass = (0.0, 0.0, 0.0)
                
                inertia_elem = inertial_elem.find('inertia')
                if inertia_elem is not None:
                    ixx = float(inertia_elem.get('ixx', 0.0))
                    ixy = float(inertia_elem.get('ixy', 0.0))
                    ixz = float(inertia_elem.get('ixz', 0.0))
                    iyy = float(inertia_elem.get('iyy', 0.0))
                    iyz = float(inertia_elem.get('iyz', 0.0))
                    izz = float(inertia_elem.get('izz', 0.0))
                    
                    inertia_matrix = np.array([
                        [ixx, ixy, ixz],
                        [ixy, iyy, iyz],
                        [ixz, iyz, izz]
                    ])
                else:
                    inertia_matrix = np.eye(3)
            else:
                mass = 0.0
                center_of_mass = (0.0, 0.0, 0.0)
                inertia_matrix = np.eye(3)
            
            # 解析视觉信息
            visual_elem = link_elem.find('visual')
            mesh_filename = None
            if visual_elem is not None:
                geometry_elem = visual_elem.find('geometry')
                if geometry_elem is not None:
                    mesh_elem = geometry_elem.find('mesh')
                    if mesh_elem is not None:
                        mesh_filename = mesh_elem.get('filename')
            
            # 创建链接信息
            link_info = LinkInfo(
                name=link_name,
                mass=mass,
                inertia_matrix=inertia_matrix,
                center_of_mass=center_of_mass,
                mesh_filename=mesh_filename
            )
            
            links[link_name] = link_info
            
        return links
    
    def _parse_joints(self, root: ET.Element) -> Dict[str, JointInfo]:
        """解析关节信息"""
        joints = {}
        
        for joint_elem in root.findall('joint'):
            joint_name = joint_elem.get('name')
            joint_type = joint_elem.get('type')
            
            if not joint_name or joint_type not in self._supported_joint_types:
                continue
            
            # 解析父子链接
            parent_elem = joint_elem.find('parent')
            child_elem = joint_elem.find('child')
            
            if parent_elem is None or child_elem is None:
                continue
                
            parent_link = parent_elem.get('link')
            child_link = child_elem.get('link')
            
            # 解析原点信息
            origin_elem = joint_elem.find('origin')
            if origin_elem is not None:
                xyz_str = origin_elem.get('xyz', '0 0 0')
                rpy_str = origin_elem.get('rpy', '0 0 0')
                origin_xyz = tuple(map(float, xyz_str.split()))
                origin_rpy = tuple(map(float, rpy_str.split()))
            else:
                origin_xyz = (0.0, 0.0, 0.0)
                origin_rpy = (0.0, 0.0, 0.0)
            
            # 解析轴信息
            axis_elem = joint_elem.find('axis')
            if axis_elem is not None:
                xyz_str = axis_elem.get('xyz', '0 0 1')
                axis_xyz = tuple(map(float, xyz_str.split()))
            else:
                axis_xyz = (0.0, 0.0, 1.0)
            
            # 解析限制信息
            limit_elem = joint_elem.find('limit')
            limit_lower = limit_upper = limit_effort = limit_velocity = None
            
            if limit_elem is not None:
                if limit_elem.get('lower'):
                    limit_lower = float(limit_elem.get('lower'))
                if limit_elem.get('upper'):
                    limit_upper = float(limit_elem.get('upper'))
                if limit_elem.get('effort'):
                    limit_effort = float(limit_elem.get('effort'))
                if limit_elem.get('velocity'):
                    limit_velocity = float(limit_elem.get('velocity'))
            
            # 解析动力学信息
            dynamics_elem = joint_elem.find('dynamics')
            dynamics_damping = dynamics_friction = 0.0
            
            if dynamics_elem is not None:
                if dynamics_elem.get('damping'):
                    dynamics_damping = float(dynamics_elem.get('damping'))
                if dynamics_elem.get('friction'):
                    dynamics_friction = float(dynamics_elem.get('friction'))
            
            # 创建关节信息
            joint_info = JointInfo(
                name=joint_name,
                joint_type=joint_type,
                parent_link=parent_link,
                child_link=child_link,
                origin_xyz=origin_xyz,
                origin_rpy=origin_rpy,
                axis_xyz=axis_xyz,
                limit_lower=limit_lower,
                limit_upper=limit_upper,
                limit_effort=limit_effort,
                limit_velocity=limit_velocity,
                dynamics_damping=dynamics_damping,
                dynamics_friction=dynamics_friction
            )
            
            joints[joint_name] = joint_info
            
        return joints
    
    def _classify_joints(self, joints: Dict[str, JointInfo]) -> Tuple[List[str], List[str]]:
        """
        分类关节为轮子关节和腿部关节
        
        Args:
            joints: 关节信息字典
            
        Returns:
            Tuple[List[str], List[str]]: (轮子关节列表, 腿部关节列表)
        """
        wheel_joints = []
        leg_joints = []
        
        for joint_name, joint_info in joints.items():
            # 根据关节名称和子链接名称判断类型
            if 'wheel' in joint_name.lower() or 'wheel' in joint_info.child_link.lower():
                wheel_joints.append(joint_name)
            elif any(leg_prefix in joint_name.lower() for leg_prefix in ['lf', 'rf', 'lb', 'rb', 'leg']):
                leg_joints.append(joint_name)
            else:
                # 默认归类为腿部关节
                leg_joints.append(joint_name)
                
        return wheel_joints, leg_joints
    
    def _find_base_link(self, links: Dict[str, LinkInfo], joints: Dict[str, JointInfo]) -> str:
        """
        查找基座链接
        
        Args:
            links: 链接信息字典
            joints: 关节信息字典
            
        Returns:
            str: 基座链接名称
        """
        # 查找没有父关节的链接作为基座
        child_links = {joint.child_link for joint in joints.values()}
        
        for link_name in links.keys():
            if link_name not in child_links:
                return link_name
                
        # 如果没找到，查找名称包含'base'的链接
        for link_name in links.keys():
            if 'base' in link_name.lower():
                return link_name
                
        # 默认返回第一个链接
        return list(links.keys())[0] if links else 'base_link'
    
    def get_joint_limits(self) -> Dict[str, Tuple[float, float]]:
        """
        获取所有关节的限制范围
        
        Returns:
            Dict[str, Tuple[float, float]]: 关节名称到(下限, 上限)的映射
        """
        if not self.robot_model:
            return {}
            
        limits = {}
        for joint_name, joint_info in self.robot_model.joints.items():
            if joint_info.limit_lower is not None and joint_info.limit_upper is not None:
                limits[joint_name] = (joint_info.limit_lower, joint_info.limit_upper)
            else:
                # 默认限制范围
                limits[joint_name] = (-np.pi, np.pi)
                
        return limits
    
    def get_joint_efforts(self) -> Dict[str, float]:
        """
        获取所有关节的力矩限制
        
        Returns:
            Dict[str, float]: 关节名称到最大力矩的映射
        """
        if not self.robot_model:
            return {}
            
        efforts = {}
        for joint_name, joint_info in self.robot_model.joints.items():
            efforts[joint_name] = joint_info.limit_effort or 30.0  # 默认30N·m
            
        return efforts
    
    def get_joint_velocities(self) -> Dict[str, float]:
        """
        获取所有关节的速度限制
        
        Returns:
            Dict[str, float]: 关节名称到最大速度的映射
        """
        if not self.robot_model:
            return {}
            
        velocities = {}
        for joint_name, joint_info in self.robot_model.joints.items():
            velocities[joint_name] = joint_info.limit_velocity or 1000.0  # 默认1000rad/s
            
        return velocities
    
    def validate_urdf(self) -> List[str]:
        """
        验证URDF模型的完整性
        
        Returns:
            List[str]: 验证错误信息列表，空列表表示验证通过
        """
        if not self.robot_model:
            return ["未加载URDF模型"]
            
        errors = []
        
        # 检查基本结构
        if not self.robot_model.links:
            errors.append("未找到任何链接")
            
        if not self.robot_model.joints:
            errors.append("未找到任何关节")
            
        # 检查轮腿机器人特定结构
        if not self.robot_model.wheel_joints:
            errors.append("未找到轮子关节")
            
        if not self.robot_model.leg_joints:
            errors.append("未找到腿部关节")
            
        # 检查关节连接的完整性
        for joint_name, joint_info in self.robot_model.joints.items():
            if joint_info.parent_link not in self.robot_model.links:
                errors.append(f"关节 {joint_name} 的父链接 {joint_info.parent_link} 不存在")
                
            if joint_info.child_link not in self.robot_model.links:
                errors.append(f"关节 {joint_name} 的子链接 {joint_info.child_link} 不存在")
        
        return errors
    
    def get_robot_info(self) -> Dict[str, Any]:
        """
        获取机器人信息摘要
        
        Returns:
            Dict[str, Any]: 机器人信息字典
        """
        if not self.robot_model:
            return {}
            
        total_mass = sum(link.mass for link in self.robot_model.links.values())
        
        return {
            'name': self.robot_model.name,
            'total_mass': total_mass,
            'num_links': len(self.robot_model.links),
            'num_joints': len(self.robot_model.joints),
            'wheel_joints': self.robot_model.wheel_joints,
            'leg_joints': self.robot_model.leg_joints,
            'base_link': self.robot_model.base_link,
            'joint_limits': self.get_joint_limits(),
            'joint_efforts': self.get_joint_efforts(),
            'joint_velocities': self.get_joint_velocities()
        }


def load_robot_from_directory(robot_dir: str) -> RobotModel:
    """
    从目录加载机器人模型
    
    Args:
        robot_dir: 机器人模型目录路径
        
    Returns:
        RobotModel: 加载的机器人模型
        
    Raises:
        FileNotFoundError: 未找到URDF文件
        URDFParseError: URDF解析失败
    """
    # 查找URDF文件
    urdf_files = []
    for file in os.listdir(robot_dir):
        if file.endswith('.urdf'):
            urdf_files.append(os.path.join(robot_dir, file))
    
    if not urdf_files:
        raise FileNotFoundError(f"在目录 {robot_dir} 中未找到URDF文件")
    
    # 使用第一个找到的URDF文件
    urdf_path = urdf_files[0]
    
    loader = URDFLoader()
    return loader.load_urdf(urdf_path)


if __name__ == "__main__":
    # 测试代码
    try:
        # 测试加载现有的机器人模型
        robot_dir = "src/robot/urdf/RM_Serial_Wheeled-leg_Robot"
        if os.path.exists(robot_dir):
            robot_model = load_robot_from_directory(robot_dir)
            
            loader = URDFLoader()
            loader.robot_model = robot_model
            
            print("机器人信息:")
            info = loader.get_robot_info()
            for key, value in info.items():
                print(f"  {key}: {value}")
                
            print("\n验证结果:")
            errors = loader.validate_urdf()
            if errors:
                for error in errors:
                    print(f"  错误: {error}")
            else:
                print("  验证通过")
        else:
            print(f"机器人目录不存在: {robot_dir}")
            
    except Exception as e:
        print(f"测试失败: {e}")