#!/usr/bin/env python3
"""
Gazebo仿真器节点

负责管理Gazebo仿真环境，监控仿真状态，提供仿真控制接口。
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from std_msgs.msg import String, Bool
from sensor_msgs.msg import JointState
from geometry_msgs.msg import Twist
from gazebo_msgs.srv import GetEntityState, SetEntityState
from gazebo_msgs.msg import EntityState
import time
import threading
from typing import Dict, List, Optional


class GazeboSimulator(Node):
    """
    Gazebo仿真器节点类
    
    提供Gazebo仿真环境的管理和监控功能，包括：
    - 仿真状态监控
    - 机器人状态获取
    - 仿真参数调整
    - 错误处理和恢复
    """
    
    def __init__(self):
        """初始化Gazebo仿真器节点"""
        super().__init__('gazebo_simulator')
        
        # 节点参数
        self.declare_parameter('robot_name', 'wheel_legged_robot')
        self.declare_parameter('update_rate', 50.0)
        self.declare_parameter('timeout', 5.0)
        
        self.robot_name = self.get_parameter('robot_name').get_parameter_value().string_value
        self.update_rate = self.get_parameter('update_rate').get_parameter_value().double_value
        self.timeout = self.get_parameter('timeout').get_parameter_value().double_value
        
        # QoS配置
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            depth=10
        )
        
        # 发布器
        self.sim_status_pub = self.create_publisher(
            String, 
            '/gazebo/simulation_status', 
            qos_profile
        )
        
        self.robot_pose_pub = self.create_publisher(
            EntityState,
            '/gazebo/robot_pose',
            qos_profile
        )
        
        # 订阅器
        self.joint_states_sub = self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_states_callback,
            10
        )
        
        self.cmd_vel_sub = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )
        
        # 服务客户端
        self.get_entity_state_client = self.create_client(
            GetEntityState,
            '/gazebo/get_entity_state'
        )
        
        self.set_entity_state_client = self.create_client(
            SetEntityState,
            '/gazebo/set_entity_state'
        )
        
        # 状态变量
        self.simulation_running = False
        self.last_joint_state = None
        self.robot_pose = None
        self.error_count = 0
        self.max_errors = 10
        
        # 定时器
        self.status_timer = self.create_timer(
            1.0 / self.update_rate,
            self.status_update_callback
        )
        
        self.monitor_timer = self.create_timer(
            1.0,  # 每秒检查一次
            self.monitor_simulation
        )
        
        # 等待服务可用
        self.wait_for_services()
        
        self.get_logger().info(f"Gazebo仿真器节点已启动，机器人名称: {self.robot_name}")
    
    def wait_for_services(self):
        """等待Gazebo服务可用"""
        self.get_logger().info("等待Gazebo服务...")
        
        # 等待获取实体状态服务
        while not self.get_entity_state_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("等待 /gazebo/get_entity_state 服务...")
        
        # 等待设置实体状态服务
        while not self.set_entity_state_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("等待 /gazebo/set_entity_state 服务...")
        
        self.get_logger().info("Gazebo服务已就绪")
        self.simulation_running = True
    
    def joint_states_callback(self, msg: JointState):
        """关节状态回调函数"""
        self.last_joint_state = msg
        
        # 重置错误计数
        if self.error_count > 0:
            self.error_count = 0
            self.get_logger().info("关节状态恢复正常")
    
    def cmd_vel_callback(self, msg: Twist):
        """速度指令回调函数"""
        # 这里可以添加速度指令处理逻辑
        # 例如将线速度和角速度转换为轮子速度
        pass
    
    def status_update_callback(self):
        """状态更新回调函数"""
        if not self.simulation_running:
            return
        
        try:
            # 获取机器人位姿
            self.update_robot_pose()
            
            # 发布仿真状态
            status_msg = String()
            if self.error_count < self.max_errors:
                status_msg.data = "running"
            else:
                status_msg.data = "error"
            
            self.sim_status_pub.publish(status_msg)
            
        except Exception as e:
            self.handle_error(f"状态更新错误: {e}")
    
    def update_robot_pose(self):
        """更新机器人位姿"""
        try:
            # 创建服务请求
            request = GetEntityState.Request()
            request.name = self.robot_name
            request.reference_frame = "world"
            
            # 调用服务
            future = self.get_entity_state_client.call_async(request)
            
            # 使用线程处理响应，避免阻塞
            def handle_response():
                try:
                    rclpy.spin_until_future_complete(self, future, timeout_sec=self.timeout)
                    if future.result() is not None:
                        response = future.result()
                        if response.success:
                            # 更新机器人位姿
                            entity_state = EntityState()
                            entity_state.name = self.robot_name
                            entity_state.pose = response.state.pose
                            entity_state.twist = response.state.twist
                            
                            self.robot_pose = entity_state
                            self.robot_pose_pub.publish(entity_state)
                        else:
                            self.handle_error(f"获取机器人状态失败: {response.status_message}")
                    else:
                        self.handle_error("获取机器人状态服务调用失败")
                        
                except Exception as e:
                    self.handle_error(f"处理机器人状态响应时出错: {e}")
            
            # 在单独线程中处理响应
            threading.Thread(target=handle_response, daemon=True).start()
            
        except Exception as e:
            self.handle_error(f"更新机器人位姿时出错: {e}")
    
    def monitor_simulation(self):
        """监控仿真状态"""
        current_time = time.time()
        
        # 检查关节状态是否超时
        if self.last_joint_state is not None:
            joint_time = self.last_joint_state.header.stamp.sec + \
                        self.last_joint_state.header.stamp.nanosec * 1e-9
            
            if current_time - joint_time > self.timeout:
                self.handle_error("关节状态数据超时")
        
        # 检查错误计数
        if self.error_count >= self.max_errors:
            self.get_logger().error("仿真错误过多，可能需要重启")
            self.simulation_running = False
    
    def handle_error(self, error_msg: str):
        """处理错误"""
        self.error_count += 1
        self.get_logger().warn(f"仿真错误 ({self.error_count}/{self.max_errors}): {error_msg}")
        
        if self.error_count >= self.max_errors:
            self.get_logger().error("达到最大错误数，停止仿真监控")
            self.simulation_running = False
    
    def reset_robot_pose(self, x: float = 0.0, y: float = 0.0, z: float = 0.2):
        """重置机器人位姿"""
        try:
            request = SetEntityState.Request()
            
            entity_state = EntityState()
            entity_state.name = self.robot_name
            entity_state.pose.position.x = x
            entity_state.pose.position.y = y
            entity_state.pose.position.z = z
            entity_state.pose.orientation.w = 1.0
            
            request.state = entity_state
            
            future = self.set_entity_state_client.call_async(request)
            rclpy.spin_until_future_complete(self, future, timeout_sec=self.timeout)
            
            if future.result() is not None and future.result().success:
                self.get_logger().info(f"机器人位姿已重置到 ({x}, {y}, {z})")
                return True
            else:
                self.get_logger().error("重置机器人位姿失败")
                return False
                
        except Exception as e:
            self.handle_error(f"重置机器人位姿时出错: {e}")
            return False
    
    def get_simulation_info(self) -> Dict:
        """获取仿真信息"""
        return {
            'running': self.simulation_running,
            'robot_name': self.robot_name,
            'error_count': self.error_count,
            'last_joint_state_time': self.last_joint_state.header.stamp if self.last_joint_state else None,
            'robot_pose': self.robot_pose
        }


def main(args=None):
    """主函数"""
    rclpy.init(args=args)
    
    try:
        gazebo_simulator = GazeboSimulator()
        
        # 多线程执行器
        executor = rclpy.executors.MultiThreadedExecutor()
        executor.add_node(gazebo_simulator)
        
        try:
            executor.spin()
        except KeyboardInterrupt:
            gazebo_simulator.get_logger().info("收到中断信号，正在关闭...")
        finally:
            gazebo_simulator.destroy_node()
            
    except Exception as e:
        print(f"启动Gazebo仿真器节点失败: {e}")
    finally:
        rclpy.shutdown()


if __name__ == '__main__':
    main()