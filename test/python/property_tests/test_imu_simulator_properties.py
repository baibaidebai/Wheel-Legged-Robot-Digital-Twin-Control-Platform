"""
IMU仿真器属性测试。

Feature: wheel-legged-robot-twin-control, Property 4: IMU数据物理一致性

验证IMU传感器生成的数据反映当前物理状态变化，
包括四元数归一化、旋转矩阵正交性、重力补偿和数据范围合理性。
"""

import os
import sys
from unittest.mock import MagicMock

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

# Mock ROS2依赖
for mod_name in [
    'geometry_msgs', 'geometry_msgs.msg',
    'sensor_msgs', 'sensor_msgs.msg',
]:
    if mod_name not in sys.modules:
        sys.modules[mod_name] = MagicMock()

from wheel_legged_control.sensors.imu_simulator import (
    IMUSimulator,
    IMUConfig,
    RobotState,
)


# ---------------------------------------------------------------------------
# Hypothesis 策略
# ---------------------------------------------------------------------------
@st.composite
def unit_quaternions(draw):
    """生成单位四元数 [x, y, z, w]。"""
    raw = [
        draw(st.floats(-1.0, 1.0, allow_nan=False, allow_infinity=False))
        for _ in range(4)
    ]
    norm = np.linalg.norm(raw)
    if norm < 1e-10:
        return np.array([0.0, 0.0, 0.0, 1.0])
    return np.array(raw) / norm


@st.composite
def imu_configs(draw):
    """生成合法的IMU配置。"""
    return IMUConfig(
        gyro_noise_std=draw(st.floats(
            0.0, 0.5, allow_nan=False, allow_infinity=False)),
        accel_noise_std=draw(st.floats(
            0.0, 1.0, allow_nan=False, allow_infinity=False)),
        gravity=draw(st.floats(
            9.0, 10.0, allow_nan=False, allow_infinity=False)),
        update_rate=draw(st.floats(
            10.0, 1000.0, allow_nan=False, allow_infinity=False)),
    )


@st.composite
def robot_states(draw):
    """生成合法的机器人状态。"""
    q = draw(unit_quaternions())
    return RobotState(
        timestamp=draw(st.floats(
            0.0, 1e6, allow_nan=False, allow_infinity=False)),
        joint_positions={},
        joint_velocities={},
        base_position=np.array([
            draw(st.floats(-10.0, 10.0,
                           allow_nan=False, allow_infinity=False)),
            draw(st.floats(-10.0, 10.0,
                           allow_nan=False, allow_infinity=False)),
            draw(st.floats(-10.0, 10.0,
                           allow_nan=False, allow_infinity=False)),
        ]),
        base_orientation=q,
        base_linear_velocity=np.array([
            draw(st.floats(-5.0, 5.0,
                           allow_nan=False, allow_infinity=False)),
            draw(st.floats(-5.0, 5.0,
                           allow_nan=False, allow_infinity=False)),
            draw(st.floats(-5.0, 5.0,
                           allow_nan=False, allow_infinity=False)),
        ]),
        base_angular_velocity=np.array([
            draw(st.floats(-5.0, 5.0,
                           allow_nan=False, allow_infinity=False)),
            draw(st.floats(-5.0, 5.0,
                           allow_nan=False, allow_infinity=False)),
            draw(st.floats(-5.0, 5.0,
                           allow_nan=False, allow_infinity=False)),
        ]),
    )


def _static_state(orientation=None):
    """创建静止状态的机器人。"""
    if orientation is None:
        orientation = np.array([0.0, 0.0, 0.0, 1.0])
    return RobotState(
        timestamp=0.0,
        joint_positions={},
        joint_velocities={},
        base_position=np.zeros(3),
        base_orientation=orientation,
        base_linear_velocity=np.zeros(3),
        base_angular_velocity=np.zeros(3),
    )


# =========================================================================
# Property 4: IMU数据物理一致性 — 四元数归一化
# =========================================================================
class TestQuaternionNormalization:
    """四元数输出始终归一化。"""

    @given(q=unit_quaternions())
    @settings(max_examples=200, deadline=10000)
    @pytest.mark.property_test
    def test_compute_orientation_normalized(self, q):
        """compute_orientation 输出四元数 ||q|| ≈ 1。"""
        sim = IMUSimulator()
        state = _static_state(orientation=q)
        result = sim.compute_orientation(state)

        norm = np.linalg.norm(result)
        np.testing.assert_allclose(norm, 1.0, atol=1e-6)

    @given(state=robot_states())
    @settings(max_examples=200, deadline=10000)
    @pytest.mark.property_test
    def test_generate_imu_data_orientation_normalized(self, state):
        """generate_imu_data 输出的姿态四元数已归一化。"""
        sim = IMUSimulator()
        orientation, _, _ = sim.generate_imu_data(state)

        norm = np.linalg.norm(orientation)
        np.testing.assert_allclose(norm, 1.0, atol=1e-6)

    @pytest.mark.property_test
    def test_identity_quaternion_preserved(self):
        """单位四元数 [0,0,0,1] 经过处理仍为单位四元数。"""
        sim = IMUSimulator()
        identity = np.array([0.0, 0.0, 0.0, 1.0])
        state = _static_state(orientation=identity)
        result = sim.compute_orientation(state)

        np.testing.assert_allclose(result, identity, atol=1e-9)


# =========================================================================
# Property 4: IMU数据物理一致性 — 旋转矩阵正交性
# =========================================================================
class TestRotationMatrixOrthogonality:
    """四元数到旋转矩阵转换保持正交性。"""

    @given(q=unit_quaternions())
    @settings(max_examples=200, deadline=10000)
    @pytest.mark.property_test
    def test_rotation_matrix_orthogonal(self, q):
        """R^T @ R ≈ I。"""
        sim = IMUSimulator()
        R = sim.quaternion_to_rotation_matrix(q)

        product = R.T @ R
        np.testing.assert_allclose(product, np.eye(3), atol=1e-6)

    @given(q=unit_quaternions())
    @settings(max_examples=200, deadline=10000)
    @pytest.mark.property_test
    def test_rotation_matrix_det_one(self, q):
        """det(R) ≈ 1（正定旋转）。"""
        sim = IMUSimulator()
        R = sim.quaternion_to_rotation_matrix(q)

        det = np.linalg.det(R)
        np.testing.assert_allclose(det, 1.0, atol=1e-6)

    @pytest.mark.property_test
    def test_identity_quaternion_produces_identity_matrix(self):
        """单位四元数产生单位旋转矩阵。"""
        sim = IMUSimulator()
        identity = np.array([0.0, 0.0, 0.0, 1.0])
        R = sim.quaternion_to_rotation_matrix(identity)

        np.testing.assert_allclose(R, np.eye(3), atol=1e-9)

    @given(q=unit_quaternions())
    @settings(max_examples=100, deadline=10000)
    @pytest.mark.property_test
    def test_rotation_preserves_vector_norm(self, q):
        """旋转不改变向量长度。"""
        sim = IMUSimulator()
        R = sim.quaternion_to_rotation_matrix(q)

        v = np.array([1.0, 2.0, 3.0])
        rotated = R @ v

        np.testing.assert_allclose(
            np.linalg.norm(rotated), np.linalg.norm(v), atol=1e-6
        )


# =========================================================================
# Property 4: IMU数据物理一致性 — 重力补偿
# =========================================================================
class TestGravityCompensation:
    """静止状态的IMU应感知重力。"""

    @pytest.mark.property_test
    def test_static_upright_senses_gravity(self):
        """竖直静止时加速度计测量值约为 [0, 0, g]。"""
        config = IMUConfig(
            gyro_noise_std=0.0,
            accel_noise_std=0.0,
            gravity=9.81,
        )
        sim = IMUSimulator(config=config)
        state = _static_state()

        accel = sim.compute_linear_acceleration(state)

        # 静止时 acceleration=0, gravity_robot=[0,0,-9.81]
        # imu_acceleration = 0 - [0,0,-9.81] = [0,0,9.81]
        np.testing.assert_allclose(accel[0], 0.0, atol=0.5)
        np.testing.assert_allclose(accel[1], 0.0, atol=0.5)
        np.testing.assert_allclose(accel[2], 9.81, atol=0.5)

    @given(q=unit_quaternions())
    @settings(max_examples=100, deadline=10000)
    @pytest.mark.property_test
    def test_static_gravity_magnitude(self, q):
        """任意姿态静止时加速度幅值 ≈ g。"""
        config = IMUConfig(
            gyro_noise_std=0.0,
            accel_noise_std=0.0,
            gravity=9.81,
        )
        sim = IMUSimulator(config=config)
        state = _static_state(orientation=q)

        accel = sim.compute_linear_acceleration(state)
        magnitude = np.linalg.norm(accel)

        np.testing.assert_allclose(magnitude, 9.81, atol=0.5)

    @pytest.mark.property_test
    def test_zero_gravity_config(self):
        """gravity=0 时静止加速度幅值为 0。"""
        config = IMUConfig(
            gyro_noise_std=0.0,
            accel_noise_std=0.0,
            gravity=0.0,
        )
        sim = IMUSimulator(config=config)
        state = _static_state()

        accel = sim.compute_linear_acceleration(state)
        magnitude = np.linalg.norm(accel)

        np.testing.assert_allclose(magnitude, 0.0, atol=0.1)


# =========================================================================
# Property 4: IMU数据物理一致性 — 角速度
# =========================================================================
class TestAngularVelocityConsistency:
    """角速度输出的物理一致性。"""

    @pytest.mark.property_test
    def test_static_angular_velocity_near_zero(self):
        """静止时角速度接近零（仅含噪声和偏差）。"""
        config = IMUConfig(gyro_noise_std=0.0)
        sim = IMUSimulator(config=config)
        state = _static_state()

        angular_vel = sim.compute_angular_velocity(state)
        np.testing.assert_allclose(angular_vel, np.zeros(3), atol=1e-6)

    @given(state=robot_states())
    @settings(max_examples=200, deadline=10000)
    @pytest.mark.property_test
    def test_angular_velocity_finite(self, state):
        """角速度输出始终有限。"""
        sim = IMUSimulator()
        angular_vel = sim.compute_angular_velocity(state)

        assert np.all(np.isfinite(angular_vel)), (
            f'角速度包含非有限值: {angular_vel}'
        )

    @given(
        bias=st.tuples(
            st.floats(-0.1, 0.1, allow_nan=False, allow_infinity=False),
            st.floats(-0.1, 0.1, allow_nan=False, allow_infinity=False),
            st.floats(-0.1, 0.1, allow_nan=False, allow_infinity=False),
        )
    )
    @settings(max_examples=50, deadline=10000)
    @pytest.mark.property_test
    def test_gyro_bias_applied(self, bias):
        """陀螺仪偏差被正确添加到输出中。"""
        config = IMUConfig(
            gyro_noise_std=0.0,
            gyro_bias=np.array(bias),
        )
        sim = IMUSimulator(config=config)
        state = _static_state()

        angular_vel = sim.compute_angular_velocity(state)

        np.testing.assert_allclose(
            angular_vel, np.array(bias), atol=1e-6,
        )


# =========================================================================
# Property 4: IMU数据物理一致性 — 数据范围与有限性
# =========================================================================
class TestIMUDataBoundsAndFiniteness:
    """所有IMU输出均为有限值且在合理范围。"""

    @given(state=robot_states())
    @settings(max_examples=200, deadline=10000)
    @pytest.mark.property_test
    def test_all_imu_outputs_finite(self, state):
        """generate_imu_data 三元组全部有限。"""
        sim = IMUSimulator()
        orientation, angular_vel, linear_accel = sim.generate_imu_data(state)

        assert np.all(np.isfinite(orientation))
        assert np.all(np.isfinite(angular_vel))
        assert np.all(np.isfinite(linear_accel))

    @given(state=robot_states())
    @settings(max_examples=200, deadline=10000)
    @pytest.mark.property_test
    def test_linear_acceleration_bounded(self, state):
        """加速度幅值不超过 max_accel(50) + gravity(~10) + noise。"""
        sim = IMUSimulator()
        accel = sim.compute_linear_acceleration(state)
        magnitude = np.linalg.norm(accel)

        # 50 (max_accel clamp) + 9.81 (gravity) + noise buffer
        assert magnitude < 100.0, (
            f'加速度幅值过大: {magnitude}'
        )

    @given(state=robot_states(), cfg=imu_configs())
    @settings(max_examples=100, deadline=10000)
    @pytest.mark.property_test
    def test_orientation_shape(self, state, cfg):
        """姿态输出形状为 (4,)。"""
        sim = IMUSimulator(config=cfg)
        orientation, _, _ = sim.generate_imu_data(state)

        assert orientation.shape == (4,)

    @given(state=robot_states())
    @settings(max_examples=100, deadline=10000)
    @pytest.mark.property_test
    def test_angular_velocity_shape(self, state):
        """角速度输出形状为 (3,)。"""
        sim = IMUSimulator()
        _, angular_vel, _ = sim.generate_imu_data(state)

        assert angular_vel.shape == (3,)

    @given(state=robot_states())
    @settings(max_examples=100, deadline=10000)
    @pytest.mark.property_test
    def test_linear_acceleration_shape(self, state):
        """线性加速度输出形状为 (3,)。"""
        sim = IMUSimulator()
        _, _, accel = sim.generate_imu_data(state)

        assert accel.shape == (3,)


# =========================================================================
# IMU 仿真器状态管理
# =========================================================================
class TestIMUSimulatorStateManagement:
    """IMU仿真器内部状态管理。"""

    @pytest.mark.property_test
    def test_reset_clears_history(self):
        """reset() 清空历史记录。"""
        sim = IMUSimulator()
        state = _static_state()

        for _ in range(5):
            sim.generate_imu_data(state)

        assert len(sim.gyro_history) > 0
        assert len(sim.accel_history) > 0

        sim.reset()

        assert len(sim.gyro_history) == 0
        assert len(sim.accel_history) == 0

    @pytest.mark.property_test
    def test_history_length_limited(self):
        """历史记录长度不超过 max_history_length。"""
        sim = IMUSimulator()
        state = _static_state()

        for _ in range(50):
            sim.generate_imu_data(state)

        assert len(sim.gyro_history) <= sim.max_history_length
        assert len(sim.accel_history) <= sim.max_history_length

    @pytest.mark.property_test
    def test_update_config(self):
        """update_config 正确更新配置。"""
        sim = IMUSimulator()
        new_config = IMUConfig(gravity=5.0, gyro_noise_std=0.05)
        sim.update_config(new_config)

        assert sim.config.gravity == 5.0
        assert sim.config.gyro_noise_std == 0.05

    @pytest.mark.property_test
    def test_get_filtered_data_empty(self):
        """空历史时滤波数据返回零向量。"""
        sim = IMUSimulator()
        gyro, accel = sim.get_filtered_data()

        np.testing.assert_array_equal(gyro, np.zeros(3))
        np.testing.assert_array_equal(accel, np.zeros(3))

    @pytest.mark.property_test
    def test_get_filtered_data_after_samples(self):
        """积累样本后滤波数据有限。"""
        sim = IMUSimulator()
        state = _static_state()

        for _ in range(10):
            sim.generate_imu_data(state)

        gyro, accel = sim.get_filtered_data()
        assert np.all(np.isfinite(gyro))
        assert np.all(np.isfinite(accel))


# =========================================================================
# IMUConfig 数据类属性
# =========================================================================
class TestIMUConfigDefaults:
    """IMUConfig 默认值和初始化。"""

    @pytest.mark.property_test
    def test_default_config_reasonable(self):
        """默认配置参数合理。"""
        cfg = IMUConfig()
        assert cfg.gravity == 9.81
        assert cfg.gyro_noise_std >= 0
        assert cfg.accel_noise_std >= 0
        assert cfg.update_rate > 0
        np.testing.assert_array_equal(cfg.gyro_bias, np.zeros(3))
        np.testing.assert_array_equal(cfg.accel_bias, np.zeros(3))

    @given(cfg=imu_configs())
    @settings(max_examples=50, deadline=10000)
    @pytest.mark.property_test
    def test_generated_config_valid(self, cfg):
        """生成的配置参数类型正确。"""
        assert isinstance(cfg.gravity, float)
        assert cfg.gyro_noise_std >= 0
        assert cfg.accel_noise_std >= 0
        assert cfg.update_rate > 0

    @pytest.mark.property_test
    def test_custom_bias(self):
        """自定义偏差正确存储。"""
        bias = np.array([0.01, -0.02, 0.03])
        cfg = IMUConfig(gyro_bias=bias.copy())
        np.testing.assert_array_equal(cfg.gyro_bias, bias)
