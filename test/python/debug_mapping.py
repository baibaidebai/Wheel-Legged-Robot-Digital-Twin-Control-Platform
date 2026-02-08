#!/usr/bin/env python3
"""
调试映射函数
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

def debug_model_structure():
    """调试模型结构"""
    print("\n=== 调试模型结构 ===")
    
    test_model = dtm.create_test_constraint_model()
    
    print(f"轮子约束数量: {len(test_model.wheel_constraints)}")
    for i, wheel in enumerate(test_model.wheel_constraints):
        print(f"  轮子 {i}: {wheel.wheel_name}")
    
    print(f"腿部约束数量: {len(test_model.leg_constraints)}")
    for i, leg in enumerate(test_model.leg_constraints):
        print(f"  腿部 {i}: {leg.leg_name}, 关节数: {len(leg.joints)}")
        for j, joint in enumerate(leg.joints):
            print(f"    关节 {j}: {joint}")
    
    return test_model

def debug_joint_indexing():
    """调试关节索引"""
    print("\n=== 调试关节索引 ===")
    
    mapper = dtm.DigitalTwinMapper()
    test_model = debug_model_structure()
    
    print("构建运动学模型...")
    success = mapper.build_kinematic_model(test_model)
    print(f"模型构建: {'成功' if success else '失败'}")
    
    # 计算预期的关节数量
    expected_joints = len(test_model.wheel_constraints)
    for leg in test_model.leg_constraints:
        expected_joints += len(leg.joints)
    
    print(f"预期关节总数: {expected_joints}")
    
    return mapper, expected_joints

def test_minimal_mapping():
    """测试最小映射"""
    print("\n=== 测试最小映射 ===")
    
    try:
        mapper, expected_joints = debug_joint_indexing()
        
        # 创建正确大小的关节角度向量
        joint_angles = np.zeros(expected_joints, dtype=np.float64)
        print(f"关节角度向量大小: {len(joint_angles)}")
        print(f"关节角度值: {joint_angles}")
        
        print("准备调用 joint_to_task_mapping...")
        
        # 尝试调用映射函数
        task_state = mapper.joint_to_task_mapping(joint_angles)
        
        print("✅ 映射成功！")
        print(f"基座位置: {task_state.base_position}")
        
        return True
        
    except Exception as e:
        print(f"❌ 映射失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 开始调试映射函数")
    
    if test_minimal_mapping():
        print("\n🎉 调试成功！")
    else:
        print("\n❌ 调试失败")

if __name__ == '__main__':
    main()