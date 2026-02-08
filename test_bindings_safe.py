#!/usr/bin/env python3
"""
安全的Python绑定测试
"""

import sys
import os
import numpy as np

# 添加构建路径到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 
                                'install/wheel_legged_control/lib/python3.12/site-packages'))

try:
    from wheel_legged_control import digital_twin_mapper_py as dtm
    print("✅ 成功导入Python绑定")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

def test_basic_creation():
    """测试基本对象创建"""
    print("\n=== 测试基本对象创建 ===")
    
    # 测试映射器创建
    mapper = dtm.DigitalTwinMapper()
    print("✅ DigitalTwinMapper创建成功")
    
    # 测试约束模型创建
    model = dtm.ConstraintModel()
    print("✅ ConstraintModel创建成功")
    
    # 测试任务空间状态创建
    state = dtm.TaskSpaceState()
    print("✅ TaskSpaceState创建成功")
    
    # 测试验证结果创建
    result = dtm.ValidationResult()
    print("✅ ValidationResult创建成功")
    
    return mapper, model, state, result

def test_wheel_constraint():
    """测试轮子约束"""
    print("\n=== 测试轮子约束 ===")
    
    wheel_constraint = dtm.WheelConstraint()
    wheel_constraint.wheel_name = "test_wheel"
    wheel_constraint.friction_coefficient = 0.8
    
    # 使用安全的设置方法
    wheel_constraint.set_contact_point(0.0, 0.0, 0.0)
    wheel_constraint.set_normal_vector(0.0, 0.0, 1.0)
    
    # 测试获取方法
    contact = wheel_constraint.get_contact_point()
    normal = wheel_constraint.get_normal_vector()
    
    print(f"✅ 轮子约束创建成功: {wheel_constraint.wheel_name}")
    print(f"   接触点: {contact}")
    print(f"   法向量: {normal}")
    print(f"   摩擦系数: {wheel_constraint.friction_coefficient}")
    
    return wheel_constraint

def test_helper_functions():
    """测试辅助函数"""
    print("\n=== 测试辅助函数 ===")
    
    # 测试创建测试约束模型
    model = dtm.create_test_constraint_model()
    print(f"✅ 测试约束模型创建成功")
    print(f"   轮子约束数量: {len(model.wheel_constraints)}")
    print(f"   腿部约束数量: {len(model.leg_constraints)}")
    
    # 测试创建测试任务空间状态
    state = dtm.create_test_task_state()
    print(f"✅ 测试任务空间状态创建成功")
    print(f"   轮子位置数量: {len(state.wheel_positions)}")
    print(f"   腿部末端位置数量: {len(state.leg_end_positions)}")
    
    return model, state

def test_kinematic_operations(mapper, model):
    """测试运动学操作"""
    print("\n=== 测试运动学操作 ===")
    
    # 构建运动学模型
    success = mapper.build_kinematic_model(model)
    print(f"✅ 运动学模型构建: {'成功' if success else '失败'}")
    
    if not success:
        return
    
    # 测试正向运动学
    joint_angles = np.array([0.0, 0.0, 0.5, -0.3, 0.5, -0.3])
    print(f"   输入关节角度: {joint_angles}")
    
    try:
        task_state = mapper.joint_to_task_mapping(joint_angles)
        print("✅ 正向运动学计算成功")
        print(f"   轮子位置数量: {len(task_state.wheel_positions)}")
        print(f"   腿部末端位置数量: {len(task_state.leg_end_positions)}")
    except Exception as e:
        print(f"❌ 正向运动学失败: {e}")
        return
    
    # 测试逆向运动学
    try:
        test_state = dtm.create_test_task_state()
        recovered_angles = mapper.task_to_joint_mapping(test_state)
        print("✅ 逆向运动学计算成功")
        print(f"   输出关节角度: {recovered_angles}")
    except Exception as e:
        print(f"❌ 逆向运动学失败: {e}")

def test_validation(mapper):
    """测试验证功能"""
    print("\n=== 测试验证功能 ===")
    
    # 测试运动一致性验证
    test_angles = np.array([0.1, -0.1, 0.3, -0.5, 0.3, -0.5])
    
    try:
        result = mapper.validate_motion_consistency(test_angles)
        print("✅ 运动一致性验证成功")
        print(f"   验证结果: {'有效' if result.is_valid else '无效'}")
        print(f"   一致性误差: {result.consistency_error}")
        print(f"   错误信息: {result.error_message}")
    except Exception as e:
        print(f"❌ 运动一致性验证失败: {e}")
    
    # 测试奇异位形处理
    try:
        singular_jacobian = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0]  # 奇异行
        ])
        
        regularized = mapper.handle_singular_configuration(singular_jacobian)
        print("✅ 奇异位形处理成功")
        print(f"   原始矩阵形状: {singular_jacobian.shape}")
        print(f"   正则化矩阵形状: {regularized.shape}")
    except Exception as e:
        print(f"❌ 奇异位形处理失败: {e}")

def main():
    """主测试函数"""
    print("🚀 开始Python绑定安全测试")
    
    # 基本创建测试
    mapper, model, state, result = test_basic_creation()
    
    # 轮子约束测试
    wheel_constraint = test_wheel_constraint()
    
    # 辅助函数测试
    test_model, test_state = test_helper_functions()
    
    # 运动学操作测试
    test_kinematic_operations(mapper, test_model)
    
    # 验证功能测试
    test_validation(mapper)
    
    print("\n🎉 所有测试完成！")

if __name__ == "__main__":
    main()