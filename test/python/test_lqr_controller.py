#!/usr/bin/env python3
"""
LQR控制器测试

测试LQR控制器的各个功能组件。
"""

import unittest
import numpy as np
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/wheel_legged_control'))

from wheel_legged_control.algorithms.lqr_controller import (
    LQRController, LQRConfig, LinearSystemModel, create_wheel_legged_robot_model
)


class TestLinearSystemModel(unittest.TestCase):
    """测试线性系统模型"""
    
    def setUp(self):
        """设置测试环境"""
        # 简单的2x2系统
        self.A = np.array([[0, 1], [-1, -0.5]])
        self.B = np.array([[0], [1]])
        self.dt = 0.1
        self.model = LinearSystemModel(self.A, self.B, self.dt)
    
    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.model.n_states, 2)
        self.assertEqual(self.model.n_controls, 1)
        self.assertEqual(self.model.dt, self.dt)
        
        # 检查离散化矩阵存在
        self.assertIsNotNone(self.model.A_discrete)
        self.assertIsNotNone(self.model.B_discrete)
    
    def test_discretization(self):
        """测试系统离散化"""
        # 检查离散化矩阵维度
        self.assertEqual(self.model.A_discrete.shape, (2, 2))
        self.assertEqual(self.model.B_discrete.shape, (2, 1))
        
        # 检查矩阵是否有限
        self.assertTrue(np.all(np.isfinite(self.model.A_discrete)))
        self.assertTrue(np.all(np.isfinite(self.model.B_discrete)))
    
    def test_prediction(self):
        """测试状态预测"""
        x = np.array([1.0, 0.0])
        u = np.array([0.5])
        
        x_next = self.model.predict(x, u)
        
        self.assertEqual(x_next.shape, (2,))
        self.assertTrue(np.all(np.isfinite(x_next)))
    
    def test_linearization(self):
        """测试线性化"""
        x_ref = np.array([0.0, 0.0])
        u_ref = np.array([0.0])
        
        A_lin, B_lin = self.model.get_linearization(x_ref, u_ref)
        
        # 对于线性系统，线性化矩阵应该等于原矩阵
        np.testing.assert_array_almost_equal(A_lin, self.model.A_discrete)
        np.testing.assert_array_almost_equal(B_lin, self.model.B_discrete)


class TestLQRConfig(unittest.TestCase):
    """测试LQR配置"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = LQRConfig()
        
        self.assertEqual(config.state_dim, 12)
        self.assertEqual(config.control_dim, 6)
        self.assertEqual(len(config.Q_weights), 12)
        self.assertEqual(len(config.R_weights), 6)
        self.assertTrue(config.check_stability)
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = LQRConfig(
            state_dim=4,
            control_dim=2,
            Q_weights=[1.0, 2.0, 3.0, 4.0],
            R_weights=[0.1, 0.2],
            dt=0.05
        )
        
        self.assertEqual(config.state_dim, 4)
        self.assertEqual(config.control_dim, 2)
        self.assertEqual(config.Q_weights, [1.0, 2.0, 3.0, 4.0])
        self.assertEqual(config.R_weights, [0.1, 0.2])
        self.assertEqual(config.dt, 0.05)


class TestLQRController(unittest.TestCase):
    """测试LQR控制器"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建简单的2D系统配置
        self.config = LQRConfig(
            state_dim=4,
            control_dim=2,
            Q_weights=[10.0, 10.0, 1.0, 1.0],  # 位置权重高，速度权重低
            R_weights=[0.1, 0.1],
            dt=0.1
        )
        
        # 创建简单的双积分器系统
        A = np.array([
            [0, 0, 1, 0],
            [0, 0, 0, 1],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ])
        B = np.array([
            [0, 0],
            [0, 0],
            [1, 0],
            [0, 1]
        ])
        
        self.system_model = LinearSystemModel(A, B, self.config.dt)
        self.lqr = LQRController(self.config)
    
    def test_initialization_without_model(self):
        """测试无系统模型的初始化"""
        lqr = LQRController(self.config)
        
        self.assertFalse(lqr.is_initialized)
        self.assertIsNone(lqr.K_gain)
        self.assertIsNone(lqr.P_matrix)
    
    def test_initialization_with_model(self):
        """测试有系统模型的初始化"""
        lqr = LQRController(self.config, self.system_model)
        
        self.assertTrue(lqr.is_initialized)
        self.assertIsNotNone(lqr.K_gain)
        self.assertIsNotNone(lqr.P_matrix)
        self.assertEqual(lqr.K_gain.shape, (2, 4))
    
    def test_set_system_model(self):
        """测试设置系统模型"""
        self.lqr.set_system_model(self.system_model)
        
        self.assertTrue(self.lqr.is_initialized)
        self.assertIsNotNone(self.lqr.K_gain)
        self.assertEqual(self.lqr.K_gain.shape, (self.config.control_dim, self.config.state_dim))
    
    def test_weight_matrices(self):
        """测试权重矩阵构建"""
        self.lqr.set_system_model(self.system_model)
        
        # 检查Q矩阵
        self.assertEqual(self.lqr.Q.shape, (4, 4))
        self.assertTrue(np.allclose(self.lqr.Q, np.diag(self.config.Q_weights)))
        
        # 检查R矩阵
        self.assertEqual(self.lqr.R.shape, (2, 2))
        self.assertTrue(np.allclose(self.lqr.R, np.diag(self.config.R_weights)))
        
        # 检查矩阵性质
        eigenvals_Q = np.linalg.eigvals(self.lqr.Q)
        eigenvals_R = np.linalg.eigvals(self.lqr.R)
        self.assertTrue(np.all(eigenvals_Q >= 0))  # Q半正定
        self.assertTrue(np.all(eigenvals_R > 0))   # R正定
    
    def test_reference_setting(self):
        """测试参考状态设置"""
        self.lqr.set_system_model(self.system_model)
        
        ref_state = np.array([1.0, 2.0, 0.0, 0.0])
        ref_control = np.array([0.1, 0.2])
        
        self.lqr.set_reference(ref_state, ref_control)
        
        np.testing.assert_array_equal(self.lqr.reference_state, ref_state)
        np.testing.assert_array_equal(self.lqr.reference_control, ref_control)
    
    def test_control_computation(self):
        """测试控制计算"""
        self.lqr.set_system_model(self.system_model)
        
        # 设置参考状态
        ref_state = np.array([1.0, 1.0, 0.0, 0.0])
        self.lqr.set_reference(ref_state)
        
        # 计算控制输入
        current_state = np.array([0.0, 0.0, 0.0, 0.0])
        control = self.lqr.compute_control(current_state)
        
        self.assertEqual(control.shape, (2,))
        self.assertTrue(np.all(np.isfinite(control)))
        
        # 控制输入应该在限制范围内
        self.assertTrue(np.all(control >= self.config.min_control_effort))
        self.assertTrue(np.all(control <= self.config.max_control_effort))
    
    def test_control_limits(self):
        """测试控制限制"""
        self.lqr.set_system_model(self.system_model)
        
        # 设置极端参考状态以测试限制
        ref_state = np.array([100.0, 100.0, 0.0, 0.0])
        self.lqr.set_reference(ref_state)
        
        current_state = np.array([0.0, 0.0, 0.0, 0.0])
        control = self.lqr.compute_control(current_state)
        
        # 控制输入应该被限制
        self.assertTrue(np.all(control >= self.config.min_control_effort))
        self.assertTrue(np.all(control <= self.config.max_control_effort))
    
    def test_performance_metrics(self):
        """测试性能指标"""
        self.lqr.set_system_model(self.system_model)
        
        # 执行几步控制
        ref_state = np.array([1.0, 1.0, 0.0, 0.0])
        self.lqr.set_reference(ref_state)
        
        current_state = np.array([0.0, 0.0, 0.0, 0.0])
        for _ in range(5):
            control = self.lqr.compute_control(current_state)
            current_state = self.system_model.predict(current_state, control)
        
        # 获取性能指标
        metrics = self.lqr.get_performance_metrics()
        
        self.assertIn('average_cost', metrics)
        self.assertIn('total_cost', metrics)
        self.assertIn('num_steps', metrics)
        self.assertEqual(metrics['num_steps'], 5)
        self.assertGreater(metrics['average_cost'], 0)
    
    def test_weight_update(self):
        """测试权重更新"""
        self.lqr.set_system_model(self.system_model)
        
        # 记录原始增益
        original_gain = self.lqr.K_gain.copy()
        
        # 更新权重
        new_Q_weights = [20.0, 20.0, 2.0, 2.0]
        self.lqr.update_weights(Q_weights=new_Q_weights)
        
        # 检查权重是否更新
        self.assertEqual(self.lqr.lqr_config.Q_weights, new_Q_weights)
        
        # 检查增益是否重新计算
        self.assertFalse(np.allclose(self.lqr.K_gain, original_gain))
    
    def test_reset(self):
        """测试重置功能"""
        self.lqr.set_system_model(self.system_model)
        
        # 执行一些控制步骤
        ref_state = np.array([1.0, 1.0, 0.0, 0.0])
        self.lqr.set_reference(ref_state)
        
        current_state = np.array([0.0, 0.0, 0.0, 0.0])
        self.lqr.compute_control(current_state)
        
        # 检查历史数据存在
        self.assertGreater(len(self.lqr.control_history), 0)
        self.assertGreater(len(self.lqr.cost_history), 0)
        
        # 重置
        self.lqr.reset()
        
        # 检查历史数据被清空
        self.assertEqual(len(self.lqr.control_history), 0)
        self.assertEqual(len(self.lqr.cost_history), 0)
        np.testing.assert_array_equal(self.lqr.reference_state, np.zeros(4))
    
    def test_base_algorithm_interface(self):
        """测试BaseAlgorithm接口"""
        # 测试初始化
        success = self.lqr.initialize(system_model=self.system_model)
        self.assertTrue(success)
        
        # 测试执行
        inputs = {
            'current_state': np.array([0.0, 0.0, 0.0, 0.0]),
            'reference_state': np.array([1.0, 1.0, 0.0, 0.0])
        }
        
        outputs = self.lqr.execute(inputs)
        
        self.assertIn('control_input', outputs)
        self.assertIn('cost', outputs)
        self.assertIn('gain_matrix', outputs)
        
        # 测试参数获取和设置
        params = self.lqr.get_parameters()
        self.assertIn('config', params)
        self.assertIn('is_initialized', params)
        
        # 测试清理
        self.lqr.cleanup()


class TestWheelLeggedRobotModel(unittest.TestCase):
    """测试轮腿机器人模型创建"""
    
    def test_model_creation(self):
        """测试模型创建"""
        config = LQRConfig()
        model = create_wheel_legged_robot_model(config)
        
        self.assertEqual(model.n_states, config.state_dim)
        self.assertEqual(model.n_controls, config.control_dim)
        self.assertEqual(model.dt, config.dt)
        
        # 检查矩阵维度
        self.assertEqual(model.A_discrete.shape, (12, 12))
        self.assertEqual(model.B_discrete.shape, (12, 6))
        
        # 检查矩阵是否有限
        self.assertTrue(np.all(np.isfinite(model.A_discrete)))
        self.assertTrue(np.all(np.isfinite(model.B_discrete)))


class TestLQRIntegration(unittest.TestCase):
    """LQR控制器集成测试"""
    
    def test_full_control_loop(self):
        """测试完整控制循环"""
        # 创建配置和模型
        config = LQRConfig(
            state_dim=4,
            control_dim=2,
            Q_weights=[10.0, 10.0, 1.0, 1.0],
            R_weights=[0.1, 0.1],
            dt=0.1
        )
        
        # 双积分器系统
        A = np.array([
            [0, 0, 1, 0],
            [0, 0, 0, 1],
            [0, 0, -0.1, 0],  # 添加阻尼
            [0, 0, 0, -0.1]
        ])
        B = np.array([
            [0, 0],
            [0, 0],
            [1, 0],
            [0, 1]
        ])
        
        system_model = LinearSystemModel(A, B, config.dt)
        lqr = LQRController(config, system_model)
        
        # 设置目标
        target_state = np.array([2.0, 1.0, 0.0, 0.0])
        lqr.set_reference(target_state)
        
        # 仿真控制循环
        current_state = np.array([0.0, 0.0, 0.0, 0.0])
        states = [current_state.copy()]
        
        for step in range(50):
            control = lqr.compute_control(current_state)
            current_state = system_model.predict(current_state, control)
            states.append(current_state.copy())
        
        # 检查收敛性
        final_state = states[-1]
        position_error = np.linalg.norm(final_state[:2] - target_state[:2])
        
        # 应该收敛到目标位置附近
        self.assertLess(position_error, 0.5, "控制器未能收敛到目标位置")
        
        # 检查性能指标
        metrics = lqr.get_performance_metrics()
        self.assertGreater(metrics['num_steps'], 0)
        self.assertGreater(metrics['average_cost'], 0)
    
    def test_stability_with_different_weights(self):
        """测试不同权重下的稳定性"""
        config = LQRConfig(
            state_dim=4,
            control_dim=2,
            dt=0.1
        )
        
        # 简单系统
        A = np.array([
            [0, 0, 1, 0],
            [0, 0, 0, 1],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ])
        B = np.array([
            [0, 0],
            [0, 0],
            [1, 0],
            [0, 1]
        ])
        
        system_model = LinearSystemModel(A, B, config.dt)
        
        # 测试不同的权重组合
        weight_combinations = [
            ([1.0, 1.0, 0.1, 0.1], [0.1, 0.1]),
            ([10.0, 10.0, 1.0, 1.0], [1.0, 1.0]),
            ([100.0, 100.0, 10.0, 10.0], [0.01, 0.01])
        ]
        
        for Q_weights, R_weights in weight_combinations:
            config.Q_weights = Q_weights
            config.R_weights = R_weights
            
            lqr = LQRController(config, system_model)
            
            # 检查控制器初始化成功
            self.assertTrue(lqr.is_initialized)
            self.assertIsNotNone(lqr.K_gain)
            
            # 简单的稳定性测试
            current_state = np.array([1.0, 1.0, 0.0, 0.0])
            lqr.set_reference(np.zeros(4))
            
            # 执行几步控制
            for _ in range(10):
                control = lqr.compute_control(current_state)
                current_state = system_model.predict(current_state, control)
                
                # 状态不应该发散
                self.assertTrue(np.all(np.abs(current_state) < 100.0))


if __name__ == '__main__':
    print("🧪 开始LQR控制器测试")
    print("=" * 50)
    
    # 运行测试
    unittest.main(verbosity=2)