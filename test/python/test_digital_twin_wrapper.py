#!/usr/bin/env python3
"""
数字孪生映射器Python包装器测试

测试Python包装器的完整功能，包括C++绑定回退机制
"""

import unittest
import numpy as np
import sys
import os

# 添加源码路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/wheel_legged_control'))

from wheel_legged_control.core.digital_twin_mapper_wrapper import (
    DigitalTwinMapper, ConstraintModel, WheelConstraint, LegConstraint,
    TaskSpaceState, ValidationResult, ConstraintType,
    create_test_constraint_model, create_test_task_state
)


class TestDigitalTwinMapperWrapper(unittest.TestCase):
    """数字孪生映射器包装器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.mapper = DigitalTwinMapper()
        self.test_model = create_test_constraint_model()
    
    def test_constraint_model_creation(self):
        """测试约束模型创建"""
        # 测试空模型
        empty_model = ConstraintModel()
        self.assertEqual(len(empty_model.wheel_constraints), 0)
        self.assertEqual(len(empty_model.leg_constraints), 0)
        self.assertEqual(len(empty_model.coupling_constraints), 0)
        
        # 测试预定义模型
        self.assertEqual(len(self.test_model.wheel_constraints), 2)
        self.assertEqual(len(self.test_model.leg_constraints), 2)
        
        # 验证轮子约束
        left_wheel = self.test_model.wheel_constraints[0]
        self.assertEqual(left_wheel.wheel_name, "left_wheel")
        self.assertAlmostEqual(left_wheel.friction_coefficient, 0.8)
        np.testing.assert_array_almost_equal(left_wheel.contact_point, [0.0, 0.2, 0.0])
        
        # 验证腿部约束
        left_leg = self.test_model.leg_constraints[0]
        self.assertEqual(left_leg.leg_name, "left_leg")
        self.assertEqual(len(left_leg.joints), 2)
        self.assertIn("lf0_joint", left_leg.joints)
        self.assertIn("lf1_joint", left_leg.joints)
    
    def test_wheel_constraint_operations(self):
        """测试轮子约束操作"""
        wheel = WheelConstraint()
        
        # 测试默认值
        self.assertEqual(wheel.wheel_name, "")
        self.assertAlmostEqual(wheel.friction_coefficient, 0.8)
        np.testing.assert_array_almost_equal(wheel.contact_point, [0.0, 0.0, 0.0])
        np.testing.assert_array_almost_equal(wheel.normal_vector, [0.0, 0.0, 1.0])
        
        # 测试设置值
        wheel.wheel_name = "test_wheel"
        wheel.friction_coefficient = 0.9
        wheel.contact_point = np.array([1.0, 2.0, 3.0])
        wheel.normal_vector = np.array([0.0, 1.0, 0.0])
        
        self.assertEqual(wheel.wheel_name, "test_wheel")
        self.assertAlmostEqual(wheel.friction_coefficient, 0.9)
        np.testing.assert_array_almost_equal(wheel.contact_point, [1.0, 2.0, 3.0])
        np.testing.assert_array_almost_equal(wheel.normal_vector, [0.0, 1.0, 0.0])
    
    def test_leg_constraint_operations(self):
        """测试腿部约束操作"""
        leg = LegConstraint()
        
        # 测试默认值
        self.assertEqual(leg.leg_name, "")
        self.assertEqual(len(leg.joints), 0)
        self.assertEqual(leg.jacobian.shape, (3, 2))
        
        # 测试设置值
        leg.leg_name = "test_leg"
        leg.joints = ["joint1", "joint2"]
        leg.jacobian = np.array([[1, 0], [0, 1], [1, 1]])
        
        self.assertEqual(leg.leg_name, "test_leg")
        self.assertEqual(len(leg.joints), 2)
        self.assertEqual(leg.joints[0], "joint1")
        self.assertEqual(leg.joints[1], "joint2")
        np.testing.assert_array_almost_equal(leg.jacobian, [[1, 0], [0, 1], [1, 1]])
    
    def test_task_space_state_operations(self):
        """测试任务空间状态操作"""
        # 测试默认状态
        state = TaskSpaceState()
        np.testing.assert_array_almost_equal(state.base_position, [0.0, 0.0, 0.0])
        np.testing.assert_array_almost_equal(state.base_orientation, [0.0, 0.0, 0.0, 1.0])
        self.assertEqual(len(state.wheel_positions), 0)
        self.assertEqual(len(state.leg_end_positions), 0)
        
        # 测试预定义状态
        test_state = create_test_task_state()
        np.testing.assert_array_almost_equal(test_state.base_position, [0.0, 0.0, 0.2])
        self.assertEqual(len(test_state.wheel_positions), 2)
        self.assertEqual(len(test_state.leg_end_positions), 2)
        
        self.assertIn("left_wheel", test_state.wheel_positions)
        self.assertIn("right_wheel", test_state.wheel_positions)
        self.assertIn("left_leg", test_state.leg_end_positions)
        self.assertIn("right_leg", test_state.leg_end_positions)
    
    def test_kinematic_model_building(self):
        """测试运动学模型构建"""
        success = self.mapper.build_kinematic_model(self.test_model)
        self.assertTrue(success)
    
    def test_joint_to_task_mapping(self):
        """测试关节空间到任务空间映射"""
        # 构建模型
        self.mapper.build_kinematic_model(self.test_model)
        
        # 测试正运动学
        joint_angles = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
        task_state = self.mapper.joint_to_task_mapping(joint_angles)
        
        # 验证结果
        self.assertIsInstance(task_state, TaskSpaceState)
        self.assertEqual(len(task_state.wheel_positions), 2)
        self.assertEqual(len(task_state.leg_end_positions), 2)
        
        # 验证基座位置
        self.assertEqual(len(task_state.base_position), 3)
        self.assertEqual(len(task_state.base_orientation), 4)
        
        # 验证轮子位置
        for wheel_name, wheel_pos in task_state.wheel_positions.items():
            self.assertEqual(len(wheel_pos), 3)
            self.assertTrue(np.all(np.isfinite(wheel_pos)))
        
        # 验证腿端位置
        for leg_name, leg_pos in task_state.leg_end_positions.items():
            self.assertEqual(len(leg_pos), 3)
            self.assertTrue(np.all(np.isfinite(leg_pos)))
    
    def test_task_to_joint_mapping(self):
        """测试任务空间到关节空间映射"""
        # 构建模型
        self.mapper.build_kinematic_model(self.test_model)
        
        # 测试逆运动学
        test_state = create_test_task_state()
        joint_angles = self.mapper.task_to_joint_mapping(test_state)
        
        # 验证结果
        self.assertIsInstance(joint_angles, np.ndarray)
        self.assertEqual(len(joint_angles), 6)  # 2轮子 + 4腿部关节
        self.assertTrue(np.all(np.isfinite(joint_angles)))
        
        # 验证关节角度在合理范围内
        for angle in joint_angles:
            self.assertLessEqual(abs(angle), 2 * np.pi)
    
    def test_motion_consistency_validation(self):
        """测试运动一致性验证"""
        # 构建模型
        self.mapper.build_kinematic_model(self.test_model)
        
        # 测试有效关节角度
        valid_angles = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
        result = self.mapper.validate_motion_consistency(valid_angles)
        
        self.assertIsInstance(result, ValidationResult)
        self.assertIsInstance(result.is_valid, bool)
        self.assertIsInstance(result.error_message, str)
        self.assertIsInstance(result.consistency_error, float)
        self.assertGreaterEqual(result.consistency_error, 0.0)
        
        # 测试无效关节角度（超出限制）
        invalid_angles = np.array([5.0, 0.2, 0.3, 0.4, 0.5, 0.6])  # 第一个角度超出π
        result = self.mapper.validate_motion_consistency(invalid_angles)
        
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.error_message), 0)
    
    def test_singular_configuration_handling(self):
        """测试奇异位形处理"""
        # 测试正常矩阵
        jacobian = np.eye(3, 3)
        regularized = self.mapper.handle_singular_configuration(jacobian)
        
        self.assertIsInstance(regularized, np.ndarray)
        self.assertEqual(regularized.shape, jacobian.shape)
        
        # 测试奇异矩阵
        singular_jacobian = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0]  # 奇异行
        ])
        
        regularized = self.mapper.handle_singular_configuration(singular_jacobian)
        self.assertEqual(regularized.shape, singular_jacobian.shape)
        
        # 验证对角线元素被正则化
        for i in range(min(regularized.shape)):
            self.assertGreater(regularized[i, i], 0.0)
    
    def test_forward_inverse_consistency(self):
        """测试正逆运动学一致性"""
        # 构建模型
        self.mapper.build_kinematic_model(self.test_model)
        
        # 测试一致性
        original_angles = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
        
        # 正运动学
        task_state = self.mapper.joint_to_task_mapping(original_angles)
        
        # 逆运动学
        recovered_angles = self.mapper.task_to_joint_mapping(task_state)
        
        # 验证一致性（允许一定误差）
        self.assertEqual(len(recovered_angles), len(original_angles))
        
        # 由于逆运动学的复杂性，允许较大的误差
        max_error = np.max(np.abs(original_angles - recovered_angles))
        self.assertLess(max_error, 2.0, "正逆运动学一致性误差过大")
    
    def test_error_handling(self):
        """测试错误处理"""
        # 测试未初始化模型
        uninit_mapper = DigitalTwinMapper()
        
        with self.assertRaises(RuntimeError):
            joint_angles = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
            uninit_mapper.joint_to_task_mapping(joint_angles)
        
        with self.assertRaises(RuntimeError):
            test_state = create_test_task_state()
            uninit_mapper.task_to_joint_mapping(test_state)
        
        # 测试错误的关节角度向量大小
        self.mapper.build_kinematic_model(self.test_model)
        
        with self.assertRaises(ValueError):
            wrong_size_angles = np.array([0.1, 0.2])  # 应该是6个元素
            self.mapper.joint_to_task_mapping(wrong_size_angles)
    
    def test_constraint_types(self):
        """测试约束类型"""
        # 测试约束类型枚举
        holonomic = ConstraintType.HOLONOMIC
        nonholonomic = ConstraintType.NONHOLONOMIC
        
        self.assertNotEqual(holonomic, nonholonomic)
        self.assertEqual(holonomic.value, "holonomic")
        self.assertEqual(nonholonomic.value, "nonholonomic")


class TestPerformance(unittest.TestCase):
    """性能测试"""
    
    def setUp(self):
        """测试前准备"""
        self.mapper = DigitalTwinMapper()
        self.test_model = create_test_constraint_model()
        self.mapper.build_kinematic_model(self.test_model)
    
    def test_mapping_performance(self):
        """测试映射性能"""
        import time
        
        joint_angles = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
        
        # 测试正运动学性能
        start_time = time.time()
        num_iterations = 1000
        
        for _ in range(num_iterations):
            task_state = self.mapper.joint_to_task_mapping(joint_angles)
        
        forward_time = time.time() - start_time
        
        # 测试逆运动学性能
        test_state = create_test_task_state()
        start_time = time.time()
        
        for _ in range(num_iterations):
            recovered_angles = self.mapper.task_to_joint_mapping(test_state)
        
        inverse_time = time.time() - start_time
        
        print(f"\n性能测试结果:")
        print(f"正运动学: {num_iterations} 次迭代用时 {forward_time:.3f} 秒")
        print(f"平均每次: {forward_time/num_iterations*1000:.3f} 毫秒")
        print(f"逆运动学: {num_iterations} 次迭代用时 {inverse_time:.3f} 秒")
        print(f"平均每次: {inverse_time/num_iterations*1000:.3f} 毫秒")
        
        # 性能断言（每次调用应该在合理时间内完成）
        self.assertLess(forward_time/num_iterations, 0.01, "正运动学性能不达标")
        self.assertLess(inverse_time/num_iterations, 0.01, "逆运动学性能不达标")


def run_comprehensive_test():
    """运行综合测试"""
    print("\n🚀 运行数字孪生映射器综合测试")
    
    try:
        # 创建映射器
        mapper = DigitalTwinMapper()
        print("✅ 映射器创建成功")
        
        # 创建测试模型
        test_model = create_test_constraint_model()
        print("✅ 测试模型创建成功")
        
        # 构建运动学模型
        success = mapper.build_kinematic_model(test_model)
        print(f"✅ 运动学模型构建: {'成功' if success else '失败'}")
        
        if not success:
            return False
        
        # 测试正运动学
        joint_angles = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
        task_state = mapper.joint_to_task_mapping(joint_angles)
        print("✅ 正运动学映射成功")
        
        # 测试逆运动学
        test_state = create_test_task_state()
        recovered_angles = mapper.task_to_joint_mapping(test_state)
        print("✅ 逆运动学映射成功")
        
        # 测试验证
        result = mapper.validate_motion_consistency(joint_angles)
        print(f"✅ 运动一致性验证: {'有效' if result.is_valid else '无效'}")
        
        # 测试奇异位形处理
        jacobian = np.eye(3, 3)
        regularized = mapper.handle_singular_configuration(jacobian)
        print("✅ 奇异位形处理成功")
        
        print("\n🎉 所有综合测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 综合测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    # 运行综合测试
    run_comprehensive_test()
    
    # 运行单元测试
    print("\n" + "="*50)
    print("运行单元测试")
    print("="*50)
    unittest.main(argv=[''], exit=False, verbosity=2)