#!/usr/bin/env python3
"""
简单的Python绑定测试
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
    
    # 测试约束模型
    model = dtm.ConstraintModel()
    print("✅ 成功创建ConstraintModel")
    
    # 测试任务空间状态
    state = dtm.TaskSpaceState()
    print("✅ 成功创建TaskSpaceState")
    
    # 测试验证结果
    result = dtm.ValidationResult()
    print("✅ 成功创建ValidationResult")
    
    print("🎉 所有基本测试通过！")
    
except ImportError as e:
    print(f"❌ 导入失败: {e}")
except Exception as e:
    print(f"❌ 运行时错误: {e}")