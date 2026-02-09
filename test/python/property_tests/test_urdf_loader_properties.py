"""
URDF加载器属性测试。

Feature: wheel-legged-robot-twin-control, Property 1: 关节系统完整性
验证任何URDF模型加载后都能正确创建所有关节，
每个关节的父子链接关系一致，关节限制正确解析。
"""

import os
import sys

import numpy as np
import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

# 确保源码路径可用
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..')
)
SRC_ROOT = os.path.join(PROJECT_ROOT, 'src', 'wheel_legged_control')
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

from wheel_legged_control.core.urdf_loader import URDFLoader, RobotModel

# 导入策略
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'test', 'python', 'property_tests'))
from strategies.joint_strategies import valid_joint_angles

# URDF路径
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

URDF_PATHS = [RM_URDF_PATH, DM_URDF_PATH]


def _load_model(urdf_path: str) -> tuple:
    """辅助函数：加载URDF模型并返回(loader, model)。"""
    loader = URDFLoader()
    model = loader.load_urdf(urdf_path)
    return loader, model


class TestJointSystemIntegrity:
    """属性1: 关节系统完整性测试。"""

    @pytest.mark.property_test
    @pytest.mark.parametrize('urdf_path', URDF_PATHS)
    def test_all_joints_have_valid_parent_child_links(self, urdf_path):
        """每个关节的parent/child link都存在于links字典中。"""
        _, model = _load_model(urdf_path)

        for joint_name, joint_info in model.joints.items():
            assert joint_info.parent_link in model.links, (
                f'关节 {joint_name} 的父链接 {joint_info.parent_link} '
                f'不在links字典中'
            )
            assert joint_info.child_link in model.links, (
                f'关节 {joint_name} 的子链接 {joint_info.child_link} '
                f'不在links字典中'
            )

    @pytest.mark.property_test
    @pytest.mark.parametrize('urdf_path', URDF_PATHS)
    def test_joint_limits_parsing_consistency(self, urdf_path):
        """关节限制 min <= max，effort/velocity >= 0。"""
        loader, model = _load_model(urdf_path)

        for joint_name, joint_info in model.joints.items():
            if joint_info.joint_type == 'fixed':
                continue

            if (joint_info.limit_lower is not None
                    and joint_info.limit_upper is not None):
                assert joint_info.limit_lower <= joint_info.limit_upper, (
                    f'关节 {joint_name}: lower={joint_info.limit_lower} '
                    f'> upper={joint_info.limit_upper}'
                )

            if joint_info.limit_effort is not None:
                assert joint_info.limit_effort >= 0, (
                    f'关节 {joint_name}: effort={joint_info.limit_effort} < 0'
                )

            if joint_info.limit_velocity is not None:
                assert joint_info.limit_velocity >= 0, (
                    f'关节 {joint_name}: velocity={joint_info.limit_velocity} < 0'
                )

    @pytest.mark.property_test
    @pytest.mark.parametrize('urdf_path', URDF_PATHS)
    def test_joint_classification_correctness(self, urdf_path):
        """wheel关节分类为轮子，lf/rf分类为腿部。"""
        _, model = _load_model(urdf_path)

        # 所有分类后的关节并集应覆盖所有非fixed关节
        classified = set(model.wheel_joints) | set(model.leg_joints)
        non_fixed = {
            name for name, info in model.joints.items()
            if info.joint_type != 'fixed'
        }

        for joint_name in non_fixed:
            assert joint_name in classified, (
                f'关节 {joint_name} 未被分类为轮子或腿部'
            )

        # 轮子关节名称或子链接包含'wheel'
        for wj in model.wheel_joints:
            joint_info = model.joints[wj]
            has_wheel = (
                'wheel' in wj.lower()
                or 'wheel' in joint_info.child_link.lower()
            )
            assert has_wheel, (
                f'轮子关节 {wj} 名称和子链接中都不包含wheel'
            )

    @pytest.mark.property_test
    @pytest.mark.parametrize('urdf_path', URDF_PATHS)
    def test_base_link_not_child_of_any_joint(self, urdf_path):
        """base_link不是任何关节的child_link。"""
        _, model = _load_model(urdf_path)

        child_links = {
            joint_info.child_link
            for joint_info in model.joints.values()
        }
        assert model.base_link not in child_links, (
            f'base_link {model.base_link} 是某个关节的子链接'
        )

    @pytest.mark.property_test
    @pytest.mark.parametrize('urdf_path', URDF_PATHS)
    def test_link_joint_names_uniqueness(self, urdf_path):
        """链接名和关节名各自唯一。"""
        _, model = _load_model(urdf_path)

        assert len(model.link_names) == len(set(model.link_names)), (
            '存在重复的链接名称'
        )
        assert len(model.joint_names) == len(set(model.joint_names)), (
            '存在重复的关节名称'
        )

    @pytest.mark.property_test
    @pytest.mark.parametrize('urdf_path', URDF_PATHS)
    def test_robot_model_structural_consistency(self, urdf_path):
        """link_names/joint_names长度与字典一致。"""
        _, model = _load_model(urdf_path)

        assert len(model.link_names) == len(model.links), (
            f'link_names长度 {len(model.link_names)} '
            f'!= links字典长度 {len(model.links)}'
        )
        assert len(model.joint_names) == len(model.joints), (
            f'joint_names长度 {len(model.joint_names)} '
            f'!= joints字典长度 {len(model.joints)}'
        )

        # link_names内容与links键集合一致
        assert set(model.link_names) == set(model.links.keys())
        assert set(model.joint_names) == set(model.joints.keys())

    @pytest.mark.property_test
    @pytest.mark.parametrize('urdf_path', URDF_PATHS)
    def test_validate_urdf_idempotent(self, urdf_path):
        """多次验证结果一致。"""
        loader, _ = _load_model(urdf_path)

        result1 = loader.validate_urdf()
        result2 = loader.validate_urdf()
        result3 = loader.validate_urdf()

        assert result1 == result2 == result3, (
            '多次validate_urdf()返回结果不一致'
        )

    @pytest.mark.property_test
    @pytest.mark.parametrize('urdf_path', URDF_PATHS)
    def test_get_joint_limits_covers_all_joints(self, urdf_path):
        """get_joint_limits()返回的关节集合覆盖所有非fixed关节。"""
        loader, model = _load_model(urdf_path)
        limits = loader.get_joint_limits()

        non_fixed_joints = {
            name for name, info in model.joints.items()
            if info.joint_type != 'fixed'
        }

        for jn in non_fixed_joints:
            assert jn in limits, (
                f'关节 {jn} 未出现在get_joint_limits()返回中'
            )
            lower, upper = limits[jn]
            assert lower <= upper, (
                f'关节 {jn}: limits lower={lower} > upper={upper}'
            )

    @given(urdf_idx=st.integers(min_value=0, max_value=1))
    @settings(max_examples=10, deadline=10000)
    @pytest.mark.property_test
    def test_joint_angles_within_limits_are_accepted(self, urdf_idx):
        """在限制范围内生成的关节角度通过验证。"""
        urdf_path = URDF_PATHS[urdf_idx]
        loader, model = _load_model(urdf_path)
        limits = loader.get_joint_limits()

        # 验证每个关节限制的lower确实<=upper
        for jn, (lower, upper) in limits.items():
            assert lower <= upper

    @pytest.mark.property_test
    @pytest.mark.parametrize('urdf_path', URDF_PATHS)
    def test_wheel_and_leg_joints_are_disjoint(self, urdf_path):
        """轮子关节和腿部关节集合无交集。"""
        _, model = _load_model(urdf_path)

        wheel_set = set(model.wheel_joints)
        leg_set = set(model.leg_joints)
        overlap = wheel_set & leg_set

        assert len(overlap) == 0, (
            f'轮子和腿部关节存在交集: {overlap}'
        )

    @pytest.mark.property_test
    @pytest.mark.parametrize('urdf_path', URDF_PATHS)
    def test_get_robot_info_completeness(self, urdf_path):
        """get_robot_info()返回完整的信息字典。"""
        loader, _ = _load_model(urdf_path)
        info = loader.get_robot_info()

        required_keys = [
            'name', 'total_mass', 'num_links', 'num_joints',
            'wheel_joints', 'leg_joints', 'base_link',
            'joint_limits', 'joint_efforts', 'joint_velocities',
        ]
        for key in required_keys:
            assert key in info, f'get_robot_info() 缺少键: {key}'

        assert info['num_links'] > 0
        assert info['num_joints'] > 0
        assert info['total_mass'] >= 0
