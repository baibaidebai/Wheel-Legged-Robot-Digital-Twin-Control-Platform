#!/usr/bin/env python3
"""
ROS2通信接口测试脚本
测试关节控制器的ROS2通信功能
"""

import rclpy
from rclpy.node import Node
import numpy as np
import time
import threading
from std_msgs.msg import Float64MultiArray
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration
from std_srvs.srv import Trigger, SetBool


class ROS2InterfaceTester(Node):
    """ROS2接口测试节点"""
    
    def __init__(self):
        super().__init__('ros2_interface_tester')
        
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
        
        # 创建服务客户端
        self.emergency_stop_client = self.create_client(
            Trigger,
            '/joint_controller/emergency_stop'
        )
        
        self.reset_client = self.create_client(
            Trigger,
            '/joint_controller/reset'
        )
        
        self.enable_client = self.create_client(
            SetBool,
            '/joint_controller/enable'
        )
        
        # 状态变量
        self.current_joint_states = None
        self.joint_state_history = []
        self.test_results = {}
        
        self.get_logger().info('ROS2接口测试节点已启动')
    
    def joint_state_callback(self, msg: JointState):
        """关节状态回调"""
        self.current_joint_states = msg
        self.joint_state_history.append({
            'timestamp': time.time(),
            'positions': dict(zip(msg.name, msg.position)),
            'velocities': dict(zip(msg.name, msg.velocity)),
            'efforts': dict(zip(msg.name, msg.effort))
        })
        
        # 保持历史记录在合理范围内
        if len(self.joint_state_history) > 1000:
            self.joint_state_history = self.joint_state_history[-500:]
    
    def wait_for_joint_states(self, timeout=10.0):
        """等待关节状态"""
        start_time = time.time()
        while self.current_joint_states is None:
            rclpy.spin_once(self, timeout_sec=0.1)
            if time.time() - start_time > timeout:
                self.get_logger().error('等待关节状态超时')
                return False
        return True
    
    def wait_for_service(self, client, timeout=5.0):
        """等待服务可用"""
        if not client.wait_for_service(timeout_sec=timeout):
            self.get_logger().error(f'服务 {client.srv_name} 不可用')
            return False
        return True
    
    def test_joint_command_publishing(self):
        """测试关节指令发布"""
        self.get_logger().info('=== 测试关节指令发布 ===')
        
        test_commands = [
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # 零位
            [0.5, -0.3, -0.5, 0.3, 1.0, -1.0],  # 复合运动
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # 回零
        ]
        
        success_count = 0
        
        for i, command in enumerate(test_commands):
            self.get_logger().info(f'发送指令 {i+1}: {command}')
            
            # 记录发送前状态
            initial_states = self.current_joint_states
            
            # 发送指令
            msg = Float64MultiArray()
            msg.data = command
            self.joint_cmd_pub.publish(msg)
            
            # 等待响应
            time.sleep(2.0)
            rclpy.spin_once(self, timeout_sec=0.1)
            
            # 检查是否有状态变化
            if self.current_joint_states and initial_states:
                position_changed = False
                for j, name in enumerate(self.joint_names):
                    if name in dict(zip(self.current_joint_states.name, self.current_joint_states.position)):
                        current_pos = dict(zip(self.current_joint_states.name, self.current_joint_states.position))[name]
                        initial_pos = dict(zip(initial_states.name, initial_states.position)).get(name, 0.0)
                        if abs(current_pos - initial_pos) > 0.01:  # 1cm阈值
                            position_changed = True
                            break
                
                if position_changed:
                    success_count += 1
                    self.get_logger().info(f'指令 {i+1} 执行成功')
                else:
                    self.get_logger().warn(f'指令 {i+1} 可能未执行或变化太小')
            else:
                self.get_logger().warn(f'指令 {i+1} 无法验证执行结果')
        
        success_rate = success_count / len(test_commands)
        self.test_results['joint_command_publishing'] = {
            'success_rate': success_rate,
            'total_tests': len(test_commands),
            'successful_tests': success_count
        }
        
        self.get_logger().info(f'关节指令发布测试完成，成功率: {success_rate:.2%}')
        return success_rate > 0.5
    
    def test_trajectory_publishing(self):
        """测试轨迹发布"""
        self.get_logger().info('=== 测试轨迹发布 ===')
        
        # 创建简单轨迹
        trajectory = JointTrajectory()
        trajectory.joint_names = self.joint_names
        
        # 轨迹点
        points = [
            ([0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 0.0),
            ([0.3, -0.2, -0.3, 0.2, 0.5, -0.5], 2.0),
            ([0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 4.0),
        ]
        
        for positions, time_sec in points:
            point = JointTrajectoryPoint()
            point.positions = positions
            point.time_from_start = Duration(sec=int(time_sec), nanosec=int((time_sec % 1) * 1e9))
            trajectory.points.append(point)
        
        # 记录初始状态
        initial_time = time.time()
        initial_positions = None
        if self.current_joint_states:
            initial_positions = dict(zip(self.current_joint_states.name, self.current_joint_states.position))
        
        # 发布轨迹
        self.trajectory_pub.publish(trajectory)
        self.get_logger().info('轨迹已发布，等待执行...')
        
        # 监控执行过程
        execution_time = 5.0  # 轨迹总时间 + 缓冲
        start_time = time.time()
        position_changes = []
        
        while time.time() - start_time < execution_time:
            rclpy.spin_once(self, timeout_sec=0.1)
            
            if self.current_joint_states:
                current_positions = dict(zip(self.current_joint_states.name, self.current_joint_states.position))
                if initial_positions:
                    max_change = max(abs(current_positions.get(name, 0.0) - initial_positions.get(name, 0.0)) 
                                   for name in self.joint_names if name in current_positions and name in initial_positions)
                    position_changes.append(max_change)
            
            time.sleep(0.1)
        
        # 评估结果
        if position_changes:
            max_change = max(position_changes)
            trajectory_executed = max_change > 0.05  # 5cm阈值
            
            self.test_results['trajectory_publishing'] = {
                'executed': trajectory_executed,
                'max_position_change': max_change,
                'execution_time': execution_time
            }
            
            if trajectory_executed:
                self.get_logger().info(f'轨迹执行成功，最大位置变化: {max_change:.3f}')
                return True
            else:
                self.get_logger().warn(f'轨迹可能未执行，最大位置变化: {max_change:.3f}')
                return False
        else:
            self.get_logger().error('无法监控轨迹执行')
            return False
    
    def test_service_calls(self):
        """测试服务调用"""
        self.get_logger().info('=== 测试服务调用 ===')
        
        service_results = {}
        
        # 测试紧急停止服务
        if self.wait_for_service(self.emergency_stop_client):
            try:
                request = Trigger.Request()
                future = self.emergency_stop_client.call_async(request)
                rclpy.spin_until_future_complete(self, future, timeout_sec=5.0)
                
                if future.result():
                    response = future.result()
                    service_results['emergency_stop'] = {
                        'success': response.success,
                        'message': response.message
                    }
                    self.get_logger().info(f'紧急停止服务: {response.success}, {response.message}')
                else:
                    service_results['emergency_stop'] = {'success': False, 'message': '服务调用超时'}
                    self.get_logger().error('紧急停止服务调用超时')
            except Exception as e:
                service_results['emergency_stop'] = {'success': False, 'message': str(e)}
                self.get_logger().error(f'紧急停止服务调用失败: {e}')
        
        # 等待一段时间
        time.sleep(1.0)
        
        # 测试复位服务
        if self.wait_for_service(self.reset_client):
            try:
                request = Trigger.Request()
                future = self.reset_client.call_async(request)
                rclpy.spin_until_future_complete(self, future, timeout_sec=5.0)
                
                if future.result():
                    response = future.result()
                    service_results['reset'] = {
                        'success': response.success,
                        'message': response.message
                    }
                    self.get_logger().info(f'复位服务: {response.success}, {response.message}')
                else:
                    service_results['reset'] = {'success': False, 'message': '服务调用超时'}
                    self.get_logger().error('复位服务调用超时')
            except Exception as e:
                service_results['reset'] = {'success': False, 'message': str(e)}
                self.get_logger().error(f'复位服务调用失败: {e}')
        
        # 测试使能服务
        if self.wait_for_service(self.enable_client):
            for enable_state in [False, True]:  # 先禁用再启用
                try:
                    request = SetBool.Request()
                    request.data = enable_state
                    future = self.enable_client.call_async(request)
                    rclpy.spin_until_future_complete(self, future, timeout_sec=5.0)
                    
                    if future.result():
                        response = future.result()
                        service_results[f'enable_{enable_state}'] = {
                            'success': response.success,
                            'message': response.message
                        }
                        self.get_logger().info(f'使能服务({enable_state}): {response.success}, {response.message}')
                    else:
                        service_results[f'enable_{enable_state}'] = {'success': False, 'message': '服务调用超时'}
                        self.get_logger().error(f'使能服务({enable_state})调用超时')
                except Exception as e:
                    service_results[f'enable_{enable_state}'] = {'success': False, 'message': str(e)}
                    self.get_logger().error(f'使能服务({enable_state})调用失败: {e}')
                
                time.sleep(0.5)
        
        self.test_results['service_calls'] = service_results
        
        # 计算成功率
        successful_services = sum(1 for result in service_results.values() if result.get('success', False))
        total_services = len(service_results)
        success_rate = successful_services / total_services if total_services > 0 else 0.0
        
        self.get_logger().info(f'服务调用测试完成，成功率: {success_rate:.2%} ({successful_services}/{total_services})')
        return success_rate > 0.5
    
    def test_joint_state_subscription(self):
        """测试关节状态订阅"""
        self.get_logger().info('=== 测试关节状态订阅 ===')
        
        # 清空历史记录
        self.joint_state_history.clear()
        
        # 监控一段时间
        monitor_duration = 5.0
        start_time = time.time()
        
        while time.time() - start_time < monitor_duration:
            rclpy.spin_once(self, timeout_sec=0.1)
            time.sleep(0.1)
        
        # 分析结果
        if self.joint_state_history:
            message_count = len(self.joint_state_history)
            time_span = self.joint_state_history[-1]['timestamp'] - self.joint_state_history[0]['timestamp']
            frequency = message_count / time_span if time_span > 0 else 0.0
            
            # 检查数据完整性
            complete_messages = 0
            for state in self.joint_state_history:
                if all(name in state['positions'] for name in self.joint_names):
                    complete_messages += 1
            
            completeness = complete_messages / message_count if message_count > 0 else 0.0
            
            self.test_results['joint_state_subscription'] = {
                'message_count': message_count,
                'frequency': frequency,
                'completeness': completeness,
                'monitor_duration': monitor_duration
            }
            
            self.get_logger().info(f'关节状态订阅测试完成:')
            self.get_logger().info(f'  消息数量: {message_count}')
            self.get_logger().info(f'  频率: {frequency:.1f} Hz')
            self.get_logger().info(f'  完整性: {completeness:.2%}')
            
            return frequency > 10.0 and completeness > 0.9  # 期望>10Hz且>90%完整性
        else:
            self.get_logger().error('未收到关节状态消息')
            return False
    
    def generate_test_report(self):
        """生成测试报告"""
        self.get_logger().info('=== 测试报告 ===')
        
        total_tests = 0
        passed_tests = 0
        
        for test_name, result in self.test_results.items():
            total_tests += 1
            
            if test_name == 'joint_command_publishing':
                success = result['success_rate'] > 0.5
                self.get_logger().info(f'{test_name}: {"PASS" if success else "FAIL"} (成功率: {result["success_rate"]:.2%})')
                if success:
                    passed_tests += 1
            
            elif test_name == 'trajectory_publishing':
                success = result['executed']
                self.get_logger().info(f'{test_name}: {"PASS" if success else "FAIL"} (最大变化: {result["max_position_change"]:.3f})')
                if success:
                    passed_tests += 1
            
            elif test_name == 'service_calls':
                successful_services = sum(1 for r in result.values() if r.get('success', False))
                total_services = len(result)
                success = successful_services / total_services > 0.5 if total_services > 0 else False
                self.get_logger().info(f'{test_name}: {"PASS" if success else "FAIL"} ({successful_services}/{total_services})')
                if success:
                    passed_tests += 1
            
            elif test_name == 'joint_state_subscription':
                success = result['frequency'] > 10.0 and result['completeness'] > 0.9
                self.get_logger().info(f'{test_name}: {"PASS" if success else "FAIL"} ({result["frequency"]:.1f}Hz, {result["completeness"]:.2%})')
                if success:
                    passed_tests += 1
        
        overall_success = passed_tests / total_tests if total_tests > 0 else 0.0
        self.get_logger().info(f'总体结果: {passed_tests}/{total_tests} 通过 ({overall_success:.2%})')
        
        return overall_success > 0.75  # 75%通过率
    
    def run_all_tests(self):
        """运行所有测试"""
        self.get_logger().info('开始ROS2接口测试')
        
        # 等待关节状态
        if not self.wait_for_joint_states():
            self.get_logger().error('无法获取关节状态，测试终止')
            return False
        
        try:
            # 运行各项测试
            self.test_joint_state_subscription()
            time.sleep(1.0)
            
            self.test_joint_command_publishing()
            time.sleep(1.0)
            
            self.test_trajectory_publishing()
            time.sleep(1.0)
            
            self.test_service_calls()
            time.sleep(1.0)
            
            # 生成报告
            return self.generate_test_report()
            
        except Exception as e:
            self.get_logger().error(f'测试过程中发生错误: {e}')
            return False


def main(args=None):
    """主函数"""
    rclpy.init(args=args)
    
    try:
        tester = ROS2InterfaceTester()
        
        # 等待系统稳定
        time.sleep(3.0)
        
        # 运行测试
        success = tester.run_all_tests()
        
        if success:
            tester.get_logger().info('🎉 所有ROS2接口测试通过！')
        else:
            tester.get_logger().warn('⚠️ 部分ROS2接口测试失败')
        
        return success
        
    except KeyboardInterrupt:
        print('测试被用户中断')
        return False
    except Exception as e:
        print(f'测试运行错误: {e}')
        return False
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)