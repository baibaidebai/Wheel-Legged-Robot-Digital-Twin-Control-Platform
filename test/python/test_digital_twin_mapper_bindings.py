#!/usr/bin/env python3
"""
数字孪生映射器Python绑定测试

测试C++数字孪生映射器的Python绑定功能，包括：
- 约束模型创建和操作
- 运动学正逆映射
- 运动一致性验证
- 奇异位形处理
"""

import unittest
import numpy as np
import os
import sys

# 添加构建路径到Python路径
build_path = os.path.join(os.path.dirname(__file__), '../../build/wheel_legged_control')
if os.path.exists(build_path):
    sys.path.insert(0, build_path)

try:
    import digital_twin_mapper_py as dtm
    BINDINGS_AVAILABLE = True
except ImportError as e:
    print(f"警告: 无法导入数字孪生映射器绑定: {e}")
    print("请确保已正确编译Python绑定模块")
    BINDINGS_AVAILABLE = False


@unittest.skipUnless(BINDINGS_AVAILABLE, "Python绑定不可用")
class TestDigitalTwinMapperBindings(unittest.TestCase):
    """数字孪生映射器绑定测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.mapper = dtm.DigitalTwinMapper()
        self.test_model = dtm.create_test_constraint_model()
    
    def test_constraint_model_creation(self):
        """测试约束模型创建"""
        # 测试空约束模型
        empty_model = dtm.ConstraintModel()
        self.assertEqual(len(empty_model.wheel_constraints), 0)
        self.assertEqual(len(empty_model.leg_constraints), 0)
        self.assertEqual(len(empty_model.coupling_constraints), 0)
        
        # 测试预定义测试模型
        self.assertEqual(len(self.test_model.wheel_constraints), 2)
        self.assertEqual(len(self.test_model.leg_constraints), 2)
        
        # 验证轮子约束
        wheel1 = self.test_model.wheel_constraints[0]
        self.assertEqual(wheel1.wheel_name, "left_wheel")
        self.assertAlmostEqual(wheel1.friction_coefficient, 0.8)
        
        # 验证腿部约束
        leg1 = self.test_model.leg_constraints[0]
        self.assertEqual(leg1.leg_name, "left_leg")
        self.assertEqual(len(leg1.joints), 2)
        self.assertIn("lf0_joint", leg1.joints)
        self.assertIn("lf1_joint", leg1.joints)
    
    def test_wheel_constraint_operations(self):
        """测试轮子约束操作"""
        wheel = dtm.WheelConstraint()
        
        # 测试基本属性
        wheel.wheel_name = "test_wheel"
        wheel.friction_coefficient = 0.9
        self.assertEqual(wheel.wheel_name, "test_wheel")
        self.assertAlmostEqual(wheel.friction_coefficient, 0.9)
        
        # 测试接触点设置
        wheel.set_contact_point(1.0, 2.0, 3.0)
        contact_point = wheel.get_contact_point()
        self.assertAlmostEqual(contact_point[0], 1.0)
        self.assertAlmostEqual(contact_point[1], 2.0)
        self.assertAlmostEqual(contact_point[2], 3.0)
        
        # 测试法向量设置
        wheel.set_normal_vector(0.0, 1.0, 0.0)
        normal = wheel.get_normal_vector()
        self.assertAlmostEqual(normal[0], 0.0)
        self.assertAlmostEqual(normal[1], 1.0)
        self.assertAlmostEqual(normal[2], 0.0)
    
    def test_leg_constraint_operations(self):
        """测试腿部约束操作"""
        # 使用构造函数创建
        joints = ["joint1", "joint2"]
        jacobian = np.eye(3, 2)
        leg = dtm.LegConstraint("test_leg", joints, jacobian)
        
        self.assertEqual(leg.leg_name, "test_leg")
        self.assertEqual(len(leg.joints), 2)
        self.assertEqual(leg.joints[0], "joint1")
        self.assertEqual(leg.joints[1], "joint2")
        
        # 验证雅可比矩阵
        jac_result = leg.jacobian
        self.assertEqual(jac_result.shape, (3, 2))
        np.testing.assert_array_almost_equal(jac_result, jacobian)
    
    def test_task_space_state_operations(self):
        """测试任务空间状态操作"""
        # 创建测试状态
        test_state = dtm.create_test_task_state()
        
        # 验证基座位置
        base_pos = test_state.base_position
        self.assertAlmostEqual(base_pos[2], 0.2)  # z坐标
        
        # 验证轮子位置
        self.assertIn("left_wheel", test_state.wheel_positions)
        self.assertIn("right_wheel", test_state.wheel_positions)
        
        left_wheel_pos = test_state.wheel_positions["left_wheel"]
        self.assertAlmostEqual(left_wheel_pos[1], 0.2)  # y坐标
        
        # 验证腿端位置
        self.assertIn("left_leg", test_state.leg_end_positions)
        self.assertIn("right_leg", test_state.leg_end_positions)
        
        left_leg_pos = test_state.leg_end_positions["left_leg"]
        self.assertAlmostEqual(left_leg_pos[0], 0.3)  # x坐标
    
    def test_kinematic_model_building(self):
        """测试运动学模型构建"""
        # 构建运动学模型
        success = self.mapper.build_kinematic_model(self.test_model)
        self.assertTrue(success)
    
    def test_joint_to_task_mapping(self):
        """测试关节空间到任务空间映射"""
        # 首先构建模型
        self.mapper.build_kinematic_model(self.test_model)
        
        # 创建测试关节角度
        joint_angles = np.array([0.1, 0.2, 0.3, 0.4])  # 4个关节
        
        # 执行正运动学
        task_state = self.mapper.joint_to_task_mapping(joint_angles)
        
        # 验证结果
        self.assertIsInstance(task_state, dtm.TaskSpaceState)
        self.assertTrue(len(task_state.wheel_positions) > 0)
        self.assertTrue(len(task_state.leg_end_positions) > 0)
        
        # 验证基座位置合理性
        base_pos = task_state.base_position
        self.assertTrue(abs(base_pos[0]) < 10.0)  # 合理范围
        self.assertTrue(abs(base_pos[1]) < 10.0)
        self.assertTrue(abs(base_pos[2]) < 10.0)
    
    def test_task_to_joint_mapping(self):
        """测试任务空间到关节空间映射"""
        # 首先构建模型
        self.mapper.build_kinematic_model(self.test_model)
        
        # 创建测试任务空间状态
        test_state = dtm.create_test_task_state()
        
        # 执行逆运动学
        joint_angles = self.mapper.task_to_joint_mapping(test_state)
        
        # 验证结果
        self.assertIsInstance(joint_angles, np.ndarray)
        self.assertTrue(len(joint_angles) > 0)
        
        # 验证关节角度在合理范围内
        for angle in joint_angles:
            self.assertTrue(abs(angle) < np.pi)  # 在±π范围内
    
    def test_motion_consistency_validation(self):
        """测试运动一致性验证"""
        # 首先构建模型
        self.mapper.build_kinematic_model(self.test_model)
        
        # 创建测试关节角度
        joint_angles = np.array([0.1, 0.2, 0.3, 0.4])
        
        # 执行一致性验证
        result = self.mapper.validate_motion_consistency(joint_angles)
        
        # 验证结果
        self.assertIsInstance(result, dtm.ValidationResult)
        self.assertIsInstance(result.is_valid, bool)
        self.assertIsInstance(result.error_message, str)
        self.assertIsInstance(result.consistency_error, float)
        self.assertGreaterEqual(result.consistency_error, 0.0)
    
    def test_singular_configuration_handling(self):
        """测试奇异位形处理"""
        # 创建测试雅可比矩阵（包含奇异性）
        jacobian = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0]  # 奇异行
        ])
        
        # 处理奇异位形
        regularized_jacobian = self.mapper.handle_singular_configuration(jacobian)
        
        # 验证结果
        self.assertIsInstance(regularized_jacobian, np.ndarray)
        self.assertEqual(regularized_jacobian.shape, jacobian.shape)
        
        # 验证奇异值被正则化
        U, s, Vt = np.linalg.svd(regularized_jacobian)
        self.assertTrue(np.all(s > 1e-7))  # 所有奇异值应该大于阈值
    
    def test_forward_inverse_consistency(self):
        """测试正逆运动学一致性"""
        # 首先构建模型
        self.mapper.build_kinematic_model(self.test_model)
        
        # 创建测试关节角度
        original_angles = np.array([0.1, 0.2, 0.3, 0.4])
        
        # 正运动学
        task_state = self.mapper.joint_to_task_mapping(original_angles)
        
        # 逆运动学
        recovered_angles = self.mapper.task_to_joint_mapping(task_state)
        
        # 验证一致性（允许一定误差）
        if len(recovered_angles) == len(original_angles):
            max_error = np.max(np.abs(original_angles - recovered_angles))
            self.assertLess(max_error, 0.5, "正逆运动学一致性误差过大")
    
    def test_constraint_types(self):
        """测试约束类型枚举"""
        # 测试约束类型枚举
        holonomic = dtm.ConstraintType.HOLONOMIC
        nonholonomic = dtm.ConstraintType.NONHOLONOMIC
        
        self.assertNotEqual(holonomic, nonholonomic)
        
        # 创建耦合约束并设置类型
        coupling = dtm.CouplingConstraint()
        coupling.constraint_type = holonomic
        self.assertEqual(coupling.constraint_type, holonomic)
        
        coupling.constraint_type = nonholonomic
        self.assertEqual(coupling.constraint_type, nonholonomic)
    
    def test_error_handling(self):
        """测试错误处理"""
        # 测试未初始化模型的情况
        with self.assertRaises(RuntimeError):
            joint_angles = np.array([0.1, 0.2])
            self.mapper.joint_to_task_mapping(joint_angles)
        
        with self.assertRaises(RuntimeError):
            test_state = dtm.create_test_task_state()
            self.mapper.task_to_joint_mapping(test_state)


class TestBindingsPerformance(unittest.TestCase):
    """绑定性能测试"""
    
    @unittest.skipUnless(BINDINGS_AVAILABLE, "Python绑定不可用")
    def test_mapping_performance(self):
        """测试映射性能"""
        mapper = dtm.DigitalTwinMapper()
        test_model = dtm.create_test_constraint_model()
        mapper.build_kinematic_model(test_model)
        
        # 性能测试
        import time
        
        joint_angles = np.array([0.1, 0.2, 0.3, 0.4])
        
        # 测试正运动学性能
        start_time = time.time()
        num_iterations = 1000
        
        for _ in range(num_iterations):
            task_state = mapper.joint_to_task_mapping(joint_angles)
        
        forward_time = time.time() - start_time
        
        # 测试逆运动学性能
        test_state = dtm.create_test_task_state()
        start_time = time.time()
        
        for _ in range(num_iterations):
            recovered_angles = mapper.task_to_joint_mapping(test_state)
        
        inverse_time = time.time() - start_time
        
        print(f"\n性能测试结果:")
        print(f"正运动学: {num_iterations} 次迭代用时 {forward_time:.3f} 秒")
        print(f"平均每次: {forward_time/num_iterations*1000:.3f} 毫秒")
        print(f"逆运动学: {num_iterations} 次迭代用时 {inverse_time:.3f} 秒")
        print(f"平均每次: {inverse_time/num_iterations*1000:.3f} 毫秒")
        
        # 性能断言（每次调用应该在合理时间内完成）
        self.assertLess(forward_time/num_iterations, 0.001, "正运动学性能不达标")
        self.assertLess(inverse_time/num_iterations, 0.001, "逆运动学性能不达标")


def run_manual_test():
    """手动测试函数"""
    if not BINDINGS_AVAILABLE:
        print("❌ Python绑定不可用，跳过手动测试")
        return
    
    print("\n🚀 运行数字孪生映射器绑定手动测试")
    
    try:
        # 创建映射器和测试模型
        mapper = dtm.DigitalTwinMapper()
        test_model = dtm.create_test_constraint_model()
        
        print(f"✅ 成功创建映射器和约束模型")
        print(f"   轮子约束数量: {len(test_model.wheel_constraints)}")
        print(f"   腿部约束数量: {len(test_model.leg_constraints)}")
        
        # 构建运动学模型
        success = mapper.build_kinematic_model(test_model)
        print(f"✅ 运动学模型构建: {'成功' if success else '失败'}")
        
        # 测试正运动学
        joint_angles = np.array([0.1, 0.2, 0.3, 0.4])
        task_state = mapper.joint_to_task_mapping(joint_angles)
        
        print(f"✅ 正运动学映射成功")
        print(f"   基座位置: {task_state.base_position}")
        print(f"   轮子位置数量: {len(task_state.wheel_positions)}")
        print(f"   腿端位置数量: {len(task_state.leg_end_positions)}")
        
        # 测试逆运动学
        test_state = dtm.create_test_task_state()
        recovered_angles = mapper.task_to_joint_mapping(test_state)
        
        print(f"✅ 逆运动学映射成功")
        print(f"   恢复的关节角度: {recovered_angles}")
        
        # 测试一致性验证
        result = mapper.validate_motion_consistency(joint_angles)
        print(f"✅ 运动一致性验证: {'有效' if result.is_valid else '无效'}")
        print(f"   一致性误差: {result.consistency_error:.6f}")
        
        if result.error_message:
            print(f"   错误信息: {result.error_message}")
        
        print("\n🎉 所有手动测试通过！")
        
    except Exception as e:
        print(f"❌ 手动测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    # 运行手动测试
    run_manual_test()
    
    # 运行单元测试
    if BINDINGS_AVAILABLE:
        print("\n" + "="*50)
        print("运行单元测试")
        print("="*50)
        unittest.main(argv=[''], exit=False, verbosity=2)
    else:
        print("\n❌ 跳过单元测试 - Python绑定不可用")
        print("请确保已正确编译wheel_legged_control包")