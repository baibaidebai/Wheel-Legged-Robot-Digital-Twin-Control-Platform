#!/usr/bin/env python3
"""
最小化测试Python绑定
"""

import sys
import os

# 添加构建路径
sys.path.insert(0, 'src/wheel_legged_control/build/wheel_legged_control')

try:
    import digital_twin_mapper_py as dtm
    print("✅ 成功导入Python绑定")
    
    # 测试基本创建
    mapper = dtm.DigitalTwinMapper()
    print("✅ 成功创建DigitalTwinMapper")
    
    model = dtm.ConstraintModel()
    print("✅ 成功创建ConstraintModel")
    
    # 测试辅助函数（这些应该工作，因为它们在C++中创建对象）
    print("测试辅助函数...")
    test_model = dtm.create_test_constraint_model()
    print("✅ 成功创建测试约束模型")
    print(f"轮子约束数量: {len(test_model.wheel_constraints)}")
    print(f"腿部约束数量: {len(test_model.leg_constraints)}")
    
    test_state = dtm.create_test_task_state()
    print("✅ 成功创建测试任务状态")
    print(f"轮子位置数量: {len(test_state.wheel_positions)}")
    print(f"腿端位置数量: {len(test_state.leg_end_positions)}")
    
    # 测试访问已创建对象的属性
    print("测试访问对象属性...")
    first_wheel = test_model.wheel_constraints[0]
    print(f"第一个轮子名称: {first_wheel.wheel_name}")
    print(f"摩擦系数: {first_wheel.friction_coefficient}")
    
    # 尝试访问Eigen向量（这里可能出问题）
    print("测试访问Eigen向量...")
    try:
        contact_point = first_wheel.contact_point
        print(f"✅ 成功访问contact_point: {contact_point}")
    except Exception as e:
        print(f"❌ 访问contact_point失败: {e}")
        
    try:
        normal_vector = first_wheel.normal_vector
        print(f"✅ 成功访问normal_vector: {normal_vector}")
    except Exception as e:
        print(f"❌ 访问normal_vector失败: {e}")
    
    print("🎉 最小化测试完成！")
    
except ImportError as e:
    print(f"❌ 导入失败: {e}")
except Exception as e:
    print(f"❌ 运行时错误: {e}")
    import traceback
    traceback.print_exc()