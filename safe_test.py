#!/usr/bin/env python3
"""
安全测试Python绑定
"""

import sys
import os

# 添加构建路径
sys.path.insert(0, 'src/wheel_legged_control/build/wheel_legged_control')

try:
    import digital_twin_mapper_py as dtm
    print("✅ 成功导入Python绑定")
    
    # 创建轮子约束
    wheel = dtm.WheelConstraint()
    print("✅ 成功创建WheelConstraint")
    
    # 设置基本属性
    wheel.wheel_name = "test_wheel"
    wheel.friction_coefficient = 0.8
    print("✅ 成功设置基本属性")
    
    # 使用安全的方法设置向量
    wheel.set_contact_point(1.0, 2.0, 3.0)
    print("✅ 成功设置contact_point")
    
    wheel.set_normal_vector(0.0, 0.0, 1.0)
    print("✅ 成功设置normal_vector")
    
    # 读取向量
    contact = wheel.get_contact_point()
    normal = wheel.get_normal_vector()
    
    print(f"Contact point: {contact}")
    print(f"Normal vector: {normal}")
    
    print("🎉 安全测试完成！")
    
except ImportError as e:
    print(f"❌ 导入失败: {e}")
except Exception as e:
    print(f"❌ 运行时错误: {e}")
    import traceback
    traceback.print_exc()