#!/usr/bin/env python3
"""
Gazebo URDF集成测试

测试URDF文件是否能正确加载到Gazebo中。
"""

import pytest
import sys
import os
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path

# 添加源码路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/wheel_legged_control'))


class TestGazeboURDF:
    """Gazebo URDF集成测试类"""
    
    def test_urdf_file_exists(self):
        """测试URDF文件是否存在"""
        urdf_file = Path("src/wheel_legged_control/urdf/wheel_legged_robot.urdf")
        assert urdf_file.exists(), f"URDF文件不存在: {urdf_file}"
        
    def test_urdf_syntax_valid(self):
        """测试URDF文件语法是否正确"""
        urdf_file = "src/wheel_legged_control/urdf/wheel_legged_robot.urdf"
        
        try:
            tree = ET.parse(urdf_file)
            root = tree.getroot()
            
            # 检查根元素
            assert root.tag == 'robot', "根元素必须是'robot'"
            assert root.get('name') == 'wheel_legged_robot', "机器人名称不正确"
            
        except ET.ParseError as e:
            pytest.fail(f"URDF XML语法错误: {e}")
            
    def test_urdf_structure(self):
        """测试URDF结构是否完整"""
        urdf_file = "src/wheel_legged_control/urdf/wheel_legged_robot.urdf"
        tree = ET.parse(urdf_file)
        root = tree.getroot()
        
        # 检查必要的链接
        links = root.findall('link')
        link_names = [link.get('name') for link in links]
        
        required_links = [
            'base_link', 'imu_link',
            'lf0_link', 'lf1_link', 'l_wheel_link',
            'rf0_link', 'rf1_link', 'r_wheel_link'
        ]
        
        for required_link in required_links:
            assert required_link in link_names, f"缺少必要链接: {required_link}"
            
        # 检查必要的关节
        joints = root.findall('joint')
        joint_names = [joint.get('name') for joint in joints]
        
        required_joints = [
            'lf0_Joint', 'lf1_Joint', 'l_wheel_Joint',
            'rf0_Joint', 'rf1_Joint', 'r_wheel_Joint'
        ]
        
        for required_joint in required_joints:
            assert required_joint in joint_names, f"缺少必要关节: {required_joint}"
            
    def test_joint_limits(self):
        """测试关节限制是否正确设置"""
        urdf_file = "src/wheel_legged_control/urdf/wheel_legged_robot.urdf"
        tree = ET.parse(urdf_file)
        root = tree.getroot()
        
        # 检查旋转关节的限制
        revolute_joints = ['lf0_Joint', 'lf1_Joint', 'rf0_Joint', 'rf1_Joint']
        
        for joint_name in revolute_joints:
            joint = None
            for j in root.findall('joint'):
                if j.get('name') == joint_name:
                    joint = j
                    break
                    
            assert joint is not None, f"未找到关节: {joint_name}"
            assert joint.get('type') == 'revolute', f"关节类型错误: {joint_name}"
            
            # 检查限制元素
            limit = joint.find('limit')
            assert limit is not None, f"关节缺少限制: {joint_name}"
            
            # 检查限制值
            lower = float(limit.get('lower'))
            upper = float(limit.get('upper'))
            effort = float(limit.get('effort'))
            velocity = float(limit.get('velocity'))
            
            assert lower < upper, f"关节限制错误: {joint_name}"
            assert effort > 0, f"关节力矩限制错误: {joint_name}"
            assert velocity > 0, f"关节速度限制错误: {joint_name}"
            
    def test_wheel_joints(self):
        """测试轮子关节配置"""
        urdf_file = "src/wheel_legged_control/urdf/wheel_legged_robot.urdf"
        tree = ET.parse(urdf_file)
        root = tree.getroot()
        
        wheel_joints = ['l_wheel_Joint', 'r_wheel_Joint']
        
        for joint_name in wheel_joints:
            joint = None
            for j in root.findall('joint'):
                if j.get('name') == joint_name:
                    joint = j
                    break
                    
            assert joint is not None, f"未找到轮子关节: {joint_name}"
            assert joint.get('type') == 'continuous', f"轮子关节类型应为continuous: {joint_name}"
            
            # 检查轴向
            axis = joint.find('axis')
            assert axis is not None, f"轮子关节缺少轴向: {joint_name}"
            
    def test_gazebo_plugins(self):
        """测试Gazebo插件配置"""
        urdf_file = "src/wheel_legged_control/urdf/wheel_legged_robot.urdf"
        tree = ET.parse(urdf_file)
        root = tree.getroot()
        
        # 检查Gazebo元素
        gazebo_elements = root.findall('gazebo')
        assert len(gazebo_elements) > 0, "缺少Gazebo配置"
        
        # 检查IMU传感器配置
        imu_found = False
        for gazebo in gazebo_elements:
            if gazebo.get('reference') == 'imu_link':
                sensor = gazebo.find('sensor')
                if sensor is not None and sensor.get('type') == 'imu':
                    imu_found = True
                    break
                    
        assert imu_found, "未找到IMU传感器配置"
        
    def test_world_file_exists(self):
        """测试世界文件是否存在"""
        world_file = Path("src/wheel_legged_control/worlds/wheel_legged_robot.world")
        assert world_file.exists(), f"世界文件不存在: {world_file}"
        
    def test_world_file_syntax(self):
        """测试世界文件语法"""
        world_file = "src/wheel_legged_control/worlds/wheel_legged_robot.world"
        
        try:
            tree = ET.parse(world_file)
            root = tree.getroot()
            
            assert root.tag == 'sdf', "世界文件根元素必须是'sdf'"
            
            world = root.find('world')
            assert world is not None, "缺少world元素"
            
            # 检查基本元素
            physics = world.find('physics')
            assert physics is not None, "缺少physics配置"
            
            gravity = world.find('gravity')
            assert gravity is not None, "缺少gravity配置"
            
        except ET.ParseError as e:
            pytest.fail(f"世界文件XML语法错误: {e}")
            
    def test_launch_files_exist(self):
        """测试启动文件是否存在"""
        launch_files = [
            "src/wheel_legged_control/launch/gazebo_simulation.launch.py",
            "src/wheel_legged_control/launch/simple_gazebo.launch.py",
            "src/wheel_legged_control/launch/system_launch.py"
        ]
        
        for launch_file in launch_files:
            path = Path(launch_file)
            assert path.exists(), f"启动文件不存在: {launch_file}"
            
    def test_launch_file_syntax(self):
        """测试启动文件语法"""
        launch_files = [
            "src/wheel_legged_control/launch/simple_gazebo.launch.py"
        ]
        
        for launch_file in launch_files:
            try:
                result = subprocess.run(
                    ['python3', '-m', 'py_compile', launch_file],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                assert result.returncode == 0, f"启动文件语法错误: {launch_file}\n{result.stderr}"
            except subprocess.TimeoutExpired:
                pytest.fail(f"启动文件语法检查超时: {launch_file}")
                
    def test_config_file_exists(self):
        """测试配置文件是否存在"""
        config_file = Path("src/wheel_legged_control/config/wheel_legged_control.yaml")
        assert config_file.exists(), f"配置文件不存在: {config_file}"
        
    def test_config_file_content(self):
        """测试配置文件内容"""
        import yaml
        
        config_file = "src/wheel_legged_control/config/wheel_legged_control.yaml"
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        # 检查关节状态广播器配置
        assert 'joint_state_broadcaster' in config, "缺少关节状态广播器配置"
        
        joints = config['joint_state_broadcaster']['ros__parameters']['joints']
        expected_joints = ['lf0_Joint', 'lf1_Joint', 'rf0_Joint', 'rf1_Joint', 'l_wheel_Joint', 'r_wheel_Joint']
        
        for joint in expected_joints:
            assert joint in joints, f"配置文件中缺少关节: {joint}"


def test_urdf_loader_integration():
    """测试URDF加载器与新模型的集成"""
    try:
        from wheel_legged_control.core.urdf_loader import URDFLoader
        
        loader = URDFLoader()
        urdf_file = "src/wheel_legged_control/urdf/wheel_legged_robot.urdf"
        
        robot_model = loader.load_urdf(urdf_file)
        
        # 验证加载结果
        assert robot_model.name == "wheel_legged_robot"
        assert len(robot_model.links) == 8  # 包括IMU链接
        assert len(robot_model.joints) == 7  # 包括IMU关节
        
        # 验证关节分类
        expected_wheel_joints = ['l_wheel_Joint', 'r_wheel_Joint']
        expected_leg_joints = ['lf0_Joint', 'lf1_Joint', 'rf0_Joint', 'rf1_Joint']
        
        for joint in expected_wheel_joints:
            assert joint in robot_model.wheel_joints, f"轮子关节分类错误: {joint}"
            
        for joint in expected_leg_joints:
            assert joint in robot_model.leg_joints, f"腿部关节分类错误: {joint}"
            
        # 验证关节限制
        limits = loader.get_joint_limits()
        for joint_name in expected_leg_joints:
            assert joint_name in limits, f"缺少关节限制: {joint_name}"
            
        print("✅ URDF加载器集成测试通过")
        
    except ImportError:
        pytest.skip("URDF加载器模块不可用")
    except Exception as e:
        pytest.fail(f"URDF加载器集成测试失败: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])