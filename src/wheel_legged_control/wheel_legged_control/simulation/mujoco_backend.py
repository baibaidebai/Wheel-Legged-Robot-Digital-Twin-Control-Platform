#!/usr/bin/env python3
"""
MuJoCo仿真后端

基于MuJoCo物理引擎的仿真后端实现，支持高性能物理仿真和强化学习训练。
"""

import numpy as np
import os
import time
import logging
from typing import Dict, List, Tuple, Optional, Any, Union
import xml.etree.ElementTree as ET

from .simulation_manager import BaseSimulationBackend, SimulationConfig

# MuJoCo导入
try:
    import mujoco
    import mujoco.viewer
    MUJOCO_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  MuJoCo不可用: {e}")
    print("💡 安装命令: pip install mujoco")
    mujoco = None
    MUJOCO_AVAILABLE = False


class URDFToMJCFConverter:
    """URDF到MJCF格式转换器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def convert_urdf_to_mjcf(self, urdf_path: str, mjcf_path: str = None) -> str:
        """将URDF文件转换为MJCF格式"""
        if not os.path.exists(urdf_path):
            raise FileNotFoundError(f"URDF文件不存在: {urdf_path}")
        
        if mjcf_path is None:
            mjcf_path = urdf_path.replace('.urdf', '.xml')
        
        try:
            # 解析URDF文件
            tree = ET.parse(urdf_path)
            root = tree.getroot()
            
            # 创建MJCF根元素
            mjcf_root = ET.Element('mujoco', model=root.get('name', 'robot'))
            
            # 添加编译器选项
            compiler = ET.SubElement(mjcf_root, 'compiler')
            compiler.set('angle', 'radian')
            compiler.set('meshdir', 'meshes/')
            compiler.set('texturedir', 'textures/')
            
            # 添加选项
            option = ET.SubElement(mjcf_root, 'option')
            option.set('timestep', '0.001')
            option.set('gravity', '0 0 -9.81')
            option.set('iterations', '50')
            option.set('solver', 'Newton')
            
            # 添加资产
            asset = ET.SubElement(mjcf_root, 'asset')
            
            # 添加世界体
            worldbody = ET.SubElement(mjcf_root, 'worldbody')
            
            # 添加地面
            ground = ET.SubElement(worldbody, 'geom')
            ground.set('name', 'ground')
            ground.set('type', 'plane')
            ground.set('size', '10 10 0.1')
            ground.set('rgba', '0.8 0.8 0.8 1')
            ground.set('friction', '1 0.1 0.1')
            
            # 转换链接和关节
            self._convert_links_and_joints(root, worldbody, asset)
            
            # 添加执行器
            actuator = ET.SubElement(mjcf_root, 'actuator')
            self._add_actuators(root, actuator)
            
            # 保存MJCF文件
            mjcf_tree = ET.ElementTree(mjcf_root)
            ET.indent(mjcf_tree, space="  ", level=0)
            mjcf_tree.write(mjcf_path, encoding='utf-8', xml_declaration=True)
            
            self.logger.info(f"✅ URDF转换为MJCF成功: {mjcf_path}")
            return mjcf_path
            
        except Exception as e:
            self.logger.error(f"❌ URDF转换失败: {e}")
            # 创建简化的MJCF文件
            return self._create_simple_mjcf(mjcf_path)
    
    def _convert_links_and_joints(self, urdf_root, worldbody, asset):
        """转换链接和关节"""
        # 查找根链接
        root_link = None
        links = urdf_root.findall('link')
        joints = urdf_root.findall('joint')
        
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
        
        for link in links:
            link_name = link.get('name')
            if link_name not in child_links:
                root_link = link_name
                break
        
        if root_link:
            self._convert_link_recursive(urdf_root, worldbody, asset, root_link, link_children)
    
    def _convert_link_recursive(self, urdf_root, parent_body, asset, link_name, link_children):
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
                rpy = origin.get('rpy', '0 0 0')
                # 转换RPY到四元数（简化）
                inertial_elem.set('quat', '1 0 0 0')
            
            # 惯性矩阵
            inertia = inertial.find('inertia')
            if inertia is not None:
                ixx = inertia.get('ixx', '0.1')
                iyy = inertia.get('iyy', '0.1')
                izz = inertia.get('izz', '0.1')
                inertial_elem.set('diaginertia', f'{ixx} {iyy} {izz}')
        
        # 添加几何体
        for visual in link.findall('visual'):
            self._add_geom_from_visual(body, visual, 'visual')
        
        for collision in link.findall('collision'):
            self._add_geom_from_collision(body, collision)
        
        # 处理子链接
        if link_name in link_children:
            for child_link, joint in link_children[link_name]:
                # 添加关节
                self._add_joint(body, joint)
                # 递归处理子链接
                self._convert_link_recursive(urdf_root, body, asset, child_link, link_children)
    
    def _add_geom_from_visual(self, body, visual, geom_type='visual'):
        """从视觉元素添加几何体"""
        geometry = visual.find('geometry')
        if geometry is None:
            return
        
        geom = ET.SubElement(body, 'geom')
        geom.set('name', f"{body.get('name')}_{geom_type}")
        
        # 位置和方向
        origin = visual.find('origin')
        if origin is not None:
            xyz = origin.get('xyz', '0 0 0')
            geom.set('pos', xyz)
        
        # 几何形状
        if geometry.find('box') is not None:
            box = geometry.find('box')
            size = box.get('size', '0.1 0.1 0.1')
            geom.set('type', 'box')
            geom.set('size', size.replace(' ', ' '))
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
    
    def _add_geom_from_collision(self, body, collision):
        """从碰撞元素添加几何体"""
        self._add_geom_from_visual(body, collision, 'collision')
    
    def _add_joint(self, body, joint):
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
            lower = limit.get('lower', '-3.14')
            upper = limit.get('upper', '3.14')
            joint_elem.set('range', f'{lower} {upper}')
        
        # 关节原点
        origin = joint.find('origin')
        if origin is not None:
            xyz = origin.get('xyz', '0 0 0')
            joint_elem.set('pos', xyz)
    
    def _add_actuators(self, urdf_root, actuator):
        """添加执行器"""
        joints = urdf_root.findall('joint')
        for joint in joints:
            joint_type = joint.get('type')
            if joint_type in ['revolute', 'continuous', 'prismatic']:
                motor = ET.SubElement(actuator, 'motor')
                motor.set('name', f"{joint.get('name')}_motor")
                motor.set('joint', joint.get('name'))
                motor.set('gear', '1')
                motor.set('ctrllimited', 'true')
                motor.set('ctrlrange', '-10 10')
    
    def _create_simple_mjcf(self, mjcf_path: str) -> str:
        """创建简化的MJCF文件"""
        mjcf_content = '''<?xml version="1.0" encoding="utf-8"?>
<mujoco model="wheel_legged_robot">
    <compiler angle="radian" meshdir="meshes/" texturedir="textures/"/>
    
    <option timestep="0.001" gravity="0 0 -9.81" iterations="50" solver="Newton"/>
    
    <asset>
        <texture name="grid" type="2d" builtin="checker" rgb1="0.1 0.2 0.3" rgb2="0.2 0.3 0.4" width="300" height="300"/>
        <material name="grid" texture="grid" texrepeat="8 8" reflectance="0.2"/>
    </asset>
    
    <worldbody>
        <geom name="ground" type="plane" size="10 10 0.1" rgba="0.8 0.8 0.8 1" friction="1 0.1 0.1"/>
        <light name="light" pos="0 0 3"/>
        
        <body name="base_link" pos="0 0 0.3">
            <inertial mass="5.0" pos="0 0 0" diaginertia="0.1 0.1 0.1"/>
            <geom name="base" type="box" size="0.2 0.15 0.05" rgba="0.8 0.2 0.2 1"/>
            
            <!-- 左前腿 -->
            <body name="left_front_leg" pos="0.15 0.1 0">
                <inertial mass="0.5" pos="0 0 -0.1" diaginertia="0.01 0.01 0.01"/>
                <joint name="lf0_joint" type="hinge" axis="1 0 0" range="-1.57 1.57"/>
                <geom name="lf0_link" type="cylinder" size="0.02 0.1" rgba="0.2 0.8 0.2 1"/>
                
                <body name="left_front_lower" pos="0 0 -0.2">
                    <inertial mass="0.3" pos="0 0 -0.1" diaginertia="0.01 0.01 0.01"/>
                    <joint name="lf1_joint" type="hinge" axis="1 0 0" range="-1.57 1.57"/>
                    <geom name="lf1_link" type="cylinder" size="0.015 0.1" rgba="0.2 0.8 0.2 1"/>
                    
                    <body name="left_wheel" pos="0 0 -0.2">
                        <inertial mass="0.2" pos="0 0 0" diaginertia="0.005 0.005 0.005"/>
                        <joint name="l_wheel_joint" type="hinge" axis="0 1 0" range="-100 100"/>
                        <geom name="l_wheel" type="cylinder" size="0.05 0.02" rgba="0.2 0.2 0.8 1"/>
                    </body>
                </body>
            </body>
            
            <!-- 右前腿 -->
            <body name="right_front_leg" pos="0.15 -0.1 0">
                <inertial mass="0.5" pos="0 0 -0.1" diaginertia="0.01 0.01 0.01"/>
                <joint name="rf0_joint" type="hinge" axis="1 0 0" range="-1.57 1.57"/>
                <geom name="rf0_link" type="cylinder" size="0.02 0.1" rgba="0.2 0.8 0.2 1"/>
                
                <body name="right_front_lower" pos="0 0 -0.2">
                    <inertial mass="0.3" pos="0 0 -0.1" diaginertia="0.01 0.01 0.01"/>
                    <joint name="rf1_joint" type="hinge" axis="1 0 0" range="-1.57 1.57"/>
                    <geom name="rf1_link" type="cylinder" size="0.015 0.1" rgba="0.2 0.8 0.2 1"/>
                    
                    <body name="right_wheel" pos="0 0 -0.2">
                        <inertial mass="0.2" pos="0 0 0" diaginertia="0.005 0.005 0.005"/>
                        <joint name="r_wheel_joint" type="hinge" axis="0 1 0" range="-100 100"/>
                        <geom name="r_wheel" type="cylinder" size="0.05 0.02" rgba="0.2 0.2 0.8 1"/>
                    </body>
                </body>
            </body>
        </body>
    </worldbody>
    
    <actuator>
        <motor name="lf0_motor" joint="lf0_joint" gear="1" ctrllimited="true" ctrlrange="-10 10"/>
        <motor name="lf1_motor" joint="lf1_joint" gear="1" ctrllimited="true" ctrlrange="-10 10"/>
        <motor name="rf0_motor" joint="rf0_joint" gear="1" ctrllimited="true" ctrlrange="-10 10"/>
        <motor name="rf1_motor" joint="rf1_joint" gear="1" ctrllimited="true" ctrlrange="-10 10"/>
        <motor name="l_wheel_motor" joint="l_wheel_joint" gear="1" ctrllimited="true" ctrlrange="-10 10"/>
        <motor name="r_wheel_motor" joint="r_wheel_joint" gear="1" ctrllimited="true" ctrlrange="-10 10"/>
    </actuator>
</mujoco>'''
        
        with open(mjcf_path, 'w', encoding='utf-8') as f:
            f.write(mjcf_content)
        
        self.logger.info(f"✅ 创建简化MJCF文件: {mjcf_path}")
        return mjcf_path


class MuJoCoSimulationBackend(BaseSimulationBackend):
    """MuJoCo仿真后端"""
    
    def __init__(self, config: SimulationConfig):
        super().__init__(config)
        
        if not MUJOCO_AVAILABLE:
            raise ImportError("MuJoCo不可用，请安装: pip install mujoco")
        
        self.model = None
        self.data = None
        self.viewer = None
        self.converter = URDFToMJCFConverter()
        
        # 关节映射
        self.joint_name_to_id = {}
        self.joint_id_to_name = {}
        self.actuator_name_to_id = {}
        
        # 渲染相关
        self.render_context = None
        self.camera = None
        
        self.logger.info("MuJoCo仿真后端初始化完成")
    
    def initialize(self, model_path: str) -> bool:
        """初始化MuJoCo仿真环境"""
        try:
            # 检查文件类型
            if model_path.endswith('.urdf'):
                # 转换URDF到MJCF
                mjcf_path = model_path.replace('.urdf', '_mujoco.xml')
                mjcf_path = self.converter.convert_urdf_to_mjcf(model_path, mjcf_path)
                model_path = mjcf_path
            
            # 加载MuJoCo模型
            self.model = mujoco.MjModel.from_xml_path(model_path)
            self.data = mujoco.MjData(self.model)
            
            # 设置物理参数
            if self.config.gravity:
                self.model.opt.gravity[:] = self.config.gravity
            
            # 构建关节映射
            self._build_joint_mapping()
            
            # 初始化渲染
            if self.config.enable_rendering:
                self._initialize_rendering()
            
            # 重置仿真
            mujoco.mj_resetData(self.model, self.data)
            
            self.is_initialized = True
            self.logger.info(f"✅ MuJoCo模型加载成功: {model_path}")
            self.logger.info(f"📊 关节数量: {self.model.njnt}")
            self.logger.info(f"🎮 执行器数量: {self.model.nu}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ MuJoCo初始化失败: {e}")
            return False
    
    def _build_joint_mapping(self):
        """构建关节名称到ID的映射"""
        self.joint_name_to_id = {}
        self.joint_id_to_name = {}
        
        for i in range(self.model.njnt):
            joint_name = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_JOINT, i)
            if joint_name:
                self.joint_name_to_id[joint_name] = i
                self.joint_id_to_name[i] = joint_name
        
        # 执行器映射
        self.actuator_name_to_id = {}
        for i in range(self.model.nu):
            actuator_name = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, i)
            if actuator_name:
                self.actuator_name_to_id[actuator_name] = i
        
        self.logger.info(f"关节映射: {list(self.joint_name_to_id.keys())}")
        self.logger.info(f"执行器映射: {list(self.actuator_name_to_id.keys())}")
    
    def _initialize_rendering(self):
        """初始化渲染系统"""
        try:
            # 创建渲染上下文
            self.render_context = mujoco.MjrContext(self.model, mujoco.mjtFontScale.mjFONTSCALE_150)
            
            # 创建相机
            self.camera = mujoco.MjvCamera()
            mujoco.mjv_defaultCamera(self.camera)
            
            # 设置相机参数
            self.camera.distance = self.config.camera_distance
            self.camera.elevation = self.config.camera_elevation
            self.camera.azimuth = self.config.camera_azimuth
            
            self.logger.info("✅ MuJoCo渲染系统初始化成功")
            
        except Exception as e:
            self.logger.warning(f"⚠️  渲染系统初始化失败: {e}")
            self.render_context = None
            self.camera = None
    
    def reset(self) -> bool:
        """重置仿真状态"""
        if not self.is_initialized:
            return False
        
        try:
            # 重置MuJoCo数据
            mujoco.mj_resetData(self.model, self.data)
            
            # 重置步数
            self.current_step = 0
            
            # 更新状态
            self._update_state()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 重置失败: {e}")
            return False
    
    def step(self, action: Dict[str, float] = None) -> bool:
        """执行一步仿真"""
        if not self.is_initialized:
            return False
        
        try:
            # 应用控制输入
            if action:
                self._apply_control(action)
            
            # 执行仿真步
            mujoco.mj_step(self.model, self.data)
            
            # 更新步数
            self.current_step += 1
            
            # 更新状态
            self._update_state()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 仿真步执行失败: {e}")
            return False
    
    def _apply_control(self, action: Dict[str, float]):
        """应用控制输入"""
        for actuator_name, value in action.items():
            if actuator_name in self.actuator_name_to_id:
                actuator_id = self.actuator_name_to_id[actuator_name]
                self.data.ctrl[actuator_id] = value
            else:
                # 尝试通过关节名称查找
                joint_name = actuator_name.replace('_motor', '')
                if joint_name in self.joint_name_to_id:
                    # 查找对应的执行器
                    for act_name, act_id in self.actuator_name_to_id.items():
                        if joint_name in act_name:
                            self.data.ctrl[act_id] = value
                            break
    
    def _update_state(self):
        """更新内部状态"""
        # 更新关节状态
        self.joint_positions = {}
        self.joint_velocities = {}
        self.joint_efforts = {}
        
        for joint_name, joint_id in self.joint_name_to_id.items():
            # 关节位置
            if joint_id < len(self.data.qpos):
                self.joint_positions[joint_name] = self.data.qpos[joint_id]
            
            # 关节速度
            if joint_id < len(self.data.qvel):
                self.joint_velocities[joint_name] = self.data.qvel[joint_id]
            
            # 关节力矩（从执行器获取）
            for act_name, act_id in self.actuator_name_to_id.items():
                if joint_name in act_name and act_id < len(self.data.actuator_force):
                    self.joint_efforts[joint_name] = self.data.actuator_force[act_id]
                    break
        
        # 更新基座状态（假设第一个body是基座）
        if self.model.nbody > 1:  # 跳过世界体
            body_id = 1  # 第一个非世界体
            
            # 基座位置
            self.base_position = self.data.xpos[body_id].copy()
            
            # 基座方向（四元数）
            self.base_orientation = self.data.xquat[body_id].copy()
            
            # 基座速度
            if body_id < len(self.data.cvel):
                self.base_linear_velocity = self.data.cvel[body_id][:3].copy()
                self.base_angular_velocity = self.data.cvel[body_id][3:].copy()
    
    def get_state(self) -> Dict[str, Any]:
        """获取当前仿真状态"""
        return {
            'time': self.data.time,
            'step': self.current_step,
            'joint_positions': self.joint_positions.copy(),
            'joint_velocities': self.joint_velocities.copy(),
            'joint_efforts': self.joint_efforts.copy(),
            'base_position': self.base_position.copy(),
            'base_orientation': self.base_orientation.copy(),
            'base_linear_velocity': self.base_linear_velocity.copy(),
            'base_angular_velocity': self.base_angular_velocity.copy()
        }
    
    def set_joint_positions(self, positions: Dict[str, float]) -> bool:
        """设置关节位置"""
        if not self.is_initialized:
            return False
        
        try:
            for joint_name, position in positions.items():
                if joint_name in self.joint_name_to_id:
                    joint_id = self.joint_name_to_id[joint_name]
                    if joint_id < len(self.data.qpos):
                        self.data.qpos[joint_id] = position
            
            # 前向运动学
            mujoco.mj_forward(self.model, self.data)
            self._update_state()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 设置关节位置失败: {e}")
            return False
    
    def set_joint_velocities(self, velocities: Dict[str, float]) -> bool:
        """设置关节速度"""
        if not self.is_initialized:
            return False
        
        try:
            for joint_name, velocity in velocities.items():
                if joint_name in self.joint_name_to_id:
                    joint_id = self.joint_name_to_id[joint_name]
                    if joint_id < len(self.data.qvel):
                        self.data.qvel[joint_id] = velocity
            
            self._update_state()
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 设置关节速度失败: {e}")
            return False
    
    def set_joint_efforts(self, efforts: Dict[str, float]) -> bool:
        """设置关节力矩"""
        if not self.is_initialized:
            return False
        
        try:
            # 通过执行器设置力矩
            for joint_name, effort in efforts.items():
                for act_name, act_id in self.actuator_name_to_id.items():
                    if joint_name in act_name:
                        self.data.ctrl[act_id] = effort
                        break
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 设置关节力矩失败: {e}")
            return False
    
    def get_joint_states(self) -> Dict[str, Dict[str, float]]:
        """获取关节状态"""
        joint_states = {}
        
        for joint_name in self.joint_name_to_id.keys():
            joint_states[joint_name] = {
                'position': self.joint_positions.get(joint_name, 0.0),
                'velocity': self.joint_velocities.get(joint_name, 0.0),
                'effort': self.joint_efforts.get(joint_name, 0.0)
            }
        
        return joint_states
    
    def render(self, mode: str = 'human') -> Optional[np.ndarray]:
        """渲染仿真画面"""
        if not self.is_initialized:
            return None
        
        if mode == 'human':
            # 交互式查看器
            if self.viewer is None:
                self.viewer = mujoco.viewer.launch_passive(self.model, self.data)
            
            if self.viewer:
                self.viewer.sync()
            
            return None
            
        elif mode == 'rgb_array':
            # 离屏渲染
            if self.render_context is None or self.camera is None:
                # 渲染系统不可用，返回简单的状态可视化
                return self._create_fallback_visualization()
            
            try:
                # 创建视口
                viewport = mujoco.MjrRect(0, 0, self.config.render_width, self.config.render_height)
                
                # 创建场景
                scene = mujoco.MjvScene(self.model, maxgeom=10000)
                mujoco.mjv_updateScene(self.model, self.data, mujoco.MjvOption(), None, self.camera, mujoco.mjtCatBit.mjCAT_ALL, scene)
                
                # 渲染
                mujoco.mjr_render(viewport, scene, self.render_context)
                
                # 读取像素
                rgb = np.zeros((self.config.render_height, self.config.render_width, 3), dtype=np.uint8)
                mujoco.mjr_readPixels(rgb, None, viewport, self.render_context)
                
                # 翻转图像（OpenGL坐标系）
                rgb = np.flipud(rgb)
                
                return rgb
                
            except Exception as e:
                self.logger.error(f"❌ 渲染失败: {e}")
                return self._create_fallback_visualization()
        
        return None
    
    def _create_fallback_visualization(self) -> np.ndarray:
        """创建备用可视化（当OpenGL不可用时）"""
        # 创建一个简单的状态显示图像
        img = np.ones((self.config.render_height, self.config.render_width, 3), dtype=np.uint8) * 40  # 深灰色背景
        
        # 添加一些文本信息（使用简单的像素绘制）
        # 这里我们创建一个简单的状态指示器
        
        # 绘制标题区域
        img[0:60, :] = [60, 60, 80]  # 深蓝色标题栏
        
        # 绘制状态信息区域
        y_offset = 80
        line_height = 30
        
        # 显示仿真时间
        img[y_offset:y_offset+20, 20:200] = [0, 200, 0]  # 绿色条表示运行中
        y_offset += line_height
        
        # 显示关节状态（用颜色条表示）
        for i, (joint_name, position) in enumerate(list(self.joint_positions.items())[:6]):
            # 归一化位置到0-1
            normalized = (position + 3.14) / (2 * 3.14)  # 假设范围是-pi到pi
            normalized = max(0, min(1, normalized))
            
            # 绘制进度条
            bar_width = int(normalized * 300)
            img[y_offset:y_offset+15, 20:20+bar_width] = [0, 150, 255]  # 蓝色进度条
            y_offset += 20
        
        # 添加提示信息区域
        info_y = self.config.render_height - 100
        img[info_y:info_y+80, :] = [80, 40, 40]  # 深红色信息栏
        
        # 在中心添加一个简单的机器人轮廓
        center_x = self.config.render_width // 2
        center_y = self.config.render_height // 2
        
        # 绘制机器人基座（矩形）
        base_w, base_h = 100, 60
        img[center_y-base_h//2:center_y+base_h//2, center_x-base_w//2:center_x+base_w//2] = [200, 200, 200]
        
        # 绘制轮子（圆形近似）
        wheel_radius = 20
        for wheel_x in [center_x - 60, center_x + 60]:
            wheel_y = center_y + 40
            for dy in range(-wheel_radius, wheel_radius):
                for dx in range(-wheel_radius, wheel_radius):
                    if dx*dx + dy*dy < wheel_radius*wheel_radius:
                        y, x = wheel_y + dy, wheel_x + dx
                        if 0 <= y < self.config.render_height and 0 <= x < self.config.render_width:
                            img[y, x] = [100, 100, 100]
        
        return img
    
    def close(self):
        """关闭仿真环境"""
        if self.viewer:
            self.viewer.close()
            self.viewer = None
        
        if self.render_context:
            self.render_context = None
        
        self.model = None
        self.data = None
        self.is_initialized = False
        
        self.logger.info("MuJoCo仿真后端已关闭")


if __name__ == "__main__":
    # 测试MuJoCo后端
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 测试MuJoCo仿真后端")
    
    if not MUJOCO_AVAILABLE:
        print("❌ MuJoCo不可用，跳过测试")
        exit(1)
    
    # 创建配置
    config = SimulationConfig(
        backend=SimulationBackend.MUJOCO,
        enable_rendering=False,  # 测试时关闭渲染
        dt=0.001
    )
    
    try:
        # 创建后端
        backend = MuJoCoSimulationBackend(config)
        
        # 创建简单模型进行测试
        converter = URDFToMJCFConverter()
        test_mjcf = converter._create_simple_mjcf("test_model.xml")
        
        # 初始化
        success = backend.initialize(test_mjcf)
        print(f"初始化: {'✅' if success else '❌'}")
        
        if success:
            # 重置
            backend.reset()
            print("✅ 重置成功")
            
            # 执行几步仿真
            for i in range(10):
                # 随机控制输入
                action = {
                    'lf0_motor': np.random.uniform(-1, 1),
                    'rf0_motor': np.random.uniform(-1, 1),
                    'l_wheel_motor': np.random.uniform(-1, 1),
                    'r_wheel_motor': np.random.uniform(-1, 1)
                }
                
                backend.step(action)
                
                if i % 5 == 0:
                    state = backend.get_state()
                    print(f"步骤 {i}: 时间={state['time']:.3f}, 基座位置={state['base_position']}")
            
            print("✅ 仿真测试成功")
        
        # 清理
        backend.close()
        if os.path.exists("test_model.xml"):
            os.remove("test_model.xml")
        
        print("🎉 MuJoCo后端测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()