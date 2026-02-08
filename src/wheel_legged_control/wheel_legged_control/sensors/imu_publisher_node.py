#!/usr/bin/env python3
"""
IMU数据发布器节点
基于机器人状态发布IMU传感器数据
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from sensor_msgs.msg import Imu, JointState
from geometry_msgs.msg import Twist
from std_msgs.msg import Header
import numpy as np
import time
from typing import Dict, Optional

from .imu_simulator import IMUSimulator, IMUConfig, RobotState


class IMUPublisherNode(Node):
    """IMU数据发布器节点"""
    
    def __init__(self):
        super().__init__('imu_publisher_node')
        
        # 声明参数
        self.declare_parameter('imu_topic', '/imu/data')
        self.declare_parameter('joint_state_topic', '/joint_states')
        self.declare_parameter('cmd_vel_topic', '/cmd_vel')
        self.declare_parameter('imu_frame_id', 'imu_link')
        self.declare_parameter('publish_rate', 100.0)
        self.declare_parameter('gyro_noise_std', 0.01)
        self.declare_parameter('accel_noise_std', 0.1)
        self.declare_parameter('gravity', 9.81)
        
        # 获取参数
        self.imu_topic = self.get_parameter('imu_topic').value
        self.joint_state_topic = self.get_parameter('joint_state_topic').value
        self.cmd_vel_topic = self.get_parameter('cmd_vel_topic').value
        self.imu_frame_id = self.get_parameter('imu_frame_id').value
        self.publish_rate = self.get_parameter('publish_rate').value
        self.gyro_noise_std = self.get_parameter('gyro_noise_std').value
        self.accel_noise_std = self.get_parameter('accel_noise_std').value
        self.gravity = self.get_parameter('gravity').value
        
        # 创建IMU配置
        imu_config = IMUConfig(
            gyro_noise_std=self.gyro_noise_std,
            accel_noise_std=self.accel_noise_std,
            gravity=self.gravity,
            update_rate=self.publish_rate
        )
        
        # 创建IMU仿真器
        self.imu_simulator = IMUSimulator(imu_config)
        
        # QoS配置
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
            depth=10
        )
        
        # 创建发布器
        self.imu_publisher = self.create_publisher(
            Imu, 
            self.imu_topic, 
            qos_profile
        )
        
        # 创建订阅器
        self.joint_state_subscriber = self.create_subscription(
            JointState,
            self.joint_state_topic,
            self.joint_state_callback,
            qos_profile
        )
        
        self.cmd_vel_subscriber = self.create_subscription(
            Twist,
            self.cmd_vel_topic,
            self.cmd_vel_callback,
            qos_profile
        )
        
        # 状态变量
        self.current_joint_positions: Dict[str, float] = {}
        self.current_joint_velocities: Dict[str, float] = {}
        self.current_linear_velocity = np.zeros(3)
        self.current_angular_velocity = np.zeros(3)
        self.current_position = np.zeros(3)
        self.current_orientation = np.array([0.0, 0.0, 0.0, 1.0])  # 单位四元数
        
        # 运动积分变量
        self.last_update_time = time.time()
        
        # 创建定时器
        timer_period = 1.0 / self.publish_rate
        self.timer = self.create_timer(timer_period, self.publish_imu_data)
        
        # 统计变量
        self.publish_count = 0
        self.last_log_time = time.time()
        
        self.get_logger().info(f'IMU发布器节点已启动')
        self.get_logger().info(f'  IMU话题: {self.imu_topic}')
        self.get_logger().info(f'  关节状态话题: {self.joint_state_topic}')
        self.get_logger().info(f'  速度指令话题: {self.cmd_vel_topic}')
        self.get_logger().info(f'  发布频率: {self.publish_rate} Hz')
        self.get_logger().info(f'  IMU坐标系: {self.imu_frame_id}')
        
    def joint_state_callback(self, msg: JointState):
        """关节状态回调函数"""
        # 更新关节位置和速度
        for i, name in enumerate(msg.name):
            if i < len(msg.position):
                self.current_joint_positions[name] = msg.position[i]
            if i < len(msg.velocity):
                self.current_joint_velocities[name] = msg.velocity[i]
                
        # 基于关节状态估计机器人姿态（简化版本）
        self.estimate_robot_pose_from_joints()
        
    def cmd_vel_callback(self, msg: Twist):
        """速度指令回调函数"""
        # 更新线性和角速度
        self.current_linear_velocity = np.array([
            msg.linear.x,
            msg.linear.y,
            msg.linear.z
        ])
        
        self.current_angular_velocity = np.array([
            msg.angular.x,
            msg.angular.y,
            msg.angular.z
        ])
        
    def estimate_robot_pose_from_joints(self):
        """基于关节状态估计机器人位姿（简化版本）"""
        current_time = time.time()
        dt = current_time - self.last_update_time
        
        if dt <= 0:
            return
            
        # 简化的位置积分
        self.current_position += self.current_linear_velocity * dt
        
        # 简化的姿态积分（使用小角度近似）
        angular_displacement = self.current_angular_velocity * dt
        
        # 将角位移转换为四元数增量
        angle = np.linalg.norm(angular_displacement)
        if angle > 1e-6:
            axis = angular_displacement / angle
            # 四元数增量 [sin(θ/2)*axis, cos(θ/2)]
            dq = np.array([
                axis[0] * np.sin(angle/2),
                axis[1] * np.sin(angle/2),
                axis[2] * np.sin(angle/2),
                np.cos(angle/2)
            ])
            
            # 四元数乘法更新姿态
            self.current_orientation = self.quaternion_multiply(self.current_orientation, dq)
            
            # 归一化四元数
            norm = np.linalg.norm(self.current_orientation)
            if norm > 0:
                self.current_orientation = self.current_orientation / norm
        
        self.last_update_time = current_time
        
    def quaternion_multiply(self, q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
        """
        四元数乘法
        
        Args:
            q1, q2: 四元数 [x, y, z, w]
            
        Returns:
            乘积四元数
        """
        x1, y1, z1, w1 = q1
        x2, y2, z2, w2 = q2
        
        return np.array([
            w1*x2 + x1*w2 + y1*z2 - z1*y2,
            w1*y2 - x1*z2 + y1*w2 + z1*x2,
            w1*z2 + x1*y2 - y1*x2 + z1*w2,
            w1*w2 - x1*x2 - y1*y2 - z1*z2
        ])
        
    def create_robot_state(self) -> RobotState:
        """创建当前机器人状态"""
        return RobotState(
            timestamp=time.time(),
            joint_positions=self.current_joint_positions.copy(),
            joint_velocities=self.current_joint_velocities.copy(),
            base_position=self.current_position.copy(),
            base_orientation=self.current_orientation.copy(),
            base_linear_velocity=self.current_linear_velocity.copy(),
            base_angular_velocity=self.current_angular_velocity.copy()
        )
        
    def publish_imu_data(self):
        """发布IMU数据"""
        try:
            # 创建当前机器人状态
            robot_state = self.create_robot_state()
            
            # 生成IMU消息
            imu_msg = self.imu_simulator.create_imu_message(robot_state, self.imu_frame_id)
            
            # 验证数据
            if self.imu_simulator.validate_imu_data(imu_msg):
                # 发布IMU数据
                self.imu_publisher.publish(imu_msg)
                self.publish_count += 1
                
                # 定期记录日志
                current_time = time.time()
                if current_time - self.last_log_time > 5.0:  # 每5秒记录一次
                    self.get_logger().info(
                        f'IMU数据发布中... 已发布 {self.publish_count} 条消息 '
                        f'(角速度: [{imu_msg.angular_velocity.x:.3f}, {imu_msg.angular_velocity.y:.3f}, {imu_msg.angular_velocity.z:.3f}], '
                        f'加速度: [{imu_msg.linear_acceleration.x:.3f}, {imu_msg.linear_acceleration.y:.3f}, {imu_msg.linear_acceleration.z:.3f}])'
                    )
                    self.last_log_time = current_time
            else:
                self.get_logger().warn('生成的IMU数据无效，跳过发布')
                
        except Exception as e:
            self.get_logger().error(f'发布IMU数据时出错: {str(e)}')
            
    def get_imu_statistics(self) -> Dict:
        """获取IMU统计信息"""
        filtered_gyro, filtered_accel = self.imu_simulator.get_filtered_data()
        
        return {
            'publish_count': self.publish_count,
            'publish_rate': self.publish_rate,
            'filtered_gyro': filtered_gyro.tolist(),
            'filtered_accel': filtered_accel.tolist(),
            'current_position': self.current_position.tolist(),
            'current_orientation': self.current_orientation.tolist()
        }


def main(args=None):
    """主函数"""
    rclpy.init(args=args)
    
    try:
        # 创建IMU发布器节点
        imu_publisher_node = IMUPublisherNode()
        
        # 运行节点
        rclpy.spin(imu_publisher_node)
        
    except KeyboardInterrupt:
        print('\n用户中断，正在关闭IMU发布器节点...')
    except Exception as e:
        print(f'IMU发布器节点运行出错: {e}')
    finally:
        # 清理资源
        if 'imu_publisher_node' in locals():
            imu_publisher_node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()