#!/usr/bin/env python3
"""
关节控制器测试脚本
"""

import rclpy
from rclpy.node import Node
import numpy as np
import time
from std_msgs.msg import Float64MultiArray
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration


class JointControllerTester(Node):
    """关节控制器测试节点"""
    
    def __init__(self):
        super().__init__('joint_controller_tester')
        
        # 关节名称
        self.joint_names = [
            'lf0_joint', 'lf1_joint', 
            'rf0_joint', 'rf1_joint',
            'l_wheel_joint', 'r_wheel_joint'
        ]
        
        # 创建发布者
        self.joint_cmd_pub = self.create_publisher(
            Float64MultiArray,
            '/joint_commands',
            10
        )
        
        self.trajectory_pub = self.create_publisher(
            JointTrajectory,
            '/joint_trajectory',
            10
        )
        
        # 创建订阅者
        self.joint_state_sub = self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_state_callback,
            10
        )
        
        # 状态变量
        self.current_joint_states = None
        self.test_running = False
        
        self.get_logger().info('关节控制器测试节点已启动')
    
    def joint_state_callback(self, msg: JointState):
        """关节状态回调"""
        self.current_joint_states = msg
    
    def wait_for_joint_states(self, timeout=5.0):
        """等待关节状态"""
        start_time = time.time()
        while self.current_joint_states is None:
            rclpy.spin_once(self, timeout_sec=0.1)
            if time.time() - start_time > timeout:
                self.get_logger().error('等待关节状态超时')
                return False
        return True
    
    def send_joint_command(self, positions):
        """发送关节位置指令"""
        msg = Float64MultiArray()
        msg.data = positions
        self.joint_cmd_pub.publish(msg)
        self.get_logger().info(f'发送关节指令: {positions}')
    
    def send_trajectory(self, waypoints, durations):
        """
        发送轨迹指令
        
        Args:
            waypoints: 路径点列表，每个点是关节位置列表
            durations: 每个点的时间（秒）
        """
        msg = JointTrajectory()
        msg.joint_names = self.joint_names
        
        for i, (waypoint, duration) in enumerate(zip(waypoints, durations)):
            point = JointTrajectoryPoint()
            point.positions = waypoint
            point.time_from_start = Duration(sec=int(duration), nanosec=int((duration % 1) * 1e9))
            msg.points.append(point)
        
        self.trajectory_pub.publish(msg)
        self.get_logger().info(f'发送轨迹，包含{len(waypoints)}个点')
    
    def test_basic_position_control(self):
        """测试基本位置控制"""
        self.get_logger().info('=== 测试基本位置控制 ===')
        
        # 测试1: 复位到零位
        self.get_logger().info('测试1: 复位到零位')
        zero_positions = [0.0] * len(self.joint_names)
        self.send_joint_command(zero_positions)
        time.sleep(3.0)
        
        # 测试2: 腿部关节运动
        self.get_logger().info('测试2: 腿部关节运动')
        leg_positions = [0.5, -0.3, -0.5, 0.3, 0.0, 0.0]  # 腿部弯曲，轮子不动
        self.send_joint_command(leg_positions)
        time.sleep(3.0)
        
        # 测试3: 轮子旋转
        self.get_logger().info('测试3: 轮子旋转')
        wheel_positions = [0.0, 0.0, 0.0, 0.0, 3.14, -3.14]  # 轮子反向旋转
        self.send_joint_command(wheel_positions)
        time.sleep(3.0)
        
        # 测试4: 复合运动
        self.get_logger().info('测试4: 复合运动')
        complex_positions = [0.3, -0.5, -0.3, 0.5, 1.57, 1.57]  # 腿部和轮子同时运动
        self.send_joint_command(complex_positions)
        time.sleep(3.0)
        
        # 回到零位
        self.get_logger().info('回到零位')
        self.send_joint_command(zero_positions)
        time.sleep(2.0)
    
    def test_trajectory_execution(self):
        """测试轨迹执行"""
        self.get_logger().info('=== 测试轨迹执行 ===')
        
        # 创建一个简单的轨迹：腿部做周期性运动
        waypoints = [
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],      # 起始点
            [0.5, -0.3, -0.5, 0.3, 0.0, 0.0],    # 腿部弯曲
            [0.0, -0.6, 0.0, 0.6, 0.0, 0.0],     # 腿部伸展
            [-0.5, -0.3, 0.5, 0.3, 0.0, 0.0],    # 腿部反向弯曲
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],      # 回到起始点
        ]
        
        durations = [0.0, 2.0, 4.0, 6.0, 8.0]  # 每个点的时间
        
        self.send_trajectory(waypoints, durations)
        
        # 等待轨迹执行完成
        time.sleep(10.0)
    
    def test_joint_limits(self):
        """测试关节限制"""
        self.get_logger().info('=== 测试关节限制 ===')
        
        # 测试超出限制的指令
        self.get_logger().info('发送超出限制的指令')
        extreme_positions = [5.0, -5.0, 5.0, -5.0, 0.0, 0.0]  # 超出腿部关节限制
        self.send_joint_command(extreme_positions)
        time.sleep(3.0)
        
        # 检查是否被限制
        if self.current_joint_states:
            for i, (name, pos) in enumerate(zip(self.current_joint_states.name, 
                                              self.current_joint_states.position)):
                if name in ['lf0_joint', 'lf1_joint', 'rf0_joint', 'rf1_joint']:
                    if abs(pos) > 3.15:  # 超出π
                        self.get_logger().warn(f'关节{name}位置{pos:.3f}可能超出限制')
                    else:
                        self.get_logger().info(f'关节{name}位置{pos:.3f}在限制范围内')
        
        # 回到安全位置
        safe_positions = [0.0] * len(self.joint_names)
        self.send_joint_command(safe_positions)
        time.sleep(2.0)
    
    def monitor_joint_states(self, duration=10.0):
        """监控关节状态"""
        self.get_logger().info(f'=== 监控关节状态 {duration}秒 ===')
        
        start_time = time.time()
        while time.time() - start_time < duration:
            rclpy.spin_once(self, timeout_sec=0.1)
            
            if self.current_joint_states:
                positions = []
                velocities = []
                efforts = []
                
                for name in self.joint_names:
                    if name in self.current_joint_states.name:
                        idx = self.current_joint_states.name.index(name)
                        pos = self.current_joint_states.position[idx] if idx < len(self.current_joint_states.position) else 0.0
                        vel = self.current_joint_states.velocity[idx] if idx < len(self.current_joint_states.velocity) else 0.0
                        eff = self.current_joint_states.effort[idx] if idx < len(self.current_joint_states.effort) else 0.0
                        
                        positions.append(pos)
                        velocities.append(vel)
                        efforts.append(eff)
                
                self.get_logger().info(
                    f'位置: {[f"{p:.3f}" for p in positions]} | '
                    f'速度: {[f"{v:.3f}" for v in velocities]} | '
                    f'力矩: {[f"{e:.3f}" for e in efforts]}'
                )
            
            time.sleep(1.0)
    
    def run_all_tests(self):
        """运行所有测试"""
        self.get_logger().info('开始关节控制器测试')
        
        # 等待关节状态
        if not self.wait_for_joint_states():
            self.get_logger().error('无法获取关节状态，测试终止')
            return
        
        try:
            # 基本位置控制测试
            self.test_basic_position_control()
            
            # 轨迹执行测试
            self.test_trajectory_execution()
            
            # 关节限制测试
            self.test_joint_limits()
            
            # 状态监控
            self.monitor_joint_states(5.0)
            
            self.get_logger().info('所有测试完成')
            
        except Exception as e:
            self.get_logger().error(f'测试过程中发生错误: {e}')


def main(args=None):
    """主函数"""
    rclpy.init(args=args)
    
    try:
        tester = JointControllerTester()
        
        # 等待一段时间让系统稳定
        time.sleep(2.0)
        
        # 运行测试
        tester.run_all_tests()
        
    except KeyboardInterrupt:
        print('测试被用户中断')
    except Exception as e:
        print(f'测试运行错误: {e}')
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()