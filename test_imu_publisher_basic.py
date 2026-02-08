#!/usr/bin/env python3
"""
IMU发布器基本功能测试
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu, JointState
from geometry_msgs.msg import Twist
import time
import threading
import signal
import sys


class IMUSubscriberTest(Node):
    """IMU订阅器测试节点"""
    
    def __init__(self):
        super().__init__('imu_subscriber_test')
        
        # 创建订阅器
        self.imu_subscriber = self.create_subscription(
            Imu,
            '/imu/data',
            self.imu_callback,
            10
        )
        
        # 创建发布器用于测试
        self.joint_state_publisher = self.create_publisher(
            JointState,
            '/joint_states',
            10
        )
        
        self.cmd_vel_publisher = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )
        
        # 统计变量
        self.imu_count = 0
        self.start_time = time.time()
        self.last_imu_time = 0
        
        # 创建定时器发布测试数据
        self.timer = self.create_timer(0.1, self.publish_test_data)
        
        self.get_logger().info('IMU订阅器测试节点已启动')
        
    def imu_callback(self, msg: Imu):
        """IMU数据回调"""
        self.imu_count += 1
        current_time = time.time()
        
        if self.imu_count % 20 == 0:  # 每20条消息记录一次
            elapsed = current_time - self.start_time
            rate = self.imu_count / elapsed if elapsed > 0 else 0
            
            self.get_logger().info(
                f'接收到IMU数据 #{self.imu_count} (频率: {rate:.1f} Hz)'
            )
            self.get_logger().info(
                f'  姿态: [{msg.orientation.x:.3f}, {msg.orientation.y:.3f}, {msg.orientation.z:.3f}, {msg.orientation.w:.3f}]'
            )
            self.get_logger().info(
                f'  角速度: [{msg.angular_velocity.x:.3f}, {msg.angular_velocity.y:.3f}, {msg.angular_velocity.z:.3f}]'
            )
            self.get_logger().info(
                f'  线性加速度: [{msg.linear_acceleration.x:.3f}, {msg.linear_acceleration.y:.3f}, {msg.linear_acceleration.z:.3f}]'
            )
            
        self.last_imu_time = current_time
        
    def publish_test_data(self):
        """发布测试数据"""
        current_time = time.time()
        t = current_time - self.start_time
        
        # 发布关节状态
        joint_msg = JointState()
        joint_msg.header.stamp = self.get_clock().now().to_msg()
        joint_msg.name = ['lf0_joint', 'lf1_joint', 'rf0_joint', 'rf1_joint', 'l_wheel_joint', 'r_wheel_joint']
        joint_msg.position = [0.1 * (t % 6.28)] * 6  # 简单的时间变化
        joint_msg.velocity = [0.1] * 6
        
        self.joint_state_publisher.publish(joint_msg)
        
        # 发布速度指令
        cmd_vel = Twist()
        cmd_vel.linear.x = 0.1
        cmd_vel.angular.z = 0.05
        
        self.cmd_vel_publisher.publish(cmd_vel)
        
    def get_statistics(self):
        """获取统计信息"""
        elapsed = time.time() - self.start_time
        rate = self.imu_count / elapsed if elapsed > 0 else 0
        
        return {
            'total_messages': self.imu_count,
            'elapsed_time': elapsed,
            'average_rate': rate,
            'last_message_time': self.last_imu_time
        }


def signal_handler(signum, frame):
    """信号处理器"""
    print('\n收到中断信号，正在关闭...')
    rclpy.shutdown()
    sys.exit(0)


def main():
    """主函数"""
    print("🚀 启动IMU发布器基本功能测试")
    print("请确保IMU发布器节点正在运行:")
    print("  ros2 run wheel_legged_control imu_publisher_node")
    print("\n开始测试...")
    
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    
    rclpy.init()
    
    try:
        # 创建测试节点
        test_node = IMUSubscriberTest()
        
        # 运行测试
        start_time = time.time()
        test_duration = 10.0  # 测试10秒
        
        def check_test_completion():
            while rclpy.ok():
                elapsed = time.time() - start_time
                if elapsed >= test_duration:
                    # 获取统计信息
                    stats = test_node.get_statistics()
                    
                    print(f"\n📊 测试完成！统计信息:")
                    print(f"  测试时长: {stats['elapsed_time']:.1f} 秒")
                    print(f"  接收消息数: {stats['total_messages']}")
                    print(f"  平均频率: {stats['average_rate']:.1f} Hz")
                    
                    # 评估结果
                    if stats['total_messages'] > 0:
                        print("✅ IMU发布器基本功能正常")
                        if stats['average_rate'] > 50:
                            print("✅ 发布频率满足要求 (>50Hz)")
                        else:
                            print("⚠️  发布频率较低")
                    else:
                        print("❌ 未接收到IMU数据")
                    
                    rclpy.shutdown()
                    break
                    
                time.sleep(0.1)
        
        # 在单独线程中检查测试完成
        completion_thread = threading.Thread(target=check_test_completion)
        completion_thread.daemon = True
        completion_thread.start()
        
        # 运行ROS2节点
        rclpy.spin(test_node)
        
    except Exception as e:
        print(f'测试出错: {e}')
    finally:
        # 清理
        if 'test_node' in locals():
            test_node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
        print("测试结束")


if __name__ == '__main__':
    main()