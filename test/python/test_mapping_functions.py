#!/usr/bin/env python3
"""
测试映射函数的具体实现
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

def test_joint_to_task_mapping():
    """测试关节到任务空间映射"""
    print("\n=== 测试关节到任务空间映射 ===")
    
    try:
        # 创建映射器和模型
        mapper = dtm.DigitalTwinMapper()
        test_model = dtm.create_test_constraint_model()
        
        # 构建模型
        success = mapper.build_kinematic_model(test_model)
        if not success:
            print("❌ 模型构建失败")
            return False
        
        print("✅ 模型构建成功，开始测试映射...")
        
        # 创建正确大小的关节角度向量
        # 根据测试模型：2个轮子 + 4个腿部关节 = 6个关节
        joint_angles = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float64)
        print(f"输入关节角度 (6个关节): {joint_angles}")
        
        # 尝试映射
        print("调用 joint_to_task_mapping...")
        task_state = mapper.joint_to_task_mapping(joint_angles)
        print("✅ 正运动学映射成功")
        
        # 打印结果
        print(f"基座位置: {task_state.base_position}")
        print(f"轮子位置数量: {len(task_state.wheel_positions)}")
        print(f"腿端位置数量: {len(task_state.leg_end_positions)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 关节到任务空间映射失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_task_to_joint_mapping():
    """测试任务到关节空间映射"""
    print("\n=== 测试任务到关节空间映射 ===")
    
    try:
        # 创建映射器和模型
        mapper = dtm.DigitalTwinMapper()
        test_model = dtm.create_test_constraint_model()
        
        # 构建模型
        success = mapper.build_kinematic_model(test_model)
        if not success:
            print("❌ 模型构建失败")
            return False
        
        print("✅ 模型构建成功，开始测试逆映射...")
        
        # 创建简单的任务状态
        task_state = dtm.TaskSpaceState()
        
        # 设置基座位置
        task_state.base_position = np.array([0.0, 0.0, 0.2])
        
        # 设置轮子位置
        task_state.wheel_positions["left_wheel"] = np.array([0.0, 0.2, 0.0])
        task_state.wheel_positions["right_wheel"] = np.array([0.0, -0.2, 0.0])
        
        # 设置腿端位置
        task_state.leg_end_positions["left_leg"] = np.array([0.3, 0.2, -0.1])
        task_state.leg_end_positions["right_leg"] = np.array([0.3, -0.2, -0.1])
        
        print("调用 task_to_joint_mapping...")
        joint_angles = mapper.task_to_joint_mapping(task_state)
        print("✅ 逆运动学映射成功")
        
        print(f"输出关节角度: {joint_angles}")
        
        return True
        
    except Exception as e:
        print(f"❌ 任务到关节空间映射失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_validation():
    """测试验证函数"""
    print("\n=== 测试验证函数 ===")
    
    try:
        # 创建映射器和模型
        mapper = dtm.DigitalTwinMapper()
        test_model = dtm.create_test_constraint_model()
        
        # 构建模型
        success = mapper.build_kinematic_model(test_model)
        if not success:
            print("❌ 模型构建失败")
            return False
        
        print("✅ 模型构建成功，开始测试验证...")
        
        # 创建测试关节角度 (6个关节)
        joint_angles = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6], dtype=np.float64)
        
        print("调用 validate_motion_consistency...")
        result = mapper.validate_motion_consistency(joint_angles)
        print("✅ 运动一致性验证成功")
        
        print(f"验证结果: 有效={result.is_valid}, 误差={result.consistency_error}")
        if result.error_message:
            print(f"错误信息: {result.error_message}")
        
        return True
        
    except Exception as e:
        print(f"❌ 验证函数测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 开始映射函数测试")
    
    # 测试正运动学
    if not test_joint_to_task_mapping():
        print("❌ 正运动学测试失败")
        return False
    
    # 测试逆运动学
    if not test_task_to_joint_mapping():
        print("❌ 逆运动学测试失败")
        return False
    
    # 测试验证
    if not test_validation():
        print("❌ 验证测试失败")
        return False
    
    print("\n🎉 所有映射函数测试通过！")
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)