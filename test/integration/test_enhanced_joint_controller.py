#!/usr/bin/env python3
"""
增强型关节控制器集成测试

测试算法管理器与关节控制器的集成功能。
"""

import unittest
import time
import threading
from unittest.mock import Mock, patch
import numpy as np

# 添加项目路径
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/wheel_legged_control'))

from wheel_legged_control.controllers.joint_controller_enhanced import (
    EnhancedJointControllerNode, RobotSpecificPIDAlgorithm, AdaptivePIDAlgorithm
)
from wheel_legged_control.algorithms.algorithm_manager import (
    AlgorithmManager, AlgorithmType, AlgorithmConfig
)


class TestRobotSpecificPIDAlgorithm(unittest.TestCase):
    """机器人专用PID算法测试"""
    
    def setUp(self):
        """测试前准备"""
        config = AlgorithmConfig(
            name="测试PID",
            algorithm_type=AlgorithmType.CONTROL,
            parameters={
                'kp': 1.0,
                'ki': 0.1,
                'kd': 0.05,
                'max_integral': 1.0,
                'max_output': 10.0
            }
        )
        self.pid = RobotSpecificPIDAlgorithm(config)
        self.pid.initialize()
    
    def test_pid_initialization(self):
        """测试PID初始化"""
        self.assertTrue(self.pid.initialize())
        self.assertEqual(self.pid.kp, 1.0)
        self.assertEqual(self.pid.ki, 0.1)
        self.assertEqual(self.pid.kd, 0.05)
        self.assertEqual(self.pid.joint_states, {})
    
    def test_pid_single_joint_execution(self):
        """测试单关节PID执行"""
        inputs = {
            'joint_name': 'test_joint',
            'setpoint': 1.0,
            'current_value': 0.5,
            'dt': 0.01
        }
        
        result = self.pid.execute(inputs)
        
        self.assertIn('output', result)
        self.assertIn('error', result)
        self.assertIn('joint_name', result)
        self.assertEqual(result['joint_name'], 'test_joint')
        self.assertEqual(result['error'], 0.5)
        
        # 检查关节状态是否创建
        self.assertIn('test_joint', self.pid.joint_states)
    
    def test_pid_multiple_joints(self):
        """测试多关节PID执行"""
        joints = ['joint1', 'joint2', 'joint3']
        
        for joint in joints:
            inputs = {
                'joint_name': joint,
                'setpoint': 1.0,
                'current_value': 0.0,
                'dt': 0.01
            }
            result = self.pid.execute(inputs)
            self.assertEqual(result['joint_name'], joint)
        
        # 检查所有关节状态都已创建
        for joint in joints:
            self.assertIn(joint, self.pid.joint_states)
    
    def test_pid_integral_limiting(self):
        """测试积分限幅"""
        inputs = {
            'joint_name': 'test_joint',
            'setpoint': 10.0,  # 大误差
            'current_value': 0.0,
            'dt': 0.1
        }
        
        # 执行多次以累积积分
        for _ in range(20):
            result = self.pid.execute(inputs)
        
        # 检查积分是否被限制
        joint_state = self.pid.joint_states['test_joint']
        self.assertLessEqual(abs(joint_state['integral']), self.pid.max_integral)
    
    def test_pid_output_limiting(self):
        """测试输出限幅"""
        inputs = {
            'joint_name': 'test_joint',
            'setpoint': 100.0,  # 极大误差
            'current_value': 0.0,
            'dt': 0.01
        }
        
        result = self.pid.execute(inputs)
        
        # 检查输出是否被限制
        self.assertLessEqual(abs(result['output']), self.pid.max_output)
    
    def test_pid_cleanup(self):
        """测试PID清理"""
        # 先执行一些操作创建状态
        inputs = {
            'joint_name': 'test_joint',
            'setpoint': 1.0,
            'current_value': 0.5,
            'dt': 0.01
        }
        self.pid.execute(inputs)
        
        # 清理
        self.assertTrue(self.pid.cleanup())
        self.assertEqual(self.pid.joint_states, {})


class TestAdaptivePIDAlgorithm(unittest.TestCase):
    """自适应PID算法测试"""
    
    def setUp(self):
        """测试前准备"""
        config = AlgorithmConfig(
            name="自适应PID测试",
            algorithm_type=AlgorithmType.CONTROL,
            parameters={
                'base_kp': 1.0,
                'base_ki': 0.1,
                'base_kd': 0.05,
                'adaptation_rate': 0.1,
                'max_output': 10.0
            }
        )
        self.adaptive_pid = AdaptivePIDAlgorithm(config)
        self.adaptive_pid.initialize()
    
    def test_adaptive_initialization(self):
        """测试自适应PID初始化"""
        self.assertTrue(self.adaptive_pid.initialize())
        self.assertEqual(self.adaptive_pid.base_kp, 1.0)
        self.assertEqual(self.adaptive_pid.adaptation_rate, 0.1)
    
    def test_adaptive_gain_adjustment(self):
        """测试增益自适应调整"""
        inputs = {
            'joint_name': 'test_joint',
            'setpoint': 1.0,
            'current_value': 0.0,  # 大误差
            'dt': 0.01
        }
        
        # 执行多次以触发自适应
        initial_kp = self.adaptive_pid.base_kp
        for _ in range(10):
            result = self.adaptive_pid.execute(inputs)
        
        # 检查增益是否调整
        joint_state = self.adaptive_pid.joint_states['test_joint']
        self.assertIn('adaptive_kp', result)
        
        # 由于误差较大，增益应该增加
        self.assertGreaterEqual(joint_state['kp'], initial_kp)
    
    def test_adaptive_small_error_response(self):
        """测试小误差时的自适应响应"""
        inputs = {
            'joint_name': 'test_joint',
            'setpoint': 1.0,
            'current_value': 0.995,  # 小误差
            'dt': 0.01
        }
        
        # 执行多次
        for _ in range(10):
            result = self.adaptive_pid.execute(inputs)
        
        # 检查增益调整
        joint_state = self.adaptive_pid.joint_states['test_joint']
        
        # 小误差时增益可能减少
        self.assertLessEqual(joint_state['kp'], self.adaptive_pid.base_kp * 2)


class MockROS2Node:
    """模拟ROS2节点"""
    
    def __init__(self):
        self.parameters = {}
        self.subscriptions = []
        self.publishers = []
        self.services = []
        self.timers = []
        
    def declare_parameter(self, name, default_value):
        self.parameters[name] = default_value
    
    def get_parameter(self, name):
        mock_param = Mock()
        mock_param.value = self.parameters.get(name)
        return mock_param
    
    def create_subscription(self, msg_type, topic, callback, qos):
        sub = Mock()
        self.subscriptions.append((msg_type, topic, callback, qos))
        return sub
    
    def create_publisher(self, msg_type, topic, qos):
        pub = Mock()
        self.publishers.append((msg_type, topic, qos))
        return pub
    
    def create_service(self, srv_type, name, callback):
        srv = Mock()
        self.services.append((srv_type, name, callback))
        return srv
    
    def create_timer(self, period, callback):
        timer = Mock()
        self.timers.append((period, callback))
        return timer
    
    def get_logger(self):
        logger = Mock()
        logger.info = Mock()
        logger.warn = Mock()
        logger.error = Mock()
        logger.debug = Mock()
        return logger
    
    def get_clock(self):
        clock = Mock()
        now = Mock()
        now.nanoseconds = int(time.time() * 1e9)
        now.to_msg = Mock(return_value=Mock())
        clock.now = Mock(return_value=now)
        return clock


class TestEnhancedJointControllerIntegration(unittest.TestCase):
    """增强型关节控制器集成测试"""
    
    def setUp(self):
        """测试前准备"""
        # 模拟ROS2环境
        self.mock_node = MockROS2Node()
        
    def test_algorithm_manager_integration(self):
        """测试算法管理器集成"""
        # 创建算法管理器
        manager = AlgorithmManager()
        
        # 注册机器人专用算法
        manager.register_algorithm_factory('robot_pid', RobotSpecificPIDAlgorithm)
        manager.register_algorithm_factory('adaptive_pid', AdaptivePIDAlgorithm)
        
        # 创建算法配置
        robot_pid_config = AlgorithmConfig(
            name="机器人PID",
            algorithm_type=AlgorithmType.CONTROL,
            parameters={'kp': 10.0, 'ki': 0.1, 'kd': 0.5}
        )
        
        adaptive_pid_config = AlgorithmConfig(
            name="自适应PID",
            algorithm_type=AlgorithmType.CONTROL,
            parameters={'base_kp': 10.0, 'base_ki': 0.1, 'base_kd': 0.5}
        )
        
        # 创建算法实例
        self.assertTrue(manager.create_algorithm('robot_pid', 'robot_pid', robot_pid_config))
        self.assertTrue(manager.create_algorithm('adaptive_pid', 'adaptive_pid', adaptive_pid_config))
        
        # 设置活跃算法
        self.assertTrue(manager.set_active_algorithm(AlgorithmType.CONTROL, 'robot_pid'))
        
        # 测试算法执行
        inputs = {
            'joint_name': 'test_joint',
            'setpoint': 1.0,
            'current_value': 0.5,
            'dt': 0.01
        }
        
        result = manager.execute_algorithm(AlgorithmType.CONTROL, inputs)
        self.assertIsNotNone(result)
        self.assertIn('output', result)
        
        # 切换算法
        self.assertTrue(manager.set_active_algorithm(AlgorithmType.CONTROL, 'adaptive_pid'))
        
        result2 = manager.execute_algorithm(AlgorithmType.CONTROL, inputs)
        self.assertIsNotNone(result2)
        self.assertIn('output', result2)
        
        # 清理
        manager.cleanup()
    
    def test_algorithm_performance_monitoring(self):
        """测试算法性能监控"""
        manager = AlgorithmManager()
        manager.register_algorithm_factory('robot_pid', RobotSpecificPIDAlgorithm)
        
        config = AlgorithmConfig(
            name="性能测试PID",
            algorithm_type=AlgorithmType.CONTROL,
            parameters={'kp': 1.0, 'ki': 0.1, 'kd': 0.05}
        )
        
        self.assertTrue(manager.create_algorithm('perf_pid', 'robot_pid', config))
        self.assertTrue(manager.set_active_algorithm(AlgorithmType.CONTROL, 'perf_pid'))
        
        # 执行多次算法
        inputs = {
            'joint_name': 'test_joint',
            'setpoint': 1.0,
            'current_value': 0.5,
            'dt': 0.01
        }
        
        for _ in range(10):
            result = manager.execute_algorithm(AlgorithmType.CONTROL, inputs)
            self.assertIsNotNone(result)
        
        # 检查性能报告
        report = manager.get_performance_report()
        self.assertIn('algorithms', report)
        self.assertIn('perf_pid', report['algorithms'])
        
        alg_report = report['algorithms']['perf_pid']
        self.assertEqual(alg_report['total_calls'], 10)
        self.assertEqual(alg_report['success_rate'], 1.0)
        self.assertGreater(alg_report['avg_execution_time'], 0)
        
        manager.cleanup()
    
    def test_algorithm_switching_performance(self):
        """测试算法切换性能"""
        manager = AlgorithmManager()
        manager.register_algorithm_factory('robot_pid', RobotSpecificPIDAlgorithm)
        manager.register_algorithm_factory('adaptive_pid', AdaptivePIDAlgorithm)
        
        # 创建两个算法
        config1 = AlgorithmConfig(
            name="PID1", algorithm_type=AlgorithmType.CONTROL,
            parameters={'kp': 1.0, 'ki': 0.1, 'kd': 0.05}
        )
        config2 = AlgorithmConfig(
            name="PID2", algorithm_type=AlgorithmType.CONTROL,
            parameters={'base_kp': 2.0, 'base_ki': 0.2, 'base_kd': 0.1}
        )
        
        self.assertTrue(manager.create_algorithm('pid1', 'robot_pid', config1))
        self.assertTrue(manager.create_algorithm('pid2', 'adaptive_pid', config2))
        
        inputs = {
            'joint_name': 'test_joint',
            'setpoint': 1.0,
            'current_value': 0.5,
            'dt': 0.01
        }
        
        # 测试算法切换
        algorithms = ['pid1', 'pid2']
        results = []
        
        for i in range(10):
            alg_name = algorithms[i % 2]
            self.assertTrue(manager.set_active_algorithm(AlgorithmType.CONTROL, alg_name))
            
            result = manager.execute_algorithm(AlgorithmType.CONTROL, inputs)
            self.assertIsNotNone(result)
            results.append(result)
        
        # 检查结果
        self.assertEqual(len(results), 10)
        
        # 检查性能报告
        report = manager.get_performance_report()
        self.assertIn('pid1', report['algorithms'])
        self.assertIn('pid2', report['algorithms'])
        
        manager.cleanup()
    
    def test_joint_controller_algorithm_integration(self):
        """测试关节控制器与算法的集成"""
        # 创建独立的算法管理器进行测试
        manager = AlgorithmManager()
        manager.register_algorithm_factory('robot_pid', RobotSpecificPIDAlgorithm)
        
        config = AlgorithmConfig(
            name="关节控制PID",
            algorithm_type=AlgorithmType.CONTROL,
            parameters={
                'kp': 10.0,
                'ki': 0.1,
                'kd': 0.5,
                'max_output': 30.0
            }
        )
        
        self.assertTrue(manager.create_algorithm('joint_pid', 'robot_pid', config))
        self.assertTrue(manager.set_active_algorithm(AlgorithmType.CONTROL, 'joint_pid'))
        
        # 模拟多关节控制
        joint_names = ['lf0_joint', 'lf1_joint', 'rf0_joint', 'rf1_joint']
        target_positions = [0.5, -0.3, 0.2, -0.1]
        current_positions = [0.0, 0.0, 0.0, 0.0]
        
        efforts = []
        
        for i, joint_name in enumerate(joint_names):
            inputs = {
                'joint_name': joint_name,
                'setpoint': target_positions[i],
                'current_value': current_positions[i],
                'dt': 0.01
            }
            
            result = manager.execute_algorithm(AlgorithmType.CONTROL, inputs)
            self.assertIsNotNone(result)
            self.assertIn('output', result)
            
            efforts.append(result['output'])
        
        # 检查控制输出
        self.assertEqual(len(efforts), len(joint_names))
        for effort in efforts:
            self.assertIsInstance(effort, (int, float))
            self.assertLessEqual(abs(effort), 30.0)  # 检查输出限制
        
        manager.cleanup()


if __name__ == '__main__':
    # 配置日志
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    print("🧪 运行增强型关节控制器集成测试")
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestRobotSpecificPIDAlgorithm,
        TestAdaptivePIDAlgorithm,
        TestEnhancedJointControllerIntegration
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
        print("🎉 增强型关节控制器集成测试完成")
        exit(0)
    else:
        print(f"\n❌ 测试失败: {len(result.failures)} 个失败, {len(result.errors)} 个错误")
        exit(1)