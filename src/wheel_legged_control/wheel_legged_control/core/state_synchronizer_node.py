#!/usr/bin/env python3
"""
状态同步器ROS2节点

提供状态同步功能的ROS2节点，包括：
- 虚拟和物理状态的订阅和同步
- 同步质量监控和报告
- 状态校正和错误处理
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from rclpy.executors import MultiThreadedExecutor
import threading
import time
import json
from typing import Dict, Optional

# ROS2消息类型
from sensor_msgs.msg import JointState, Imu
from std_msgs.msg import String, Float64MultiArray, Header
from geometry_msgs.msg import Twist
from std_srvs.srv import Trigger, SetBool

# 导入状态同步器
from .state_synchronizer import (
    StateSynchronizer, SyncConfig, RobotStateSnapshot,
    create_robot_state_from_joint_state, SyncState
)


class StateSynchronizerNode(Node):
    """状态同步器ROS2节点"""
    
    def __init__(self):
        super().__init__('state_synchronizer')
        
        # 声明参数
        self.declare_parameters(
            namespace='',
            parameters=[
                ('network_delay_mean', 0.05),
                ('network_delay_std', 0.01),
                ('packet_loss_rate', 0.01),
                ('sync_frequency', 20.0),
                ('max_sync_error', 0.1),
                ('correction_gain', 0.5),
                ('publish_quality_rate', 1.0),
                ('auto_correction', True),
                ('log_level', 'INFO')
            ]
        )
        
        # 获取参数
        self.config = SyncConfig(
            network_delay_mean=self.get_parameter('network_delay_mean').value,
            network_delay_std=self.get_parameter('network_delay_std').value,
            packet_loss_rate=self.get_parameter('packet_loss_rate').value,
            sync_frequency=self.get_parameter('sync_frequency').value,
            max_sync_error=self.get_parameter('max_sync_error').value,
            correction_gain=self.get_parameter('correction_gain').value
        )
        
        self.publish_quality_rate = self.get_parameter('publish_quality_rate').value
        self.auto_correction = self.get_parameter('auto_correction').value
        
        # 创建状态同步器
        self.synchronizer = StateSynchronizer(self.config)
        
        # 状态缓存
        self.latest_joint_state: Optional[JointState] = None
        self.latest_imu_state: Optional[Imu] = None
        self.last_sync_time = time.time()
        
        # QoS配置
        self.qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
            depth=10
        )
        
        # 创建订阅器
        self._create_subscribers()
        
        # 创建发布器
        self._create_publishers()
        
        # 创建服务
        self._create_services()
        
        # 创建定时器
        self._create_timers()
        
        # 线程锁
        self.lock = threading.RLock()
        
        self.get_logger().info('状态同步器节点已启动')
        self.get_logger().info(f'同步频率: {self.config.sync_frequency} Hz')
        self.get_logger().info(f'网络延迟: {self.config.network_delay_mean}±{self.config.network_delay_std} s')
        self.get_logger().info(f'丢包率: {self.config.packet_loss_rate:.1%}')
    
    def _create_subscribers(self):
        """创建订阅器"""
        # 虚拟关节状态订阅器
        self.virtual_joint_subscriber = self.create_subscription(
            JointState,
            '/virtual/joint_states',
            self.virtual_joint_state_callback,
            self.qos_profile
        )
        
        # 物理关节状态订阅器（模拟）
        self.physical_joint_subscriber = self.create_subscription(
            JointState,
            '/joint_states',
            self.physical_joint_state_callback,
            self.qos_profile
        )
        
        # 虚拟IMU订阅器
        self.virtual_imu_subscriber = self.create_subscription(
            Imu,
            '/virtual/imu/data',
            self.virtual_imu_callback,
            self.qos_profile
        )
        
        # 物理IMU订阅器（模拟）
        self.physical_imu_subscriber = self.create_subscription(
            Imu,
            '/imu/data',
            self.physical_imu_callback,
            self.qos_profile
        )
    
    def _create_publishers(self):
        """创建发布器"""
        # 同步质量报告发布器
        self.quality_publisher = self.create_publisher(
            String,
            '/sync/quality_report',
            self.qos_profile
        )
        
        # 同步状态发布器
        self.sync_state_publisher = self.create_publisher(
            String,
            '/sync/state',
            self.qos_profile
        )
        
        # 同步误差发布器
        self.sync_error_publisher = self.create_publisher(
            Float64MultiArray,
            '/sync/errors',
            self.qos_profile
        )
        
        # 校正指令发布器
        self.correction_publisher = self.create_publisher(
            JointState,
            '/sync/correction_commands',
            self.qos_profile
        )
    
    def _create_services(self):
        """创建服务"""
        # 重置同步器服务
        self.reset_service = self.create_service(
            Trigger,
            '/sync/reset',
            self.reset_synchronizer_callback
        )
        
        # 获取质量报告服务
        self.quality_report_service = self.create_service(
            Trigger,
            '/sync/get_quality_report',
            self.get_quality_report_callback
        )
        
        # 启用/禁用自动校正服务
        self.auto_correction_service = self.create_service(
            SetBool,
            '/sync/set_auto_correction',
            self.set_auto_correction_callback
        )
        
        # 导出同步数据服务
        self.export_data_service = self.create_service(
            Trigger,
            '/sync/export_data',
            self.export_data_callback
        )
    
    def _create_timers(self):
        """创建定时器"""
        # 同步执行定时器
        sync_period = 1.0 / self.config.sync_frequency
        self.sync_timer = self.create_timer(
            sync_period,
            self.sync_timer_callback
        )
        
        # 质量报告发布定时器
        quality_period = 1.0 / self.publish_quality_rate
        self.quality_timer = self.create_timer(
            quality_period,
            self.quality_timer_callback
        )
    
    def virtual_joint_state_callback(self, msg: JointState):
        """虚拟关节状态回调"""
        with self.lock:
            self.latest_joint_state = msg
            
            # 创建状态快照
            state_snapshot = create_robot_state_from_joint_state(
                msg, self.latest_imu_state
            )
            
            # 更新虚拟状态
            self.synchronizer.update_virtual_state(state_snapshot)
    
    def physical_joint_state_callback(self, msg: JointState):
        """物理关节状态回调（模拟）"""
        with self.lock:
            # 创建状态快照
            state_snapshot = create_robot_state_from_joint_state(
                msg, self.latest_imu_state
            )
            
            # 更新物理状态
            self.synchronizer.update_physical_state(state_snapshot)
    
    def virtual_imu_callback(self, msg: Imu):
        """虚拟IMU回调"""
        with self.lock:
            self.latest_imu_state = msg
    
    def physical_imu_callback(self, msg: Imu):
        """物理IMU回调（模拟）"""
        # 在实际应用中，这里会处理真实的IMU数据
        pass
    
    def sync_timer_callback(self):
        """同步定时器回调"""
        with self.lock:
            try:
                # 执行状态同步
                sync_success = self.synchronizer.perform_synchronization()
                
                # 发布同步状态
                state_msg = String()
                state_msg.data = self.synchronizer.sync_state.value
                self.sync_state_publisher.publish(state_msg)
                
                # 如果启用自动校正且同步失败
                if not sync_success and self.auto_correction:
                    self._handle_sync_failure()
                
                self.last_sync_time = time.time()
                
            except Exception as e:
                self.get_logger().error(f'同步执行失败: {e}')
    
    def quality_timer_callback(self):
        """质量报告定时器回调"""
        try:
            # 获取质量报告
            quality_report = self.synchronizer.get_sync_quality_report()
            
            # 发布质量报告
            quality_msg = String()
            quality_msg.data = json.dumps(quality_report, indent=2)
            self.quality_publisher.publish(quality_msg)
            
            # 发布同步误差
            if 'quality_metrics' in quality_report:
                error_msg = Float64MultiArray()
                error_msg.data = [
                    quality_report['quality_metrics']['avg_sync_error'],
                    quality_report['quality_metrics']['max_sync_error'],
                    quality_report['quality_metrics']['sync_success_rate'],
                    quality_report['quality_metrics']['avg_network_delay']
                ]
                self.sync_error_publisher.publish(error_msg)
            
        except Exception as e:
            self.get_logger().error(f'发布质量报告失败: {e}')
    
    def _handle_sync_failure(self):
        """处理同步失败"""
        self.get_logger().warn('检测到同步失败，尝试自动校正')
        
        # 在实际应用中，这里会发送校正指令到物理系统
        # 现在我们只是发布一个校正消息
        if self.latest_joint_state:
            correction_msg = JointState()
            correction_msg.header = Header()
            correction_msg.header.stamp = self.get_clock().now().to_msg()
            correction_msg.header.frame_id = 'correction'
            
            correction_msg.name = self.latest_joint_state.name
            correction_msg.position = self.latest_joint_state.position
            correction_msg.velocity = [0.0] * len(self.latest_joint_state.name)
            correction_msg.effort = [0.0] * len(self.latest_joint_state.name)
            
            self.correction_publisher.publish(correction_msg)
    
    def reset_synchronizer_callback(self, request, response):
        """重置同步器服务回调"""
        try:
            with self.lock:
                self.synchronizer.reset_synchronizer()
                self.latest_joint_state = None
                self.latest_imu_state = None
            
            response.success = True
            response.message = "状态同步器已重置"
            self.get_logger().info("状态同步器已通过服务重置")
            
        except Exception as e:
            response.success = False
            response.message = f"重置失败: {str(e)}"
            self.get_logger().error(f"重置同步器失败: {e}")
        
        return response
    
    def get_quality_report_callback(self, request, response):
        """获取质量报告服务回调"""
        try:
            quality_report = self.synchronizer.get_sync_quality_report()
            
            response.success = True
            response.message = json.dumps(quality_report, indent=2)
            
        except Exception as e:
            response.success = False
            response.message = f"获取质量报告失败: {str(e)}"
            self.get_logger().error(f"获取质量报告失败: {e}")
        
        return response
    
    def set_auto_correction_callback(self, request, response):
        """设置自动校正服务回调"""
        try:
            self.auto_correction = request.data
            
            response.success = True
            response.message = f"自动校正已{'启用' if request.data else '禁用'}"
            self.get_logger().info(f"自动校正已{'启用' if request.data else '禁用'}")
            
        except Exception as e:
            response.success = False
            response.message = f"设置自动校正失败: {str(e)}"
            self.get_logger().error(f"设置自动校正失败: {e}")
        
        return response
    
    def export_data_callback(self, request, response):
        """导出数据服务回调"""
        try:
            timestamp = int(time.time())
            filename = f"/tmp/sync_data_{timestamp}.json"
            
            success = self.synchronizer.export_sync_data(filename)
            
            if success:
                response.success = True
                response.message = f"同步数据已导出到: {filename}"
                self.get_logger().info(f"同步数据已导出到: {filename}")
            else:
                response.success = False
                response.message = "导出同步数据失败"
            
        except Exception as e:
            response.success = False
            response.message = f"导出数据失败: {str(e)}"
            self.get_logger().error(f"导出数据失败: {e}")
        
        return response


def main(args=None):
    """主函数"""
    rclpy.init(args=args)
    
    try:
        # 创建状态同步器节点
        sync_node = StateSynchronizerNode()
        
        # 创建多线程执行器
        executor = MultiThreadedExecutor()
        executor.add_node(sync_node)
        
        sync_node.get_logger().info("状态同步器节点已启动，开始同步...")
        
        try:
            # 运行节点
            executor.spin()
        except KeyboardInterrupt:
            sync_node.get_logger().info("收到中断信号，正在关闭...")
        finally:
            # 清理资源
            sync_node.destroy_node()
            
    except Exception as e:
        print(f"节点启动失败: {e}")
        return 1
    finally:
        rclpy.shutdown()
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())