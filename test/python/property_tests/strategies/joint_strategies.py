"""
关节相关的Hypothesis测试策略。

提供关节角度、速度、力矩等数据的生成策略，
用于属性测试中生成合法的关节空间输入。
"""

from typing import Dict, List, Tuple

import numpy as np
from hypothesis import strategies as st


def valid_joint_angles(
    limits: Dict[str, Tuple[float, float]]
) -> st.SearchStrategy[Dict[str, float]]:
    """
    生成符合URDF限制的关节角度字典。

    Args:
        limits: 关节限制字典 {joint_name: (lower, upper)}

    Returns:
        Hypothesis策略，生成 Dict[str, float]
    """
    if not limits:
        return st.just({})

    keys = sorted(limits.keys())

    value_strategies = []
    for key in keys:
        lower, upper = limits[key]
        if np.isinf(lower) or np.isinf(upper):
            value_strategies.append(
                st.floats(min_value=-2 * np.pi, max_value=2 * np.pi,
                          allow_nan=False, allow_infinity=False)
            )
        else:
            value_strategies.append(
                st.floats(min_value=float(lower), max_value=float(upper),
                          allow_nan=False, allow_infinity=False)
            )

    @st.composite
    def strategy(draw):
        result = {}
        for key, val_st in zip(keys, value_strategies):
            result[key] = draw(val_st)
        return result

    return strategy()


def joint_angle_vectors(
    num_joints: int,
    limits: List[Tuple[float, float]] = None
) -> st.SearchStrategy[np.ndarray]:
    """
    生成numpy数组形式的关节角度向量。

    Args:
        num_joints: 关节数量
        limits: 每个关节的(lower, upper)列表，None则使用[-pi, pi]

    Returns:
        Hypothesis策略，生成 np.ndarray
    """
    if limits is None:
        limits = [(-np.pi, np.pi)] * num_joints

    element_strategies = []
    for lower, upper in limits:
        if np.isinf(lower) or np.isinf(upper):
            element_strategies.append(
                st.floats(min_value=-2 * np.pi, max_value=2 * np.pi,
                          allow_nan=False, allow_infinity=False)
            )
        else:
            element_strategies.append(
                st.floats(min_value=float(lower), max_value=float(upper),
                          allow_nan=False, allow_infinity=False)
            )

    @st.composite
    def strategy(draw):
        values = [draw(s) for s in element_strategies]
        return np.array(values, dtype=np.float64)

    return strategy()


def joint_velocity_vectors(
    num_joints: int,
    max_velocity: float = 10.0
) -> st.SearchStrategy[np.ndarray]:
    """
    生成合法的关节速度向量。

    Args:
        num_joints: 关节数量
        max_velocity: 最大速度 (rad/s)

    Returns:
        Hypothesis策略，生成 np.ndarray
    """
    @st.composite
    def strategy(draw):
        values = [
            draw(st.floats(
                min_value=-max_velocity, max_value=max_velocity,
                allow_nan=False, allow_infinity=False
            ))
            for _ in range(num_joints)
        ]
        return np.array(values, dtype=np.float64)

    return strategy()
