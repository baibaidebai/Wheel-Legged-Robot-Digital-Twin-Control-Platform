#!/usr/bin/env python3
"""
LQR (Linear Quadratic Regulator) 控制器

实现线性二次调节器，用于轮腿机器人的最优控制。
LQR控制器通过最小化二次代价函数来计算最优控制增益。
"""

import numpy as np
import scipy.linalg
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import time

# 导入算法基类
from wheel_legged_control.algorithms.algorithm_manager import BaseAlgorithm


@dataclass
class LQRConfig:
    """LQR控制器配置参数"""
    # 状态空间维度
    state_dim: int = 12          # 状态维度 (位置、速度、姿态等)
    control_dim: int = 6         # 控制输入维度 (关节力矩)
    
    # 代价函数权重矩阵
    Q_weights: List[float] = field(default_factory=lambda: [
        10.0, 10.0, 10.0,  # 位置权重 (x, y, z)
        1.0, 1.0, 1.0,     # 姿态权重 (roll, pitch, yaw)
        1.0, 1.0, 1.0,     # 线速度权重
        0.1, 0.1, 0.1      # 角速度权重
    ])
    
    R_weights: List[float] = field(default_factory=lambda: [
        0.1, 0.1, 0.1, 0.1, 0.1, 0.1  # 控制输入权重
    ])
    
    # 系统参数
    dt: float = 0.01             # 采样时间
    max_iterations: int = 1000   # 最大迭代次数
    tolerance: float = 1e-6      # 收敛容差
    
    # 控制限制
    max_control_effort: float = 30.0    # 最大控制力矩
    min_control_effort: float = -30.0   # 最小控制力矩
    
    # 稳定性检查
    check_stability: bool = True         # 是否检查稳定性
    max_eigenvalue_real: float = -0.01   # 最大特征值实部
    
    # 自适应参数
    adaptive_weights: bool = False       # 是否使用自适应权重
    weight_adaptation_rate: float = 0.01 # 权重适应速率


class LinearSystemModel:
    """线性系统模型"""
    
    def __init__(self, A: np.ndarray, B: np.ndarray, dt: float = 0.01):
        """
        初始化线性系统模型
        
        Args:
            A: 状态转移矩阵 (n x n)
            B: 控制输入矩阵 (n x m)
            dt: 采样时间
        """
        self.A_continuous = A
        self.B_continuous = B
        self.dt = dt
        self.n_states = A.shape[0]
        self.n_controls = B.shape[1]
        
        # 离散化系统矩阵
        self._discretize_system()
        
        # 验证矩阵维度
        self._validate_matrices()
    
    def _discretize_system(self):
        """将连续时间系统离散化"""
        try:
            # 使用矩阵指数进行精确离散化
            n = self.n_states
            m = self.n_controls
            
            # 构建增广矩阵
            M = np.zeros((n + m, n + m))
            M[:n, :n] = self.A_continuous * self.dt
            M[:n, n:] = self.B_continuous * self.dt
            
            # 计算矩阵指数
            exp_M = scipy.linalg.expm(M)
            
            # 提取离散化矩阵
            self.A_discrete = exp_M[:n, :n]
            self.B_discrete = exp_M[:n, n:]
            
        except Exception as e:
            logging.warning(f"精确离散化失败，使用近似方法: {e}")
            # 使用一阶近似
            I = np.eye(self.n_states)
            self.A_discrete = I + self.A_continuous * self.dt
            self.B_discrete = self.B_continuous * self.dt
    
    def _validate_matrices(self):
        """验证矩阵维度和性质"""
        # 检查矩阵维度
        assert self.A_discrete.shape == (self.n_states, self.n_states), \
            f"A矩阵维度错误: {self.A_discrete.shape}"
        assert self.B_discrete.shape == (self.n_states, self.n_controls), \
            f"B矩阵维度错误: {self.B_discrete.shape}"
        
        # 检查矩阵是否为有限值
        assert np.all(np.isfinite(self.A_discrete)), "A矩阵包含无限值"
        assert np.all(np.isfinite(self.B_discrete)), "B矩阵包含无限值"
    
    def predict(self, x: np.ndarray, u: np.ndarray) -> np.ndarray:
        """
        预测下一状态
        
        Args:
            x: 当前状态 (n,)
            u: 控制输入 (m,)
            
        Returns:
            下一状态 (n,)
        """
        return self.A_discrete @ x + self.B_discrete @ u
    
    def get_linearization(self, x_ref: np.ndarray, u_ref: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        获取在参考点处的线性化矩阵
        
        Args:
            x_ref: 参考状态
            u_ref: 参考控制输入
            
        Returns:
            (A, B): 线性化矩阵
        """
        # 对于线性系统，线性化矩阵就是原矩阵
        return self.A_discrete, self.B_discrete


class LQRController(BaseAlgorithm):
    """LQR控制器实现"""
    
    def __init__(self, config: LQRConfig, system_model: LinearSystemModel = None):
        """
        初始化LQR控制器
        
        Args:
            config: LQR配置参数
            system_model: 线性系统模型
        """
        super().__init__()
        self.config = config
        self.system_model = system_model
        self.logger = logging.getLogger(__name__)
        
        # 控制器状态
        self.is_initialized = False
        self.K_gain = None  # 控制增益矩阵
        self.P_matrix = None  # Riccati方程解
        self.reference_state = np.zeros(config.state_dim)
        self.reference_control = np.zeros(config.control_dim)
        
        # 性能监控
        self.control_history = []
        self.state_history = []
        self.cost_history = []
        
        # 构建权重矩阵
        self._build_weight_matrices()
        
        # 如果提供了系统模型，立即计算增益
        if system_model is not None:
            self.set_system_model(system_model)
    
    def _build_weight_matrices(self):
        """构建权重矩阵Q和R"""
        # 状态权重矩阵Q
        self.Q = np.diag(self.config.Q_weights)
        
        # 控制权重矩阵R
        self.R = np.diag(self.config.R_weights)
        
        # 验证权重矩阵
        assert self.Q.shape == (self.config.state_dim, self.config.state_dim)
        assert self.R.shape == (self.config.control_dim, self.config.control_dim)
        assert np.all(np.linalg.eigvals(self.Q) >= 0), "Q矩阵必须半正定"
        assert np.all(np.linalg.eigvals(self.R) > 0), "R矩阵必须正定"
    
    def set_system_model(self, system_model: LinearSystemModel):
        """
        设置系统模型并计算LQR增益
        
        Args:
            system_model: 线性系统模型
        """
        self.system_model = system_model
        
        # 验证维度匹配
        assert system_model.n_states == self.config.state_dim, \
            f"状态维度不匹配: {system_model.n_states} vs {self.config.state_dim}"
        assert system_model.n_controls == self.config.control_dim, \
            f"控制维度不匹配: {system_model.n_controls} vs {self.config.control_dim}"
        
        # 计算LQR增益
        self._compute_lqr_gain()
        self.is_initialized = True
        
        self.logger.info("LQR控制器初始化完成")
    
    def _compute_lqr_gain(self):
        """计算LQR控制增益"""
        try:
            # 获取系统矩阵
            A = self.system_model.A_discrete
            B = self.system_model.B_discrete
            Q = self.Q
            R = self.R
            
            # 检查可控性
            if not self._check_controllability(A, B):
                self.logger.warning("系统不完全可控，LQR解可能不稳定")
            
            # 求解离散时间代数Riccati方程
            self.P_matrix = self._solve_dare(A, B, Q, R)
            
            # 计算控制增益矩阵
            temp = R + B.T @ self.P_matrix @ B
            self.K_gain = np.linalg.solve(temp, B.T @ self.P_matrix @ A)
            
            # 检查闭环稳定性
            if self.config.check_stability:
                self._check_closed_loop_stability(A, B)
            
            self.logger.info(f"LQR增益计算完成，增益矩阵形状: {self.K_gain.shape}")
            
        except Exception as e:
            self.logger.error(f"LQR增益计算失败: {e}")
            raise
    
    def _solve_dare(self, A: np.ndarray, B: np.ndarray, Q: np.ndarray, R: np.ndarray) -> np.ndarray:
        """
        求解离散时间代数Riccati方程 (DARE)
        
        Args:
            A, B: 系统矩阵
            Q, R: 权重矩阵
            
        Returns:
            P: Riccati方程的解
        """
        try:
            # 使用scipy求解DARE
            P = scipy.linalg.solve_discrete_are(A, B, Q, R)
            
            # 验证解的性质
            if not np.allclose(P, P.T):
                self.logger.warning("Riccati方程解不对称")
            
            eigenvals = np.linalg.eigvals(P)
            if not np.all(eigenvals >= -1e-10):  # 允许小的数值误差
                self.logger.warning("Riccati方程解不是半正定的")
            
            return P
            
        except Exception as e:
            self.logger.error(f"DARE求解失败: {e}")
            # 使用迭代方法作为备选
            return self._solve_dare_iterative(A, B, Q, R)
    
    def _solve_dare_iterative(self, A: np.ndarray, B: np.ndarray, Q: np.ndarray, R: np.ndarray) -> np.ndarray:
        """
        使用迭代方法求解DARE
        
        Args:
            A, B: 系统矩阵
            Q, R: 权重矩阵
            
        Returns:
            P: Riccati方程的解
        """
        n = A.shape[0]
        P = np.eye(n)  # 初始猜测
        
        for i in range(self.config.max_iterations):
            P_prev = P.copy()
            
            # Riccati迭代
            temp = R + B.T @ P @ B
            try:
                temp_inv = np.linalg.solve(temp, np.eye(temp.shape[0]))
                P = Q + A.T @ P @ A - A.T @ P @ B @ temp_inv @ B.T @ P @ A
            except np.linalg.LinAlgError:
                self.logger.error("Riccati迭代中矩阵奇异")
                break
            
            # 检查收敛
            if np.linalg.norm(P - P_prev) < self.config.tolerance:
                self.logger.info(f"DARE迭代收敛，迭代次数: {i+1}")
                break
        else:
            self.logger.warning(f"DARE迭代未收敛，最大迭代次数: {self.config.max_iterations}")
        
        return P
    
    def _check_controllability(self, A: np.ndarray, B: np.ndarray) -> bool:
        """检查系统可控性"""
        n = A.shape[0]
        controllability_matrix = B.copy()
        
        # 构建可控性矩阵 [B, AB, A^2B, ..., A^(n-1)B]
        A_power = np.eye(n)
        for i in range(1, n):
            A_power = A_power @ A
            controllability_matrix = np.hstack([controllability_matrix, A_power @ B])
        
        # 检查矩阵的秩
        rank = np.linalg.matrix_rank(controllability_matrix)
        is_controllable = (rank == n)
        
        self.logger.info(f"可控性检查: 秩={rank}, 状态维度={n}, 可控={is_controllable}")
        return is_controllable
    
    def _check_closed_loop_stability(self, A: np.ndarray, B: np.ndarray):
        """检查闭环系统稳定性"""
        # 闭环系统矩阵
        A_cl = A - B @ self.K_gain
        
        # 计算特征值
        eigenvals = np.linalg.eigvals(A_cl)
        
        # 检查稳定性（离散系统特征值模长应小于1）
        max_eigenval_magnitude = np.max(np.abs(eigenvals))
        is_stable = max_eigenval_magnitude < 1.0
        
        # 检查特征值实部
        max_real_part = np.max(np.real(eigenvals))
        
        self.logger.info(f"闭环稳定性: 最大特征值模长={max_eigenval_magnitude:.4f}, "
                        f"最大实部={max_real_part:.4f}, 稳定={is_stable}")
        
        if not is_stable:
            self.logger.warning("闭环系统不稳定！")
        
        return is_stable
    
    def set_reference(self, reference_state: np.ndarray, reference_control: np.ndarray = None):
        """
        设置参考状态和控制输入
        
        Args:
            reference_state: 参考状态
            reference_control: 参考控制输入（可选）
        """
        assert len(reference_state) == self.config.state_dim, \
            f"参考状态维度错误: {len(reference_state)} vs {self.config.state_dim}"
        
        self.reference_state = reference_state.copy()
        
        if reference_control is not None:
            assert len(reference_control) == self.config.control_dim, \
                f"参考控制维度错误: {len(reference_control)} vs {self.config.control_dim}"
            self.reference_control = reference_control.copy()
        else:
            self.reference_control = np.zeros(self.config.control_dim)
    
    def compute_control(self, current_state: np.ndarray) -> np.ndarray:
        """
        计算控制输入
        
        Args:
            current_state: 当前状态
            
        Returns:
            控制输入
        """
        if not self.is_initialized:
            raise RuntimeError("LQR控制器未初始化")
        
        # 计算状态误差
        state_error = current_state - self.reference_state
        
        # LQR控制律: u = -K * (x - x_ref) + u_ref
        control_input = -self.K_gain @ state_error + self.reference_control
        
        # 应用控制限制
        control_input = np.clip(control_input, 
                               self.config.min_control_effort, 
                               self.config.max_control_effort)
        
        # 记录历史数据
        self.control_history.append(control_input.copy())
        self.state_history.append(current_state.copy())
        
        # 计算代价
        cost = self._compute_cost(state_error, control_input - self.reference_control)
        self.cost_history.append(cost)
        
        return control_input
    
    def _compute_cost(self, state_error: np.ndarray, control_error: np.ndarray) -> float:
        """计算二次代价"""
        state_cost = state_error.T @ self.Q @ state_error
        control_cost = control_error.T @ self.R @ control_error
        return float(state_cost + control_cost)
    
    def update_weights(self, Q_weights: List[float] = None, R_weights: List[float] = None):
        """
        更新权重矩阵并重新计算增益
        
        Args:
            Q_weights: 新的状态权重
            R_weights: 新的控制权重
        """
        if Q_weights is not None:
            self.config.Q_weights = Q_weights
        if R_weights is not None:
            self.config.R_weights = R_weights
        
        # 重新构建权重矩阵
        self._build_weight_matrices()
        
        # 重新计算增益
        if self.system_model is not None:
            self._compute_lqr_gain()
            self.logger.info("权重更新完成，增益重新计算")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        if not self.cost_history:
            return {}
        
        costs = np.array(self.cost_history)
        controls = np.array(self.control_history) if self.control_history else np.array([])
        
        metrics = {
            'average_cost': np.mean(costs),
            'total_cost': np.sum(costs),
            'cost_std': np.std(costs),
            'min_cost': np.min(costs),
            'max_cost': np.max(costs),
            'num_steps': len(costs)
        }
        
        if len(controls) > 0:
            metrics.update({
                'average_control_effort': np.mean(np.abs(controls)),
                'max_control_effort': np.max(np.abs(controls)),
                'control_smoothness': np.mean(np.diff(controls, axis=0)**2) if len(controls) > 1 else 0.0
            })
        
        return metrics
    
    def reset(self):
        """重置控制器状态"""
        self.control_history.clear()
        self.state_history.clear()
        self.cost_history.clear()
        self.reference_state = np.zeros(self.config.state_dim)
        self.reference_control = np.zeros(self.config.control_dim)
    
    # BaseAlgorithm接口实现
    def initialize(self, **kwargs) -> bool:
        """初始化算法"""
        try:
            if 'system_model' in kwargs:
                self.set_system_model(kwargs['system_model'])
            return self.is_initialized
        except Exception as e:
            self.logger.error(f"LQR初始化失败: {e}")
            return False
    
    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """执行控制算法"""
        try:
            current_state = inputs.get('current_state')
            if current_state is None:
                raise ValueError("缺少当前状态输入")
            
            # 设置参考状态（如果提供）
            if 'reference_state' in inputs:
                ref_control = inputs.get('reference_control')
                self.set_reference(inputs['reference_state'], ref_control)
            
            # 计算控制输入
            control_input = self.compute_control(current_state)
            
            return {
                'control_input': control_input,
                'cost': self.cost_history[-1] if self.cost_history else 0.0,
                'gain_matrix': self.K_gain.copy() if self.K_gain is not None else None
            }
            
        except Exception as e:
            self.logger.error(f"LQR执行失败: {e}")
            return {'error': str(e)}
    
    def cleanup(self):
        """清理算法资源"""
        self.reset()
        self.logger.info("LQR控制器清理完成")
    
    def get_parameters(self) -> Dict[str, Any]:
        """获取算法参数"""
        return {
            'config': self.config.__dict__,
            'Q_matrix': self.Q.tolist() if hasattr(self, 'Q') else None,
            'R_matrix': self.R.tolist() if hasattr(self, 'R') else None,
            'K_gain': self.K_gain.tolist() if self.K_gain is not None else None,
            'is_initialized': self.is_initialized
        }
    
    def set_parameters(self, parameters: Dict[str, Any]):
        """设置算法参数"""
        if 'Q_weights' in parameters:
            self.config.Q_weights = parameters['Q_weights']
        if 'R_weights' in parameters:
            self.config.R_weights = parameters['R_weights']
        
        # 重新构建权重矩阵
        self._build_weight_matrices()
        
        # 如果系统模型存在，重新计算增益
        if self.system_model is not None:
            self._compute_lqr_gain()


def create_wheel_legged_robot_model(config: LQRConfig) -> LinearSystemModel:
    """
    创建轮腿机器人的简化线性模型
    
    Args:
        config: LQR配置
        
    Returns:
        线性系统模型
    """
    # 简化的轮腿机器人线性模型
    # 状态: [x, y, z, roll, pitch, yaw, vx, vy, vz, wx, wy, wz]
    # 控制: [tau1, tau2, tau3, tau4, tau5, tau6] (关节力矩)
    
    n_states = config.state_dim
    n_controls = config.control_dim
    
    # 构建状态转移矩阵A (连续时间)
    A = np.zeros((n_states, n_states))
    
    # 位置-速度关系
    A[0, 6] = 1.0  # dx/dt = vx
    A[1, 7] = 1.0  # dy/dt = vy
    A[2, 8] = 1.0  # dz/dt = vz
    
    # 姿态-角速度关系
    A[3, 9] = 1.0   # droll/dt = wx
    A[4, 10] = 1.0  # dpitch/dt = wy
    A[5, 11] = 1.0  # dyaw/dt = wz
    
    # 简化的动力学（阻尼项）
    damping = 0.1
    A[6, 6] = -damping   # 线速度阻尼
    A[7, 7] = -damping
    A[8, 8] = -damping
    A[9, 9] = -damping   # 角速度阻尼
    A[10, 10] = -damping
    A[11, 11] = -damping
    
    # 构建控制输入矩阵B
    B = np.zeros((n_states, n_controls))
    
    # 简化的控制输入到加速度的映射
    # 假设关节力矩直接影响基座的线性和角加速度
    mass = 10.0  # 机器人质量 (kg)
    inertia = 1.0  # 简化的转动惯量
    
    # 控制输入影响线性加速度
    B[6, 0] = 1.0 / mass  # 前后运动
    B[7, 1] = 1.0 / mass  # 左右运动
    B[8, 2] = 1.0 / mass  # 上下运动
    
    # 控制输入影响角加速度
    B[9, 3] = 1.0 / inertia   # roll
    B[10, 4] = 1.0 / inertia  # pitch
    B[11, 5] = 1.0 / inertia  # yaw
    
    return LinearSystemModel(A, B, config.dt)


if __name__ == "__main__":
    # 测试LQR控制器
    import matplotlib.pyplot as plt
    
    print("🧪 测试LQR控制器")
    print("=" * 50)
    
    # 创建配置
    config = LQRConfig(
        state_dim=12,
        control_dim=6,
        dt=0.01,
        Q_weights=[10.0] * 6 + [1.0] * 6,  # 位置和姿态权重高，速度权重低
        R_weights=[0.1] * 6  # 控制权重
    )
    
    # 创建系统模型
    system_model = create_wheel_legged_robot_model(config)
    
    # 创建LQR控制器
    lqr = LQRController(config, system_model)
    
    print(f"✅ LQR控制器创建成功")
    print(f"📊 增益矩阵形状: {lqr.K_gain.shape}")
    print(f"🎯 系统稳定性检查通过")
    
    # 设置参考状态（目标位置）
    reference_state = np.array([1.0, 0.5, 0.3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    lqr.set_reference(reference_state)
    
    # 仿真测试
    print("\n🎮 开始仿真测试...")
    
    # 初始状态
    current_state = np.zeros(12)
    states = [current_state.copy()]
    controls = []
    costs = []
    
    # 仿真100步
    for step in range(100):
        # 计算控制输入
        control = lqr.compute_control(current_state)
        controls.append(control.copy())
        
        # 更新状态
        current_state = system_model.predict(current_state, control)
        states.append(current_state.copy())
        
        # 记录代价
        costs.append(lqr.cost_history[-1])
    
    # 分析结果
    states = np.array(states)
    controls = np.array(controls)
    costs = np.array(costs)
    
    print(f"\n📈 仿真结果:")
    print(f"   最终位置误差: {np.linalg.norm(states[-1][:3] - reference_state[:3]):.4f}")
    print(f"   平均代价: {np.mean(costs):.4f}")
    print(f"   最大控制力矩: {np.max(np.abs(controls)):.4f}")
    
    # 获取性能指标
    metrics = lqr.get_performance_metrics()
    print(f"\n📊 性能指标:")
    for key, value in metrics.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.4f}")
        else:
            print(f"   {key}: {value}")
    
    print("\n🎉 LQR控制器测试完成！")