"""
配置相关的Hypothesis测试策略。

提供 PID增益、同步配置、数据记录配置等参数的生成策略。
"""

from hypothesis import strategies as st


def pid_gains() -> st.SearchStrategy:
    """
    生成合法的PID控制增益参数字典。

    Returns:
        Hypothesis策略，生成 dict(kp, ki, kd, max_integral, max_output)
    """
    @st.composite
    def strategy(draw):
        return {
            'kp': draw(st.floats(
                min_value=0.1, max_value=50.0,
                allow_nan=False, allow_infinity=False
            )),
            'ki': draw(st.floats(
                min_value=0.0, max_value=5.0,
                allow_nan=False, allow_infinity=False
            )),
            'kd': draw(st.floats(
                min_value=0.0, max_value=5.0,
                allow_nan=False, allow_infinity=False
            )),
            'max_integral': draw(st.floats(
                min_value=0.1, max_value=10.0,
                allow_nan=False, allow_infinity=False
            )),
            'max_output': draw(st.floats(
                min_value=1.0, max_value=100.0,
                allow_nan=False, allow_infinity=False
            )),
        }

    return strategy()


def sync_configs() -> st.SearchStrategy:
    """
    生成合法的同步器配置参数字典。

    Returns:
        Hypothesis策略，生成 dict
    """
    @st.composite
    def strategy(draw):
        return {
            'network_delay_mean': draw(st.floats(
                min_value=0.001, max_value=0.5,
                allow_nan=False, allow_infinity=False
            )),
            'network_delay_std': draw(st.floats(
                min_value=0.001, max_value=0.1,
                allow_nan=False, allow_infinity=False
            )),
            'packet_loss_rate': draw(st.floats(
                min_value=0.0, max_value=0.5,
                allow_nan=False, allow_infinity=False
            )),
            'sync_frequency': draw(st.floats(
                min_value=1.0, max_value=100.0,
                allow_nan=False, allow_infinity=False
            )),
            'max_sync_error': draw(st.floats(
                min_value=0.001, max_value=1.0,
                allow_nan=False, allow_infinity=False
            )),
            'correction_gain': draw(st.floats(
                min_value=0.01, max_value=1.0,
                allow_nan=False, allow_infinity=False
            )),
            'max_history_length': draw(st.integers(
                min_value=10, max_value=5000
            )),
            'state_buffer_size': draw(st.integers(
                min_value=5, max_value=500
            )),
        }

    return strategy()


def recording_configs() -> st.SearchStrategy:
    """
    生成合法的数据记录配置参数字典。

    Returns:
        Hypothesis策略，生成 dict
    """
    @st.composite
    def strategy(draw):
        return {
            'max_buffer_size': draw(st.integers(
                min_value=10, max_value=50000
            )),
            'flush_interval': draw(st.floats(
                min_value=0.1, max_value=10.0,
                allow_nan=False, allow_infinity=False
            )),
            'save_json': draw(st.booleans()),
            'save_csv': draw(st.booleans()),
        }

    return strategy()
