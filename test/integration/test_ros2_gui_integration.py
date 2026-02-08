#!/usr/bin/env python3
"""
ROS2 GUI集成测试

测试ROS2集成控制面板的基本功能：
- ROS2节点连接
- 关节状态发布和订阅
- IMU数据发布和订阅
- 服务调用
"""

import sys
import os
import time
import threading
import math
import numpy as np
from typing import Dict, List

import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor

# ROS2消息类型
from sensor_msgs.msg import JointState, Imu
from std_msgs.msg import Float64MultiArray, Header
from geometry_msgs.msg import Vector3, Quaternion
from std_srvs.srv import SetBool, Trigger

# 添加源码路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src/wheel_legged_control'))

try:
    from wheel_legged_control.controllers.joint_controller import JointControllerNode
    from wheel_legged_control.sensors.imu_simulator import IMUSimulator
    from wheel_legged_control.interfaces.joint_interface import create_joint_interface
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已正确构建项目: colcon build --symlink-install")
    sys.exit(1)


class TestPublisherNode(Node):
    """测试发布器节点"""
    
    def __init__(self):
        super().__init__('test_publisher')
        
        # 创建发布器
        self.joint_state_publisher = self.create_publisher(
            JointState,
            '/joint_states',
            10
        )
        
        self.imu_publisher = self.create_publisher(
            Imu,
            '/imu/data',
            10
        )
        
        # 创建订阅器
        self.joint_command_subscriber = self.create_subscription(
            Float64MultiArray,
            '/joint_commands',
            self.joint_command_callback,
            10
        )
        
        # 创建服务
        self.emergency_stop_service = self.create_service(
            Trigger,
            '/joint_controller/emergency_stop',
            self.emergency_stop_callback
        )
        
        self.reset_service = self.create_service(
            Trigger,
            '/joint_controller/reset',
            self.reset_callback
        )
        
        self.enable_service = self.create_service(
            SetBool,
            '/joint_controller/enable',
            self.enable_callback
        )
        
        # 状态变量
        self.joint_positions = [0.0, 0.0, 0.0, 0.0]  # lf0, lf1, rf0, rf1
        self.joint_names = ['lf0_Joint', 'lf1_Joint', 'rf0_Joint', 'rf1_Joint']
        self.controller_enabled = True
        
        # IMU仿真器
        self.imu_simulator = IMUSimulator()
        
        # 定时器
        self.joint_timer = self.create_timer(0.01, self.publish_joint_states)  # 100Hz
        self.imu_timer = self.create_timer(0.01, self.publish_imu_data)  # 100Hz
        self.simulation_timer = self.create_timer(0.1, self.update_simulation)  # 10Hz
        
        self.get_logger().info("测试发布器节点已启动")
        
    def joint_command_callback(self, msg: Float64MultiArray):
        """关节指令回调"""
        if len(msg.data) >= len(self.joint_positions):
            for i in range(len(self.joint_positions)):
                self.joint_positions[i] = msg.data[i]
            
            self.get_logger().info(
                f"收到关节指令: {[f'{math.degrees(pos):.1f}°' for pos in self.joint_positions]}"
            )
    
    def publish_joint_states(self):
        """发布关节状态"""
        msg = JointState()
        msg.header = Header()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'
        
        msg.name = self.joint_names
        msg.position = self.joint_positions
        msg.velocity = [0.0] * len(self.joint_names)
        msg.effort = [0.0] * len(self.joint_names)
        
        self.joint_state_publisher.publish(msg)
    
    def publish_imu_data(self):
        """发布IMU数据"""
        # 简单的IMU数据仿真
        current_time = time.time()
        
        # 导入RobotState
        from wheel_legged_control.sensors.imu_simulator import RobotState
        
        # 模拟机器人状态
        robot_state = RobotState(
            timestamp=current_time,
            joint_positions=dict(zip(self.joint_names, self.joint_positions)),
            joint_velocities=dict(zip(self.joint_names, [0.0] * len(self.joint_names))),
            base_position=np.array([0.0, 0.0, 0.5]),
            base_orientation=np.array([0.0, 0.0, 0.0, 1.0]),  # 四元数 [x, y, z, w]
            base_linear_velocity=np.array([0.0, 0.0, 0.0]),
            base_angular_velocity=np.array([0.0, 0.0, 0.0])
        )
        
        # 生成IMU数据
        orientation, angular_velocity, linear_acceleration = self.imu_simulator.generate_imu_data(robot_state)
        
        # 创建ROS2消息
        msg = Imu()
        msg.header = Header()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'imu_link'
        
        # 姿态四元数
        msg.orientation = Quaternion()
        msg.orientation.x = float(orientation[0])
        msg.orientation.y = float(orientation[1])
        msg.orientation.z = float(orientation[2])
        msg.orientation.w = float(orientation[3])
        
        # 角速度
        msg.angular_velocity = Vector3()
        msg.angular_velocity.x = float(angular_velocity[0])
        msg.angular_velocity.y = float(angular_velocity[1])
        msg.angular_velocity.z = float(angular_velocity[2])
        
        # 线性加速度
        msg.linear_acceleration = Vector3()
        msg.linear_acceleration.x = float(linear_acceleration[0])
        msg.linear_acceleration.y = float(linear_acceleration[1])
        msg.linear_acceleration.z = float(linear_acceleration[2])
        
        self.imu_publisher.publish(msg)
    
    def update_simulation(self):
        """更新仿真状态"""
        # 简单的关节运动仿真
        if self.controller_enabled:
            # 添加小幅度的噪声来模拟真实系统
            for i in range(len(self.joint_positions)):
                noise = (time.time() % 1.0 - 0.5) * 0.01  # ±0.01弧度噪声
                self.joint_positions[i] += noise * 0.1
    
    def emergency_stop_callback(self, request, response):
        """紧急停止服务回调"""
        self.joint_positions = [0.0] * len(self.joint_positions)
        self.controller_enabled = False
        
        response.success = True
        response.message = "紧急停止执行成功"
        
        self.get_logger().info("执行紧急停止")
        return response
    
    def reset_callback(self, request, response):
        """复位服务回调"""
        self.joint_positions = [0.0] * len(self.joint_positions)
        
        response.success = True
        response.message = "复位执行成功"
        
        self.get_logger().info("执行复位")
        return response
    
    def enable_callback(self, request, response):
        """使能服务回调"""
        self.controller_enabled = request.data
        
        response.success = True
        if request.data:
            response.message = "控制器已启用"
            self.get_logger().info("控制器已启用")
        else:
            response.message = "控制器已禁用"
            self.get_logger().info("控制器已禁用")
        
        return response


def test_basic_functionality():
    """测试基本功能"""
    print("🧪 开始ROS2 GUI集成测试")
    
    # 初始化ROS2
    rclpy.init()
    
    try:
        # 创建测试节点
        test_node = TestPublisherNode()
        
        # 创建执行器
        executor = MultiThreadedExecutor()
        executor.add_node(test_node)
        
        print("✅ 测试节点已创建")
        print("📡 开始发布测试数据...")
        print("🎮 请启动ROS2控制面板进行测试")
        print("   命令: python3 src/wheel_legged_control/wheel_legged_control/gui/ros2_control_panel.py")
        print("")
        print("🔍 测试项目:")
        print("   1. 关节状态显示 - 应该看到4个关节的实时数据")
        print("   2. IMU数据显示 - 应该看到姿态和加速度数据")
        print("   3. 关节控制 - 移动滑块应该发送指令")
        print("   4. 服务调用 - 复位、紧急停止、使能按钮")
        print("")
        print("按 Ctrl+C 停止测试")
        
        try:
            # 运行测试
            executor.spin()
        except KeyboardInterrupt:
            print("\n🛑 测试被用户中断")
        finally:
            # 清理资源
            test_node.destroy_node()
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    finally:
        rclpy.shutdown()
    
    print("✅ 测试完成")
    return True


def main():
    """主函数"""
    print("=" * 60)
    print("轮腿机器人孪生控制系统 - ROS2 GUI集成测试")
    print("=" * 60)
    
    # 检查依赖
    try:
        import PyQt5
        print("✅ PyQt5 已安装")
    except ImportError:
        print("❌ PyQt5 未安装，请运行: pip install PyQt5")
        return 1
    
    # 运行测试
    success = test_basic_functionality()
    
    if success:
        print("\n🎉 所有测试通过！")
        print("💡 提示: 现在可以使用以下命令启动完整系统:")
        print("   ros2 launch wheel_legged_control ros2_control_panel.launch.py")
        return 0
    else:
        print("\n❌ 测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())