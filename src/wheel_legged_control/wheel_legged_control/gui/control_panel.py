#!/usr/bin/env python3
"""
轮腿机器人控制面板

基于PyQt5的图形用户界面，用于控制和监控轮腿机器人。
"""

import sys
import os
import math
import time
from pathlib import Path
from typing import Dict, Optional

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QLabel, QSlider, QPushButton, QTextEdit, QTabWidget,
    QGroupBox, QProgressBar, QSpinBox, QDoubleSpinBox, QComboBox,
    QTableWidget, QTableWidgetItem, QSplitter, QFrame
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QPalette, QColor, QPixmap, QPainter, QPen

# 添加源码路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

try:
    from wheel_legged_control.core.urdf_loader import load_robot_from_directory, URDFLoader
except ImportError:
    print("警告: 无法导入URDF加载器，某些功能可能不可用")


class RobotVisualizationWidget(QWidget):
    """机器人可视化组件"""
    
    def __init__(self):
        super().__init__()
        self.joint_angles = {}
        self.setMinimumSize(400, 300)
        self.setStyleSheet("background-color: #2b2b2b; border: 1px solid #555;")
        
    def update_joint_angles(self, angles: Dict[str, float]):
        """更新关节角度"""
        self.joint_angles = angles
        self.update()
        
    def paintEvent(self, event):
        """绘制机器人"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 设置坐标系
        width = self.width()
        height = self.height()
        center_x = width // 2
        center_y = height // 2
        
        # 绘制基座
        painter.setPen(QPen(QColor(100, 150, 255), 3))
        base_rect = (-60, -20, 120, 40)
        painter.drawRect(center_x + base_rect[0], center_y + base_rect[1], 
                        base_rect[2], base_rect[3])
        
        # 绘制文字标签
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawText(center_x - 30, center_y, "base_link")
        
        # 获取关节角度
        lf0_angle = math.radians(self.joint_angles.get('lf0_Joint', 0))
        lf1_angle = math.radians(self.joint_angles.get('lf1_Joint', 0))
        rf0_angle = math.radians(self.joint_angles.get('rf0_Joint', 0))
        rf1_angle = math.radians(self.joint_angles.get('rf1_Joint', 0))
        
        # 绘制左腿
        self._draw_leg(painter, center_x - 30, center_y - 20, lf0_angle, lf1_angle, "L")
        
        # 绘制右腿
        self._draw_leg(painter, center_x + 30, center_y + 20, rf0_angle, rf1_angle, "R")
        
    def _draw_leg(self, painter, start_x, start_y, angle1, angle2, side):
        """绘制腿部"""
        # 第一段腿
        link1_length = 60
        end1_x = start_x + link1_length * math.cos(angle1)
        end1_y = start_y + link1_length * math.sin(angle1)
        
        painter.setPen(QPen(QColor(255, 150, 50), 3))
        painter.drawLine(start_x, start_y, int(end1_x), int(end1_y))
        
        # 关节点
        painter.setPen(QPen(QColor(255, 0, 0), 1))
        painter.drawEllipse(int(end1_x) - 3, int(end1_y) - 3, 6, 6)
        
        # 第二段腿
        link2_length = 80
        total_angle = angle1 + angle2
        end2_x = end1_x + link2_length * math.cos(total_angle)
        end2_y = end1_y + link2_length * math.sin(total_angle)
        
        painter.setPen(QPen(QColor(255, 150, 50), 3))
        painter.drawLine(int(end1_x), int(end1_y), int(end2_x), int(end2_y))
        
        # 轮子
        wheel_radius = 15
        painter.setPen(QPen(QColor(0, 255, 0), 3))
        painter.drawEllipse(int(end2_x) - wheel_radius, int(end2_y) - wheel_radius,
                          wheel_radius * 2, wheel_radius * 2)
        
        # 标签
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawText(int(end2_x) - 10, int(end2_y) + 25, f"{side} Wheel")


class JointControlWidget(QWidget):
    """关节控制组件"""
    
    joint_changed = pyqtSignal(str, float)
    
    def __init__(self, joint_name: str, min_angle: float, max_angle: float):
        super().__init__()
        self.joint_name = joint_name
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()
        
        # 关节名称
        name_label = QLabel(self.joint_name)
        name_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(name_label)
        
        # 角度显示
        self.angle_label = QLabel("0.0°")
        self.angle_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.angle_label)
        
        # 滑块
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(int(math.degrees(self.min_angle)))
        self.slider.setMaximum(int(math.degrees(self.max_angle)))
        self.slider.setValue(0)
        self.slider.valueChanged.connect(self.on_slider_changed)
        layout.addWidget(self.slider)
        
        # 范围标签
        range_layout = QHBoxLayout()
        range_layout.addWidget(QLabel(f"{math.degrees(self.min_angle):.0f}°"))
        range_layout.addStretch()
        range_layout.addWidget(QLabel(f"{math.degrees(self.max_angle):.0f}°"))
        layout.addLayout(range_layout)
        
        self.setLayout(layout)
        
    def on_slider_changed(self, value):
        """滑块值改变"""
        angle_deg = value
        self.angle_label.setText(f"{angle_deg:.1f}°")
        self.joint_changed.emit(self.joint_name, math.radians(angle_deg))
        
    def set_angle(self, angle_rad: float):
        """设置角度"""
        angle_deg = math.degrees(angle_rad)
        self.slider.setValue(int(angle_deg))
        self.angle_label.setText(f"{angle_deg:.1f}°")


class StatusWidget(QWidget):
    """状态监控组件"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()
        
        # 系统状态
        status_group = QGroupBox("系统状态")
        status_layout = QGridLayout()
        
        self.connection_status = QLabel("🔴 未连接")
        self.simulation_status = QLabel("⏸️ 未启动")
        self.control_mode = QLabel("手动模式")
        
        status_layout.addWidget(QLabel("连接状态:"), 0, 0)
        status_layout.addWidget(self.connection_status, 0, 1)
        status_layout.addWidget(QLabel("仿真状态:"), 1, 0)
        status_layout.addWidget(self.simulation_status, 1, 1)
        status_layout.addWidget(QLabel("控制模式:"), 2, 0)
        status_layout.addWidget(self.control_mode, 2, 1)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # 机器人信息
        robot_group = QGroupBox("机器人信息")
        robot_layout = QGridLayout()
        
        self.robot_name = QLabel("未加载")
        self.joint_count = QLabel("0")
        self.total_mass = QLabel("0.0 kg")
        
        robot_layout.addWidget(QLabel("机器人名称:"), 0, 0)
        robot_layout.addWidget(self.robot_name, 0, 1)
        robot_layout.addWidget(QLabel("关节数量:"), 1, 0)
        robot_layout.addWidget(self.joint_count, 1, 1)
        robot_layout.addWidget(QLabel("总质量:"), 2, 0)
        robot_layout.addWidget(self.total_mass, 2, 1)
        
        robot_group.setLayout(robot_layout)
        layout.addWidget(robot_group)
        
        # 日志区域
        log_group = QGroupBox("系统日志")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("background-color: #1e1e1e; color: #ffffff; font-family: monospace;")
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def update_robot_info(self, name: str, joint_count: int, mass: float):
        """更新机器人信息"""
        self.robot_name.setText(name)
        self.joint_count.setText(str(joint_count))
        self.total_mass.setText(f"{mass:.2f} kg")
        
    def add_log(self, message: str):
        """添加日志"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
    def update_status(self, connected: bool, simulation_running: bool):
        """更新状态"""
        if connected:
            self.connection_status.setText("🟢 已连接")
        else:
            self.connection_status.setText("🔴 未连接")
            
        if simulation_running:
            self.simulation_status.setText("▶️ 运行中")
        else:
            self.simulation_status.setText("⏸️ 已停止")


class ControlPanelMainWindow(QMainWindow):
    """主控制面板窗口"""
    
    def __init__(self):
        super().__init__()
        self.robot_model = None
        self.joint_controls = {}
        self.current_joint_angles = {}
        self.setup_ui()
        self.load_robot_model()
        self.setup_timer()
        
    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("轮腿机器人孪生控制系统 - 控制面板 v0.1.0")
        self.setGeometry(100, 100, 1200, 800)
        
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
        """)
        
        # 中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout()
        
        # 左侧面板
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel, 1)
        
        # 右侧面板
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, 2)
        
        central_widget.setLayout(main_layout)
        
        # 状态栏
        self.statusBar().showMessage("轮腿机器人孪生控制系统已启动")
        
    def create_left_panel(self):
        """创建左侧控制面板"""
        panel = QWidget()
        layout = QVBoxLayout()
        
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
        
        button_layout.addWidget(self.reset_button, 0, 0)
        button_layout.addWidget(self.demo_button, 0, 1)
        button_layout.addWidget(self.stop_button, 1, 0, 1, 2)
        
        button_group.setLayout(button_layout)
        layout.addWidget(button_group)
        
        # 状态监控
        self.status_widget = StatusWidget()
        layout.addWidget(self.status_widget)
        
        panel.setLayout(layout)
        return panel
        
    def create_right_panel(self):
        """创建右侧显示面板"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # 机器人可视化
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
        self.data_table.setColumnCount(4)
        self.data_table.setHorizontalHeaderLabels(["关节名称", "当前角度", "目标角度", "状态"])
        data_layout.addWidget(self.data_table)
        
        data_group.setLayout(data_layout)
        layout.addWidget(data_group)
        
        panel.setLayout(layout)
        return panel
        
    def load_robot_model(self):
        """加载机器人模型"""
        try:
            # 使用新的model目录中的RM模型
            robot_urdf = "src/model/RM_Serial_Wheeled-leg_Robot/urdf/RM_Serial_Wheeled-leg_Robot.urdf"
            if not Path(robot_urdf).exists():
                self.status_widget.add_log("❌ 机器人URDF文件不存在")
                return
                
            from wheel_legged_control.core.urdf_loader import URDFLoader
            loader = URDFLoader()
            self.robot_model = loader.load_urdf(robot_urdf)
            
            # 更新状态信息
            total_mass = sum(link.mass for link in self.robot_model.links.values())
            self.status_widget.update_robot_info(
                self.robot_model.name,
                len(self.robot_model.joints),
                total_mass
            )
            
            # 创建关节控制器
            self.create_joint_controls()
            
            # 更新数据表格
            self.update_data_table()
            
            self.status_widget.add_log(f"✅ 成功加载机器人模型: {self.robot_model.name}")
            
        except Exception as e:
            self.status_widget.add_log(f"❌ 加载机器人模型失败: {e}")
            
    def create_joint_controls(self):
        """创建关节控制器"""
        if not self.robot_model:
            return
            
        # 清除现有控制器
        for i in reversed(range(self.joint_control_layout.count())):
            self.joint_control_layout.itemAt(i).widget().setParent(None)
            
        # 为每个关节创建控制器
        for joint_name, joint_info in self.robot_model.joints.items():
            min_angle = joint_info.limit_lower if joint_info.limit_lower else -math.pi
            max_angle = joint_info.limit_upper if joint_info.limit_upper else math.pi
            
            control = JointControlWidget(joint_name, min_angle, max_angle)
            control.joint_changed.connect(self.on_joint_changed)
            
            self.joint_controls[joint_name] = control
            self.joint_control_layout.addWidget(control)
            self.current_joint_angles[joint_name] = 0.0
            
    def on_joint_changed(self, joint_name: str, angle: float):
        """关节角度改变"""
        self.current_joint_angles[joint_name] = angle
        
        # 更新可视化
        angle_degrees = {name: math.degrees(angle) for name, angle in self.current_joint_angles.items()}
        self.robot_viz.update_joint_angles(angle_degrees)
        
        # 更新数据表格
        self.update_data_table()
        
        # 添加日志
        self.status_widget.add_log(f"关节 {joint_name} 设置为 {math.degrees(angle):.1f}°")
        
    def update_data_table(self):
        """更新数据表格"""
        if not self.robot_model:
            return
            
        self.data_table.setRowCount(len(self.robot_model.joints))
        
        for row, (joint_name, joint_info) in enumerate(self.robot_model.joints.items()):
            current_angle = self.current_joint_angles.get(joint_name, 0.0)
            
            self.data_table.setItem(row, 0, QTableWidgetItem(joint_name))
            self.data_table.setItem(row, 1, QTableWidgetItem(f"{math.degrees(current_angle):.1f}°"))
            self.data_table.setItem(row, 2, QTableWidgetItem(f"{math.degrees(current_angle):.1f}°"))
            self.data_table.setItem(row, 3, QTableWidgetItem("正常"))
            
    def reset_joints(self):
        """复位所有关节"""
        for joint_name, control in self.joint_controls.items():
            control.set_angle(0.0)
            self.current_joint_angles[joint_name] = 0.0
            
        self.robot_viz.update_joint_angles({name: 0.0 for name in self.current_joint_angles.keys()})
        self.update_data_table()
        self.status_widget.add_log("✅ 所有关节已复位")
        
    def demo_gait(self):
        """演示步态"""
        self.status_widget.add_log("🎬 开始步态演示...")
        
        # 简单的步态序列
        gait_sequence = [
            {"lf0_Joint": 30, "lf1_Joint": -45, "rf0_Joint": 0, "rf1_Joint": 0},
            {"lf0_Joint": -15, "lf1_Joint": -30, "rf0_Joint": 0, "rf1_Joint": 0},
            {"lf0_Joint": 0, "lf1_Joint": 0, "rf0_Joint": 0, "rf1_Joint": 0},
            {"lf0_Joint": 0, "lf1_Joint": 0, "rf0_Joint": -30, "rf1_Joint": 45},
            {"lf0_Joint": 0, "lf1_Joint": 0, "rf0_Joint": 15, "rf1_Joint": 30},
            {"lf0_Joint": 0, "lf1_Joint": 0, "rf0_Joint": 0, "rf1_Joint": 0},
        ]
        
        # 这里应该用QTimer来实现动画，简化版本直接设置最后状态
        if gait_sequence:
            final_pose = gait_sequence[-1]
            for joint_name, angle_deg in final_pose.items():
                if joint_name in self.joint_controls:
                    self.joint_controls[joint_name].set_angle(math.radians(angle_deg))
                    
        self.status_widget.add_log("✅ 步态演示完成")
        
    def emergency_stop(self):
        """紧急停止"""
        self.reset_joints()
        self.status_widget.add_log("🛑 紧急停止 - 所有关节已复位")
        
    def setup_timer(self):
        """设置定时器"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(1000)  # 每秒更新一次
        
    def update_status(self):
        """更新状态"""
        # 模拟状态更新
        self.status_widget.update_status(True, True)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName("轮腿机器人孪生控制系统")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("轮腿机器人项目团队")
    
    # 创建主窗口
    window = ControlPanelMainWindow()
    window.show()
    
    # 启动应用
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()