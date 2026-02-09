#!/usr/bin/env python3
"""
ROS2集成控制面板

基于PyQt5的图形用户界面，集成ROS2通信功能，用于控制和监控轮腿机器人。
"""

import sys
import os
import math
import time
import threading
from pathlib import Path
from typing import Dict, Optional, List

import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QLabel, QSlider, QPushButton, QTextEdit, QTabWidget,
    QGroupBox, QProgressBar, QSpinBox, QDoubleSpinBox, QComboBox,
    QTableWidget, QTableWidgetItem, QSplitter, QFrame, QCheckBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject, pyqtSlot
from PyQt5.QtGui import QFont, QPalette, QColor, QPixmap, QPainter, QPen

# ROS2消息类型
from sensor_msgs.msg import JointState, Imu
from std_msgs.msg import Float64MultiArray, Header, Bool
from geometry_msgs.msg import Twist, Vector3, Quaternion
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from control_msgs.msg import JointTrajectoryControllerState
from std_srvs.srv import SetBool, Trigger

# 添加源码路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

try:
    from wheel_legged_control.core.urdf_loader import URDFLoader
    from wheel_legged_control.interfaces.joint_interface import (
        JointStatePublisher, JointCommandSubscriber, QoSConfig
    )
except ImportError as e:
    print(f"警告: 无法导入模块: {e}")


class ROS2Worker(QObject):
    """ROS2工作线程"""
    
    # 信号定义
    joint_state_received = pyqtSignal(dict)
    imu_data_received = pyqtSignal(dict)
    controller_state_received = pyqtSignal(dict)
    connection_status_changed = pyqtSignal(bool)
    log_message = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.node = None
        self.executor = None
        self.running = False
        
        # 订阅器
        self.joint_state_subscriber = None
        self.imu_subscriber = None
        self.controller_state_subscriber = None
        
        # 发布器
        self.joint_command_publisher = None
        
        # 服务客户端
        self.emergency_stop_client = None
        self.reset_client = None
        self.enable_client = None
        
    def initialize_ros2(self):
        """初始化ROS2"""
        try:
            if not rclpy.ok():
                rclpy.init()
            
            self.node = Node('wheel_legged_control_panel')
            self.executor = MultiThreadedExecutor()
            self.executor.add_node(self.node)
            
            # 创建订阅器
            self._create_subscribers()
            
            # 创建发布器
            self._create_publishers()
            
            # 创建服务客户端
            self._create_service_clients()
            
            self.running = True
            self.connection_status_changed.emit(True)
            self.log_message.emit("✅ ROS2节点初始化成功")
            
        except Exception as e:
            self.log_message.emit(f"❌ ROS2初始化失败: {e}")
            self.connection_status_changed.emit(False)
    
    def _create_subscribers(self):
        """创建订阅器"""
        # QoS配置
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
            depth=10
        )
        
        # 关节状态订阅器
        self.joint_state_subscriber = self.node.create_subscription(
            JointState,
            '/joint_states',
            self._joint_state_callback,
            qos_profile
        )
        
        # IMU数据订阅器
        self.imu_subscriber = self.node.create_subscription(
            Imu,
            '/imu/data',
            self._imu_callback,
            qos_profile
        )
        
        # 控制器状态订阅器
        self.controller_state_subscriber = self.node.create_subscription(
            JointTrajectoryControllerState,
            '/joint_controller_state',
            self._controller_state_callback,
            qos_profile
        )
        
        self.log_message.emit("📡 ROS2订阅器创建完成")
    
    def _create_publishers(self):
        """创建发布器"""
        # QoS配置
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
            depth=10
        )
        
        # 关节指令发布器
        self.joint_command_publisher = self.node.create_publisher(
            Float64MultiArray,
            '/joint_commands',
            qos_profile
        )
        
        self.log_message.emit("📤 ROS2发布器创建完成")
    
    def _create_service_clients(self):
        """创建服务客户端"""
        # 紧急停止服务
        self.emergency_stop_client = self.node.create_client(
            Trigger,
            '/joint_controller/emergency_stop'
        )
        
        # 复位服务
        self.reset_client = self.node.create_client(
            Trigger,
            '/joint_controller/reset'
        )
        
        # 使能服务
        self.enable_client = self.node.create_client(
            SetBool,
            '/joint_controller/enable'
        )
        
        self.log_message.emit("🔧 ROS2服务客户端创建完成")
    
    def _joint_state_callback(self, msg: JointState):
        """关节状态回调"""
        joint_data = {}
        for i, name in enumerate(msg.name):
            joint_data[name] = {
                'position': msg.position[i] if i < len(msg.position) else 0.0,
                'velocity': msg.velocity[i] if i < len(msg.velocity) else 0.0,
                'effort': msg.effort[i] if i < len(msg.effort) else 0.0
            }
        
        self.joint_state_received.emit(joint_data)
    
    def _imu_callback(self, msg: Imu):
        """IMU数据回调"""
        imu_data = {
            'orientation': {
                'x': msg.orientation.x,
                'y': msg.orientation.y,
                'z': msg.orientation.z,
                'w': msg.orientation.w
            },
            'angular_velocity': {
                'x': msg.angular_velocity.x,
                'y': msg.angular_velocity.y,
                'z': msg.angular_velocity.z
            },
            'linear_acceleration': {
                'x': msg.linear_acceleration.x,
                'y': msg.linear_acceleration.y,
                'z': msg.linear_acceleration.z
            }
        }
        
        self.imu_data_received.emit(imu_data)
    
    def _controller_state_callback(self, msg: JointTrajectoryControllerState):
        """控制器状态回调"""
        controller_data = {
            'joint_names': msg.joint_names,
            'desired_positions': list(msg.desired.positions),
            'actual_positions': list(msg.actual.positions),
            'error_positions': list(msg.error.positions)
        }
        
        self.controller_state_received.emit(controller_data)
    
    def publish_joint_commands(self, joint_positions: List[float]):
        """发布关节指令"""
        if self.joint_command_publisher:
            msg = Float64MultiArray()
            msg.data = joint_positions
            self.joint_command_publisher.publish(msg)
    
    def call_emergency_stop(self):
        """调用紧急停止服务"""
        if self.emergency_stop_client and self.emergency_stop_client.service_is_ready():
            request = Trigger.Request()
            future = self.emergency_stop_client.call_async(request)
            return future
        return None
    
    def call_reset(self):
        """调用复位服务"""
        if self.reset_client and self.reset_client.service_is_ready():
            request = Trigger.Request()
            future = self.reset_client.call_async(request)
            return future
        return None
    
    def call_enable(self, enable: bool):
        """调用使能服务"""
        if self.enable_client and self.enable_client.service_is_ready():
            request = SetBool.Request()
            request.data = enable
            future = self.enable_client.call_async(request)
            return future
        return None
    
    def spin(self):
        """运行ROS2事件循环"""
        if self.executor and self.running:
            try:
                self.executor.spin()
            except Exception as e:
                self.log_message.emit(f"❌ ROS2执行器错误: {e}")
    
    def shutdown(self):
        """关闭ROS2"""
        self.running = False
        if self.executor:
            self.executor.shutdown()
        if self.node:
            self.node.destroy_node()
        self.connection_status_changed.emit(False)
        self.log_message.emit("🔌 ROS2连接已断开")


class IMUVisualizationWidget(QWidget):
    """IMU数据可视化组件"""
    
    def __init__(self):
        super().__init__()
        self.imu_data = {}
        self.setMinimumSize(300, 200)
        self.setStyleSheet("background-color: #2b2b2b; border: 1px solid #555;")
        
    def update_imu_data(self, imu_data: Dict):
        """更新IMU数据"""
        self.imu_data = imu_data
        self.update()
        
    def paintEvent(self, event):
        """绘制IMU数据"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # 绘制标题
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawText(10, 20, "IMU数据")
        
        if not self.imu_data:
            painter.drawText(10, 50, "等待IMU数据...")
            return
        
        # 绘制姿态信息
        y_offset = 50
        if 'orientation' in self.imu_data:
            quat = self.imu_data['orientation']
            # 简化的欧拉角转换
            roll = math.atan2(2*(quat['w']*quat['x'] + quat['y']*quat['z']),
                             1 - 2*(quat['x']**2 + quat['y']**2))
            pitch = math.asin(2*(quat['w']*quat['y'] - quat['z']*quat['x']))
            yaw = math.atan2(2*(quat['w']*quat['z'] + quat['x']*quat['y']),
                            1 - 2*(quat['y']**2 + quat['z']**2))
            
            painter.drawText(10, y_offset, f"Roll: {math.degrees(roll):.1f}°")
            painter.drawText(10, y_offset + 20, f"Pitch: {math.degrees(pitch):.1f}°")
            painter.drawText(10, y_offset + 40, f"Yaw: {math.degrees(yaw):.1f}°")
            y_offset += 70
        
        # 绘制角速度
        if 'angular_velocity' in self.imu_data:
            ang_vel = self.imu_data['angular_velocity']
            painter.drawText(10, y_offset, f"ωx: {ang_vel['x']:.2f} rad/s")
            painter.drawText(10, y_offset + 20, f"ωy: {ang_vel['y']:.2f} rad/s")
            painter.drawText(10, y_offset + 40, f"ωz: {ang_vel['z']:.2f} rad/s")


class ROS2ControlPanelMainWindow(QMainWindow):
    """ROS2集成主控制面板窗口"""
    
    def __init__(self):
        super().__init__()
        self.robot_model = None
        self.joint_controls = {}
        self.current_joint_angles = {}
        self.received_joint_states = {}
        self.imu_data = {}
        self.ros2_connected = False
        
        # ROS2工作线程
        self.ros2_thread = QThread()
        self.ros2_worker = ROS2Worker()
        self.ros2_worker.moveToThread(self.ros2_thread)
        
        # 连接信号
        self.ros2_worker.joint_state_received.connect(self.on_joint_state_received)
        self.ros2_worker.imu_data_received.connect(self.on_imu_data_received)
        self.ros2_worker.controller_state_received.connect(self.on_controller_state_received)
        self.ros2_worker.connection_status_changed.connect(self.on_connection_status_changed)
        self.ros2_worker.log_message.connect(self.add_log)
        
        self.ros2_thread.started.connect(self.ros2_worker.initialize_ros2)
        
        self.setup_ui()
        self.load_robot_model()
        self.setup_timer()
        
        # 启动ROS2线程
        self.ros2_thread.start()
        
        # 启动ROS2事件循环
        self.ros2_spin_thread = threading.Thread(target=self.ros2_worker.spin, daemon=True)
        self.ros2_spin_thread.start()
        
    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("轮腿机器人孪生控制系统 - ROS2控制面板 v0.2.0")
        self.setGeometry(100, 100, 1400, 900)
        
        # 设置深色主题
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #404040;
                border: 1px solid #555555;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #606060;
            }
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #c4c4c4);
                margin: 2px 0;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);
                border: 1px solid #5c5c5c;
                width: 18px;
                margin: -2px 0;
                border-radius: 3px;
            }
            QCheckBox {
                color: #ffffff;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #404040;
                border: 1px solid #555555;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                border: 1px solid #555555;
            }
        """)
        
        # 中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout()
        
        # 左侧面板
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel, 1)
        
        # 中间面板
        middle_panel = self.create_middle_panel()
        main_layout.addWidget(middle_panel, 2)
        
        # 右侧面板
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, 1)
        
        central_widget.setLayout(main_layout)
        
        # 状态栏
        self.statusBar().showMessage("轮腿机器人孪生控制系统已启动 - 等待ROS2连接")
        
    def create_left_panel(self):
        """创建左侧控制面板"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # ROS2连接控制
        ros2_group = QGroupBox("ROS2连接")
        ros2_layout = QVBoxLayout()
        
        self.connection_status_label = QLabel("🔴 未连接")
        ros2_layout.addWidget(self.connection_status_label)
        
        self.auto_send_checkbox = QCheckBox("自动发送关节指令")
        self.auto_send_checkbox.setChecked(True)
        ros2_layout.addWidget(self.auto_send_checkbox)
        
        ros2_group.setLayout(ros2_layout)
        layout.addWidget(ros2_group)
        
        # 关节控制区域
        joint_group = QGroupBox("关节控制")
        joint_layout = QVBoxLayout()
        
        # 这里会在加载机器人模型后动态添加关节控制器
        self.joint_control_layout = joint_layout
        joint_group.setLayout(joint_layout)
        layout.addWidget(joint_group)
        
        # 控制按钮
        button_group = QGroupBox("控制操作")
        button_layout = QGridLayout()
        
        self.reset_button = QPushButton("复位关节")
        self.reset_button.clicked.connect(self.reset_joints)
        
        self.demo_button = QPushButton("演示步态")
        self.demo_button.clicked.connect(self.demo_gait)
        
        self.stop_button = QPushButton("紧急停止")
        self.stop_button.clicked.connect(self.emergency_stop)
        self.stop_button.setStyleSheet("QPushButton { background-color: #cc4444; }")
        
        self.enable_button = QPushButton("启用控制器")
        self.enable_button.clicked.connect(self.toggle_controller)
        self.controller_enabled = False
        
        button_layout.addWidget(self.reset_button, 0, 0)
        button_layout.addWidget(self.demo_button, 0, 1)
        button_layout.addWidget(self.enable_button, 1, 0)
        button_layout.addWidget(self.stop_button, 1, 1)
        
        button_group.setLayout(button_layout)
        layout.addWidget(button_group)
        
        panel.setLayout(layout)
        return panel
        
    def create_middle_panel(self):
        """创建中间显示面板"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # 机器人可视化
        from .control_panel import RobotVisualizationWidget
        viz_group = QGroupBox("机器人可视化")
        viz_layout = QVBoxLayout()
        
        self.robot_viz = RobotVisualizationWidget()
        viz_layout.addWidget(self.robot_viz)
        
        viz_group.setLayout(viz_layout)
        layout.addWidget(viz_group)
        
        # 数据表格
        data_group = QGroupBox("关节数据")
        data_layout = QVBoxLayout()
        
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(5)
        self.data_table.setHorizontalHeaderLabels(["关节名称", "指令角度", "实际角度", "误差", "状态"])
        data_layout.addWidget(self.data_table)
        
        data_group.setLayout(data_layout)
        layout.addWidget(data_group)
        
        panel.setLayout(layout)
        return panel
        
    def create_right_panel(self):
        """创建右侧状态面板"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # IMU数据可视化
        imu_group = QGroupBox("IMU传感器")
        imu_layout = QVBoxLayout()
        
        self.imu_viz = IMUVisualizationWidget()
        imu_layout.addWidget(self.imu_viz)
        
        imu_group.setLayout(imu_layout)
        layout.addWidget(imu_group)
        
        # 系统状态
        status_group = QGroupBox("系统状态")
        status_layout = QGridLayout()
        
        self.simulation_status = QLabel("⏸️ 未启动")
        self.control_mode = QLabel("手动模式")
        self.joint_count_label = QLabel("0")
        
        status_layout.addWidget(QLabel("仿真状态:"), 0, 0)
        status_layout.addWidget(self.simulation_status, 0, 1)
        status_layout.addWidget(QLabel("控制模式:"), 1, 0)
        status_layout.addWidget(self.control_mode, 1, 1)
        status_layout.addWidget(QLabel("关节数量:"), 2, 0)
        status_layout.addWidget(self.joint_count_label, 2, 1)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # 日志区域
        log_group = QGroupBox("系统日志")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setStyleSheet("background-color: #1e1e1e; color: #ffffff; font-family: monospace;")
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        panel.setLayout(layout)
        return panel
        
    def load_robot_model(self):
        """加载机器人模型"""
        try:
            # 使用新的model目录中的RM模型
            robot_urdf = "src/model/RM_Serial_Wheeled-leg_Robot/urdf/RM_Serial_Wheeled-leg_Robot.urdf"
            if not Path(robot_urdf).exists():
                self.add_log("❌ 机器人URDF文件不存在")
                return
                
            loader = URDFLoader()
            self.robot_model = loader.load_urdf(robot_urdf)
            
            # 创建关节控制器
            self.create_joint_controls()
            
            # 更新数据表格
            self.update_data_table()
            
            self.joint_count_label.setText(str(len(self.robot_model.joints)))
            self.add_log(f"✅ 成功加载机器人模型: {self.robot_model.name}")
            
        except Exception as e:
            self.add_log(f"❌ 加载机器人模型失败: {e}")
            
    def create_joint_controls(self):
        """创建关节控制器"""
        if not self.robot_model:
            return
            
        # 清除现有控制器
        for i in reversed(range(self.joint_control_layout.count())):
            self.joint_control_layout.itemAt(i).widget().setParent(None)
            
        # 为每个关节创建控制器
        from .control_panel import JointControlWidget
        for joint_name, joint_info in self.robot_model.joints.items():
            min_angle = joint_info.limit_lower if joint_info.limit_lower else -math.pi
            max_angle = joint_info.limit_upper if joint_info.limit_upper else math.pi
            
            control = JointControlWidget(joint_name, min_angle, max_angle)
            control.joint_changed.connect(self.on_joint_changed)
            
            self.joint_controls[joint_name] = control
            self.joint_control_layout.addWidget(control)
            self.current_joint_angles[joint_name] = 0.0
            
    @pyqtSlot(str, float)
    def on_joint_changed(self, joint_name: str, angle: float):
        """关节角度改变"""
        self.current_joint_angles[joint_name] = angle
        
        # 更新可视化
        angle_degrees = {name: math.degrees(angle) for name, angle in self.current_joint_angles.items()}
        self.robot_viz.update_joint_angles(angle_degrees)
        
        # 更新数据表格
        self.update_data_table()
        
        # 自动发送ROS2指令
        if self.auto_send_checkbox.isChecked() and self.ros2_connected:
            self.send_joint_commands()
            
    @pyqtSlot(dict)
    def on_joint_state_received(self, joint_data: Dict):
        """接收到关节状态"""
        self.received_joint_states = joint_data
        self.update_data_table()
        
        # 更新可视化（使用实际关节状态）
        angle_degrees = {name: math.degrees(data['position']) 
                        for name, data in joint_data.items()}
        self.robot_viz.update_joint_angles(angle_degrees)
        
    @pyqtSlot(dict)
    def on_imu_data_received(self, imu_data: Dict):
        """接收到IMU数据"""
        self.imu_data = imu_data
        self.imu_viz.update_imu_data(imu_data)
        
    @pyqtSlot(dict)
    def on_controller_state_received(self, controller_data: Dict):
        """接收到控制器状态"""
        # 可以在这里处理控制器状态信息
        pass
        
    @pyqtSlot(bool)
    def on_connection_status_changed(self, connected: bool):
        """连接状态改变"""
        self.ros2_connected = connected
        if connected:
            self.connection_status_label.setText("🟢 已连接")
            self.simulation_status.setText("▶️ 运行中")
            self.statusBar().showMessage("ROS2连接已建立")
        else:
            self.connection_status_label.setText("🔴 未连接")
            self.simulation_status.setText("⏸️ 已停止")
            self.statusBar().showMessage("ROS2连接断开")
            
    @pyqtSlot(str)
    def add_log(self, message: str):
        """添加日志"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
    def send_joint_commands(self):
        """发送关节指令"""
        if not self.ros2_connected or not self.robot_model:
            return
            
        # 按关节名称排序确保一致性
        joint_names = sorted(self.current_joint_angles.keys())
        positions = [self.current_joint_angles[name] for name in joint_names]
        
        self.ros2_worker.publish_joint_commands(positions)
        
    def update_data_table(self):
        """更新数据表格"""
        if not self.robot_model:
            return
            
        self.data_table.setRowCount(len(self.robot_model.joints))
        
        for row, joint_name in enumerate(sorted(self.robot_model.joints.keys())):
            command_angle = self.current_joint_angles.get(joint_name, 0.0)
            actual_data = self.received_joint_states.get(joint_name, {})
            actual_angle = actual_data.get('position', 0.0)
            error = command_angle - actual_angle
            
            self.data_table.setItem(row, 0, QTableWidgetItem(joint_name))
            self.data_table.setItem(row, 1, QTableWidgetItem(f"{math.degrees(command_angle):.1f}°"))
            self.data_table.setItem(row, 2, QTableWidgetItem(f"{math.degrees(actual_angle):.1f}°"))
            self.data_table.setItem(row, 3, QTableWidgetItem(f"{math.degrees(error):.1f}°"))
            
            # 状态判断
            if abs(error) < 0.1:  # 小于5.7度
                status = "正常"
            elif abs(error) < 0.2:  # 小于11.5度
                status = "偏差"
            else:
                status = "异常"
            self.data_table.setItem(row, 4, QTableWidgetItem(status))
            
    def reset_joints(self):
        """复位所有关节"""
        if self.ros2_connected:
            # 调用ROS2服务
            future = self.ros2_worker.call_reset()
            if future:
                self.add_log("📡 发送复位指令到ROS2服务")
        
        # 本地复位
        for joint_name, control in self.joint_controls.items():
            control.set_angle(0.0)
            self.current_joint_angles[joint_name] = 0.0
            
        self.robot_viz.update_joint_angles({name: 0.0 for name in self.current_joint_angles.keys()})
        self.update_data_table()
        self.add_log("✅ 本地关节已复位")
        
    def demo_gait(self):
        """演示步态"""
        self.add_log("🎬 开始步态演示...")
        
        # 简单的步态序列
        gait_sequence = [
            {"lf0_Joint": 30, "lf1_Joint": -45, "rf0_Joint": 0, "rf1_Joint": 0},
            {"lf0_Joint": -15, "lf1_Joint": -30, "rf0_Joint": 0, "rf1_Joint": 0},
            {"lf0_Joint": 0, "lf1_Joint": 0, "rf0_Joint": 0, "rf1_Joint": 0},
            {"lf0_Joint": 0, "lf1_Joint": 0, "rf0_Joint": -30, "rf1_Joint": 45},
            {"lf0_Joint": 0, "lf1_Joint": 0, "rf0_Joint": 15, "rf1_Joint": 30},
            {"lf0_Joint": 0, "lf1_Joint": 0, "rf0_Joint": 0, "rf1_Joint": 0},
        ]
        
        # 设置最后状态
        if gait_sequence:
            final_pose = gait_sequence[-1]
            for joint_name, angle_deg in final_pose.items():
                if joint_name in self.joint_controls:
                    self.joint_controls[joint_name].set_angle(math.radians(angle_deg))
                    
        self.add_log("✅ 步态演示完成")
        
    def emergency_stop(self):
        """紧急停止"""
        if self.ros2_connected:
            # 调用ROS2服务
            future = self.ros2_worker.call_emergency_stop()
            if future:
                self.add_log("🛑 发送紧急停止指令到ROS2服务")
        
        # 本地停止
        self.reset_joints()
        self.add_log("🛑 紧急停止 - 所有关节已复位")
        
    def toggle_controller(self):
        """切换控制器使能状态"""
        if self.ros2_connected:
            new_state = not self.controller_enabled
            future = self.ros2_worker.call_enable(new_state)
            if future:
                self.controller_enabled = new_state
                if new_state:
                    self.enable_button.setText("禁用控制器")
                    self.add_log("✅ 控制器已启用")
                else:
                    self.enable_button.setText("启用控制器")
                    self.add_log("⏸️ 控制器已禁用")
        
    def setup_timer(self):
        """设置定时器"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.periodic_update)
        self.timer.start(100)  # 10Hz更新
        
    def periodic_update(self):
        """定期更新"""
        # 定期发送关节指令（如果启用自动发送）
        if (self.auto_send_checkbox.isChecked() and 
            self.ros2_connected and 
            self.controller_enabled):
            self.send_joint_commands()
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.add_log("🔌 正在关闭ROS2连接...")
        self.ros2_worker.shutdown()
        self.ros2_thread.quit()
        self.ros2_thread.wait()
        event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName("轮腿机器人孪生控制系统")
    app.setApplicationVersion("0.2.0")
    app.setOrganizationName("轮腿机器人项目团队")
    
    # 创建主窗口
    window = ROS2ControlPanelMainWindow()
    window.show()
    
    # 启动应用
    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        print("程序被用户中断")
    finally:
        # 确保ROS2正确关闭
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()