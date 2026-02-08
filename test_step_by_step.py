#!/usr/bin/env python3
"""
逐步测试Python绑定
"""

import sys
import os

# 设置环境
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 
                                'install/wheel_legged_control/lib/python3.12/site-packages'))

try:
    from wheel_legged_control import digital_twin_mapper_py as dtm
    print("✅ 成功导入Python绑定")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

def test_step_1():
    """步骤1: 基本对象创建"""
    print("\n=== 步骤1: 基本对象创建 ===")
    
    mapper = dtm.DigitalTwinMapper()
    print("✅ DigitalTwinMapper创建成功")
    
    model = dtm.ConstraintModel()
    print("✅ ConstraintModel创建成功")
    
    return mapper, model

def test_step_2():
    """步骤2: 轮子约束创建"""
    print("\n=== 步骤2: 轮子约束创建 ===")
    
    wheel = dtm.WheelConstraint()
    print("✅ WheelConstraint创建成功")
    
    wheel.wheel_name = "test_wheel"
    print("✅ 轮子名称设置成功")
    
    wheel.friction_coefficient = 0.8
    print("✅ 摩擦系数设置成功")
    
    wheel.set_contact_point(0.0, 0.0, 0.0)
    print("✅ 接触点设置成功")
    
    wheel.set_normal_vector(0.0, 0.0, 1.0)
    print("✅ 法向量设置成功")
    
    return wheel

def test_step_3():
    """步骤3: 腿部约束创建"""
    print("\n=== 步骤3: 腿部约束创建 ===")
    
    leg = dtm.LegConstraint()
    print("✅ LegConstraint创建成功")
    
    leg.leg_name = "test_leg"
    print("✅ 腿部名称设置成功")
    
    return leg

def test_step_4():
    """步骤4: 字符串向量创建"""
    print("\n=== 步骤4: 字符串向量创建 ===")
    
    try:
        joints = dtm.StringVector()
        print("✅ StringVector创建成功")
        
        joints.append("joint1")
        print("✅ 第一个关节添加成功")
        
        joints.append("joint2")
        print("✅ 第二个关节添加成功")
        
        print(f"   关节数量: {len(joints)}")
        return joints
    except Exception as e:
        print(f"❌ 字符串向量操作失败: {e}")
        return None

def test_step_5(leg, joints):
    """步骤5: 关节赋值"""
    print("\n=== 步骤5: 关节赋值 ===")
    
    if joints is None:
        print("❌ 跳过关节赋值（字符串向量创建失败）")
        return
    
    try:
        leg.joints = joints
        print("✅ 关节赋值成功")
    except Exception as e:
        print(f"❌ 关节赋值失败: {e}")

def test_step_6(model, wheel):
    """步骤6: 轮子约束添加到模型"""
    print("\n=== 步骤6: 轮子约束添加到模型 ===")
    
    try:
        model.wheel_constraints.append(wheel)
        print(f"✅ 轮子约束添加成功: {len(model.wheel_constraints)} 个")
    except Exception as e:
        print(f"❌ 轮子约束添加失败: {e}")

def test_step_7(model, leg):
    """步骤7: 腿部约束添加到模型"""
    print("\n=== 步骤7: 腿部约束添加到模型 ===")
    
    try:
        model.leg_constraints.append(leg)
        print(f"✅ 腿部约束添加成功: {len(model.leg_constraints)} 个")
    except Exception as e:
        print(f"❌ 腿部约束添加失败: {e}")

def main():
    """主函数"""
    print("🚀 开始逐步测试Python绑定")
    
    # 步骤1: 基本对象创建
    mapper, model = test_step_1()
    
    # 步骤2: 轮子约束创建
    wheel = test_step_2()
    
    # 步骤3: 腿部约束创建
    leg = test_step_3()
    
    # 步骤4: 字符串向量创建
    joints = test_step_4()
    
    # 步骤5: 关节赋值
    test_step_5(leg, joints)
    
    # 步骤6: 轮子约束添加到模型
    test_step_6(model, wheel)
    
    # 步骤7: 腿部约束添加到模型
    test_step_7(model, leg)
    
    print("\n🎉 逐步测试完成！")

if __name__ == "__main__":
    main()