#!/usr/bin/env python3
"""
IMU发布器ROS2节点

提供IMU数据发布功能的ROS2节点，包括：
- IMU数据仿真
- sensor_msgs/Imu消息发布
- 可配置的发布频率和噪声参数
"""

import rclpy
from rclpy.node import Node
from rclpy.executors import SingleThreadedExecutor
import sys
import os

# 添加源码路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))

try:
    from wheel_legged_control.sensors.imu_publisher_node import IMUPublisherNode
except ImportError as e:
    print(f"导入错误: {e}")
    sys.exit(1)


def main(args=None):
    """主函数"""
    rclpy.init(args=args)
    
    try:
        # 创建IMU发布器节点
        imu_node = IMUPublisherNode()
        
        # 创建执行器
        executor = SingleThreadedExecutor()
        executor.add_node(imu_node)
        
        imu_node.get_logger().info("IMU发布器节点已启动")
        
        try:
            # 运行节点
            executor.spin()
        except KeyboardInterrupt:
            imu_node.get_logger().info("收到中断信号，正在关闭...")
        finally:
            # 清理资源
            imu_node.destroy_node()
            
    except Exception as e:
        print(f"节点启动失败: {e}")
        return 1
    finally:
        rclpy.shutdown()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())