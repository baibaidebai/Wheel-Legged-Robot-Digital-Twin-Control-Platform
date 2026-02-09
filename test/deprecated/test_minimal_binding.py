#!/usr/bin/env python3
"""
最小化Python绑定测试
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

def test_basic_functionality():
    """测试基本功能"""
    print("\n=== 测试基本功能 ===")
    
    # 创建映射器
    mapper = dtm.DigitalTwinMapper()
    print("✅ 映射器创建成功")
    
    # 创建约束模型
    model = dtm.ConstraintModel()
    print("✅ 约束模型创建成功")
    
    # 创建轮子约束
    wheel = dtm.WheelConstraint()
    wheel.wheel_name = "test_wheel"
    wheel.friction_coefficient = 0.8
    wheel.set_contact_point(0.0, 0.0, 0.0)
    wheel.set_normal_vector(0.0, 0.0, 1.0)
    
    model.wheel_constraints.append(wheel)
    print(f"✅ 轮子约束添加成功: {len(model.wheel_constraints)} 个")
    
    # 创建腿部约束
    leg = dtm.LegConstraint()
    leg.leg_name = "test_leg"
    
    # 创建字符串向量
    joints = dtm.StringVector()
    joints.append("joint1")
    joints.append("joint2")
    leg.joints = joints
    
    # 创建简单的雅可比矩阵
    jacobian = np.eye(3, 2)  # 3x2 单位矩阵
    leg.jacobian = jacobian
    
    model.leg_constraints.append(leg)
    print(f"✅ 腿部约束添加成功: {len(model.leg_constraints)} 个")
    
    return mapper, model

def test_urdf_parsing():
    """测试URDF解析"""
    print("\n=== 测试URDF解析 ===")
    
    mapper = dtm.DigitalTwinMapper()
    
    # 测试URDF文件路径
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
        print(f"❌ URDF文件不存在: {urdf_path}")
        return None

def test_validation_only():
    """仅测试验证功能"""
    print("\n=== 测试验证功能 ===")
    
    mapper = dtm.DigitalTwinMapper()
    
    # 测试验证结果创建
    result = dtm.ValidationResult()
    result.is_valid = True
    result.error_message = "测试消息"
    result.consistency_error = 0.1
    
    print("✅ 验证结果创建成功")
    print(f"   有效性: {result.is_valid}")
    print(f"   错误消息: {result.error_message}")
    print(f"   一致性误差: {result.consistency_error}")

def main():
    """主函数"""
    print("🚀 开始最小化Python绑定测试")
    
    # 基本功能测试
    mapper, model = test_basic_functionality()
    
    # URDF解析测试
    urdf_model = test_urdf_parsing()
    
    # 验证功能测试
    test_validation_only()
    
    print("\n🎉 最小化测试完成！")

if __name__ == "__main__":
    main()