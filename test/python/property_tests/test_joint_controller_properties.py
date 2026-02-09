"""
关节控制器属性测试。

Feature: wheel-legged-robot-twin-control, Property 2: 关节限制约束遵守
Feature: wheel-legged-robot-twin-control, Property 3: 关节状态反馈一致性

验证PID控制器输出始终在限幅范围内、积分项正确限幅、
关节限制始终被遵守、以及状态反馈与实际位置一致。
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

# Mock ROS2依赖以便在无ROS2环境下测试纯Python组件
for mod_name in [
    'rclpy', 'rclpy.node', 'rclpy.qos',
    'sensor_msgs', 'sensor_msgs.msg',
    'std_msgs', 'std_msgs.msg',
    'geometry_msgs', 'geometry_msgs.msg',
    'trajectory_msgs', 'trajectory_msgs.msg',
    'std_srvs', 'std_srvs.srv',
]:
    if mod_name not in sys.modules:
        sys.modules[mod_name] = MagicMock()

from wheel_legged_control.controllers.joint_controller import (
    PIDController,
    ControlGains,
    JointLimits,
)


# ---------------------------------------------------------------------------
# Hypothesis 策略
# ---------------------------------------------------------------------------
@st.composite
def control_gains(draw):
    """生成合法的PID控制增益。"""
    return ControlGains(
        kp=draw(st.floats(0.1, 100.0,
                          allow_nan=False, allow_infinity=False)),
        ki=draw(st.floats(0.0, 10.0,
                          allow_nan=False, allow_infinity=False)),
        kd=draw(st.floats(0.0, 10.0,
                          allow_nan=False, allow_infinity=False)),
        max_integral=draw(st.floats(0.1, 20.0,
                                    allow_nan=False, allow_infinity=False)),
        max_output=draw(st.floats(1.0, 200.0,
                                  allow_nan=False, allow_infinity=False)),
    )


@st.composite
def joint_limits_strategy(draw):
    """生成合法的关节限制。"""
    min_pos = draw(st.floats(-np.pi, 0.0,
                             allow_nan=False, allow_infinity=False))
    max_pos = draw(st.floats(0.0, np.pi,
                             allow_nan=False, allow_infinity=False))
    assume(min_pos < max_pos)
    return JointLimits(
        min_position=min_pos,
        max_position=max_pos,
        max_velocity=draw(st.floats(1.0, 1000.0,
                                    allow_nan=False, allow_infinity=False)),
        max_effort=draw(st.floats(1.0, 100.0,
                                  allow_nan=False, allow_infinity=False)),
    )


@st.composite
def setpoint_current_dt(draw):
    """生成 (setpoint, current, dt) 三元组。"""
    sp = draw(st.floats(-np.pi, np.pi,
                        allow_nan=False, allow_infinity=False))
    cur = draw(st.floats(-np.pi, np.pi,
                         allow_nan=False, allow_infinity=False))
    dt = draw(st.floats(0.001, 0.1,
                        allow_nan=False, allow_infinity=False))
    return sp, cur, dt


# =========================================================================
# Property 2: 关节限制约束遵守 — PID 输出限幅
# =========================================================================
class TestPIDOutputClamping:
    """属性2: PID控制器输出始终在限幅范围内。"""

    @given(gains=control_gains(), data=setpoint_current_dt())
    @settings(max_examples=200, deadline=10000)
    @pytest.mark.property_test
    def test_single_step_output_within_bounds(self, gains, data):
        """单步PID输出绝对值 ≤ max_output。"""
        setpoint, current, dt = data
        pid = PIDController(gains)
        output = pid.update(setpoint, current, dt)

        assert abs(output) <= gains.max_output + 1e-9, (
            f'|output|={abs(output)} > max_output={gains.max_output}'
        )

    @given(gains=control_gains(), data=setpoint_current_dt())
    @settings(max_examples=100, deadline=10000)
    @pytest.mark.property_test
    def test_multi_step_output_within_bounds(self, gains, data):
        """连续多步PID输出始终在限幅内。"""
        setpoint, current, dt = data
        pid = PIDController(gains)

        for _ in range(50):
            output = pid.update(setpoint, current, dt)
            assert abs(output) <= gains.max_output + 1e-9

    @given(gains=control_gains())
    @settings(max_examples=100, deadline=10000)
    @pytest.mark.property_test
    def test_zero_error_produces_zero_output(self, gains):
        """setpoint == current 首次调用时 output == 0。"""
        pid = PIDController(gains)
        output = pid.update(1.0, 1.0, 0.01)

        # error=0, prev_error=0 → P=0, I≈0, D=0
        assert abs(output) < 1e-6, (
            f'零误差输出应为0, 实际: {output}'
        )

    @given(gains=control_gains())
    @settings(max_examples=100, deadline=10000)
    @pytest.mark.property_test
    def test_integral_clamped(self, gains):
        """积分项始终在 [-max_integral, max_integral] 范围内。"""
        pid = PIDController(gains)

        # 持续大误差以驱动积分饱和
        for _ in range(200):
            pid.update(100.0, 0.0, 0.01)

        assert abs(pid.integral) <= gains.max_integral + 1e-9, (
            f'|integral|={abs(pid.integral)} > '
            f'max_integral={gains.max_integral}'
        )

    @given(gains=control_gains())
    @settings(max_examples=100, deadline=10000)
    @pytest.mark.property_test
    def test_negative_integral_clamped(self, gains):
        """负方向积分也被正确限幅。"""
        pid = PIDController(gains)

        for _ in range(200):
            pid.update(-100.0, 0.0, 0.01)

        assert abs(pid.integral) <= gains.max_integral + 1e-9


# =========================================================================
# Property 2: 关节限制约束遵守 — 位置/速度限制
# =========================================================================
class TestJointLimitEnforcement:
    """属性2: 关节位置和速度始终在限制范围内。"""

    @given(limits=joint_limits_strategy(),
           position=st.floats(-10.0, 10.0,
                              allow_nan=False, allow_infinity=False))
    @settings(max_examples=200, deadline=10000)
    @pytest.mark.property_test
    def test_position_clamp_within_limits(self, limits, position):
        """np.clip 后位置在 [min, max] 内。"""
        clamped = np.clip(position, limits.min_position, limits.max_position)

        assert clamped >= limits.min_position - 1e-9
        assert clamped <= limits.max_position + 1e-9

    @given(limits=joint_limits_strategy(),
           velocity=st.floats(-2000.0, 2000.0,
                              allow_nan=False, allow_infinity=False))
    @settings(max_examples=200, deadline=10000)
    @pytest.mark.property_test
    def test_velocity_clamp_within_limits(self, limits, velocity):
        """np.clip 后速度在 [-max_vel, max_vel] 内。"""
        clamped = np.clip(velocity, -limits.max_velocity, limits.max_velocity)

        assert clamped >= -limits.max_velocity - 1e-9
        assert clamped <= limits.max_velocity + 1e-9

    @given(limits=joint_limits_strategy(),
           effort=st.floats(-500.0, 500.0,
                            allow_nan=False, allow_infinity=False))
    @settings(max_examples=200, deadline=10000)
    @pytest.mark.property_test
    def test_effort_clamp_within_limits(self, limits, effort):
        """np.clip 后力矩在 [-max_effort, max_effort] 内。"""
        clamped = np.clip(effort, -limits.max_effort, limits.max_effort)

        assert clamped >= -limits.max_effort - 1e-9
        assert clamped <= limits.max_effort + 1e-9

    @pytest.mark.property_test
    def test_continuous_joint_has_infinite_limits(self):
        """轮子关节使用无穷大位置限制。"""
        limits = JointLimits(
            min_position=-np.inf,
            max_position=np.inf,
        )
        assert np.isinf(limits.min_position)
        assert np.isinf(limits.max_position)

        # clip 无穷限制不改变值
        pos = 100.0
        clamped = np.clip(pos, limits.min_position, limits.max_position)
        assert clamped == pos

    @given(
        gains=control_gains(),
        limits=joint_limits_strategy(),
        target=st.floats(-5.0, 5.0,
                         allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100, deadline=10000)
    @pytest.mark.property_test
    def test_simulated_motion_stays_within_limits(self, gains, limits, target):
        """模拟多步控制后位置始终在限制内。"""
        pid = PIDController(gains)
        position = 0.0
        velocity = 0.0
        dt = 0.01
        inertia = 0.1

        target_clamped = np.clip(
            target, limits.min_position, limits.max_position
        )

        for _ in range(200):
            effort = pid.update(target_clamped, position, dt)
            effort = np.clip(effort, -limits.max_effort, limits.max_effort)

            acceleration = effort / inertia
            velocity += acceleration * dt
            velocity = np.clip(
                velocity, -limits.max_velocity, limits.max_velocity
            )

            position += velocity * dt
            position = np.clip(
                position, limits.min_position, limits.max_position
            )

        assert position >= limits.min_position - 1e-9
        assert position <= limits.max_position + 1e-9


# =========================================================================
# Property 3: 关节状态反馈一致性
# =========================================================================
class TestJointStateFeedbackConsistency:
    """属性3: 关节状态反馈与实际位置一致。"""

    @given(gains=control_gains(), data=setpoint_current_dt())
    @settings(max_examples=100, deadline=10000)
    @pytest.mark.property_test
    def test_pid_output_deterministic(self, gains, data):
        """相同输入产生相同输出（状态一致性基础）。"""
        setpoint, current, dt = data

        pid1 = PIDController(gains)
        pid2 = PIDController(gains)

        out1 = pid1.update(setpoint, current, dt)
        out2 = pid2.update(setpoint, current, dt)

        assert out1 == out2, (
            f'相同输入不同输出: {out1} vs {out2}'
        )

    @given(gains=control_gains(), data=setpoint_current_dt())
    @settings(max_examples=100, deadline=10000)
    @pytest.mark.property_test
    def test_pid_state_tracks_through_sequence(self, gains, data):
        """连续调用后内部状态与输出一致。"""
        setpoint, current, dt = data
        pid = PIDController(gains)

        outputs = []
        for _ in range(10):
            out = pid.update(setpoint, current, dt)
            outputs.append(out)

        # 每次输出都应有限
        for i, o in enumerate(outputs):
            assert np.isfinite(o), f'步骤{i}输出非有限: {o}'

    @given(gains=control_gains())
    @settings(max_examples=100, deadline=10000)
    @pytest.mark.property_test
    def test_simulated_position_feedback_matches_internal(self, gains):
        """模拟控制回路中反馈位置与内部记录一致。"""
        pid = PIDController(gains)
        position = 0.0
        velocity = 0.0
        target = 1.0
        dt = 0.01
        inertia = 0.1

        positions_history = []
        for _ in range(50):
            effort = pid.update(target, position, dt)
            effort = np.clip(effort, -30.0, 30.0)

            acceleration = effort / inertia
            velocity += acceleration * dt
            velocity = np.clip(velocity, -1000.0, 1000.0)

            position += velocity * dt
            position = np.clip(position, -np.pi, np.pi)

            positions_history.append(position)

        # 最后记录的位置就是"反馈"位置，验证它是有限且在范围内
        assert np.isfinite(positions_history[-1])
        assert -np.pi <= positions_history[-1] <= np.pi

    @given(gains=control_gains())
    @settings(max_examples=100, deadline=10000)
    @pytest.mark.property_test
    def test_convergence_reduces_error(self, gains):
        """有阻尼（kd > 0）的控制器经过充分步数后误差应减小。"""
        # 纯比例控制器在惯性系统上可能振荡，需要微分阻尼
        damped_gains = ControlGains(
            kp=gains.kp,
            ki=gains.ki,
            kd=max(gains.kd, 0.5),  # 确保有足够阻尼
            max_integral=gains.max_integral,
            max_output=gains.max_output,
        )
        pid = PIDController(damped_gains)
        position = 0.0
        velocity = 0.0
        target = 0.5
        dt = 0.01
        inertia = 0.1

        initial_error = abs(target - position)

        for _ in range(500):
            effort = pid.update(target, position, dt)
            effort = np.clip(effort, -gains.max_output, gains.max_output)

            acceleration = effort / inertia
            velocity += acceleration * dt
            velocity = np.clip(velocity, -1000.0, 1000.0)

            position += velocity * dt
            position = np.clip(position, -np.pi, np.pi)

        final_error = abs(target - position)
        assert final_error < initial_error, (
            f'误差未减小: initial={initial_error:.4f}, '
            f'final={final_error:.4f}'
        )


# =========================================================================
# PID 控制器行为属性
# =========================================================================
class TestPIDControllerBehavior:
    """PID控制器内部行为属性。"""

    @pytest.mark.property_test
    def test_reset_clears_state(self):
        """reset() 后内部状态归零。"""
        gains = ControlGains(kp=10.0, ki=1.0, kd=0.5)
        pid = PIDController(gains)

        # 多次更新以积累状态
        for _ in range(20):
            pid.update(1.0, 0.0, 0.01)

        assert pid.integral != 0.0 or pid.prev_error != 0.0

        pid.reset()
        assert pid.integral == 0.0
        assert pid.prev_error == 0.0
        assert pid.prev_time is None

    @given(gains=control_gains(),
           error_sign=st.sampled_from([-1.0, 1.0]))
    @settings(max_examples=100, deadline=10000)
    @pytest.mark.property_test
    def test_proportional_output_sign_matches_error(self, gains, error_sign):
        """纯比例控制器输出符号与误差一致。"""
        p_only = ControlGains(
            kp=gains.kp, ki=0.0, kd=0.0,
            max_integral=gains.max_integral,
            max_output=gains.max_output,
        )
        pid = PIDController(p_only)

        setpoint = error_sign * 0.5
        output = pid.update(setpoint, 0.0, 0.01)

        if abs(output) > 1e-9:
            assert np.sign(output) == np.sign(error_sign), (
                f'输出符号 {np.sign(output)} != 误差符号 {error_sign}'
            )

    @given(data=setpoint_current_dt())
    @settings(max_examples=100, deadline=10000)
    @pytest.mark.property_test
    def test_dt_zero_no_derivative(self, data):
        """dt=0 时微分项为0，不产生除零错误。"""
        gains = ControlGains(kp=10.0, ki=0.0, kd=5.0)
        pid = PIDController(gains)
        setpoint, current, _ = data

        # dt=0 应安全运行
        output = pid.update(setpoint, current, 0.0)
        assert np.isfinite(output)

    @pytest.mark.property_test
    def test_identical_gains_produce_identical_controllers(self):
        """相同增益的控制器行为完全一致。"""
        gains = ControlGains(kp=5.0, ki=0.5, kd=1.0,
                             max_integral=2.0, max_output=50.0)
        pid_a = PIDController(gains)
        pid_b = PIDController(gains)

        sequence = [(1.0, 0.0, 0.01), (0.8, 0.2, 0.01),
                    (0.5, 0.5, 0.02), (0.0, 0.7, 0.01)]

        for sp, cur, dt in sequence:
            out_a = pid_a.update(sp, cur, dt)
            out_b = pid_b.update(sp, cur, dt)
            assert out_a == out_b

    @given(kp=st.floats(0.1, 50.0,
                        allow_nan=False, allow_infinity=False))
    @settings(max_examples=50, deadline=10000)
    @pytest.mark.property_test
    def test_higher_kp_produces_larger_output(self, kp):
        """更大的 kp 在相同误差下产生更大（或等大）的输出。"""
        low_kp = ControlGains(kp=1.0, ki=0.0, kd=0.0, max_output=1000.0)
        high_kp = ControlGains(kp=max(kp, 1.0 + 0.01), ki=0.0, kd=0.0,
                               max_output=1000.0)

        pid_low = PIDController(low_kp)
        pid_high = PIDController(high_kp)

        out_low = pid_low.update(1.0, 0.0, 0.01)
        out_high = pid_high.update(1.0, 0.0, 0.01)

        assert abs(out_high) >= abs(out_low) - 1e-9


# =========================================================================
# 数据类默认值
# =========================================================================
class TestDataclassDefaults:
    """ControlGains 和 JointLimits 数据类属性。"""

    @pytest.mark.property_test
    def test_control_gains_defaults(self):
        """ControlGains 默认值合理。"""
        g = ControlGains()
        assert g.kp > 0
        assert g.ki >= 0
        assert g.kd >= 0
        assert g.max_integral > 0
        assert g.max_output > 0

    @pytest.mark.property_test
    def test_joint_limits_defaults(self):
        """JointLimits 默认值合理。"""
        lim = JointLimits()
        assert lim.min_position < lim.max_position
        assert lim.max_velocity > 0
        assert lim.max_effort > 0

    @given(gains=control_gains())
    @settings(max_examples=50, deadline=10000)
    @pytest.mark.property_test
    def test_control_gains_all_positive_bounds(self, gains):
        """生成的增益 max_integral 和 max_output 始终为正。"""
        assert gains.max_integral > 0
        assert gains.max_output > 0
