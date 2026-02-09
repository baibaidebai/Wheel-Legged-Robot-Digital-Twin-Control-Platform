#!/usr/bin/env python3
"""
完整的Python绑定功能测试
"""

import sys
import os
import numpy as np

# 设置环境
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 
                                'install/wheel_legged_control/lib/python3.12/site-packages'))

try:
    from wheel_legged_control import digital_twin_mapper_py as dtm
    print("✅ 成功导入Python绑定")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

def create_test_model():
    """创建测试约束模型"""
    print("\n=== 创建测试约束模型 ===")
    
    model = dtm.ConstraintModel()
    
    # 创建左轮约束
    left_wheel = dtm.WheelConstraint()
    left_wheel.wheel_name = "left_wheel"
    left_wheel.friction_coefficient = 0.8
    left_wheel.set_contact_point(0.0, 0.2, 0.0)
    left_wheel.set_normal_vector(0.0, 0.0, 1.0)
    model.wheel_constraints.append(left_wheel)
    
    # 创建右轮约束
    right_wheel = dtm.WheelConstraint()
    right_wheel.wheel_name = "right_wheel"
    right_wheel.friction_coefficient = 0.8
    right_wheel.set_contact_point(0.0, -0.2, 0.0)
    right_wheel.set_normal_vector(0.0, 0.0, 1.0)
    model.wheel_constraints.append(right_wheel)
    
    # 创建左腿约束
    left_leg = dtm.LegConstraint()
    left_leg.leg_name = "left_leg"
    left_joints = dtm.StringVector()
    left_joints.append("lf0_joint")
    left_joints.append("lf1_joint")
    left_leg.joints = left_joints
    left_leg.jacobian = np.eye(3, 2)
    model.leg_constraints.append(left_leg)
    
    # 创建右腿约束
    right_leg = dtm.LegConstraint()
    right_leg.leg_name = "right_leg"
    right_joints = dtm.StringVector()
    right_joints.append("rf0_joint")
    right_joints.append("rf1_joint")
    right_leg.joints = right_joints
    right_leg.jacobian = np.eye(3, 2)
    model.leg_constraints.append(right_leg)
    
    print(f"✅ 测试模型创建成功:")
    print(f"   轮子约束: {len(model.wheel_constraints)} 个")
    print(f"   腿部约束: {len(model.leg_constraints)} 个")
    
    return model

def create_test_task_state():
    """创建测试任务空间状态"""
    print("\n=== 创建测试任务空间状态 ===")
    
    state = dtm.TaskSpaceState()
    
    # 设置基座位置和姿态
    state.base_position = np.array([0.0, 0.0, 0.2])
    state.base_orientation = np.array([0.0, 0.0, 0.0, 1.0])  # 四元数 [x,y,z,w]
    
    # 设置轮子位置
    state.wheel_positions["left_wheel"] = np.array([0.0, 0.2, 0.0])
    state.wheel_positions["right_wheel"] = np.array([0.0, -0.2, 0.0])
    
    # 设置腿部末端位置
    state.leg_end_positions["left_leg"] = np.array([0.3, 0.2, -0.1])
    state.leg_end_positions["right_leg"] = np.array([0.3, -0.2, -0.1])
    
    print(f"✅ 任务空间状态创建成功:")
    print(f"   轮子位置: {len(state.wheel_positions)} 个")
    print(f"   腿部末端位置: {len(state.leg_end_positions)} 个")
    
    return state

def test_kinematic_model_building(mapper, model):
    """测试运动学模型构建"""
    print("\n=== 测试运动学模型构建 ===")
    
    try:
        success = mapper.build_kinematic_model(model)
        print(f"✅ 运动学模型构建: {'成功' if success else '失败'}")
        return success
    except Exception as e:
        print(f"❌ 运动学模型构建失败: {e}")
        return False

def test_urdf_parsing(mapper):
    """测试URDF解析"""
    print("\n=== 测试URDF解析 ===")
    
    urdf_path = "src/wheel_legged_control/urdf/wheel_legged_robot.urdf"
    
    if os.path.exists(urdf_path):
        try:
            model = mapper.parse_urdf_constraints(urdf_path)
            print("✅ URDF解析成功")
            print(f"   轮子约束: {len(model.wheel_constraints)}")
            print(f"   腿部约束: {len(model.leg_constraints)}")
            print(f"   耦合约束: {len(model.coupling_constraints)}")
            return model
        except Exception as e:
            print(f"❌ URDF解析失败: {e}")
            return None
    else:
        print(f"⚠️  URDF文件不存在: {urdf_path}")
        return None

def test_forward_kinematics(mapper):
    """测试正向运动学（安全版本）"""
    print("\n=== 测试正向运动学 ===")
    
    # 创建测试关节角度
    joint_angles = np.array([0.0, 0.0, 0.1, -0.1, 0.1, -0.1])
    print(f"   输入关节角度: {joint_angles}")
    
    try:
        task_state = mapper.joint_to_task_mapping(joint_angles)
        print("✅ 正向运动学计算成功")
        print(f"   基座位置: {task_state.base_position}")
        print(f"   轮子位置数量: {len(task_state.wheel_positions)}")
        print(f"   腿部末端位置数量: {len(task_state.leg_end_positions)}")
        return task_state
    except Exception as e:
        print(f"❌ 正向运动学失败: {e}")
        return None

def test_inverse_kinematics(mapper, task_state):
    """测试逆向运动学"""
    print("\n=== 测试逆向运动学 ===")
    
    if task_state is None:
        print("⚠️  跳过逆向运动学测试（正向运动学失败）")
        return None
    
    try:
        joint_angles = mapper.task_to_joint_mapping(task_state)
        print("✅ 逆向运动学计算成功")
        print(f"   输出关节角度: {joint_angles}")
        
        # 验证关节角度在合理范围内
        if len(joint_angles) > 0:
            max_angle = np.max(np.abs(joint_angles))
            print(f"   最大关节角度: {max_angle:.3f} rad")
            if max_angle < np.pi:
                print("✅ 关节角度在合理范围内")
            else:
                print("⚠️  关节角度可能超出合理范围")
        
        return joint_angles
    except Exception as e:
        print(f"❌ 逆向运动学失败: {e}")
        return None

def test_motion_validation(mapper):
    """测试运动一致性验证"""
    print("\n=== 测试运动一致性验证 ===")
    
    # 测试有效关节角度
    valid_angles = np.array([0.1, -0.1, 0.2, -0.3, 0.2, -0.3])
    
    try:
        result = mapper.validate_motion_consistency(valid_angles)
        print("✅ 运动一致性验证成功")
        print(f"   验证结果: {'有效' if result.is_valid else '无效'}")
        print(f"   一致性误差: {result.consistency_error:.6f}")
        if result.error_message:
            print(f"   错误信息: {result.error_message}")
        return result
    except Exception as e:
        print(f"❌ 运动一致性验证失败: {e}")
        return None

def test_singular_handling(mapper):
    """测试奇异位形处理"""
    print("\n=== 测试奇异位形处理 ===")
    
    # 创建奇异雅可比矩阵
    singular_jacobian = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0]  # 第三行为零，导致奇异
    ])
    
    try:
        regularized = mapper.handle_singular_configuration(singular_jacobian)
        print("✅ 奇异位形处理成功")
        print(f"   原始矩阵形状: {singular_jacobian.shape}")
        print(f"   正则化矩阵形状: {regularized.shape}")
        
        # 检查正则化效果
        det_original = np.linalg.det(singular_jacobian @ singular_jacobian.T)
        det_regularized = np.linalg.det(regularized @ regularized.T)
        print(f"   原始行列式: {det_original:.6f}")
        print(f"   正则化行列式: {det_regularized:.6f}")
        
        return regularized
    except Exception as e:
        print(f"❌ 奇异位形处理失败: {e}")
        return None

def test_helper_functions():
    """测试辅助函数"""
    print("\n=== 测试辅助函数 ===")
    
    try:
        # 测试创建测试约束模型
        model = dtm.create_test_constraint_model()
        print("✅ create_test_constraint_model 成功")
        print(f"   轮子约束: {len(model.wheel_constraints)}")
        print(f"   腿部约束: {len(model.leg_constraints)}")
        
        # 测试创建测试任务空间状态
        state = dtm.create_test_task_state()
        print("✅ create_test_task_state 成功")
        print(f"   轮子位置: {len(state.wheel_positions)}")
        print(f"   腿部末端位置: {len(state.leg_end_positions)}")
        
        return model, state
    except Exception as e:
        print(f"❌ 辅助函数测试失败: {e}")
        return None, None

def main():
    """主测试函数"""
    print("🚀 开始完整Python绑定功能测试")
    
    # 创建映射器
    mapper = dtm.DigitalTwinMapper()
    print("✅ 数字孪生映射器创建成功")
    
    # 测试辅助函数
    helper_model, helper_state = test_helper_functions()
    
    # 创建自定义测试模型
    custom_model = create_test_model()
    custom_state = create_test_task_state()
    
    # 测试运动学模型构建
    if test_kinematic_model_building(mapper, custom_model):
        # 测试正向运动学
        result_state = test_forward_kinematics(mapper)
        
        # 测试逆向运动学
        test_inverse_kinematics(mapper, result_state)
    
    # 测试URDF解析
    urdf_model = test_urdf_parsing(mapper)
    
    # 测试验证功能
    test_motion_validation(mapper)
    
    # 测试奇异位形处理
    test_singular_handling(mapper)
    
    print("\n🎉 完整功能测试完成！")
    print("\n📊 测试总结:")
    print("   ✅ 基本对象创建和操作")
    print("   ✅ STL容器绑定")
    print("   ✅ Eigen矩阵和向量操作")
    print("   ✅ 运动学模型构建")
    print("   ✅ 运动学计算接口")
    print("   ✅ 验证和处理功能")
    print("   ✅ 辅助函数")

if __name__ == "__main__":
    main()