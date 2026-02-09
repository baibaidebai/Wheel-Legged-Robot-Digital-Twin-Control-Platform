"""
属性测试共享Fixtures。

提供跨模块共享的测试装置，包括URDF路径、预加载模型、临时目录等。
"""

import os
import sys
import tempfile

import pytest

# 将项目源码路径加入sys.path
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..')
)
SRC_ROOT = os.path.join(
    PROJECT_ROOT, 'src', 'wheel_legged_control'
)
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

# URDF模型路径
RM_URDF_PATH = os.path.join(
    PROJECT_ROOT, 'src', 'model',
    'RM_Serial_Wheeled-leg_Robot', 'urdf',
    'RM_Serial_Wheeled-leg_Robot.urdf'
)
DM_URDF_PATH = os.path.join(
    PROJECT_ROOT, 'src', 'model',
    'DM_Wheel_leg_robot', 'urdf',
    'wheel_legged_urdf_pkg.urdf'
)

# RM机器人关节名称
RM_JOINT_NAMES = [
    'lf0_Joint', 'lf1_Joint', 'l_wheel_Joint',
    'rf0_Joint', 'rf1_Joint', 'r_wheel_Joint',
]

# DM机器人关节名称
DM_JOINT_NAMES = [
    'left_front_joint_link', 'left_l1_joint_link',
    'left_l4_joint_link', 'left_wheel_joint_link',
    'right_front_joint_link', 'right_l1_joint_link',
    'right_l4_joint_link', 'right_wheel_joint_link',
]


@pytest.fixture
def rm_urdf_path():
    """RM机器人URDF文件路径。"""
    return RM_URDF_PATH


@pytest.fixture
def dm_urdf_path():
    """DM机器人URDF文件路径。"""
    return DM_URDF_PATH


@pytest.fixture
def urdf_loader_rm():
    """预加载RM机器人模型的URDFLoader实例。"""
    from wheel_legged_control.core.urdf_loader import URDFLoader
    loader = URDFLoader()
    loader.load_urdf(RM_URDF_PATH)
    return loader


@pytest.fixture
def urdf_loader_dm():
    """预加载DM机器人模型的URDFLoader实例。"""
    from wheel_legged_control.core.urdf_loader import URDFLoader
    loader = URDFLoader()
    loader.load_urdf(DM_URDF_PATH)
    return loader


@pytest.fixture
def tmp_data_dir():
    """创建临时数据目录，测试结束后自动清理。"""
    with tempfile.TemporaryDirectory(prefix='property_test_') as tmpdir:
        yield tmpdir
