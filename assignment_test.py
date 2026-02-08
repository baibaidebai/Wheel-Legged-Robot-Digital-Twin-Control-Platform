#!/usr/bin/env python3
"""
测试Eigen向量赋值
"""

import sys
import os
import numpy as np

# 添加构建路径
sys.path.insert(0, 'src/wheel_legged_control/build/wheel_legged_control')

try:
    import digital_twin_mapper_py as dtm
    print("✅ 成功导入Python绑定")
    
    # 创建测试模型
    test_model = dtm.create_test_constraint_model()
    first_wheel = test_model.wheel_constraints[0]
    
    print(f"原始contact_point: {first_wheel.contact_point}")
    
    # 尝试不同的赋值方式
    print("测试赋值方式...")
    
    try:
        # 方式1: 直接列表
        print("尝试列表赋值...")
        first_wheel.contact_point = [1.0, 2.0, 3.0]
        print(f"✅ 列表赋值成功: {first_wheel.contact_point}")
    except Exception as e:
        print(f"❌ 列表赋值失败: {e}")
        
    try:
        # 方式2: numpy数组
        print("尝试numpy数组赋值...")
        first_wheel.contact_point = np.array([4.0, 5.0, 6.0])
        print(f"✅ numpy数组赋值成功: {first_wheel.contact_point}")
    except Exception as e:
        print(f"❌ numpy数组赋值失败: {e}")
        
    try:
        # 方式3: 元组
        print("尝试元组赋值...")
        first_wheel.contact_point = (7.0, 8.0, 9.0)
        print(f"✅ 元组赋值成功: {first_wheel.contact_point}")
    except Exception as e:
        print(f"❌ 元组赋值失败: {e}")
    
    print("🎉 赋值测试完成！")
    
except ImportError as e:
    print(f"❌ 导入失败: {e}")
except Exception as e:
    print(f"❌ 运行时错误: {e}")
    import traceback
    traceback.print_exc()