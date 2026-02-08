#!/usr/bin/env python3
"""
算法管理器单元测试

测试算法管理器的核心功能，包括算法创建、切换、执行和性能监控。
"""

import unittest
import time
import tempfile
import os
import json
from unittest.mock import Mock, patch

# 添加项目路径
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/wheel_legged_control'))

from wheel_legged_control.algorithms.algorithm_manager import (
    AlgorithmManager, AlgorithmType, AlgorithmStatus, AlgorithmConfig,
    BaseAlgorithm, PIDControlAlgorithm, SimpleTrajectoryPlanner,
    create_default_algorithms
)


class MockAlgorithm(BaseAlgorithm):
    """测试用模拟算法"""
    
    def __init__(self, config: AlgorithmConfig):
        super().__init__(config)
        self.initialized = False
        self.cleaned_up = False
        self.execution_count = 0
        
    def initialize(self) -> bool:
        self.initialized = True
        self.status = AlgorithmStatus.IDLE
        return True
    
    def execute(self, inputs):
        self.execution_count += 1
        if inputs.get('should_fail', False):
            raise RuntimeError("模拟执行失败")
        return {'result': f"执行成功 #{self.execution_count}"}
    
    def cleanup(self) -> bool:
        self.cleaned_up = True
        self.status = AlgorithmStatus.STOPPED
        return True


class TestAlgorithmManager(unittest.TestCase):
    """算法管理器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.manager = AlgorithmManager()
        
        # 注册测试算法工厂
        self.manager.register_algorithm_factory('mock_algorithm', MockAlgorithm)
        
    def tearDown(self):
        """测试后清理"""
        self.manager.cleanup()
    
    def test_algorithm_creation_and_removal(self):
        """测试算法创建和移除"""
        config = AlgorithmConfig(
            name="测试算法",
            algorithm_type=AlgorithmType.CONTROL,
            parameters={'test_param': 1.0}
        )
        
        # 测试创建算法
        self.assertTrue(self.manager.create_algorithm('test_alg', 'mock_algorithm', config))
        self.assertIn('test_alg', self.manager.algorithms)
        
        # 测试重复创建
        self.assertFalse(self.manager.create_algorithm('test_alg', 'mock_algorithm', config))
        
        # 测试未知工厂
        self.assertFalse(self.manager.create_algorithm('test_alg2', 'unknown_factory', config))
        
        # 测试移除算法
        self.assertTrue(self.manager.remove_algorithm('test_alg'))
        self.assertNotIn('test_alg', self.manager.algorithms)
        
        # 测试移除不存在的算法
        self.assertFalse(self.manager.remove_algorithm('nonexistent'))
    
    def test_active_algorithm_management(self):
        """测试活跃算法管理"""
        config = AlgorithmConfig(
            name="测试控制算法",
            algorithm_type=AlgorithmType.CONTROL
        )
        
        # 创建算法
        self.assertTrue(self.manager.create_algorithm('control_alg', 'mock_algorithm', config))
        
        # 设置活跃算法
        self.assertTrue(self.manager.set_active_algorithm(AlgorithmType.CONTROL, 'control_alg'))
        self.assertEqual(self.manager.active_algorithms[AlgorithmType.CONTROL], 'control_alg')
        
        # 测试设置不存在的算法
        self.assertFalse(self.manager.set_active_algorithm(AlgorithmType.CONTROL, 'nonexistent'))
        
        # 测试类型不匹配
        planning_config = AlgorithmConfig(
            name="规划算法",
            algorithm_type=AlgorithmType.PLANNING
        )
        self.assertTrue(self.manager.create_algorithm('planning_alg', 'mock_algorithm', planning_config))
        self.assertFalse(self.manager.set_active_algorithm(AlgorithmType.CONTROL, 'planning_alg'))
    
    def test_algorithm_execution(self):
        """测试算法执行"""
        config = AlgorithmConfig(
            name="测试算法",
            algorithm_type=AlgorithmType.CONTROL
        )
        
        # 创建并设置活跃算法
        self.assertTrue(self.manager.create_algorithm('test_alg', 'mock_algorithm', config))
        self.assertTrue(self.manager.set_active_algorithm(AlgorithmType.CONTROL, 'test_alg'))
        
        # 测试成功执行
        result = self.manager.execute_algorithm(AlgorithmType.CONTROL, {'input': 'test'})
        self.assertIsNotNone(result)
        self.assertIn('result', result)
        
        # 测试执行失败
        result = self.manager.execute_algorithm(AlgorithmType.CONTROL, {'should_fail': True})
        self.assertIsNone(result)
        
        # 测试没有活跃算法
        result = self.manager.execute_algorithm(AlgorithmType.PLANNING, {})
        self.assertIsNone(result)
    
    def test_algorithm_enable_disable(self):
        """测试算法启用和禁用"""
        config = AlgorithmConfig(
            name="测试算法",
            algorithm_type=AlgorithmType.CONTROL
        )
        
        # 创建算法
        self.assertTrue(self.manager.create_algorithm('test_alg', 'mock_algorithm', config))
        self.assertTrue(self.manager.set_active_algorithm(AlgorithmType.CONTROL, 'test_alg'))
        
        # 测试禁用算法
        self.assertTrue(self.manager.disable_algorithm('test_alg'))
        self.assertFalse(self.manager.algorithms['test_alg'].config.enabled)
        self.assertNotIn(AlgorithmType.CONTROL, self.manager.active_algorithms)
        
        # 测试启用算法
        self.assertTrue(self.manager.enable_algorithm('test_alg'))
        self.assertTrue(self.manager.algorithms['test_alg'].config.enabled)
        
        # 测试不存在的算法
        self.assertFalse(self.manager.enable_algorithm('nonexistent'))
        self.assertFalse(self.manager.disable_algorithm('nonexistent'))
    
    def test_performance_monitoring(self):
        """测试性能监控"""
        config = AlgorithmConfig(
            name="测试算法",
            algorithm_type=AlgorithmType.CONTROL
        )
        
        # 创建并执行算法
        self.assertTrue(self.manager.create_algorithm('test_alg', 'mock_algorithm', config))
        self.assertTrue(self.manager.set_active_algorithm(AlgorithmType.CONTROL, 'test_alg'))
        
        # 执行几次算法
        for i in range(5):
            self.manager.execute_algorithm(AlgorithmType.CONTROL, {'input': f'test_{i}'})
        
        # 检查性能指标
        algorithm = self.manager.algorithms['test_alg']
        self.assertEqual(algorithm.metrics.total_calls, 5)
        self.assertEqual(algorithm.metrics.success_rate, 1.0)
        self.assertGreater(algorithm.metrics.avg_execution_time, 0)
        
        # 测试失败情况
        self.manager.execute_algorithm(AlgorithmType.CONTROL, {'should_fail': True})
        self.assertEqual(algorithm.metrics.total_calls, 6)
        self.assertEqual(algorithm.metrics.error_count, 1)
        self.assertLess(algorithm.metrics.success_rate, 1.0)
    
    def test_performance_report(self):
        """测试性能报告"""
        config = AlgorithmConfig(
            name="测试算法",
            algorithm_type=AlgorithmType.CONTROL
        )
        
        # 创建算法并执行
        self.assertTrue(self.manager.create_algorithm('test_alg', 'mock_algorithm', config))
        self.assertTrue(self.manager.set_active_algorithm(AlgorithmType.CONTROL, 'test_alg'))
        self.manager.execute_algorithm(AlgorithmType.CONTROL, {'input': 'test'})
        
        # 获取性能报告
        report = self.manager.get_performance_report()
        
        self.assertIn('timestamp', report)
        self.assertEqual(report['total_algorithms'], 1)
        self.assertEqual(report['active_algorithms'], 1)
        self.assertEqual(report['total_executions'], 1)
        self.assertIn('algorithms', report)
        self.assertIn('test_alg', report['algorithms'])
        
        alg_report = report['algorithms']['test_alg']
        self.assertEqual(alg_report['total_calls'], 1)
        self.assertEqual(alg_report['success_rate'], 1.0)
        self.assertEqual(alg_report['error_count'], 0)
    
    def test_data_export(self):
        """测试数据导出"""
        config = AlgorithmConfig(
            name="测试算法",
            algorithm_type=AlgorithmType.CONTROL
        )
        
        # 创建算法并执行
        self.assertTrue(self.manager.create_algorithm('test_alg', 'mock_algorithm', config))
        self.assertTrue(self.manager.set_active_algorithm(AlgorithmType.CONTROL, 'test_alg'))
        self.manager.execute_algorithm(AlgorithmType.CONTROL, {'input': 'test'})
        
        # 导出数据
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            self.assertTrue(self.manager.export_performance_data(temp_file))
            
            # 验证导出的数据
            with open(temp_file, 'r') as f:
                data = json.load(f)
            
            self.assertIn('export_timestamp', data)
            self.assertIn('performance_report', data)
            self.assertIn('execution_history', data)
            self.assertIn('performance_history', data)
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_monitoring_thread(self):
        """测试监控线程"""
        # 启动监控
        self.manager.start_monitoring()
        self.assertTrue(self.manager.monitoring_enabled)
        self.assertIsNotNone(self.manager.monitoring_thread)
        
        # 等待一小段时间
        time.sleep(0.1)
        
        # 停止监控
        self.manager.stop_monitoring()
        self.assertFalse(self.manager.monitoring_enabled)


class TestPIDControlAlgorithm(unittest.TestCase):
    """PID控制算法测试"""
    
    def setUp(self):
        """测试前准备"""
        config = AlgorithmConfig(
            name="PID测试",
            algorithm_type=AlgorithmType.CONTROL,
            parameters={'kp': 1.0, 'ki': 0.1, 'kd': 0.05}
        )
        self.pid = PIDControlAlgorithm(config)
        self.pid.initialize()
    
    def test_pid_initialization(self):
        """测试PID初始化"""
        self.assertTrue(self.pid.initialize())
        self.assertEqual(self.pid.status, AlgorithmStatus.IDLE)
        self.assertEqual(self.pid.kp, 1.0)
        self.assertEqual(self.pid.ki, 0.1)
        self.assertEqual(self.pid.kd, 0.05)
    
    def test_pid_execution(self):
        """测试PID执行"""
        inputs = {
            'setpoint': 1.0,
            'current_value': 0.5,
            'dt': 0.01
        }
        
        result = self.pid.execute(inputs)
        
        self.assertIn('output', result)
        self.assertIn('error', result)
        self.assertIn('proportional', result)
        self.assertIn('integral', result)
        self.assertIn('derivative', result)
        
        self.assertEqual(result['error'], 0.5)
        self.assertEqual(result['proportional'], 0.5)  # kp * error
    
    def test_pid_cleanup(self):
        """测试PID清理"""
        self.assertTrue(self.pid.cleanup())
        self.assertEqual(self.pid.status, AlgorithmStatus.STOPPED)
        self.assertEqual(self.pid.integral, 0.0)
        self.assertEqual(self.pid.prev_error, 0.0)


class TestSimpleTrajectoryPlanner(unittest.TestCase):
    """简单轨迹规划器测试"""
    
    def setUp(self):
        """测试前准备"""
        config = AlgorithmConfig(
            name="轨迹规划测试",
            algorithm_type=AlgorithmType.PLANNING,
            parameters={'max_velocity': 1.0, 'max_acceleration': 2.0}
        )
        self.planner = SimpleTrajectoryPlanner(config)
        self.planner.initialize()
    
    def test_planner_initialization(self):
        """测试轨迹规划器初始化"""
        self.assertTrue(self.planner.initialize())
        self.assertEqual(self.planner.status, AlgorithmStatus.IDLE)
        self.assertEqual(self.planner.max_velocity, 1.0)
        self.assertEqual(self.planner.max_acceleration, 2.0)
    
    def test_trajectory_generation(self):
        """测试轨迹生成"""
        inputs = {
            'start_position': [0.0, 0.0],
            'end_position': [1.0, 1.0],
            'duration': 2.0,
            'num_points': 10
        }
        
        result = self.planner.execute(inputs)
        
        self.assertIn('trajectory', result)
        self.assertIn('time_points', result)
        self.assertIn('duration', result)
        self.assertIn('num_points', result)
        
        self.assertEqual(len(result['trajectory']), 10)
        self.assertEqual(len(result['time_points']), 10)
        self.assertEqual(result['duration'], 2.0)
        
        # 检查轨迹起点和终点
        start_point = result['trajectory'][0]
        end_point = result['trajectory'][-1]
        
        self.assertAlmostEqual(start_point[0], 0.0, places=5)
        self.assertAlmostEqual(start_point[1], 0.0, places=5)
        self.assertAlmostEqual(end_point[0], 1.0, places=5)
        self.assertAlmostEqual(end_point[1], 1.0, places=5)
    
    def test_planner_cleanup(self):
        """测试轨迹规划器清理"""
        self.assertTrue(self.planner.cleanup())
        self.assertEqual(self.planner.status, AlgorithmStatus.STOPPED)


class TestDefaultAlgorithms(unittest.TestCase):
    """默认算法测试"""
    
    def setUp(self):
        """测试前准备"""
        self.manager = AlgorithmManager()
    
    def tearDown(self):
        """测试后清理"""
        self.manager.cleanup()
    
    def test_create_default_algorithms(self):
        """测试创建默认算法"""
        self.assertTrue(create_default_algorithms(self.manager))
        
        # 检查算法是否创建
        self.assertIn('default_pid', self.manager.algorithms)
        self.assertIn('default_planner', self.manager.algorithms)
        
        # 检查活跃算法设置
        self.assertEqual(self.manager.active_algorithms[AlgorithmType.CONTROL], 'default_pid')
        self.assertEqual(self.manager.active_algorithms[AlgorithmType.PLANNING], 'default_planner')
        
        # 测试算法执行
        pid_result = self.manager.execute_algorithm(
            AlgorithmType.CONTROL, 
            {'setpoint': 1.0, 'current_value': 0.5, 'dt': 0.01}
        )
        self.assertIsNotNone(pid_result)
        
        planner_result = self.manager.execute_algorithm(
            AlgorithmType.PLANNING,
            {
                'start_position': [0.0],
                'end_position': [1.0],
                'duration': 1.0,
                'num_points': 5
            }
        )
        self.assertIsNotNone(planner_result)


if __name__ == '__main__':
    # 配置日志
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    print("🧪 运行算法管理器单元测试")
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestAlgorithmManager,
        TestPIDControlAlgorithm,
        TestSimpleTrajectoryPlanner,
        TestDefaultAlgorithms
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 输出结果
    if result.wasSuccessful():
        print("\n✅ 所有测试通过！")
        exit(0)
    else:
        print(f"\n❌ 测试失败: {len(result.failures)} 个失败, {len(result.errors)} 个错误")
        exit(1)