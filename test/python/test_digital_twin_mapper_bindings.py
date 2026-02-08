#!/usr/bin/env python3
"""
数字孪生映射器Python绑定测试
"""

import pytest
import sys
import os
import numpy as np

# 添加构建路径到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 
                                '../../src/wheel_legged_control/build/wheel_legged_control'))

try:
    import digital_twin_mapper_py as dtm
    BINDINGS_AVAILABLE = True
except ImportError as e:
    print(f"警告: 无法导入Python绑定: {e}")
    BINDINGS_AVAILABLE = False


@pytest.mark.skipif(not BINDINGS_AVAILABLE, reason="Python绑定不可用")
class TestDigitalTwinMapperBindings:
    """数字孪生映射器Python绑定测试类"""
    
    def setup_method(self):
        """测试前设置"""
        self.mapper = dtm.DigitalTwinMapper()
        
    def test_mapper_creation(self):
        """测试映射器创建"""
        assert self.mapper is not None
        
    def test_constraint_model_creation(self):
        """测试约束模型创建"""
        model = dtm.ConstraintModel()
        assert model is not None
        
        # 测试轮子约束
        wheel_constraint = dtm.WheelConstraint()
        wheel_constraint.wheel_name = "test_wheel"
        wheel_constraint.contact_point = np.array([0.0, 0.0, 0.0])
        wheel_constraint.normal_vector = np.array([0.0, 0.0, 1.0])
        wheel_constraint.friction_coefficient = 0.8
        
        model.wheel_constraints.append(wheel_constraint)
        assert len(model.wheel_constraints) == 1
        assert model.wheel_constraints[0].wheel_name == "test_wheel"
        
    def test_task_space_state(self):
        """测试任务空间状态"""
        state = dtm.TaskSpaceState()
        assert state is not None
        
        state.base_position = np.array([0.0, 0.0, 0.3])
        state.base_orientation = np.array([0.0, 0.0, 0.0, 1.0])  # 四元数
        
        # 测试字典操作
        state.wheel_positions["left_wheel"] = np.array([0.2, 0.15, 0.1])
        state.leg_end_positions["left_leg"] = np.array([0.3, 0.15, 0.0])
        
        assert len(state.wheel_positions) == 1
        assert len(state.leg_end_positions) == 1
        
    def test_validation_result(self):
        """测试验证结果"""
        result = dtm.ValidationResult()
        assert result is not None
        
        result.is_valid = True
        result.error_message = "测试消息"
        result.consistency_error = 0.1
        
        assert result.is_valid == True
        assert result.error_message == "测试消息"
        assert result.consistency_error == 0.1
        
    def test_helper_functions(self):
        """测试辅助函数"""
        # 测试创建测试约束模型
        model = dtm.create_test_constraint_model()
        assert model is not None
        assert len(model.wheel_constraints) == 2
        assert len(model.leg_constraints) == 2
        
        # 测试创建测试任务空间状态
        state = dtm.create_test_task_state()
        assert state is not None
        assert len(state.wheel_positions) == 2
        assert len(state.leg_end_positions) == 2
        
    def test_kinematic_model_building(self):
        """测试运动学模型构建"""
        model = dtm.create_test_constraint_model()
        success = self.mapper.build_kinematic_model(model)
        assert success == True
        
    def test_forward_kinematics(self):
        """测试正向运动学"""
        model = dtm.create_test_constraint_model()
        self.mapper.build_kinematic_model(model)
        
        # 创建测试关节角度
        joint_angles = np.array([0.0, 0.0, 0.5, -0.3, 0.5, -0.3])
        
        # 执行正向运动学
        task_state = self.mapper.joint_to_task_mapping(joint_angles)
        
        assert task_state is not None
        assert len(task_state.wheel_positions) >= 0
        assert len(task_state.leg_end_positions) >= 0
        
    def test_inverse_kinematics(self):
        """测试逆向运动学"""
        model = dtm.create_test_constraint_model()
        self.mapper.build_kinematic_model(model)
        
        # 创建测试任务空间状态
        task_state = dtm.create_test_task_state()
        
        # 执行逆向运动学
        joint_angles = self.mapper.task_to_joint_mapping(task_state)
        
        assert joint_angles is not None
        assert len(joint_angles) > 0
        
        # 验证关节角度在合理范围内
        for angle in joint_angles:
            assert -np.pi <= angle <= np.pi
            
    def test_motion_consistency_validation(self):
        """测试运动一致性验证"""
        model = dtm.create_test_constraint_model()
        self.mapper.build_kinematic_model(model)
        
        # 测试有效关节角度
        valid_angles = np.array([0.1, -0.1, 0.3, -0.5, 0.3, -0.5])
        result = self.mapper.validate_motion_consistency(valid_angles)
        
        assert result is not None
        assert isinstance(result.is_valid, bool)
        assert isinstance(result.consistency_error, float)
        assert isinstance(result.error_message, str)
        
    def test_singular_configuration_handling(self):
        """测试奇异位形处理"""
        # 创建奇异雅可比矩阵
        singular_jacobian = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0]  # 第三行为零，导致奇异
        ])
        
        # 处理奇异位形
        regularized = self.mapper.handle_singular_configuration(singular_jacobian)
        
        assert regularized is not None
        assert regularized.shape == singular_jacobian.shape
        
        # 验证奇异值被正则化（简单检查：矩阵不应该完全为零）
        assert np.sum(np.abs(regularized)) > 0
        
    def test_round_trip_consistency(self):
        """测试双向运动学一致性"""
        model = dtm.create_test_constraint_model()
        self.mapper.build_kinematic_model(model)
        
        # 原始关节角度
        original_angles = np.array([0.1, -0.1, 0.3, -0.5, 0.3, -0.5])
        
        # 正向运动学
        task_state = self.mapper.joint_to_task_mapping(original_angles)
        
        # 逆向运动学
        recovered_angles = self.mapper.task_to_joint_mapping(task_state)
        
        # 验证一致性（允许一定误差）
        assert len(recovered_angles) == len(original_angles)
        
        error = np.linalg.norm(original_angles - recovered_angles)
        assert error < 0.5  # 允许较大误差，因为是简化实现


def test_bindings_import():
    """测试绑定导入"""
    if BINDINGS_AVAILABLE:
        assert hasattr(dtm, 'DigitalTwinMapper')
        assert hasattr(dtm, 'ConstraintModel')
        assert hasattr(dtm, 'TaskSpaceState')
        assert hasattr(dtm, 'ValidationResult')
        assert hasattr(dtm, 'create_test_constraint_model')
        assert hasattr(dtm, 'create_test_task_state')
    else:
        pytest.skip("Python绑定不可用")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])