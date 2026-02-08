#!/usr/bin/env python3
"""
基本关节控制器测试
"""

import sys
import os
import subprocess
import time
import signal

# 添加包路径
sys.path.insert(0, 'src/wheel_legged_control')

def test_joint_controller_import():
    """测试关节控制器导入"""
    try:
        from wheel_legged_control.controllers.joint_controller import JointControllerNode, PIDController, ControlGains
        print("✅ 成功导入关节控制器模块")
        
        # 测试PID控制器
        gains = ControlGains(kp=10.0, ki=0.1, kd=0.5)
        pid = PIDController(gains)
        print("✅ 成功创建PID控制器")
        
        # 测试PID更新
        output = pid.update(1.0, 0.0, 0.1)  # 目标1.0，当前0.0，dt=0.1
        print(f"✅ PID输出: {output:.3f}")
        
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_joint_controller_node():
    """测试关节控制器节点启动"""
    print("测试关节控制器节点启动...")
    
    # 设置环境
    env = os.environ.copy()
    env['PYTHONPATH'] = 'src/wheel_legged_control:' + env.get('PYTHONPATH', '')
    
    try:
        # 启动节点（后台运行）
        process = subprocess.Popen([
            'python3', '-c', 
            '''
import sys
sys.path.insert(0, "src/wheel_legged_control")
import rclpy
from wheel_legged_control.controllers.joint_controller import JointControllerNode

rclpy.init()
node = JointControllerNode()
print("节点启动成功")
import time
time.sleep(2)  # 运行2秒
node.destroy_node()
rclpy.shutdown()
print("节点正常关闭")
            '''
        ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 等待进程完成或超时
        try:
            stdout, stderr = process.communicate(timeout=10)
            
            if process.returncode == 0:
                print("✅ 关节控制器节点启动和关闭成功")
                print(f"输出: {stdout.decode()}")
                return True
            else:
                print(f"❌ 节点运行失败，返回码: {process.returncode}")
                print(f"错误输出: {stderr.decode()}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ 节点启动超时")
            process.kill()
            return False
            
    except Exception as e:
        print(f"❌ 启动节点时发生错误: {e}")
        return False

def main():
    """主测试函数"""
    print("开始关节控制器基本测试...")
    
    # 测试1: 模块导入
    if not test_joint_controller_import():
        print("❌ 模块导入测试失败")
        return False
    
    # 测试2: 节点启动
    if not test_joint_controller_node():
        print("❌ 节点启动测试失败")
        return False
    
    print("🎉 所有基本测试通过！")
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)