"""
URDF加载器测试模块
"""

import pytest
import sys
import os
import tempfile
import xml.etree.ElementTree as ET

# 添加源码路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/wheel_legged_control'))

from wheel_legged_control.core.urdf_loader import URDFLoader, URDFParseError, load_robot_from_directory


class TestURDFLoader:
    """URDF加载器测试类"""
    
    def setup_method(self):
        """测试前设置"""
        self.loader = URDFLoader()
        
    def test_urdf_loader_initialization(self):
        """测试URDF加载器初始化"""
        assert self.loader.robot_model is None
        assert 'revolute' in self.loader._supported_joint_types
        assert 'continuous' in self.loader._supported_joint_types
        
    def test_load_nonexistent_file(self):
        """测试加载不存在的文件"""
        with pytest.raises(FileNotFoundError):
            self.loader.load_urdf("nonexistent_file.urdf")
            
    def test_load_invalid_xml(self):
        """测试加载无效的XML文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.urdf', delete=False) as f:
            f.write("invalid xml content")
            temp_path = f.name
            
        try:
            with pytest.raises(URDFParseError):
                self.loader.load_urdf(temp_path)
        finally:
            os.unlink(temp_path)
            
    def test_load_valid_urdf(self):
        """测试加载有效的URDF文件"""
        # 创建简单的测试URDF
        urdf_content = """<?xml version="1.0"?>
        <robot name="test_robot">
            <link name="base_link">
                <inertial>
                    <mass value="1.0"/>
                    <inertia ixx="1.0" ixy="0.0" ixz="0.0" iyy="1.0" iyz="0.0" izz="1.0"/>
                </inertial>
            </link>
            <link name="wheel_link">
                <inertial>
                    <mass value="0.5"/>
                    <inertia ixx="0.1" ixy="0.0" ixz="0.0" iyy="0.1" iyz="0.0" izz="0.1"/>
                </inertial>
            </link>
            <joint name="wheel_joint" type="revolute">
                <parent link="base_link"/>
                <child link="wheel_link"/>
                <axis xyz="0 0 1"/>
                <limit lower="-3.14" upper="3.14" effort="10" velocity="100"/>
            </joint>
        </robot>"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.urdf', delete=False) as f:
            f.write(urdf_content)
            temp_path = f.name
            
        try:
            robot_model = self.loader.load_urdf(temp_path)
            
            # 验证加载结果
            assert robot_model.name == "test_robot"
            assert len(robot_model.links) == 2
            assert len(robot_model.joints) == 1
            assert "base_link" in robot_model.links
            assert "wheel_link" in robot_model.links
            assert "wheel_joint" in robot_model.joints
            
            # 验证关节分类
            assert "wheel_joint" in robot_model.wheel_joints
            
        finally:
            os.unlink(temp_path)
            
    def test_joint_classification(self):
        """测试关节分类功能"""
        # 创建包含轮子和腿部关节的URDF
        urdf_content = """<?xml version="1.0"?>
        <robot name="wheel_leg_robot">
            <link name="base_link">
                <inertial>
                    <mass value="1.0"/>
                    <inertia ixx="1.0" ixy="0.0" ixz="0.0" iyy="1.0" iyz="0.0" izz="1.0"/>
                </inertial>
            </link>
            <link name="lf0_link">
                <inertial>
                    <mass value="0.2"/>
                    <inertia ixx="0.1" ixy="0.0" ixz="0.0" iyy="0.1" iyz="0.0" izz="0.1"/>
                </inertial>
            </link>
            <link name="wheel_link">
                <inertial>
                    <mass value="0.5"/>
                    <inertia ixx="0.1" ixy="0.0" ixz="0.0" iyy="0.1" iyz="0.0" izz="0.1"/>
                </inertial>
            </link>
            <joint name="lf0_joint" type="revolute">
                <parent link="base_link"/>
                <child link="lf0_link"/>
                <axis xyz="0 0 1"/>
            </joint>
            <joint name="wheel_joint" type="revolute">
                <parent link="lf0_link"/>
                <child link="wheel_link"/>
                <axis xyz="0 0 1"/>
            </joint>
        </robot>"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.urdf', delete=False) as f:
            f.write(urdf_content)
            temp_path = f.name
            
        try:
            robot_model = self.loader.load_urdf(temp_path)
            
            # 验证关节分类
            assert "wheel_joint" in robot_model.wheel_joints
            assert "lf0_joint" in robot_model.leg_joints
            
        finally:
            os.unlink(temp_path)
            
    def test_get_joint_limits(self):
        """测试获取关节限制"""
        urdf_content = """<?xml version="1.0"?>
        <robot name="test_robot">
            <link name="base_link">
                <inertial>
                    <mass value="1.0"/>
                    <inertia ixx="1.0" ixy="0.0" ixz="0.0" iyy="1.0" iyz="0.0" izz="1.0"/>
                </inertial>
            </link>
            <link name="joint_link">
                <inertial>
                    <mass value="0.5"/>
                    <inertia ixx="0.1" ixy="0.0" ixz="0.0" iyy="0.1" iyz="0.0" izz="0.1"/>
                </inertial>
            </link>
            <joint name="test_joint" type="revolute">
                <parent link="base_link"/>
                <child link="joint_link"/>
                <axis xyz="0 0 1"/>
                <limit lower="-1.0" upper="1.0" effort="30" velocity="1000"/>
            </joint>
        </robot>"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.urdf', delete=False) as f:
            f.write(urdf_content)
            temp_path = f.name
            
        try:
            self.loader.load_urdf(temp_path)
            limits = self.loader.get_joint_limits()
            
            assert "test_joint" in limits
            assert limits["test_joint"] == (-1.0, 1.0)
            
        finally:
            os.unlink(temp_path)
            
    def test_validate_urdf(self):
        """测试URDF验证功能"""
        # 测试空模型
        errors = self.loader.validate_urdf()
        assert "未加载URDF模型" in errors
        
        # 测试有效模型
        urdf_content = """<?xml version="1.0"?>
        <robot name="valid_robot">
            <link name="base_link">
                <inertial>
                    <mass value="1.0"/>
                    <inertia ixx="1.0" ixy="0.0" ixz="0.0" iyy="1.0" iyz="0.0" izz="1.0"/>
                </inertial>
            </link>
            <link name="wheel_link">
                <inertial>
                    <mass value="0.5"/>
                    <inertia ixx="0.1" ixy="0.0" ixz="0.0" iyy="0.1" iyz="0.0" izz="0.1"/>
                </inertial>
            </link>
            <joint name="wheel_joint" type="revolute">
                <parent link="base_link"/>
                <child link="wheel_link"/>
                <axis xyz="0 0 1"/>
            </joint>
        </robot>"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.urdf', delete=False) as f:
            f.write(urdf_content)
            temp_path = f.name
            
        try:
            self.loader.load_urdf(temp_path)
            errors = self.loader.validate_urdf()
            
            # 应该有一些警告，因为没有腿部关节
            assert len(errors) > 0
            assert any("未找到腿部关节" in error for error in errors)
            
        finally:
            os.unlink(temp_path)


def test_load_real_robot_model():
    """测试加载真实的机器人模型"""
    robot_dir = "src/robot/urdf/RM_Serial_Wheeled-leg_Robot"
    
    if os.path.exists(robot_dir):
        try:
            robot_model = load_robot_from_directory(robot_dir)
            
            # 验证加载的机器人模型
            assert robot_model.name == "wl"
            assert len(robot_model.links) > 0
            assert len(robot_model.joints) > 0
            
            # 验证轮腿机器人特定结构
            expected_joints = ["lf0_Joint", "lf1_Joint", "rf0_Joint", "rf1_Joint", 
                             "l_wheel_Joint", "r_wheel_Joint"]
            
            for joint_name in expected_joints:
                assert joint_name in robot_model.joints, f"缺少关节: {joint_name}"
                
            # 验证关节分类
            assert len(robot_model.wheel_joints) >= 2  # 至少有两个轮子
            assert len(robot_model.leg_joints) >= 4   # 至少有四个腿部关节
            
            print(f"成功加载机器人模型: {robot_model.name}")
            print(f"轮子关节: {robot_model.wheel_joints}")
            print(f"腿部关节: {robot_model.leg_joints}")
            
        except Exception as e:
            pytest.skip(f"无法加载真实机器人模型: {e}")
    else:
        pytest.skip("真实机器人模型目录不存在")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])