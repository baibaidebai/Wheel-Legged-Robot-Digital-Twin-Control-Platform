#!/usr/bin/env python3
"""
调试Python绑定
"""

import sys
import os
import numpy as np

# 添加构建路径
sys.path.insert(0, 'src/wheel_legged_control/build/wheel_legged_control')

try:
    import digital_twin_mapper_py as dtm
    print("✅ 成功导入Python绑定")
    
    # 测试基本创建
    print("测试基本对象创建...")
    mapper = dtm.DigitalTwinMapper()
    print("✅ 成功创建DigitalTwinMapper")
    
    model = dtm.ConstraintModel()
    print("✅ 成功创建ConstraintModel")
    
    # 测试轮子约束创建
    print("测试轮子约束...")
    wheel_constraint = dtm.WheelConstraint()
    print("✅ 成功创建WheelConstraint")
    
    # 测试基本属性设置
    wheel_constraint.wheel_name = "test_wheel"
    print("✅ 成功设置wheel_name")
    
    wheel_constraint.friction_coefficient = 0.8
    print("✅ 成功设置friction_coefficient")
    
    # 测试Eigen向量设置（这里可能出问题）
    print("测试Eigen向量设置...")
    try:
        # 尝试直接设置
        wheel_constraint.contact_point = [0.0, 0.0, 0.0]
        print("✅ 成功设置contact_point (list)")
    except Exception as e:
        print(f"❌ 设置contact_point (list)失败: {e}")
        
    try:
        # 尝试numpy数组
        wheel_constraint.contact_point = np.array([0.0, 0.0, 0.0])
        print("✅ 成功设置contact_point (numpy)")
    except Exception as e:
        print(f"❌ 设置contact_point (numpy)失败: {e}")
        
    try:
        wheel_constraint.normal_vector = [0.0, 0.0, 1.0]
        print("✅ 成功设置normal_vector")
    except Exception as e:
        print(f"❌ 设置normal_vector失败: {e}")
    
    # 测试添加到模型
    print("测试添加约束到模型...")
    try:
        model.wheel_constraints.append(wheel_constraint)
        print("✅ 成功添加轮子约束到模型")
        print(f"模型中轮子约束数量: {len(model.wheel_constraints)}")
    except Exception as e:
        print(f"❌ 添加轮子约束失败: {e}")
    
    print("🎉 调试测试完成！")
    
except ImportError as e:
    print(f"❌ 导入失败: {e}")
except Exception as e:
    print(f"❌ 运行时错误: {e}")
    import traceback
    traceback.print_exc()