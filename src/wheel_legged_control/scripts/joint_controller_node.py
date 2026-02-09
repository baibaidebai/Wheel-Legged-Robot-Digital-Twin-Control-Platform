#!/usr/bin/env python3
"""
关节控制器ROS2节点

提供关节控制功能的ROS2节点，包括：
- 关节状态发布
- 关节指令订阅
- PID控制算法
- 轨迹执行
"""

import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
import sys
import os

# 添加源码路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))

try:
    from wheel_legged_control.controllers.joint_controller import JointControllerNode
    from wheel_legged_control.interfaces.joint_interface import create_joint_interface
except ImportError as e:
    print(f"导入错误: {e}")
    sys.exit(1)


def main(args=None):
    """主函数"""
    rclpy.init(args=args)
    
    try:
        # 创建关节控制器节点
        controller_node = JointControllerNode()
        
        # 创建ROS2接口管理器
        interface_manager = create_joint_interface(controller_node, controller_node)
        
        # 创建多线程执行器
        executor = MultiThreadedExecutor()
        executor.add_node(controller_node)
        
        controller_node.get_logger().info("关节控制器节点已启动")
        
        try:
            # 运行节点
            executor.spin()
        except KeyboardInterrupt:
            controller_node.get_logger().info("收到中断信号，正在关闭...")
        finally:
            # 清理资源
            controller_node.destroy_node()
            
    except Exception as e:
        print(f"节点启动失败: {e}")
        return 1
    finally:
        rclpy.shutdown()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())