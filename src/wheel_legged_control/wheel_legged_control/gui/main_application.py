#!/usr/bin/env python3
"""
轮腿机器人孪生控制系统 - 主应用程序

实现完整的用户界面流程：配置选择页面 → 可视化仿真界面
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, Optional, Any

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QLabel, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
    QGroupBox, QTabWidget, QTextEdit, QProgressBar, QSplitter, QFrame,
    QCheckBox, QSlider, QFileDialog, QMessageBox, QStackedWidget,
    QListWidget, QListWidgetItem, QScrollArea, QFormLayout
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize
from PyQt5.QtGui import QFont, QPalette, QColor, QPixmap, QIcon

# 添加源码路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

try:
    from wheel_legged_control.simulation import (
        SimulationManager, SimulationBackend, SimulationConfig,
        ConfigManager, get_backend_registry, create_simulation_manager
    )
    # 尝试导入算法模块，如果失败则跳过
    try:
        from wheel_legged_control.algorithms import AlgorithmManager, LQRController
    except ImportError as alg_error:
        print(f"警告: 算法模块导入失败 - {alg_error}")
        AlgorithmManager = None
        LQRController = None
        
    from wheel_legged_control.core.urdf_loader import URDFLoader
    from wheel_legged_control.gui.control_panel import RobotVisualizationWidget, JointControlWidget
    
    # 验证URDFLoader是否可用
    if URDFLoader is None:
        raise ImportError("URDFLoader is None")
        
except ImportError as e:
    print(f"警告: 导入模块失败 - {e}")
    
    # 尝试单独导入URDFLoader
    try:
        from wheel_legged_control.core.urdf_loader import URDFLoader
        print("✅ URDFLoader单独导入成功")
    except ImportError as e2:
        print(f"❌ URDFLoader单独导入也失败: {e2}")
        URDFLoader = None


class ConfigurationPage(QWidget):
    """配置选择页面"""
    
    configuration_complete = pyqtSignal(dict)  # 配置完成信号
    
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.backend_registry = get_backend_registry()
        self.selected_config = {}
        self.setup_ui()
        self.load_available_options()
        
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("轮腿机器人孪生控制系统 - 配置选择")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2196F3; margin: 20px;")
        layout.addWidget(title_label)
        
        # 主配置区域
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        
        # 左侧配置选项
        left_panel = self.create_configuration_panel()
        main_layout.addWidget(left_panel, 2)
        
        # 右侧预览和信息
        right_panel = self.create_preview_panel()
        main_layout.addWidget(right_panel, 1)
        
        main_widget.setLayout(main_layout)
        layout.addWidget(main_widget)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.reset_button = QPushButton("重置配置")
        self.reset_button.clicked.connect(self.reset_configuration)
        button_layout.addWidget(self.reset_button)
        
        self.start_button = QPushButton("开始仿真")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.start_button.clicked.connect(self.start_simulation)
        button_layout.addWidget(self.start_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def create_configuration_panel(self):
        """创建配置面板"""
        panel = QScrollArea()
        panel.setWidgetResizable(True)
        
        content_widget = QWidget()
        layout = QVBoxLayout()
        
        # 1. 机器人模型选择
        model_group = QGroupBox("1. 机器人模型选择")
        model_layout = QFormLayout()
        
        self.model_combo = QComboBox()
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        model_layout.addRow("机器人模型:", self.model_combo)
        
        self.model_info_label = QLabel("请选择机器人模型")
        self.model_info_label.setStyleSheet("color: #666; font-style: italic;")
        model_layout.addRow("模型信息:", self.model_info_label)
        
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        # 2. 仿真后端选择
        backend_group = QGroupBox("2. 仿真后端选择")
        backend_layout = QFormLayout()
        
        self.backend_combo = QComboBox()
        self.backend_combo.currentTextChanged.connect(self.on_backend_changed)
        backend_layout.addRow("仿真引擎:", self.backend_combo)
        
        self.backend_info_label = QLabel("请选择仿真后端")
        self.backend_info_label.setStyleSheet("color: #666; font-style: italic;")
        backend_layout.addRow("后端信息:", self.backend_info_label)
        
        backend_group.setLayout(backend_layout)
        layout.addWidget(backend_group)
        
        # 3. 配置档案选择
        profile_group = QGroupBox("3. 配置档案选择")
        profile_layout = QFormLayout()
        
        self.profile_combo = QComboBox()
        self.profile_combo.currentTextChanged.connect(self.on_profile_changed)
        profile_layout.addRow("配置档案:", self.profile_combo)
        
        self.profile_info_label = QLabel("请选择配置档案")
        self.profile_info_label.setStyleSheet("color: #666; font-style: italic;")
        profile_layout.addRow("档案描述:", self.profile_info_label)
        
        profile_group.setLayout(profile_layout)
        layout.addWidget(profile_group)
        
        # 4. 控制算法选择
        algorithm_group = QGroupBox("4. 控制算法选择")
        algorithm_layout = QFormLayout()
        
        self.algorithm_combo = QComboBox()
        self.algorithm_combo.currentTextChanged.connect(self.on_algorithm_changed)
        algorithm_layout.addRow("控制算法:", self.algorithm_combo)
        
        self.algorithm_info_label = QLabel("请选择控制算法")
        self.algorithm_info_label.setStyleSheet("color: #666; font-style: italic;")
        algorithm_layout.addRow("算法描述:", self.algorithm_info_label)
        
        algorithm_group.setLayout(algorithm_layout)
        layout.addWidget(algorithm_group)
        
        # 5. 高级参数设置
        advanced_group = QGroupBox("5. 高级参数设置")
        advanced_layout = QFormLayout()
        
        self.dt_spinbox = QDoubleSpinBox()
        self.dt_spinbox.setRange(0.001, 0.1)
        self.dt_spinbox.setValue(0.001)
        self.dt_spinbox.setSingleStep(0.001)
        self.dt_spinbox.setDecimals(3)
        self.dt_spinbox.setSuffix(" s")
        advanced_layout.addRow("时间步长:", self.dt_spinbox)
        
        self.max_steps_spinbox = QSpinBox()
        self.max_steps_spinbox.setRange(100, 1000000)
        self.max_steps_spinbox.setValue(10000)
        self.max_steps_spinbox.setSingleStep(1000)
        advanced_layout.addRow("最大步数:", self.max_steps_spinbox)
        
        self.enable_rendering_checkbox = QCheckBox("启用渲染")
        self.enable_rendering_checkbox.setChecked(True)
        advanced_layout.addRow("渲染选项:", self.enable_rendering_checkbox)
        
        self.gravity_z_spinbox = QDoubleSpinBox()
        self.gravity_z_spinbox.setRange(-20.0, 0.0)
        self.gravity_z_spinbox.setValue(-9.81)
        self.gravity_z_spinbox.setSingleStep(0.1)
        self.gravity_z_spinbox.setSuffix(" m/s²")
        advanced_layout.addRow("重力加速度:", self.gravity_z_spinbox)
        
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
        
        layout.addStretch()
        content_widget.setLayout(layout)
        panel.setWidget(content_widget)
        
        return panel
        
    def create_preview_panel(self):
        """创建预览面板"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # 配置预览
        preview_group = QGroupBox("配置预览")
        preview_layout = QVBoxLayout()
        
        self.config_preview = QTextEdit()
        self.config_preview.setReadOnly(True)
        self.config_preview.setMaximumHeight(200)
        self.config_preview.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                font-family: monospace;
                font-size: 10px;
            }
        """)
        preview_layout.addWidget(self.config_preview)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # 系统状态
        status_group = QGroupBox("系统状态")
        status_layout = QVBoxLayout()
        
        self.status_list = QListWidget()
        self.status_list.setMaximumHeight(150)
        status_layout.addWidget(self.status_list)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # 帮助信息
        help_group = QGroupBox("使用说明")
        help_layout = QVBoxLayout()
        
        help_text = QLabel("""
        <b>配置步骤:</b><br>
        1. 选择机器人模型文件<br>
        2. 选择仿真后端引擎<br>
        3. 选择预设配置档案<br>
        4. 选择控制算法<br>
        5. 调整高级参数<br>
        6. 点击"开始仿真"
        """)
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: #666; font-size: 11px;")
        help_layout.addWidget(help_text)
        
        help_group.setLayout(help_layout)
        layout.addWidget(help_group)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
        
    def load_available_options(self):
        """加载可用选项"""
        # 加载机器人模型
        self.load_robot_models()
        
        # 加载仿真后端
        self.load_simulation_backends()
        
        # 加载配置档案
        self.load_configuration_profiles()
        
        # 加载控制算法
        self.load_control_algorithms()
        
        # 更新状态
        self.update_system_status()
        
    def load_robot_models(self):
        """加载机器人模型"""
        self.model_combo.clear()
        
        # 扫描模型目录
        model_dirs = [
            "src/model/RM_Serial_Wheeled-leg_Robot",
            "src/model/DM_Wheel_leg_robot"
        ]
        
        for model_dir in model_dirs:
            model_path = Path(model_dir)
            if model_path.exists():
                urdf_files = list(model_path.glob("**/*.urdf"))
                for urdf_file in urdf_files:
                    display_name = f"{model_path.name} - {urdf_file.stem}"
                    self.model_combo.addItem(display_name, str(urdf_file))
        
        if self.model_combo.count() == 0:
            self.model_combo.addItem("未找到机器人模型", "")
            
    def load_simulation_backends(self):
        """加载仿真后端"""
        self.backend_combo.clear()
        
        available_backends = self.backend_registry.get_available_backends()
        for backend in available_backends:
            info = self.backend_registry.get_backend_info(backend)
            display_name = f"{info.name} ({backend.value})"
            self.backend_combo.addItem(display_name, backend.value)
            
        if self.backend_combo.count() == 0:
            self.backend_combo.addItem("无可用后端", "")
            
    def load_configuration_profiles(self):
        """加载配置档案"""
        self.profile_combo.clear()
        
        profiles = self.config_manager.list_profiles()
        
        # 添加默认档案
        for profile in profiles['default']:
            self.profile_combo.addItem(f"[默认] {profile}", f"default:{profile}")
            
        # 添加用户档案
        for profile in profiles['user']:
            self.profile_combo.addItem(f"[用户] {profile}", f"user:{profile}")
            
        if self.profile_combo.count() == 0:
            self.profile_combo.addItem("无可用配置档案", "")
            
    def load_control_algorithms(self):
        """加载控制算法"""
        self.algorithm_combo.clear()
        
        algorithms = [
            ("手动控制", "manual", "用户手动控制关节"),
            ("LQR控制器", "lqr", "线性二次调节器"),
            ("PID控制器", "pid", "比例积分微分控制器"),
            ("强化学习", "rl", "基于PPO的强化学习控制")
        ]
        
        for name, key, desc in algorithms:
            self.algorithm_combo.addItem(name, key)
            
    def on_model_changed(self, text):
        """机器人模型改变"""
        model_path = self.model_combo.currentData()
        if model_path and Path(model_path).exists():
            try:
                # 检查URDFLoader是否可用
                if 'URDFLoader' not in globals() or URDFLoader is None:
                    self.model_info_label.setText("URDFLoader不可用")
                    return
                    
                loader = URDFLoader()
                robot = loader.load_urdf(model_path)
                info = f"关节数: {len(robot.joints)}, 链接数: {len(robot.links)}"
                self.model_info_label.setText(info)
                self.selected_config['model_path'] = model_path
                self.selected_config['model_name'] = robot.name
            except Exception as e:
                self.model_info_label.setText(f"加载失败: {e}")
        else:
            self.model_info_label.setText("无效的模型路径")
            
        self.update_config_preview()
        
    def on_backend_changed(self, text):
        """仿真后端改变"""
        backend_key = self.backend_combo.currentData()
        if backend_key:
            try:
                backend = SimulationBackend(backend_key)
                info = self.backend_registry.get_backend_info(backend)
                desc = f"{info.description} (v{info.version})"
                self.backend_info_label.setText(desc)
                self.selected_config['backend'] = backend_key
            except Exception as e:
                self.backend_info_label.setText(f"后端信息获取失败: {e}")
        else:
            self.backend_info_label.setText("无效的后端")
            
        self.update_config_preview()
        
    def on_profile_changed(self, text):
        """配置档案改变"""
        profile_key = self.profile_combo.currentData()
        if profile_key:
            try:
                profile_type, profile_name = profile_key.split(':', 1)
                if profile_type == 'default':
                    config = self.config_manager.get_default_config(profile_name)
                    desc = f"默认配置档案: {profile_name}"
                else:
                    config = self.config_manager.load_profile(profile_name)
                    desc = f"用户配置档案: {profile_name}"
                    
                self.profile_info_label.setText(desc)
                self.selected_config['profile'] = profile_key
                
                # 更新高级参数
                if config:
                    self.dt_spinbox.setValue(config.dt)
                    self.max_steps_spinbox.setValue(config.max_steps)
                    self.enable_rendering_checkbox.setChecked(config.enable_rendering)
                    self.gravity_z_spinbox.setValue(config.gravity[2])
                    
            except Exception as e:
                self.profile_info_label.setText(f"档案加载失败: {e}")
        else:
            self.profile_info_label.setText("无效的配置档案")
            
        self.update_config_preview()
        
    def on_algorithm_changed(self, text):
        """控制算法改变"""
        algorithm_key = self.algorithm_combo.currentData()
        if algorithm_key:
            algorithm_descriptions = {
                'manual': '用户通过界面手动控制机器人关节',
                'lqr': '线性二次调节器，适用于线性系统控制',
                'pid': '经典PID控制器，适用于位置和速度控制',
                'rl': '基于PPO的强化学习控制，适用于复杂任务'
            }
            desc = algorithm_descriptions.get(algorithm_key, '未知算法')
            self.algorithm_info_label.setText(desc)
            self.selected_config['algorithm'] = algorithm_key
        else:
            self.algorithm_info_label.setText("无效的算法")
            
        self.update_config_preview()
        
    def update_config_preview(self):
        """更新配置预览"""
        config = {
            '机器人模型': self.selected_config.get('model_name', '未选择'),
            '仿真后端': self.selected_config.get('backend', '未选择'),
            '配置档案': self.selected_config.get('profile', '未选择'),
            '控制算法': self.selected_config.get('algorithm', '未选择'),
            '时间步长': f"{self.dt_spinbox.value():.3f} s",
            '最大步数': str(self.max_steps_spinbox.value()),
            '启用渲染': '是' if self.enable_rendering_checkbox.isChecked() else '否',
            '重力加速度': f"{self.gravity_z_spinbox.value():.2f} m/s²"
        }
        
        preview_text = "当前配置:\n" + "="*30 + "\n"
        for key, value in config.items():
            preview_text += f"{key}: {value}\n"
            
        self.config_preview.setPlainText(preview_text)
        
    def update_system_status(self):
        """更新系统状态"""
        self.status_list.clear()
        
        # 检查各项状态
        status_items = []
        
        # 检查模型
        if self.model_combo.count() > 0 and self.model_combo.currentData():
            status_items.append(("✅", "机器人模型可用"))
        else:
            status_items.append(("❌", "未找到机器人模型"))
            
        # 检查后端
        available_backends = self.backend_registry.get_available_backends()
        if available_backends:
            status_items.append(("✅", f"仿真后端可用 ({len(available_backends)}个)"))
        else:
            status_items.append(("❌", "无可用仿真后端"))
            
        # 检查配置档案
        profiles = self.config_manager.list_profiles()
        total_profiles = len(profiles['default']) + len(profiles['user'])
        if total_profiles > 0:
            status_items.append(("✅", f"配置档案可用 ({total_profiles}个)"))
        else:
            status_items.append(("❌", "无可用配置档案"))
            
        # 添加到列表
        for icon, text in status_items:
            item = QListWidgetItem(f"{icon} {text}")
            self.status_list.addItem(item)
            
    def reset_configuration(self):
        """重置配置"""
        self.model_combo.setCurrentIndex(0)
        self.backend_combo.setCurrentIndex(0)
        self.profile_combo.setCurrentIndex(0)
        self.algorithm_combo.setCurrentIndex(0)
        
        self.dt_spinbox.setValue(0.001)
        self.max_steps_spinbox.setValue(10000)
        self.enable_rendering_checkbox.setChecked(True)
        self.gravity_z_spinbox.setValue(-9.81)
        
        self.selected_config.clear()
        self.update_config_preview()
        
    def start_simulation(self):
        """开始仿真"""
        # 验证配置
        if not self.validate_configuration():
            return
            
        # 收集最终配置
        final_config = {
            'model_path': self.selected_config.get('model_path'),
            'model_name': self.selected_config.get('model_name'),
            'backend': self.selected_config.get('backend'),
            'profile': self.selected_config.get('profile'),
            'algorithm': self.selected_config.get('algorithm'),
            'dt': self.dt_spinbox.value(),
            'max_steps': self.max_steps_spinbox.value(),
            'enable_rendering': self.enable_rendering_checkbox.isChecked(),
            'gravity_z': self.gravity_z_spinbox.value()
        }
        
        # 发送配置完成信号
        self.configuration_complete.emit(final_config)
        
    def validate_configuration(self):
        """验证配置"""
        errors = []
        
        if not self.selected_config.get('model_path'):
            errors.append("请选择机器人模型")
            
        if not self.selected_config.get('backend'):
            errors.append("请选择仿真后端")
            
        if not self.selected_config.get('profile'):
            errors.append("请选择配置档案")
            
        if not self.selected_config.get('algorithm'):
            errors.append("请选择控制算法")
            
        if errors:
            QMessageBox.warning(self, "配置验证失败", "\n".join(errors))
            return False
            
        return True


class SimulationPage(QWidget):
    """仿真界面页面"""
    
    back_to_config = pyqtSignal()  # 返回配置页面信号
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        self.simulation_manager = None
        self.robot_model = None
        self.joint_controls = {}
        self.current_joint_angles = {}
        self.setup_ui()
        self.initialize_simulation()
        
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout()
        
        # 顶部工具栏
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)
        
        # 主仿真区域
        main_splitter = QSplitter(Qt.Horizontal)
        
        # 左侧控制面板
        left_panel = self.create_control_panel()
        main_splitter.addWidget(left_panel)
        
        # 右侧可视化面板
        right_panel = self.create_visualization_panel()
        main_splitter.addWidget(right_panel)
        
        # 设置分割比例
        main_splitter.setSizes([400, 800])
        layout.addWidget(main_splitter)
        
        # 底部状态栏
        status_bar = self.create_status_bar()
        layout.addWidget(status_bar)
        
        self.setLayout(layout)
        
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = QWidget()
        toolbar.setFixedHeight(50)
        toolbar.setStyleSheet("background-color: #f0f0f0; border-bottom: 1px solid #ccc;")
        
        layout = QHBoxLayout()
        
        # 标题
        title_label = QLabel(f"仿真运行中 - {self.config.get('model_name', '未知模型')}")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # 控制按钮
        self.play_pause_button = QPushButton("⏸️ 暂停")
        self.play_pause_button.clicked.connect(self.toggle_simulation)
        layout.addWidget(self.play_pause_button)
        
        self.reset_button = QPushButton("🔄 重置")
        self.reset_button.clicked.connect(self.reset_simulation)
        layout.addWidget(self.reset_button)
        
        self.config_button = QPushButton("⚙️ 重新配置")
        self.config_button.clicked.connect(self.back_to_configuration)
        layout.addWidget(self.config_button)
        
        toolbar.setLayout(layout)
        return toolbar
        
    def create_control_panel(self):
        """创建控制面板"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # 关节控制区域
        joint_group = QGroupBox("关节控制")
        self.joint_control_layout = QVBoxLayout()
        joint_group.setLayout(self.joint_control_layout)
        layout.addWidget(joint_group)
        
        # 算法控制区域
        algorithm_group = QGroupBox("算法控制")
        algorithm_layout = QVBoxLayout()
        
        self.algorithm_status_label = QLabel(f"当前算法: {self.config.get('algorithm', '未知')}")
        algorithm_layout.addWidget(self.algorithm_status_label)
        
        if self.config.get('algorithm') == 'manual':
            # 手动控制模式
            manual_info = QLabel("手动控制模式 - 使用滑块控制关节")
            manual_info.setStyleSheet("color: #666; font-style: italic;")
            algorithm_layout.addWidget(manual_info)
        else:
            # 自动控制模式
            self.start_algorithm_button = QPushButton("启动算法")
            self.start_algorithm_button.clicked.connect(self.start_algorithm)
            algorithm_layout.addWidget(self.start_algorithm_button)
            
            self.stop_algorithm_button = QPushButton("停止算法")
            self.stop_algorithm_button.clicked.connect(self.stop_algorithm)
            self.stop_algorithm_button.setEnabled(False)
            algorithm_layout.addWidget(self.stop_algorithm_button)
        
        algorithm_group.setLayout(algorithm_layout)
        layout.addWidget(algorithm_group)
        
        # 仿真信息
        info_group = QGroupBox("仿真信息")
        info_layout = QVBoxLayout()
        
        self.sim_info_label = QLabel("正在初始化...")
        info_layout.addWidget(self.sim_info_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
        
    def create_visualization_panel(self):
        """创建可视化面板"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # 机器人可视化
        self.robot_viz = RobotVisualizationWidget()
        layout.addWidget(self.robot_viz)
        
        panel.setLayout(layout)
        return panel
        
    def create_status_bar(self):
        """创建状态栏"""
        status_bar = QWidget()
        status_bar.setFixedHeight(30)
        status_bar.setStyleSheet("background-color: #f0f0f0; border-top: 1px solid #ccc;")
        
        layout = QHBoxLayout()
        
        self.status_label = QLabel("就绪")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        self.fps_label = QLabel("FPS: 0")
        layout.addWidget(self.fps_label)
        
        status_bar.setLayout(layout)
        return status_bar
        
    def initialize_simulation(self):
        """初始化仿真"""
        try:
            # 创建仿真管理器
            backend = SimulationBackend(self.config['backend'])
            profile_type, profile_name = self.config['profile'].split(':', 1)
            
            self.simulation_manager = create_simulation_manager(
                backend=backend,
                config_profile=profile_name if profile_type == 'default' else None
            )
            
            # 加载机器人模型
            self.load_robot_model()
            
            # 初始化仿真
            success = self.simulation_manager.initialize(self.config['model_path'])
            
            if success:
                self.status_label.setText("仿真初始化成功")
                self.sim_info_label.setText(f"""
                后端: {self.config['backend']}
                模型: {self.config['model_name']}
                算法: {self.config['algorithm']}
                状态: 运行中
                """)
            else:
                self.status_label.setText("仿真初始化失败")
                
        except Exception as e:
            self.status_label.setText(f"初始化错误: {e}")
            QMessageBox.critical(self, "初始化失败", f"仿真初始化失败:\n{e}")
            
    def load_robot_model(self):
        """加载机器人模型"""
        try:
            # 检查URDFLoader是否可用
            if 'URDFLoader' not in globals() or URDFLoader is None:
                print("❌ URDFLoader不可用，无法加载机器人模型")
                return
                
            loader = URDFLoader()
            self.robot_model = loader.load_urdf(self.config['model_path'])
            
            # 创建关节控制器
            self.create_joint_controls()
            
        except Exception as e:
            print(f"加载机器人模型失败: {e}")
            
    def create_joint_controls(self):
        """创建关节控制器"""
        if not self.robot_model:
            return
            
        # 清除现有控制器
        for i in reversed(range(self.joint_control_layout.count())):
            self.joint_control_layout.itemAt(i).widget().setParent(None)
            
        # 为每个关节创建控制器
        import math
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
        import math
        angle_degrees = {name: math.degrees(angle) for name, angle in self.current_joint_angles.items()}
        self.robot_viz.update_joint_angles(angle_degrees)
        
        # 如果是手动模式，发送到仿真器
        if self.config.get('algorithm') == 'manual' and self.simulation_manager:
            try:
                self.simulation_manager.set_joint_positions(self.current_joint_angles)
            except Exception as e:
                print(f"设置关节位置失败: {e}")
                
    def toggle_simulation(self):
        """切换仿真状态"""
        # 这里实现播放/暂停逻辑
        if self.play_pause_button.text() == "⏸️ 暂停":
            self.play_pause_button.setText("▶️ 播放")
            self.status_label.setText("仿真已暂停")
        else:
            self.play_pause_button.setText("⏸️ 暂停")
            self.status_label.setText("仿真运行中")
            
    def reset_simulation(self):
        """重置仿真"""
        if self.simulation_manager:
            self.simulation_manager.reset()
            
        # 重置关节角度
        for joint_name, control in self.joint_controls.items():
            control.set_angle(0.0)
            self.current_joint_angles[joint_name] = 0.0
            
        self.robot_viz.update_joint_angles({name: 0.0 for name in self.current_joint_angles.keys()})
        self.status_label.setText("仿真已重置")
        
    def start_algorithm(self):
        """启动算法"""
        self.start_algorithm_button.setEnabled(False)
        self.stop_algorithm_button.setEnabled(True)
        self.status_label.setText(f"算法 {self.config['algorithm']} 已启动")
        
    def stop_algorithm(self):
        """停止算法"""
        self.start_algorithm_button.setEnabled(True)
        self.stop_algorithm_button.setEnabled(False)
        self.status_label.setText("算法已停止")
        
    def back_to_configuration(self):
        """返回配置页面"""
        reply = QMessageBox.question(
            self, "确认返回", 
            "返回配置页面将停止当前仿真，确定要继续吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.simulation_manager:
                self.simulation_manager.close()
            self.back_to_config.emit()


class MainApplication(QMainWindow):
    """主应用程序"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.show_configuration_page()
        
    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("轮腿机器人孪生控制系统")
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
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #606060;
            }
            QComboBox {
                background-color: #404040;
                border: 1px solid #555555;
                padding: 5px;
                border-radius: 3px;
            }
            QSpinBox, QDoubleSpinBox {
                background-color: #404040;
                border: 1px solid #555555;
                padding: 5px;
                border-radius: 3px;
            }
        """)
        
        # 创建堆叠窗口
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
    def show_configuration_page(self):
        """显示配置页面"""
        self.config_page = ConfigurationPage()
        self.config_page.configuration_complete.connect(self.show_simulation_page)
        
        self.stacked_widget.addWidget(self.config_page)
        self.stacked_widget.setCurrentWidget(self.config_page)
        
    def show_simulation_page(self, config: Dict[str, Any]):
        """显示仿真页面"""
        self.simulation_page = SimulationPage(config)
        self.simulation_page.back_to_config.connect(self.back_to_configuration)
        
        self.stacked_widget.addWidget(self.simulation_page)
        self.stacked_widget.setCurrentWidget(self.simulation_page)
        
    def back_to_configuration(self):
        """返回配置页面"""
        # 移除仿真页面
        if hasattr(self, 'simulation_page'):
            self.stacked_widget.removeWidget(self.simulation_page)
            self.simulation_page.deleteLater()
            
        # 显示配置页面
        self.stacked_widget.setCurrentWidget(self.config_page)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName("轮腿机器人孪生控制系统")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("轮腿机器人项目团队")
    
    # 创建主应用程序
    main_app = MainApplication()
    main_app.show()
    
    # 启动应用
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()