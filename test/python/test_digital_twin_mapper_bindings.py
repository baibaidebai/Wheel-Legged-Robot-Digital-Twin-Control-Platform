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
                                '../../install/wheel_legged_control/lib/python3.12/site-packages'))

try:
    from wheel_legged_control import digital_twin_mapper_py as dtm
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
        wheel_constraint.set_contact_point(0.0, 0.0, 0.0)
        wheel_constraint.set_normal_vector(0.0, 0.0, 1.0)
        wheel_constraint.friction_coefficient = 0.8
        
        model.wheel_constraints.append(wheel_constraint)
        assert len(model.wheel_constraints) == 1
        assert model.wheel_constraints[0].wheel_name == "test_wheel"
        
    def test_task_space_state(self):
        """测试任务空间状态"""
        state = dtm.TaskSpaceState()
        assert state is not None
        
        # 使用Eigen向量直接赋值
        import numpy as np
        state.base_position = np.array([0.0, 0.0, 0.3])
        
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
        
    def test_stl_containers(self):
        """测试STL容器操作"""
        # 测试字符串向量
        string_vec = dtm.StringVector()
        string_vec.append("joint1")
        string_vec.append("joint2")
        
        assert len(string_vec) == 2
        assert string_vec[0] == "joint1"
        assert string_vec[1] == "joint2"
        
        # 测试约束向量
        wheel_vec = dtm.WheelConstraintVector()
        leg_vec = dtm.LegConstraintVector()
        
        assert len(wheel_vec) == 0
        assert len(leg_vec) == 0
        
    def test_wheel_constraint_operations(self):
        """测试轮子约束操作"""
        wheel = dtm.WheelConstraint()
        wheel.wheel_name = "test_wheel"
        wheel.friction_coefficient = 0.8
        
        # 测试设置和获取接触点
        wheel.set_contact_point(1.0, 2.0, 3.0)
        contact = wheel.get_contact_point()
        assert contact == (1.0, 2.0, 3.0)
        
        # 测试设置和获取法向量
        wheel.set_normal_vector(0.0, 0.0, 1.0)
        normal = wheel.get_normal_vector()
        assert normal == (0.0, 0.0, 1.0)
        
    def test_leg_constraint_operations(self):
        """测试腿部约束操作"""
        leg = dtm.LegConstraint()
        leg.leg_name = "test_leg"
        
        # 测试关节设置
        joints = dtm.StringVector()
        joints.append("joint1")
        joints.append("joint2")
        leg.joints = joints
        
        assert leg.leg_name == "test_leg"
        assert len(leg.joints) == 2


def test_bindings_import():
    """测试绑定导入"""
    if BINDINGS_AVAILABLE:
        assert hasattr(dtm, 'DigitalTwinMapper')
        assert hasattr(dtm, 'ConstraintModel')
        assert hasattr(dtm, 'TaskSpaceState')
        assert hasattr(dtm, 'ValidationResult')
        assert hasattr(dtm, 'WheelConstraint')
        assert hasattr(dtm, 'LegConstraint')
        assert hasattr(dtm, 'StringVector')
        assert hasattr(dtm, 'create_test_constraint_model')
        assert hasattr(dtm, 'create_test_task_state')
    else:
        pytest.skip("Python绑定不可用")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])