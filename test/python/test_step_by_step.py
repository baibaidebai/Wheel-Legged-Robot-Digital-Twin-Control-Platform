#!/usr/bin/env python3
"""
逐步测试每个函数
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

def test_step_1():
    """步骤1：创建映射器"""
    print("\n=== 步骤1：创建映射器 ===")
    try:
        mapper = dtm.DigitalTwinMapper()
        print("✅ 映射器创建成功")
        return mapper
    except Exception as e:
        print(f"❌ 映射器创建失败: {e}")
        return None

def test_step_2():
    """步骤2：创建约束模型"""
    print("\n=== 步骤2：创建约束模型 ===")
    try:
        model = dtm.ConstraintModel()
        print("✅ 约束模型创建成功")
        return model
    except Exception as e:
        print(f"❌ 约束模型创建失败: {e}")
        return None

def test_step_3(model):
    """步骤3：添加轮子约束"""
    print("\n=== 步骤3：添加轮子约束 ===")
    try:
        wheel = dtm.WheelConstraint()
        wheel.wheel_name = "test_wheel"
        print("✅ 轮子约束创建成功")
        
        model.wheel_constraints.append(wheel)
        print("✅ 轮子约束添加成功")
        return True
    except Exception as e:
        print(f"❌ 轮子约束操作失败: {e}")
        return False

def test_step_4(mapper, model):
    """步骤4：构建运动学模型"""
    print("\n=== 步骤4：构建运动学模型 ===")
    try:
        success = mapper.build_kinematic_model(model)
        print(f"✅ 运动学模型构建: {'成功' if success else '失败'}")
        return success
    except Exception as e:
        print(f"❌ 运动学模型构建失败: {e}")
        return False

def test_step_5(mapper):
    """步骤5：测试奇异位形处理"""
    print("\n=== 步骤5：测试奇异位形处理 ===")
    try:
        print("创建3x3单位矩阵...")
        jacobian = np.eye(3, 3, dtype=np.float64)
        print(f"输入雅可比矩阵形状: {jacobian.shape}")
        
        print("调用 handle_singular_configuration...")
        regularized = mapper.handle_singular_configuration(jacobian)
        print(f"✅ 奇异位形处理成功，输出形状: {regularized.shape}")
        return True
    except Exception as e:
        print(f"❌ 奇异位形处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 开始逐步测试")
    
    # 步骤1
    mapper = test_step_1()
    if mapper is None:
        return False
    
    # 步骤2
    model = test_step_2()
    if model is None:
        return False
    
    # 步骤3
    if not test_step_3(model):
        return False
    
    # 步骤4
    if not test_step_4(mapper, model):
        return False
    
    # 步骤5
    if not test_step_5(mapper):
        return False
    
    print("\n🎉 所有步骤测试成功！")
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)