#!/usr/bin/env python3
"""
IMU系统测试脚本
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu, JointState
from geometry_msgs.msg import Twist
import numpy as np
import time
import threading
from typing import List


class IMUTestNode(Node):
    """IMU测试节点"""
    
    def __init__(self):
        super().__init__('imu_test_node')
        
        # 创建订阅器
        self.imu_subscriber = self.create_subscription(
            Imu,
            '/imu/data',
            self.imu_callback,
            10
        )
        
        # 创建发布器
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
        
        # 数据收集
        self.imu_data: List[Imu] = []
        self.max_samples = 50
        
        # 测试状态
        self.test_phase = 0
        self.test_start_time = time.time()
        
        # 创建定时器发布测试数据
        self.timer = self.create_timer(0.1, self.publish_test_data)
        
        self.get_logger().info('IMU测试节点已启动')
        
    def imu_callback(self, msg: Imu):
        """IMU数据回调"""
        self.imu_data.append(msg)
        
        # 限制数据量
        if len(self.imu_data) > self.max_samples:
            self.imu_data.pop(0)
            
        # 每10条消息记录一次
        if len(self.imu_data) % 10 == 0:
            self.get_logger().info(
                f'接收到IMU数据 #{len(self.imu_data)}: '
                f'角速度=[{msg.angular_velocity.x:.3f}, {msg.angular_velocity.y:.3f}, {msg.angular_velocity.z:.3f}], '
                f'加速度=[{msg.linear_acceleration.x:.3f}, {msg.linear_acceleration.y:.3f}, {msg.linear_acceleration.z:.3f}]'
            )
            
    def publish_test_data(self):
        """发布测试数据"""
        current_time = time.time()
        elapsed = current_time - self.test_start_time
        
        # 测试阶段1: 静止状态 (0-5秒)
        if elapsed < 5.0:
            if self.test_phase != 1:
                self.test_phase = 1
                self.get_logger().info('测试阶段1: 静止状态')
            self.publish_static_data()
            
        # 测试阶段2: 关节运动 (5-10秒)
        elif elapsed < 10.0:
            if self.test_phase != 2:
                self.test_phase = 2
                self.get_logger().info('测试阶段2: 关节运动')
            self.publish_joint_motion(elapsed - 5.0)
            
        # 测试阶段3: 基座运动 (10-15秒)
        elif elapsed < 15.0:
            if self.test_phase != 3:
                self.test_phase = 3
                self.get_logger().info('测试阶段3: 基座运动')
            self.publish_base_motion(elapsed - 10.0)
            
        # 测试阶段4: 复合运动 (15-20秒)
        elif elapsed < 20.0:
            if self.test_phase != 4:
                self.test_phase = 4
                self.get_logger().info('测试阶段4: 复合运动')
            self.publish_combined_motion(elapsed - 15.0)
            
        else:
            # 测试完成
            if self.test_phase != 5:
                self.test_phase = 5
                self.get_logger().info('测试完成，分析结果...')
                self.analyze_results()
                
    def publish_static_data(self):
        """发布静止状态数据"""
        # 发布零关节状态
        joint_msg = JointState()
        joint_msg.header.stamp = self.get_clock().now().to_msg()
        joint_msg.name = ['lf0_joint', 'lf1_joint', 'rf0_joint', 'rf1_joint', 'l_wheel_joint', 'r_wheel_joint']
        joint_msg.position = [0.0] * 6
        joint_msg.velocity = [0.0] * 6
        
        self.joint_state_publisher.publish(joint_msg)
        
        # 发布零速度指令
        cmd_vel = Twist()
        self.cmd_vel_publisher.publish(cmd_vel)
        
    def publish_joint_motion(self, t: float):
        """发布关节运动数据"""
        joint_msg = JointState()
        joint_msg.header.stamp = self.get_clock().now().to_msg()
        joint_msg.name = ['lf0_joint', 'lf1_joint', 'rf0_joint', 'rf1_joint', 'l_wheel_joint', 'r_wheel_joint']
        
        # 正弦波关节运动
        joint_msg.position = [
            0.2 * np.sin(t),      # lf0_joint
            0.3 * np.cos(t),      # lf1_joint
            0.2 * np.sin(t + np.pi),  # rf0_joint
            0.3 * np.cos(t + np.pi),  # rf1_joint
            t * 0.5,              # l_wheel_joint
            t * 0.5               # r_wheel_joint
        ]
        
        joint_msg.velocity = [
            0.2 * np.cos(t),      # lf0_joint
            -0.3 * np.sin(t),     # lf1_joint
            0.2 * np.cos(t + np.pi),  # rf0_joint
            -0.3 * np.sin(t + np.pi), # rf1_joint
            0.5,                  # l_wheel_joint
            0.5                   # r_wheel_joint
        ]
        
        self.joint_state_publisher.publish(joint_msg)
        
        # 静止基座
        cmd_vel = Twist()
        self.cmd_vel_publisher.publish(cmd_vel)
        
    def publish_base_motion(self, t: float):
        """发布基座运动数据"""
        # 静止关节
        joint_msg = JointState()
        joint_msg.header.stamp = self.get_clock().now().to_msg()
        joint_msg.name = ['lf0_joint', 'lf1_joint', 'rf0_joint', 'rf1_joint', 'l_wheel_joint', 'r_wheel_joint']
        joint_msg.position = [0.0] * 6
        joint_msg.velocity = [0.0] * 6
        
        self.joint_state_publisher.publish(joint_msg)
        
        # 基座运动
        cmd_vel = Twist()
        cmd_vel.linear.x = 0.5 * np.sin(t)
        cmd_vel.angular.z = 0.3 * np.cos(t)
        
        self.cmd_vel_publisher.publish(cmd_vel)
        
    def publish_combined_motion(self, t: float):
        """发布复合运动数据"""
        # 关节运动
        joint_msg = JointState()
        joint_msg.header.stamp = self.get_clock().now().to_msg()
        joint_msg.name = ['lf0_joint', 'lf1_joint', 'rf0_joint', 'rf1_joint', 'l_wheel_joint', 'r_wheel_joint']
        
        joint_msg.position = [
            0.1 * np.sin(2*t),
            0.15 * np.cos(2*t),
            0.1 * np.sin(2*t + np.pi),
            0.15 * np.cos(2*t + np.pi),
            t * 0.3,
            t * 0.3
        ]
        
        joint_msg.velocity = [
            0.2 * np.cos(2*t),
            -0.3 * np.sin(2*t),
            0.2 * np.cos(2*t + np.pi),
            -0.3 * np.sin(2*t + np.pi),
            0.3,
            0.3
        ]
        
        self.joint_state_publisher.publish(joint_msg)
        
        # 基座运动
        cmd_vel = Twist()
        cmd_vel.linear.x = 0.3 * np.sin(t)
        cmd_vel.linear.y = 0.2 * np.cos(t)
        cmd_vel.angular.z = 0.2 * np.sin(t)
        
        self.cmd_vel_publisher.publish(cmd_vel)
        
    def analyze_results(self):
        """分析测试结果"""
        if not self.imu_data:
            self.get_logger().error('未收到IMU数据！')
            return
            
        self.get_logger().info(f'收到 {len(self.imu_data)} 条IMU数据')
        
        # 分析数据
        orientations = []
        angular_velocities = []
        linear_accelerations = []
        
        for imu_msg in self.imu_data:
            orientations.append([
                imu_msg.orientation.x,
                imu_msg.orientation.y,
                imu_msg.orientation.z,
                imu_msg.orientation.w
            ])
            
            angular_velocities.append([
                imu_msg.angular_velocity.x,
                imu_msg.angular_velocity.y,
                imu_msg.angular_velocity.z
            ])
            
            linear_accelerations.append([
                imu_msg.linear_acceleration.x,
                imu_msg.linear_acceleration.y,
                imu_msg.linear_acceleration.z
            ])
            
        orientations = np.array(orientations)
        angular_velocities = np.array(angular_velocities)
        linear_accelerations = np.array(linear_accelerations)
        
        # 统计分析
        self.get_logger().info('=== IMU数据分析结果 ===')
        
        # 四元数归一化检查
        q_norms = np.linalg.norm(orientations, axis=1)
        self.get_logger().info(f'四元数归一化: 平均={np.mean(q_norms):.4f}, 标准差={np.std(q_norms):.4f}')
        
        # 角速度统计
        gyro_mean = np.mean(angular_velocities, axis=0)
        gyro_std = np.std(angular_velocities, axis=0)
        self.get_logger().info(f'角速度统计:')
        self.get_logger().info(f'  平均值: [{gyro_mean[0]:.4f}, {gyro_mean[1]:.4f}, {gyro_mean[2]:.4f}]')
        self.get_logger().info(f'  标准差: [{gyro_std[0]:.4f}, {gyro_std[1]:.4f}, {gyro_std[2]:.4f}]')
        
        # 加速度统计
        accel_mean = np.mean(linear_accelerations, axis=0)
        accel_std = np.std(linear_accelerations, axis=0)
        self.get_logger().info(f'线性加速度统计:')
        self.get_logger().info(f'  平均值: [{accel_mean[0]:.4f}, {accel_mean[1]:.4f}, {accel_mean[2]:.4f}]')
        self.get_logger().info(f'  标准差: [{accel_std[0]:.4f}, {accel_std[1]:.4f}, {accel_std[2]:.4f}]')
        
        # 重力检查（Z轴加速度应该接近9.8）
        z_accel_mean = accel_mean[2]
        gravity_error = abs(z_accel_mean - 9.81)
        self.get_logger().info(f'重力检查: Z轴加速度平均值={z_accel_mean:.4f}, 误差={gravity_error:.4f}')
        
        # 数据有效性检查
        valid_count = 0
        for i, imu_msg in enumerate(self.imu_data):
            # 检查四元数归一化
            q_norm = np.linalg.norm([imu_msg.orientation.x, imu_msg.orientation.y, 
                                   imu_msg.orientation.z, imu_msg.orientation.w])
            if abs(q_norm - 1.0) < 0.1:
                valid_count += 1
                
        validity_rate = valid_count / len(self.imu_data) * 100
        self.get_logger().info(f'数据有效性: {valid_count}/{len(self.imu_data)} ({validity_rate:.1f}%)')
        
        # 测试结果总结
        self.get_logger().info('=== 测试结果总结 ===')
        if validity_rate > 90:
            self.get_logger().info('✅ IMU系统测试通过')
        else:
            self.get_logger().warn('⚠️  IMU系统测试部分通过')
            
        # 停止定时器
        self.timer.cancel()


def main():
    """主函数"""
    print("🚀 启动IMU系统测试")
    
    rclpy.init()
    
    try:
        # 创建测试节点
        test_node = IMUTestNode()
        
        # 运行测试
        print("开始IMU系统测试，预计20秒...")
        rclpy.spin(test_node)
        
    except KeyboardInterrupt:
        print('\n用户中断测试')
    except Exception as e:
        print(f'测试出错: {e}')
    finally:
        # 清理
        if 'test_node' in locals():
            test_node.destroy_node()
        rclpy.shutdown()
        print("IMU系统测试结束")


if __name__ == '__main__':
    main()