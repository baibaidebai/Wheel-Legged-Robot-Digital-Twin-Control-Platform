#!/usr/bin/env python3
"""
安全的数字孪生映射器绑定测试

逐步测试绑定功能，避免段错误
"""

import sys
import os

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

def test_basic_creation():
    """测试基本对象创建"""
    print("\n=== 测试基本对象创建 ===")
    
    try:
        # 测试约束类型枚举
        holonomic = dtm.ConstraintType.HOLONOMIC
        nonholonomic = dtm.ConstraintType.NONHOLONOMIC
        print(f"✅ 约束类型枚举: HOLONOMIC={holonomic}, NONHOLONOMIC={nonholonomic}")
        
        # 测试轮子约束
        wheel = dtm.WheelConstraint()
        wheel.wheel_name = "test_wheel"
        wheel.friction_coefficient = 0.8
        print(f"✅ 轮子约束创建成功: {wheel.wheel_name}, 摩擦系数={wheel.friction_coefficient}")
        
        # 测试腿部约束
        leg = dtm.LegConstraint()
        leg.leg_name = "test_leg"
        print(f"✅ 腿部约束创建成功: {leg.leg_name}")
        
        # 测试约束模型
        model = dtm.ConstraintModel()
        print(f"✅ 约束模型创建成功")
        
        # 测试任务空间状态
        task_state = dtm.TaskSpaceState()
        print(f"✅ 任务空间状态创建成功")
        
        # 测试验证结果
        result = dtm.ValidationResult()
        print(f"✅ 验证结果创建成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 基本对象创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_helper_functions():
    """测试辅助函数"""
    print("\n=== 测试辅助函数 ===")
    
    try:
        # 测试创建测试约束模型
        test_model = dtm.create_test_constraint_model()
        print(f"✅ 测试约束模型创建成功")
        print(f"   轮子约束数量: {len(test_model.wheel_constraints)}")
        print(f"   腿部约束数量: {len(test_model.leg_constraints)}")
        
        # 测试创建测试任务状态
        test_state = dtm.create_test_task_state()
        print(f"✅ 测试任务状态创建成功")
        print(f"   轮子位置数量: {len(test_state.wheel_positions)}")
        print(f"   腿端位置数量: {len(test_state.leg_end_positions)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 辅助函数测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mapper_creation():
    """测试映射器创建"""
    print("\n=== 测试映射器创建 ===")
    
    try:
        mapper = dtm.DigitalTwinMapper()
        print(f"✅ 数字孪生映射器创建成功")
        return mapper
        
    except Exception as e:
        print(f"❌ 映射器创建失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_model_building(mapper):
    """测试模型构建"""
    print("\n=== 测试模型构建 ===")
    
    if mapper is None:
        print("❌ 映射器为空，跳过模型构建测试")
        return False
    
    try:
        test_model = dtm.create_test_constraint_model()
        success = mapper.build_kinematic_model(test_model)
        print(f"✅ 运动学模型构建: {'成功' if success else '失败'}")
        return success
        
    except Exception as e:
        print(f"❌ 模型构建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 开始安全的数字孪生映射器绑定测试")
    
    # 逐步测试
    if not test_basic_creation():
        print("❌ 基本对象创建测试失败，停止测试")
        return False
    
    if not test_helper_functions():
        print("❌ 辅助函数测试失败，停止测试")
        return False
    
    mapper = test_mapper_creation()
    if mapper is None:
        print("❌ 映射器创建失败，停止测试")
        return False
    
    if not test_model_building(mapper):
        print("❌ 模型构建失败，停止测试")
        return False
    
    print("\n🎉 所有安全测试通过！")
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)