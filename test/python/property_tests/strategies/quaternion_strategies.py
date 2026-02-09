"""
四元数和旋转相关的Hypothesis测试策略。

提供单位四元数、旋转矩阵等几何数据的生成策略。
"""

import numpy as np
from hypothesis import strategies as st


def unit_quaternions() -> st.SearchStrategy[np.ndarray]:
    """
    生成单位四元数 [x, y, z, w]，满足 ||q|| = 1.

    Returns:
        Hypothesis策略，生成 np.ndarray(4,)
    """
    @st.composite
    def strategy(draw):
        components = [
            draw(st.floats(min_value=-1.0, max_value=1.0,
                           allow_nan=False, allow_infinity=False))
            for _ in range(4)
        ]
        q = np.array(components, dtype=np.float64)

        norm = np.linalg.norm(q)
        if norm < 1e-10:
            return np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float64)
        return q / norm

    return strategy()


def small_angle_quaternions(
    max_angle: float = 0.3
) -> st.SearchStrategy[np.ndarray]:
    """
    生成小角度旋转四元数，适合测试线性化假设。

    Args:
        max_angle: 最大旋转角度 (rad)

    Returns:
        Hypothesis策略，生成 np.ndarray(4,)
    """
    @st.composite
    def strategy(draw):
        angle = draw(st.floats(
            min_value=0.0, max_value=max_angle,
            allow_nan=False, allow_infinity=False
        ))

        axis = np.array([
            draw(st.floats(min_value=-1.0, max_value=1.0,
                           allow_nan=False, allow_infinity=False)),
            draw(st.floats(min_value=-1.0, max_value=1.0,
                           allow_nan=False, allow_infinity=False)),
            draw(st.floats(min_value=-1.0, max_value=1.0,
                           allow_nan=False, allow_infinity=False)),
        ], dtype=np.float64)

        axis_norm = np.linalg.norm(axis)
        if axis_norm < 1e-10:
            return np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float64)

        axis = axis / axis_norm

        half_angle = angle / 2.0
        q = np.array([
            axis[0] * np.sin(half_angle),
            axis[1] * np.sin(half_angle),
            axis[2] * np.sin(half_angle),
            np.cos(half_angle),
        ], dtype=np.float64)

        return q / np.linalg.norm(q)

    return strategy()
