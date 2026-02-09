"""
机器人状态相关的Hypothesis测试策略。

提供 RobotStateSnapshot 和其他状态数据的生成策略。
"""

from typing import List

import numpy as np
from hypothesis import strategies as st

from .quaternion_strategies import unit_quaternions


def robot_state_snapshots(
    joint_names: List[str],
    base_timestamp: float = None,
) -> st.SearchStrategy:
    """
    生成完整的机器人状态快照字典。

    Args:
        joint_names: 关节名称列表
        base_timestamp: 基准时间戳，None则使用固定值

    Returns:
        Hypothesis策略，生成状态字典
    """
    if base_timestamp is None:
        base_timestamp = 1000000.0

    @st.composite
    def strategy(draw):
        ts_offset = draw(st.floats(
            min_value=0.0, max_value=100.0,
            allow_nan=False, allow_infinity=False
        ))

        joint_positions = {}
        for name in joint_names:
            joint_positions[name] = draw(st.floats(
                min_value=-np.pi, max_value=np.pi,
                allow_nan=False, allow_infinity=False
            ))

        joint_velocities = {}
        for name in joint_names:
            joint_velocities[name] = draw(st.floats(
                min_value=-10.0, max_value=10.0,
                allow_nan=False, allow_infinity=False
            ))

        joint_efforts = {}
        for name in joint_names:
            joint_efforts[name] = draw(st.floats(
                min_value=-30.0, max_value=30.0,
                allow_nan=False, allow_infinity=False
            ))

        q = draw(unit_quaternions())
        imu_orientation = (float(q[0]), float(q[1]), float(q[2]), float(q[3]))

        imu_angular_velocity = tuple(
            draw(st.floats(
                min_value=-10.0, max_value=10.0,
                allow_nan=False, allow_infinity=False
            ))
            for _ in range(3)
        )

        imu_linear_acceleration = tuple(
            draw(st.floats(
                min_value=-50.0, max_value=50.0,
                allow_nan=False, allow_infinity=False
            ))
            for _ in range(3)
        )

        return {
            'timestamp': base_timestamp + ts_offset,
            'joint_positions': joint_positions,
            'joint_velocities': joint_velocities,
            'joint_efforts': joint_efforts,
            'imu_orientation': imu_orientation,
            'imu_angular_velocity': imu_angular_velocity,
            'imu_linear_acceleration': imu_linear_acceleration,
            'base_position': (0.0, 0.0, 0.2),
            'base_velocity': (0.0, 0.0, 0.0),
        }

    return strategy()


def static_robot_state_snapshots(
    joint_names: List[str],
) -> st.SearchStrategy:
    """
    生成静止状态的机器人状态快照。

    Args:
        joint_names: 关节名称列表

    Returns:
        Hypothesis策略，生成状态字典（速度和加速度为零）
    """
    @st.composite
    def strategy(draw):
        q = draw(unit_quaternions())

        joint_positions = {}
        for name in joint_names:
            joint_positions[name] = draw(st.floats(
                min_value=-1.0, max_value=1.0,
                allow_nan=False, allow_infinity=False
            ))

        return {
            'timestamp': 1000000.0,
            'joint_positions': joint_positions,
            'joint_velocities': {name: 0.0 for name in joint_names},
            'joint_efforts': {name: 0.0 for name in joint_names},
            'imu_orientation': (float(q[0]), float(q[1]),
                                float(q[2]), float(q[3])),
            'imu_angular_velocity': (0.0, 0.0, 0.0),
            'imu_linear_acceleration': (0.0, 0.0, -9.81),
            'base_position': (0.0, 0.0, 0.2),
            'base_velocity': (0.0, 0.0, 0.0),
        }

    return strategy()
