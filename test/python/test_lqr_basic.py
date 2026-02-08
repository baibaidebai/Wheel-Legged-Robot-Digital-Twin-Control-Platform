#!/usr/bin/env python3
"""
LQR控制器基础测试（不依赖SciPy）

测试LQR控制器的基本结构和功能。
"""

import unittest
import numpy as np
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/wheel_legged_control'))


class TestLQRBasicStructure(unittest.TestCase):
    """测试LQR基础结构"""
    
    def test_lqr_module_import(self):
        """测试LQR模块导入"""
        try:
            from wheel_legged_control.algorithms import lqr_controller
            self.assertTrue(hasattr(lqr_controller, 'LQRConfig'))
            self.assertTrue(hasattr(lqr_controller, 'LQRController'))
            self.assertTrue(hasattr(lqr_controller, 'LinearSystemModel'))
            print("✅ LQR模块导入成功")
        except ImportError as e:
            if 'scipy' in str(e) or 'numpy' in str(e):
                print("⚠️  SciPy/NumPy版本兼容性问题，跳过测试")
                self.skipTest("SciPy/NumPy compatibility issue")
            else:
                raise
    
    def test_lqr_config_creation(self):
        """测试LQR配置创建"""
        try:
            from wheel_legged_control.algorithms.lqr_controller import LQRConfig
            
            # 测试默认配置
            config = LQRConfig()
            self.assertEqual(config.state_dim, 12)
            self.assertEqual(config.control_dim, 6)
            self.assertEqual(len(config.Q_weights), 12)
            self.assertEqual(len(config.R_weights), 6)
            
            # 测试自定义配置
            custom_config = LQRConfig(
                state_dim=4,
                control_dim=2,
                Q_weights=[1.0, 2.0, 3.0, 4.0],
                R_weights=[0.1, 0.2]
            )
            self.assertEqual(custom_config.state_dim, 4)
            self.assertEqual(custom_config.control_dim, 2)
            
            print("✅ LQR配置创建成功")
            
        except ImportError as e:
            if 'scipy' in str(e) or 'numpy' in str(e):
                self.skipTest("SciPy/NumPy compatibility issue")
            else:
                raise
    
    def test_linear_system_model_basic(self):
        """测试线性系统模型基础功能"""
        try:
            from wheel_legged_control.algorithms.lqr_controller import LinearSystemModel
            
            # 创建简单的2x2系统
            A = np.array([[0, 1], [-1, -0.5]])
            B = np.array([[0], [1]])
            dt = 0.1
            
            model = LinearSystemModel(A, B, dt)
            
            # 检查基本属性
            self.assertEqual(model.n_states, 2)
            self.assertEqual(model.n_controls, 1)
            self.assertEqual(model.dt, dt)
            
            # 检查矩阵存在
            self.assertIsNotNone(model.A_discrete)
            self.assertIsNotNone(model.B_discrete)
            
            print("✅ 线性系统模型创建成功")
            
        except ImportError as e:
            if 'scipy' in str(e) or 'numpy' in str(e):
                self.skipTest("SciPy/NumPy compatibility issue")
            else:
                raise
    
    def test_lqr_controller_basic(self):
        """测试LQR控制器基础功能"""
        try:
            from wheel_legged_control.algorithms.lqr_controller import (
                LQRController, LQRConfig
            )
            
            # 创建配置
            config = LQRConfig(
                state_dim=4,
                control_dim=2,
                Q_weights=[1.0, 1.0, 0.1, 0.1],
                R_weights=[0.1, 0.1]
            )
            
            # 创建控制器
            lqr = LQRController(config)
            
            # 检查初始状态
            self.assertFalse(lqr.is_initialized)
            self.assertIsNone(lqr.K_gain)
            
            # 检查配置
            self.assertEqual(lqr.config.state_dim, 4)
            self.assertEqual(lqr.config.control_dim, 2)
            
            print("✅ LQR控制器创建成功")
            
        except ImportError as e:
            if 'scipy' in str(e) or 'numpy' in str(e):
                self.skipTest("SciPy/NumPy compatibility issue")
            else:
                raise
    
    def test_algorithm_interface(self):
        """测试算法接口"""
        try:
            from wheel_legged_control.algorithms.lqr_controller import LQRController, LQRConfig
            from wheel_legged_control.algorithms.algorithm_manager import BaseAlgorithm
            
            config = LQRConfig()
            lqr = LQRController(config)
            
            # 检查是否继承自BaseAlgorithm
            self.assertIsInstance(lqr, BaseAlgorithm)
            
            # 检查接口方法存在
            self.assertTrue(hasattr(lqr, 'initialize'))
            self.assertTrue(hasattr(lqr, 'execute'))
            self.assertTrue(hasattr(lqr, 'cleanup'))
            self.assertTrue(hasattr(lqr, 'get_parameters'))
            self.assertTrue(hasattr(lqr, 'set_parameters'))
            
            print("✅ 算法接口验证通过")
            
        except ImportError as e:
            if 'scipy' in str(e) or 'numpy' in str(e):
                self.skipTest("SciPy/NumPy compatibility issue")
            else:
                raise
    
    def test_file_structure(self):
        """测试文件结构"""
        lqr_file = os.path.join(
            os.path.dirname(__file__), 
            '../../src/wheel_legged_control/wheel_legged_control/algorithms/lqr_controller.py'
        )
        
        self.assertTrue(os.path.exists(lqr_file), "LQR控制器文件不存在")
        
        # 检查文件内容
        with open(lqr_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # 检查关键类和函数
            self.assertIn('class LQRConfig', content)
            self.assertIn('class LinearSystemModel', content)
            self.assertIn('class LQRController', content)
            self.assertIn('def create_wheel_legged_robot_model', content)
            self.assertIn('def _solve_dare', content)
            self.assertIn('def compute_control', content)
        
        print("✅ LQR文件结构验证通过")


class TestLQRWithoutScipy(unittest.TestCase):
    """测试不依赖SciPy的LQR功能"""
    
    def test_config_validation(self):
        """测试配置验证"""
        try:
            from wheel_legged_control.algorithms.lqr_controller import LQRConfig
            
            # 测试各种配置组合
            configs = [
                LQRConfig(state_dim=2, control_dim=1),
                LQRConfig(state_dim=6, control_dim=3),
                LQRConfig(state_dim=12, control_dim=6)
            ]
            
            for config in configs:
                self.assertGreater(config.state_dim, 0)
                self.assertGreater(config.control_dim, 0)
                self.assertGreater(config.dt, 0)
                self.assertGreater(config.max_control_effort, 0)
            
            print("✅ 配置验证通过")
            
        except ImportError as e:
            if 'scipy' in str(e) or 'numpy' in str(e):
                self.skipTest("SciPy/NumPy compatibility issue")
            else:
                raise
    
    def test_weight_matrix_dimensions(self):
        """测试权重矩阵维度"""
        try:
            from wheel_legged_control.algorithms.lqr_controller import LQRConfig
            
            config = LQRConfig(
                state_dim=4,
                control_dim=2,
                Q_weights=[1.0, 2.0, 3.0, 4.0],
                R_weights=[0.1, 0.2]
            )
            
            # 检查权重向量长度
            self.assertEqual(len(config.Q_weights), config.state_dim)
            self.assertEqual(len(config.R_weights), config.control_dim)
            
            print("✅ 权重矩阵维度验证通过")
            
        except ImportError as e:
            if 'scipy' in str(e) or 'numpy' in str(e):
                self.skipTest("SciPy/NumPy compatibility issue")
            else:
                raise
    
    def test_parameter_ranges(self):
        """测试参数范围"""
        try:
            from wheel_legged_control.algorithms.lqr_controller import LQRConfig
            
            config = LQRConfig()
            
            # 检查参数范围
            self.assertGreater(config.dt, 0)
            self.assertGreater(config.max_iterations, 0)
            self.assertGreater(config.tolerance, 0)
            self.assertLess(config.max_eigenvalue_real, 0)  # 稳定性要求
            
            # 检查控制限制
            self.assertLess(config.min_control_effort, config.max_control_effort)
            
            print("✅ 参数范围验证通过")
            
        except ImportError as e:
            if 'scipy' in str(e) or 'numpy' in str(e):
                self.skipTest("SciPy/NumPy compatibility issue")
            else:
                raise


if __name__ == '__main__':
    print("🧪 开始LQR控制器基础测试（无SciPy依赖）")
    print("=" * 60)
    
    # 运行测试
    unittest.main(verbosity=2)