#!/usr/bin/env python3
"""
最小化绑定测试 - 避免复杂的映射函数
"""

import sys
import os
import numpy as np

# 添加构建路径
build_path = os.path.join(os.path.dirname(__file__), '../../build/wheel_legged_control')
if os.path.exists(build_path):
    sys.path.insert(0, build_path)

try:
    import digital_twin_mapper_py as dtm
    print("✅ 成功导入数字孪生映射器绑定")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

def test_basic_functionality():
    """测试基本功能，不涉及复杂映射"""
    print("\n=== 测试基本功能 ===")
    
    try:
        # 创建映射器
        mapper = dtm.DigitalTwinMapper()
        print("✅ 映射器创建成功")
        
        # 创建简单的约束模型（手动创建，不使用辅助函数）
        model = dtm.ConstraintModel()
        
        # 添加一个简单的轮子约束
        wheel = dtm.WheelConstraint()
        wheel.wheel_name = "test_wheel"
        wheel.friction_coefficient = 0.8
        model.wheel_constraints.append(wheel)
        
        print("✅ 约束模型创建成功")
        
        # 构建运动学模型
        success = mapper.build_kinematic_model(model)
        print(f"✅ 运动学模型构建: {'成功' if success else '失败'}")
        
        # 测试奇异位形处理（这个函数相对简单）
        jacobian = np.eye(3, 3)
        regularized = mapper.handle_singular_configuration(jacobian)
        print(f"✅ 奇异位形处理成功，输出形状: {regularized.shape}")
        
        return True
        
    except Exception as e:
        print(f"❌ 基本功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_validation_only():
    """只测试验证函数"""
    print("\n=== 测试验证函数 ===")
    
    try:
        mapper = dtm.DigitalTwinMapper()
        
        # 创建最简单的模型
        model = dtm.ConstraintModel()
        wheel = dtm.WheelConstraint()
        wheel.wheel_name = "simple_wheel"
        model.wheel_constraints.append(wheel)
        
        success = mapper.build_kinematic_model(model)
        if not success:
            print("❌ 模型构建失败")
            return False
        
        # 测试验证函数（只有1个关节）
        joint_angles = np.array([0.1])
        result = mapper.validate_motion_consistency(joint_angles)
        
        print(f"✅ 验证函数成功")
        print(f"   有效: {result.is_valid}")
        print(f"   误差: {result.consistency_error}")
        print(f"   消息: {result.error_message}")
        
        return True
        
    except Exception as e:
        print(f"❌ 验证函数测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 开始最小化绑定测试")
    
    success = True
    
    if not test_basic_functionality():
        success = False
    
    if not test_validation_only():
        success = False
    
    if success:
        print("\n🎉 最小化测试成功！")
    else:
        print("\n❌ 最小化测试失败")
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)