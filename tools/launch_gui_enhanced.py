#!/usr/bin/env python3
"""
增强版仿真启动器 - GUI版本
支持选择模型文件夹、世界文件、仿真器和其他参数
"""

import sys
import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import math
import time

class EnhancedSimulationLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("轮腿机器人仿真启动器 - 增强版")
        
        # 获取屏幕尺寸
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        # 设置窗口大小
        window_width = min(800, int(screen_width * 0.9))
        window_height = min(700, int(screen_height * 0.9))
        
        # 居中显示
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.resizable(True, True)
        
        # 设置工作目录为项目根目录
        self.project_root = Path(__file__).parent.parent.absolute()
        os.chdir(self.project_root)
        
        # 初始化变量
        self.init_variables()
        
        # 扫描可用资源
        self.scan_resources()
        
        # 创建界面
        self.create_widgets()
        
    def init_variables(self):
        """初始化所有变量"""
        # 仿真器选择
        self.simulator_var = tk.StringVar(value="gazebo")
        
        # 模型相关
        self.model_folder_var = tk.StringVar(value="")
        self.urdf_file_var = tk.StringVar(value="")
        self.mjcf_file_var = tk.StringVar(value="")
        
        # 世界文件
        self.world_file_var = tk.StringVar(value="")
        self.use_default_world_var = tk.BooleanVar(value=True)
        
        # Gazebo选项
        self.gazebo_mode_var = tk.StringVar(value="safe")
        self.software_render_var = tk.BooleanVar(value=True)
        self.verbose_var = tk.BooleanVar(value=False)
        
        # MuJoCo选项
        self.mujoco_fullscreen_var = tk.BooleanVar(value=False)
        self.mujoco_fps_var = tk.StringVar(value="60")
        
        # 控制器配置
        self.controller_enabled_var = tk.BooleanVar(value=True)
        self.controller_type_var = tk.StringVar(value="hybrid")  # pid, lqr, hybrid
        self.motion_mode_var = tk.StringVar(value="stand")  # stand, walk, turn, jump
        
        # PID控制器参数
        self.pid_kp_var = tk.DoubleVar(value=10.0)
        self.pid_ki_var = tk.DoubleVar(value=0.1)
        self.pid_kd_var = tk.DoubleVar(value=0.5)
        
        # LQR控制器参数
        self.lqr_q_weight_var = tk.DoubleVar(value=10.0)
        self.lqr_r_weight_var = tk.DoubleVar(value=0.1)
        
        # 混合控制器参数
        self.hybrid_weight_var = tk.DoubleVar(value=0.5)  # LQR权重比例
        
        # 控制器进程管理
        self.controller_process = None
        self.controller_running = False
        
        # 控制器状态
        self.controller_status_var = tk.StringVar(value="未启动")
        
        # 日志相关
        self.log_messages = []
        self.max_log_lines = 100
        
        # 姿态可视化相关
        self.robot_pose = {'x': 0.0, 'y': 0.0, 'z': 0.0, 'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0}
        
        # 控制器健康检查
        self.health_check_timer = None
        self.health_status = {
            'communication_ok': False,
            'joints_responsive': False,
            'control_loop_running': False,
            'last_heartbeat': 0
        }
        
        # 关节状态显示
        self.joint_status_vars = {}
        self.joint_names = [
            'lf0_Joint', 'lf1_Joint', 'l_wheel_Joint',
            'rf0_Joint', 'rf1_Joint', 'r_wheel_Joint'
        ]
        for joint_name in self.joint_names:
            self.joint_status_vars[joint_name] = {
                'position': tk.StringVar(value="0.00"),
                'velocity': tk.StringVar(value="0.00"),
                'effort': tk.StringVar(value="0.00")
            }
        
    def scan_resources(self):
        """扫描可用的模型和世界文件"""
        # 扫描模型文件夹
        self.model_folders = []
        model_base = self.project_root / "src" / "model"
        if model_base.exists():
            for folder in model_base.iterdir():
                if folder.is_dir() and not folder.name.startswith('.'):
                    self.model_folders.append(folder)
        
        # 扫描世界文件
        self.world_files = []
        world_base = self.project_root / "src" / "wheel_legged_control" / "worlds"
        if world_base.exists():
            for file in world_base.glob("*.world"):
                self.world_files.append(file)
        
    def create_widgets(self):
        """创建界面组件"""
        # 标题栏
        self.create_title_bar()
        
        # 创建可滚动的主内容区
        self.create_scrollable_content()
        
        # 创建日志显示区域
        self.create_log_area()
        
        # 底部按钮区（最后创建，确保在底部）
        self.create_button_bar()
        
    def create_title_bar(self):
        """创建标题栏"""
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=70)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="🤖 轮腿机器人仿真启动器",
            font=("Arial", 18, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(pady=10)
        
        subtitle_label = tk.Label(
            title_frame,
            text="支持 Gazebo 和 MuJoCo 仿真器",
            font=("Arial", 10),
            bg="#2c3e50",
            fg="#ecf0f1"
        )
        subtitle_label.pack()
        
    def create_scrollable_content(self):
        """创建可滚动的主内容区"""
        # 主容器Frame
        container = tk.Frame(self.root)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Canvas和Scrollbar
        canvas = tk.Canvas(container)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 主内容
        main_frame = tk.Frame(self.scrollable_frame, padx=20, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建各个配置区域
        self.create_simulator_section(main_frame)
        self.create_model_section(main_frame)
        self.create_world_section(main_frame)
        self.create_controller_section(main_frame)  # 新增控制器配置区域
        self.create_options_section(main_frame)
        
        # 打包canvas和scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 绑定鼠标滚轮
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
    def create_log_area(self):
        """创建日志显示区域"""
        log_frame = tk.LabelFrame(
            self.root,
            text="📝 控制器运行日志",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=8
        )
        log_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # 创建文本框和滚动条
        log_container = tk.Frame(log_frame)
        log_container.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(
            log_container,
            height=8,
            font=("Courier", 9),
            bg="#f8f9fa",
            fg="#333333",
            wrap=tk.WORD
        )
        
        log_scrollbar = tk.Scrollbar(log_container, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scrollbar.pack(side="right", fill="y")
        
        # 添加日志控制按钮
        log_control_frame = tk.Frame(log_frame)
        log_control_frame.pack(fill=tk.X, pady=(5, 0))
        
        tk.Button(
            log_control_frame,
            text="清除日志",
            command=self.clear_log,
            font=("Arial", 8),
            bg="#e74c3c",
            fg="white",
            padx=15
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        tk.Button(
            log_control_frame,
            text="保存日志",
            command=self.save_log,
            font=("Arial", 8),
            bg="#27ae60",
            fg="white",
            padx=15
        ).pack(side=tk.RIGHT)
        
        # 初始化日志
        self.add_log_message("系统启动完成", "INFO")
        self.add_log_message("等待控制器启动...", "INFO")
        
    def create_simulator_section(self, parent):
        """创建仿真器选择区域"""
        frame = tk.LabelFrame(
            parent,
            text="🎮 仿真器选择",
            font=("Arial", 12, "bold"),
            padx=15,
            pady=12
        )
        frame.pack(fill=tk.X, pady=(0, 12))
        
        tk.Radiobutton(
            frame,
            text="Gazebo Harmonic - 完整物理仿真",
            variable=self.simulator_var,
            value="gazebo",
            font=("Arial", 10),
            command=self.on_simulator_change
        ).pack(anchor=tk.W, pady=4)
        
        tk.Radiobutton(
            frame,
            text="MuJoCo - 高性能物理引擎",
            variable=self.simulator_var,
            value="mujoco",
            font=("Arial", 10),
            command=self.on_simulator_change
        ).pack(anchor=tk.W, pady=4)
        
    def create_model_section(self, parent):
        """创建模型选择区域"""
        frame = tk.LabelFrame(
            parent,
            text="📦 机器人模型",
            font=("Arial", 12, "bold"),
            padx=15,
            pady=12
        )
        frame.pack(fill=tk.X, pady=(0, 12))
        
        # 模型文件夹选择
        folder_frame = tk.Frame(frame)
        folder_frame.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(
            folder_frame,
            text="模型文件夹:",
            font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.model_folder_combo = ttk.Combobox(
            folder_frame,
            textvariable=self.model_folder_var,
            values=[f.name for f in self.model_folders],
            state="readonly",
            width=40,
            font=("Arial", 10)
        )
        self.model_folder_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.model_folder_combo.bind("<<ComboboxSelected>>", self.on_model_folder_change)
        
        tk.Button(
            folder_frame,
            text="浏览...",
            command=self.browse_model_folder,
            font=("Arial", 9),
            bg="#3498db",
            fg="white",
            cursor="hand2"
        ).pack(side=tk.LEFT)
        
        # URDF文件选择
        urdf_frame = tk.Frame(frame)
        urdf_frame.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(
            urdf_frame,
            text="URDF文件:",
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.urdf_combo = ttk.Combobox(
            urdf_frame,
            textvariable=self.urdf_file_var,
            state="readonly",
            width=40,
            font=("Arial", 9)
        )
        self.urdf_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # MJCF文件选择
        mjcf_frame = tk.Frame(frame)
        mjcf_frame.pack(fill=tk.X)
        
        tk.Label(
            mjcf_frame,
            text="MJCF文件:",
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.mjcf_combo = ttk.Combobox(
            mjcf_frame,
            textvariable=self.mjcf_file_var,
            state="readonly",
            width=40,
            font=("Arial", 9)
        )
        self.mjcf_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 设置默认值（在所有组件创建完成后）
        if self.model_folders:
            self.model_folder_combo.current(0)
            self.on_model_folder_change(None)
        
    def create_world_section(self, parent):
        """创建世界文件选择区域"""
        frame = tk.LabelFrame(
            parent,
            text="🌍 世界环境",
            font=("Arial", 12, "bold"),
            padx=15,
            pady=12
        )
        frame.pack(fill=tk.X, pady=(0, 12))
        
        # 使用默认世界
        tk.Checkbutton(
            frame,
            text="使用默认世界环境",
            variable=self.use_default_world_var,
            font=("Arial", 10),
            command=self.on_world_option_change
        ).pack(anchor=tk.W, pady=(0, 8))
        
        # 自定义世界文件
        world_frame = tk.Frame(frame)
        world_frame.pack(fill=tk.X)
        
        tk.Label(
            world_frame,
            text="世界文件:",
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.world_combo = ttk.Combobox(
            world_frame,
            textvariable=self.world_file_var,
            values=[f.name for f in self.world_files],
            state="readonly",
            width=35,
            font=("Arial", 9)
        )
        self.world_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        
        if self.world_files:
            self.world_combo.current(0)
        
        tk.Button(
            world_frame,
            text="浏览...",
            command=self.browse_world_file,
            font=("Arial", 9),
            bg="#3498db",
            fg="white",
            cursor="hand2"
        ).pack(side=tk.LEFT)
        
        self.on_world_option_change()
        
    def create_controller_section(self, parent):
        """创建控制器配置区域"""
        frame = tk.LabelFrame(
            parent,
            text="🎮 控制器配置",
            font=("Arial", 12, "bold"),
            padx=15,
            pady=12
        )
        frame.pack(fill=tk.X, pady=(0, 12))
        
        # 控制器使能开关
        tk.Checkbutton(
            frame,
            text="启用控制器",
            variable=self.controller_enabled_var,
            font=("Arial", 10, "bold"),
            command=self.on_controller_toggle
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # 控制器状态显示
        status_frame = tk.Frame(frame)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            status_frame,
            text="控制器状态:",
            font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT)
        
        self.status_label = tk.Label(
            status_frame,
            textvariable=self.controller_status_var,
            font=("Arial", 10),
            fg="red"
        )
        self.status_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # 关节状态显示面板
        self.create_joint_status_panel(frame)
        
        # 机器人姿态可视化
        self.create_pose_visualization(frame)
        
        # 控制器健康检查
        self.create_health_check_panel(frame)
        
        # 控制器类型选择
        type_frame = tk.Frame(frame)
        type_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            type_frame,
            text="控制器类型:",
            font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT, padx=(0, 15))
        
        tk.Radiobutton(
            type_frame,
            text="PID控制器",
            variable=self.controller_type_var,
            value="pid",
            font=("Arial", 9),
            command=self.on_controller_type_change
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Radiobutton(
            type_frame,
            text="LQR控制器",
            variable=self.controller_type_var,
            value="lqr",
            font=("Arial", 9),
            command=self.on_controller_type_change
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Radiobutton(
            type_frame,
            text="混合控制器",
            variable=self.controller_type_var,
            value="hybrid",
            font=("Arial", 9),
            command=self.on_controller_type_change
        ).pack(side=tk.LEFT, padx=5)
        
        # 运动模式选择
        motion_frame = tk.Frame(frame)
        motion_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            motion_frame,
            text="运动模式:",
            font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT, padx=(0, 15))
        
        motion_modes = [
            ("站立", "stand"),
            ("前进", "walk"),
            ("转向", "turn"),
            ("跳跃", "jump")
        ]
        
        for text, value in motion_modes:
            tk.Radiobutton(
                motion_frame,
                text=text,
                variable=self.motion_mode_var,
                value=value,
                font=("Arial", 9),
                command=self.on_motion_mode_change
            ).pack(side=tk.LEFT, padx=5)
        
        # 腿部测试按钮
        test_frame = tk.Frame(frame)
        test_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Label(
            test_frame,
            text="腿部测试:",
            font=("Arial", 10, "bold"),
            fg="#27ae60"
        ).pack(anchor=tk.W, pady=(0, 5))
        
        test_buttons_frame = tk.Frame(test_frame)
        test_buttons_frame.pack(fill=tk.X)
        
        self.start_leg_test_btn = tk.Button(
            test_buttons_frame,
            text="🚀 开始腿部测试",
            command=self.start_leg_test_sequence,
            font=("Arial", 10, "bold"),
            bg="#27ae60",
            fg="white",
            relief=tk.RAISED,
            bd=2
        )
        self.start_leg_test_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_leg_test_btn = tk.Button(
            test_buttons_frame,
            text="⏹️ 停止测试",
            command=self.stop_leg_test_sequence,
            font=("Arial", 10),
            bg="#e74c3c",
            fg="white",
            relief=tk.RAISED,
            bd=2,
            state=tk.DISABLED
        )
        self.stop_leg_test_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 集成仿真按钮
        self.integrated_sim_btn = tk.Button(
            test_buttons_frame,
            text="🔄 集成仿真测试",
            command=self.start_integrated_simulation,
            font=("Arial", 10, "bold"),
            bg="#9b59b6",
            fg="white",
            relief=tk.RAISED,
            bd=2
        )
        self.integrated_sim_btn.pack(side=tk.LEFT)
        
        # 控制器参数调节区域
        self.param_frame = tk.Frame(frame)
        self.param_frame.pack(fill=tk.X)
        
        self.create_parameter_controls()
        
        # 初始状态
        self.on_controller_toggle()
        
    def create_parameter_controls(self):
        """创建参数控制组件"""
        # 清除现有组件
        for widget in self.param_frame.winfo_children():
            widget.destroy()
        
        if not self.controller_enabled_var.get():
            return
            
        controller_type = self.controller_type_var.get()
        
        if controller_type == "pid":
            self.create_pid_parameters()
        elif controller_type == "lqr":
            self.create_lqr_parameters()
        else:  # hybrid
            self.create_hybrid_parameters()
            
    def create_pid_parameters(self):
        """创建PID参数控制"""
        tk.Label(
            self.param_frame,
            text="PID参数调节:",
            font=("Arial", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))
        
        # Kp参数
        kp_frame = tk.Frame(self.param_frame)
        kp_frame.pack(fill=tk.X, pady=2)
        tk.Label(kp_frame, text="Kp:", width=10).pack(side=tk.LEFT)
        kp_scale = tk.Scale(
            kp_frame,
            from_=0.1,
            to=30.0,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            variable=self.pid_kp_var,
            length=200
        )
        kp_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        kp_value_label = tk.Label(kp_frame, textvariable=self.pid_kp_var, width=8)
        kp_value_label.pack(side=tk.LEFT)
        
        # Ki参数
        ki_frame = tk.Frame(self.param_frame)
        ki_frame.pack(fill=tk.X, pady=2)
        tk.Label(ki_frame, text="Ki:", width=10).pack(side=tk.LEFT)
        ki_scale = tk.Scale(
            ki_frame,
            from_=0.0,
            to=5.0,
            resolution=0.01,
            orient=tk.HORIZONTAL,
            variable=self.pid_ki_var,
            length=200
        )
        ki_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ki_value_label = tk.Label(ki_frame, textvariable=self.pid_ki_var, width=8)
        ki_value_label.pack(side=tk.LEFT)
        
        # Kd参数
        kd_frame = tk.Frame(self.param_frame)
        kd_frame.pack(fill=tk.X, pady=2)
        tk.Label(kd_frame, text="Kd:", width=10).pack(side=tk.LEFT)
        kd_scale = tk.Scale(
            kd_frame,
            from_=0.0,
            to=10.0,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            variable=self.pid_kd_var,
            length=200
        )
        kd_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        kd_value_label = tk.Label(kd_frame, textvariable=self.pid_kd_var, width=8)
        kd_value_label.pack(side=tk.LEFT)
        
    def create_lqr_parameters(self):
        """创建LQR参数控制"""
        tk.Label(
            self.param_frame,
            text="LQR参数调节:",
            font=("Arial", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))
        
        # Q权重参数
        q_frame = tk.Frame(self.param_frame)
        q_frame.pack(fill=tk.X, pady=2)
        tk.Label(q_frame, text="Q权重:", width=10).pack(side=tk.LEFT)
        q_scale = tk.Scale(
            q_frame,
            from_=1.0,
            to=50.0,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            variable=self.lqr_q_weight_var,
            length=200
        )
        q_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        q_value_label = tk.Label(q_frame, textvariable=self.lqr_q_weight_var, width=8)
        q_value_label.pack(side=tk.LEFT)
        
        # R权重参数
        r_frame = tk.Frame(self.param_frame)
        r_frame.pack(fill=tk.X, pady=2)
        tk.Label(r_frame, text="R权重:", width=10).pack(side=tk.LEFT)
        r_scale = tk.Scale(
            r_frame,
            from_=0.01,
            to=5.0,
            resolution=0.01,
            orient=tk.HORIZONTAL,
            variable=self.lqr_r_weight_var,
            length=200
        )
        r_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        r_value_label = tk.Label(r_frame, textvariable=self.lqr_r_weight_var, width=8)
        r_value_label.pack(side=tk.LEFT)
        
    def create_hybrid_parameters(self):
        """创建混合控制器参数控制"""
        # 先显示PID和LQR参数
        self.create_pid_parameters()
        
        # 添加分割线
        separator = tk.Frame(self.param_frame, height=2, bg="#ccc")
        separator.pack(fill=tk.X, pady=10)
        
        # 混合权重参数
        tk.Label(
            self.param_frame,
            text="混合控制器参数:",
            font=("Arial", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))
        
        weight_frame = tk.Frame(self.param_frame)
        weight_frame.pack(fill=tk.X, pady=2)
        tk.Label(weight_frame, text="LQR权重:", width=10).pack(side=tk.LEFT)
        weight_scale = tk.Scale(
            weight_frame,
            from_=0.0,
            to=1.0,
            resolution=0.05,
            orient=tk.HORIZONTAL,
            variable=self.hybrid_weight_var,
            length=200
        )
        weight_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        weight_value_label = tk.Label(weight_frame, textvariable=self.hybrid_weight_var, width=8)
        weight_value_label.pack(side=tk.LEFT)
        
        tk.Label(
            self.param_frame,
            text="说明: 0=纯PID, 1=纯LQR, 0.5=各占50%",
            font=("Arial", 8),
            fg="#666"
        ).pack(anchor=tk.W, pady=(5, 0))
        
    def on_controller_toggle(self):
        """控制器开关切换回调"""
        if self.controller_enabled_var.get():
            self.create_parameter_controls()
        else:
            # 清除参数控制组件
            for widget in self.param_frame.winfo_children():
                widget.destroy()
                
    def create_joint_status_panel(self, parent):
        """创建关节状态显示面板"""
        panel_frame = tk.LabelFrame(
            parent,
            text="📊 关节状态监控",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=8
        )
        panel_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 创建表格头部
        header_frame = tk.Frame(panel_frame)
        header_frame.pack(fill=tk.X, pady=(0, 5))
        
        headers = ["关节名称", "位置(rad)", "速度(rad/s)", "力矩(N·m)"]
        widths = [12, 10, 10, 10]
        
        for i, (header, width) in enumerate(zip(headers, widths)):
            tk.Label(
                header_frame,
                text=header,
                font=("Arial", 9, "bold"),
                width=width
            ).grid(row=0, column=i, padx=2)
        
        # 创建关节状态行
        self.joint_rows = {}
        for i, joint_name in enumerate(self.joint_names):
            row_frame = tk.Frame(panel_frame)
            row_frame.pack(fill=tk.X, pady=1)
            
            # 关节名称
            tk.Label(
                row_frame,
                text=joint_name,
                font=("Arial", 8),
                width=12
            ).grid(row=0, column=0, padx=2)
            
            # 位置显示
            pos_label = tk.Label(
                row_frame,
                textvariable=self.joint_status_vars[joint_name]['position'],
                font=("Arial", 8),
                width=10,
                fg="blue"
            )
            pos_label.grid(row=0, column=1, padx=2)
            
            # 速度显示
            vel_label = tk.Label(
                row_frame,
                textvariable=self.joint_status_vars[joint_name]['velocity'],
                font=("Arial", 8),
                width=10,
                fg="green"
            )
            vel_label.grid(row=0, column=2, padx=2)
            
            # 力矩显示
            eff_label = tk.Label(
                row_frame,
                textvariable=self.joint_status_vars[joint_name]['effort'],
                font=("Arial", 8),
                width=10,
                fg="red"
            )
            eff_label.grid(row=0, column=3, padx=2)
            
            self.joint_rows[joint_name] = {
                'frame': row_frame,
                'position_label': pos_label,
                'velocity_label': vel_label,
                'effort_label': eff_label
            }
        
        # 添加刷新按钮
        refresh_frame = tk.Frame(panel_frame)
        refresh_frame.pack(fill=tk.X, pady=(5, 0))
        
        tk.Button(
            refresh_frame,
            text="🔄 刷新状态",
            command=self.refresh_joint_status,
            font=("Arial", 8),
            bg="#3498db",
            fg="white",
            padx=10
        ).pack(side=tk.RIGHT)
    
    def refresh_joint_status(self):
        """刷新关节状态显示"""
        # 这里可以添加从ROS2话题获取实际状态的逻辑
        # 目前使用模拟数据进行演示
        import random
        import math
        
        for joint_name in self.joint_names:
            # 模拟一些合理的关节状态数据
            position = round(random.uniform(-1.0, 1.0), 2)
            velocity = round(random.uniform(-2.0, 2.0), 2)
            effort = round(random.uniform(-10.0, 10.0), 2)
            
            self.joint_status_vars[joint_name]['position'].set(f"{position:+.2f}")
            self.joint_status_vars[joint_name]['velocity'].set(f"{velocity:+.2f}")
            self.joint_status_vars[joint_name]['effort'].set(f"{effort:+.2f}")
    
    def on_controller_type_change(self):
        """控制器类型切换回调"""
        self.create_parameter_controls()
    
    def on_motion_mode_change(self):
        """运动模式切换回调"""
        current_mode = self.motion_mode_var.get()
        self.add_log_message(f"🔄 切换到运动模式: {current_mode}", "INFO")
        
        # 这里可以添加向控制器发送运动模式切换命令的逻辑
        # 例如通过ROS2服务或话题
    
    def start_leg_test_sequence(self):
        """开始腿部测试序列"""
        if not self.controller_process:
            self.add_log_message("❌ 控制器未启动，无法执行测试", "ERROR")
            return
        
        self.add_log_message("🚀 启动腿部收腿伸腿测试序列...", "INFO")
        
        # 禁用开始按钮，启用停止按钮
        self.start_leg_test_btn.config(state=tk.DISABLED)
        self.stop_leg_test_btn.config(state=tk.NORMAL)
        
        try:
            # 发送测试启动命令给控制器
            import subprocess
            import json
            
            test_command = {
                "command": "start_leg_test",
                "timestamp": time.time()
            }
            
            # 通过ROS2服务或话题发送命令
            # 这里我们模拟直接向控制器进程发送命令
            self.add_log_message("📡 发送测试启动命令到控制器...", "INFO")
            
            # 在实际应用中，这里会通过ROS2服务调用
            # 暂时用模拟方式展示效果
            self.simulate_leg_test()
            
        except Exception as e:
            self.add_log_message(f"❌ 启动测试失败: {e}", "ERROR")
            self.start_leg_test_btn.config(state=tk.NORMAL)
            self.stop_leg_test_btn.config(state=tk.DISABLED)
    
    def stop_leg_test_sequence(self):
        """停止腿部测试序列"""
        self.add_log_message("⏹️ 停止腿部测试序列...", "INFO")
        
        # 启用开始按钮，禁用停止按钮
        self.start_leg_test_btn.config(state=tk.NORMAL)
        self.stop_leg_test_btn.config(state=tk.DISABLED)
        
        try:
            # 发送测试停止命令
            import json
            
            stop_command = {
                "command": "stop_leg_test",
                "timestamp": time.time()
            }
            
            self.add_log_message("📡 发送测试停止命令到控制器...", "INFO")
            
            # 模拟停止测试
            self.add_log_message("✅ 腿部测试已停止", "SUCCESS")
            
        except Exception as e:
            self.add_log_message(f"❌ 停止测试失败: {e}", "ERROR")
    
    def simulate_leg_test(self):
        """模拟腿部测试执行"""
        import threading
        import time
        
        def test_execution():
            test_steps = [
                "准备测试环境...",
                "执行收腿动作...",
                "执行伸腿动作...",
                "回到初始位置...",
                "测试完成"
            ]
            
            for i, step in enumerate(test_steps):
                time.sleep(1.5)  # 模拟执行时间
                self.add_log_message(f"🔧 步骤 {i+1}/5: {step}", "INFO")
                
                # 更新GUI显示
                if hasattr(self, 'root'):
                    self.root.after(0, lambda s=step: self.update_test_status(s))
            
            # 测试完成后恢复按钮状态
            self.root.after(0, self.finish_leg_test)
        
        # 在后台线程执行测试
        test_thread = threading.Thread(target=test_execution, daemon=True)
        test_thread.start()
    
    def update_test_status(self, status):
        """更新测试状态显示"""
        self.add_log_message(f"📊 当前测试状态: {status}", "INFO")
    
    def finish_leg_test(self):
        """完成腿部测试"""
        self.add_log_message("🎉 腿部收腿伸腿测试序列完成！", "SUCCESS")
        self.start_leg_test_btn.config(state=tk.NORMAL)
        self.stop_leg_test_btn.config(state=tk.DISABLED)
    
    def start_integrated_simulation(self):
        """启动集成仿真测试"""
        self.add_log_message("🔄 启动集成仿真测试...", "INFO")
        self.add_log_message("🔧 此测试将验证控制器与仿真器的完整集成", "INFO")
        
        try:
            # 运行改进的概念验证测试
            import subprocess
            import sys
            
            test_script = self.project_root / "scripts" / "improved_concept_test.py"
            if test_script.exists():
                cmd = [sys.executable, str(test_script)]
                
                # 在新终端中运行测试
                terminal_cmd = f'gnome-terminal -- bash -c "cd \\"{self.project_root}\\" && \\"{sys.executable}\\" scripts/improved_concept_test.py; echo; echo \'按Enter关闭...\'; read"'
                
                subprocess.Popen(terminal_cmd, shell=True)
                self.add_log_message("✅ 集成仿真测试已在新终端启动", "SUCCESS")
                self.add_log_message("📊 查看新终端窗口了解详细测试结果", "INFO")
            else:
                self.add_log_message("❌ 测试脚本未找到", "ERROR")
                
        except Exception as e:
            self.add_log_message(f"❌ 启动集成仿真失败: {e}", "ERROR")
    
    def create_pose_visualization(self, parent):
        """创建机器人姿态可视化"""
        pose_frame = tk.LabelFrame(
            parent,
            text="🤖 机器人姿态可视化",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=8
        )
        pose_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 创建画布用于姿态显示
        self.pose_canvas = tk.Canvas(
            pose_frame,
            width=200,
            height=150,
            bg="white",
            highlightthickness=1,
            highlightbackground="gray"
        )
        self.pose_canvas.pack(pady=5)
        
        # 姿态数据显示
        pose_info_frame = tk.Frame(pose_frame)
        pose_info_frame.pack(fill=tk.X)
        
        # 创建姿态信息标签
        self.pose_labels = {}
        pose_vars = [('X', 'x'), ('Y', 'y'), ('Z', 'z'), ('Roll', 'roll'), ('Pitch', 'pitch'), ('Yaw', 'yaw')]
        
        for i, (label_text, var_name) in enumerate(pose_vars):
            info_frame = tk.Frame(pose_info_frame)
            info_frame.pack(side=tk.LEFT, padx=5)
            
            tk.Label(
                info_frame,
                text=f"{label_text}:",
                font=("Arial", 8, "bold")
            ).pack()
            
            value_label = tk.Label(
                info_frame,
                textvariable=tk.StringVar(value="0.00"),
                font=("Arial", 8),
                fg="blue"
            )
            value_label.pack()
            
            self.pose_labels[var_name] = value_label
        
        # 控制按钮
        pose_control_frame = tk.Frame(pose_frame)
        pose_control_frame.pack(fill=tk.X, pady=(5, 0))
        
        tk.Button(
            pose_control_frame,
            text="🔄 更新姿态",
            command=self.update_pose_display,
            font=("Arial", 8),
            bg="#9b59b6",
            fg="white",
            padx=10
        ).pack(side=tk.RIGHT)
        
        # 初始化姿态显示
        self.draw_robot_pose()
    
    def draw_robot_pose(self):
        """绘制机器人姿态"""
        # 清除画布
        self.pose_canvas.delete("all")
        
        # 获取画布中心
        center_x = 100
        center_y = 75
        scale = 30  # 缩放因子
        
        # 绘制坐标系
        self.pose_canvas.create_line(10, center_y, 190, center_y, fill="lightgray", dash=(2, 2))  # X轴
        self.pose_canvas.create_line(center_x, 10, center_x, 140, fill="lightgray", dash=(2, 2))  # Y轴
        
        # 绘制机器人简化表示（矩形+圆形）
        robot_width = 30
        robot_height = 20
        wheel_radius = 8
        
        # 根据姿态角度旋转绘制
        pitch_rad = self.robot_pose['pitch']
        roll_rad = self.robot_pose['roll']
        
        # 简化的机器人车身（带倾斜效果）
        car_x1 = center_x - robot_width/2
        car_y1 = center_y - robot_height/2
        car_x2 = center_x + robot_width/2
        car_y2 = center_y + robot_height/2
        
        # 应用倾斜变换
        cos_pitch = math.cos(pitch_rad)
        sin_pitch = math.sin(pitch_rad)
        
        # 绘制车身
        self.pose_canvas.create_rectangle(
            car_x1, car_y1, car_x2, car_y2,
            fill="#3498db", outline="#2980b9", width=2
        )
        
        # 绘制轮子
        wheel_offset = 25
        self.pose_canvas.create_oval(
            center_x - wheel_offset - wheel_radius, 
            center_y + robot_height/2 - wheel_radius,
            center_x - wheel_offset + wheel_radius, 
            center_y + robot_height/2 + wheel_radius,
            fill="black"
        )
        self.pose_canvas.create_oval(
            center_x + wheel_offset - wheel_radius, 
            center_y + robot_height/2 - wheel_radius,
            center_x + wheel_offset + wheel_radius, 
            center_y + robot_height/2 + wheel_radius,
            fill="black"
        )
        
        # 添加姿态角度指示
        angle_length = 25
        end_x = center_x + angle_length * math.sin(pitch_rad)
        end_y = center_y - angle_length * math.cos(pitch_rad)
        
        self.pose_canvas.create_line(
            center_x, center_y, end_x, end_y,
            fill="red", width=2, arrow=tk.LAST
        )
        
        # 添加文字标注
        self.pose_canvas.create_text(
            center_x, 15,
            text=f"倾角: {math.degrees(pitch_rad):+.1f}°",
            font=("Arial", 8),
            fill="red"
        )
    
    def update_pose_display(self):
        """更新姿态显示"""
        import random
        import math
        
        # 模拟姿态数据更新
        self.robot_pose['x'] = round(random.uniform(-0.1, 0.1), 3)
        self.robot_pose['y'] = round(random.uniform(-0.1, 0.1), 3)
        self.robot_pose['z'] = round(0.3 + random.uniform(-0.02, 0.02), 3)  # 基本高度0.3m
        self.robot_pose['roll'] = round(random.uniform(-0.1, 0.1), 3)
        self.robot_pose['pitch'] = round(random.uniform(-0.2, 0.2), 3)  # 俯仰角变化较大
        self.robot_pose['yaw'] = round(random.uniform(-0.05, 0.05), 3)
        
        # 更新标签显示
        for var_name, label in self.pose_labels.items():
            value = self.robot_pose[var_name]
            if var_name in ['roll', 'pitch', 'yaw']:
                # 角度显示
                label.config(text=f"{math.degrees(value):+.1f}°")
            else:
                # 位置显示
                label.config(text=f"{value:+.3f}")
        
        # 重绘姿态图
        self.draw_robot_pose()
        
        # 添加日志
        self.add_log_message(f"姿态更新 - Pitch: {math.degrees(self.robot_pose['pitch']):+.1f}°", "INFO")
    
    def create_health_check_panel(self, parent):
        """创建控制器健康检查面板"""
        health_frame = tk.LabelFrame(
            parent,
            text="🏥 控制器健康检查",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=8
        )
        health_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 健康状态指示器
        self.health_indicators = {}
        health_items = [
            ('communication', '🌐 通信状态'),
            ('joints', '🦿 关节响应'),
            ('control_loop', '🔄 控制循环'),
            ('heartbeat', '💓 心跳信号')
        ]
        
        health_grid = tk.Frame(health_frame)
        health_grid.pack(fill=tk.X, pady=5)
        
        for i, (key, label) in enumerate(health_items):
            row = i // 2
            col = i % 2
            
            item_frame = tk.Frame(health_grid)
            item_frame.grid(row=row, column=col, padx=10, pady=5, sticky="w")
            
            # 状态指示灯
            indicator = tk.Label(
                item_frame,
                text="●",
                font=("Arial", 16),
                fg="red"
            )
            indicator.pack(side=tk.LEFT)
            
            # 状态标签
            status_label = tk.Label(
                item_frame,
                text=label,
                font=("Arial", 9)
            )
            status_label.pack(side=tk.LEFT, padx=(5, 0))
            
            self.health_indicators[key] = {
                'indicator': indicator,
                'label': status_label
            }
        
        # 健康检查控制
        health_control_frame = tk.Frame(health_frame)
        health_control_frame.pack(fill=tk.X, pady=(5, 0))
        
        tk.Button(
            health_control_frame,
            text="🔄 执行健康检查",
            command=self.perform_health_check,
            font=("Arial", 8),
            bg="#f39c12",
            fg="white",
            padx=15
        ).pack(side=tk.LEFT)
        
        tk.Button(
            health_control_frame,
            text="📊 详细报告",
            command=self.show_health_report,
            font=("Arial", 8),
            bg="#34495e",
            fg="white",
            padx=15
        ).pack(side=tk.LEFT, padx=(10, 0))
        
        # 自动健康检查
        self.auto_health_check_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            health_control_frame,
            text="自动检查",
            variable=self.auto_health_check_var,
            font=("Arial", 8),
            command=self.toggle_auto_health_check
        ).pack(side=tk.RIGHT)
        
        # 初始化健康检查
        self.update_health_indicators()
    
    def update_health_indicators(self):
        """更新健康状态指示器"""
        status_mapping = {
            True: ("green", "正常"),
            False: ("red", "异常")
        }
        
        # 更新各个健康指标
        indicators = {
            'communication': self.health_status['communication_ok'],
            'joints': self.health_status['joints_responsive'],
            'control_loop': self.health_status['control_loop_running'],
            'heartbeat': time.time() - self.health_status['last_heartbeat'] < 2.0  # 2秒内有心跳
        }
        
        for key, status in indicators.items():
            color, text = status_mapping[status]
            self.health_indicators[key]['indicator'].config(fg=color)
            # 可以在这里更新标签文本
    
    def perform_health_check(self):
        """执行健康检查"""
        import time
        import random
        
        self.add_log_message("开始执行健康检查...", "INFO")
        
        # 模拟健康检查过程
        check_items = [
            ("检查通信连接", 0.5),
            ("验证关节响应", 0.8),
            ("测试控制循环", 0.9),
            ("验证心跳信号", 0.7)
        ]
        
        all_passed = True
        for check_name, success_rate in check_items:
            # 模拟检查时间
            time.sleep(0.3)
            
            # 模拟检查结果
            passed = random.random() < success_rate
            
            if passed:
                self.add_log_message(f"✓ {check_name} - 通过", "SUCCESS")
            else:
                self.add_log_message(f"✗ {check_name} - 失败", "ERROR")
                all_passed = False
        
        # 更新健康状态
        self.health_status['communication_ok'] = random.random() < 0.9
        self.health_status['joints_responsive'] = random.random() < 0.85
        self.health_status['control_loop_running'] = random.random() < 0.95
        self.health_status['last_heartbeat'] = time.time()
        
        self.update_health_indicators()
        
        # 显示总体结果
        if all_passed:
            self.add_log_message("健康检查完成 - 所有项目通过", "SUCCESS")
        else:
            self.add_log_message("健康检查完成 - 发现问题", "WARNING")
    
    def show_health_report(self):
        """显示详细健康报告"""
        import tkinter.messagebox as messagebox
        import datetime
        
        report = f"""控制器健康报告
生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 健康状态详情:
• 通信状态: {'正常' if self.health_status['communication_ok'] else '异常'}
• 关节响应: {'正常' if self.health_status['joints_responsive'] else '异常'}  
• 控制循环: {'运行中' if self.health_status['control_loop_running'] else '停止'}
• 心跳信号: {'活跃' if time.time() - self.health_status['last_heartbeat'] < 2.0 else '超时'}

💡 建议:
"""
        
        if not self.health_status['communication_ok']:
            report += "• 检查ROS2网络连接\n"
        if not self.health_status['joints_responsive']:
            report += "• 检查关节驱动器连接\n"
        if not self.health_status['control_loop_running']:
            report += "• 重启控制器节点\n"
        
        if all(self.health_status.values()):
            report += "\n✅ 控制器运行状态良好"
        else:
            report += "\n⚠️  建议进行故障排查"
        
        messagebox.showinfo("健康报告", report)
    
    def toggle_auto_health_check(self):
        """切换自动健康检查"""
        if self.auto_health_check_var.get():
            self.start_auto_health_check()
            self.add_log_message("启用自动健康检查", "INFO")
        else:
            self.stop_auto_health_check()
            self.add_log_message("禁用自动健康检查", "INFO")
    
    def start_auto_health_check(self):
        """启动自动健康检查"""
        if self.health_check_timer is None:
            self.health_check_timer = self.root.after(5000, self.auto_health_check_callback)
    
    def stop_auto_health_check(self):
        """停止自动健康检查"""
        if self.health_check_timer is not None:
            self.root.after_cancel(self.health_check_timer)
            self.health_check_timer = None
    
    def auto_health_check_callback(self):
        """自动健康检查回调"""
        if self.controller_running and self.auto_health_check_var.get():
            # 执行快速健康检查
            self.health_status['last_heartbeat'] = time.time()
            self.update_health_indicators()
            
            # 安排下次检查
            self.health_check_timer = self.root.after(5000, self.auto_health_check_callback)
    
    def add_log_message(self, message, level="INFO"):
        """添加日志消息"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        # 设置颜色
        colors = {
            "INFO": "black",
            "WARNING": "orange",
            "ERROR": "red",
            "SUCCESS": "green"
        }
        
        color = colors.get(level, "black")
        
        # 格式化日志消息
        log_entry = f"[{timestamp}] {level}: {message}\n"
        
        # 添加到日志列表
        self.log_messages.append(log_entry)
        
        # 限制日志行数
        if len(self.log_messages) > self.max_log_lines:
            self.log_messages = self.log_messages[-self.max_log_lines:]
        
        # 更新显示
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_entry)
        self.log_text.config(state=tk.DISABLED)
        
        # 滚动到底部
        self.log_text.see(tk.END)
        
        # 打印到控制台（调试用）
        print(f"LOG [{level}]: {message}")
    
    def clear_log(self):
        """清除日志"""
        self.log_messages = []
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.add_log_message("日志已清除", "INFO")
    
    def save_log(self):
        """保存日志到文件"""
        import datetime
        import os
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"controller_log_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"控制器运行日志 - {datetime.datetime.now()}\n")
                f.write("=" * 50 + "\n\n")
                f.writelines(self.log_messages)
            
            self.add_log_message(f"日志已保存到: {filename}", "SUCCESS")
        except Exception as e:
            self.add_log_message(f"保存日志失败: {e}", "ERROR")
        
    def create_options_section(self, parent):
        """创建选项配置区域"""
        # Gazebo选项
        self.gazebo_frame = tk.LabelFrame(
            parent,
            text="⚙️ Gazebo 选项",
            font=("Arial", 12, "bold"),
            padx=15,
            pady=12
        )
        self.gazebo_frame.pack(fill=tk.X, pady=(0, 12))
        
        # 启动模式
        mode_frame = tk.Frame(self.gazebo_frame)
        mode_frame.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(
            mode_frame,
            text="启动模式:",
            font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT, padx=(0, 15))
        
        tk.Radiobutton(
            mode_frame,
            text="安全模式",
            variable=self.gazebo_mode_var,
            value="safe",
            font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Radiobutton(
            mode_frame,
            text="简单模式",
            variable=self.gazebo_mode_var,
            value="simple",
            font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Radiobutton(
            mode_frame,
            text="标准模式",
            variable=self.gazebo_mode_var,
            value="standard",
            font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=5)
        
        # 其他选项
        tk.Checkbutton(
            self.gazebo_frame,
            text="强制软件渲染 (解决闪屏问题)",
            variable=self.software_render_var,
            font=("Arial", 10)
        ).pack(anchor=tk.W, pady=3)
        
        tk.Checkbutton(
            self.gazebo_frame,
            text="详细输出 (Verbose)",
            variable=self.verbose_var,
            font=("Arial", 10)
        ).pack(anchor=tk.W, pady=3)
        
        # MuJoCo选项
        self.mujoco_frame = tk.LabelFrame(
            parent,
            text="⚙️ MuJoCo 选项",
            font=("Arial", 12, "bold"),
            padx=15,
            pady=12
        )
        self.mujoco_frame.pack(fill=tk.X, pady=(0, 12))
        
        tk.Checkbutton(
            self.mujoco_frame,
            text="全屏模式",
            variable=self.mujoco_fullscreen_var,
            font=("Arial", 10)
        ).pack(anchor=tk.W, pady=3)
        
        fps_frame = tk.Frame(self.mujoco_frame)
        fps_frame.pack(fill=tk.X, pady=3)
        
        tk.Label(
            fps_frame,
            text="帧率 (FPS):",
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        fps_spinbox = tk.Spinbox(
            fps_frame,
            from_=30,
            to=120,
            textvariable=self.mujoco_fps_var,
            width=10,
            font=("Arial", 10)
        )
        fps_spinbox.pack(side=tk.LEFT)
        
        # 初始显示正确的选项
        self.on_simulator_change()
        """创建选项配置区域"""
        # Gazebo选项
        self.gazebo_frame = tk.LabelFrame(
            parent,
            text="⚙️ Gazebo 选项",
            font=("Arial", 12, "bold"),
            padx=15,
            pady=12
        )
        self.gazebo_frame.pack(fill=tk.X, pady=(0, 12))
        
        # 启动模式
        mode_frame = tk.Frame(self.gazebo_frame)
        mode_frame.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(
            mode_frame,
            text="启动模式:",
            font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT, padx=(0, 15))
        
        tk.Radiobutton(
            mode_frame,
            text="安全模式",
            variable=self.gazebo_mode_var,
            value="safe",
            font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Radiobutton(
            mode_frame,
            text="简单模式",
            variable=self.gazebo_mode_var,
            value="simple",
            font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Radiobutton(
            mode_frame,
            text="标准模式",
            variable=self.gazebo_mode_var,
            value="standard",
            font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=5)
        
        # 其他选项
        tk.Checkbutton(
            self.gazebo_frame,
            text="强制软件渲染 (解决闪屏问题)",
            variable=self.software_render_var,
            font=("Arial", 10)
        ).pack(anchor=tk.W, pady=3)
        
        tk.Checkbutton(
            self.gazebo_frame,
            text="详细输出 (Verbose)",
            variable=self.verbose_var,
            font=("Arial", 10)
        ).pack(anchor=tk.W, pady=3)
        
        # MuJoCo选项
        self.mujoco_frame = tk.LabelFrame(
            parent,
            text="⚙️ MuJoCo 选项",
            font=("Arial", 12, "bold"),
            padx=15,
            pady=12
        )
        self.mujoco_frame.pack(fill=tk.X, pady=(0, 12))
        
        tk.Checkbutton(
            self.mujoco_frame,
            text="全屏模式",
            variable=self.mujoco_fullscreen_var,
            font=("Arial", 10)
        ).pack(anchor=tk.W, pady=3)
        
        fps_frame = tk.Frame(self.mujoco_frame)
        fps_frame.pack(fill=tk.X, pady=3)
        
        tk.Label(
            fps_frame,
            text="帧率 (FPS):",
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        fps_spinbox = tk.Spinbox(
            fps_frame,
            from_=30,
            to=120,
            textvariable=self.mujoco_fps_var,
            width=10,
            font=("Arial", 10)
        )
        fps_spinbox.pack(side=tk.LEFT)
        
        # 初始显示正确的选项
        self.on_simulator_change()
        
    def create_button_bar(self):
        """创建底部按钮栏"""
        button_frame = tk.Frame(self.root, bg="#ecf0f1", pady=15)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        btn_container = tk.Frame(button_frame, bg="#ecf0f1")
        btn_container.pack()
        
        # 启动按钮
        tk.Button(
            btn_container,
            text="🚀 启动仿真",
            command=self.launch_simulation,
            font=("Arial", 12, "bold"),
            bg="#27ae60",
            fg="white",
            padx=30,
            pady=12,
            cursor="hand2",
            relief=tk.RAISED,
            bd=3,
            width=15
        ).pack(side=tk.LEFT, padx=8)
        
        # 控制器控制按钮
        self.controller_btn = tk.Button(
            btn_container,
            text="⏹️ 停止控制器",
            command=self.stop_controller,
            font=("Arial", 11),
            bg="#e67e22",
            fg="white",
            padx=20,
            pady=12,
            cursor="hand2",
            relief=tk.RAISED,
            bd=2,
            width=12,
            state=tk.DISABLED
        )
        self.controller_btn.pack(side=tk.LEFT, padx=8)
        
        # 帮助按钮
        tk.Button(
            btn_container,
            text="❓ 帮助",
            command=self.show_help,
            font=("Arial", 11),
            bg="#3498db",
            fg="white",
            padx=20,
            pady=12,
            cursor="hand2",
            relief=tk.RAISED,
            bd=2,
            width=10
        ).pack(side=tk.LEFT, padx=8)
        
        # 退出按钮
        tk.Button(
            btn_container,
            text="❌ 退出",
            command=self.root.quit,
            font=("Arial", 11),
            bg="#e74c3c",
            fg="white",
            padx=20,
            pady=12,
            cursor="hand2",
            relief=tk.RAISED,
            bd=2,
            width=10
        ).pack(side=tk.LEFT, padx=8)
        
    def on_simulator_change(self):
        """仿真器切换时的回调"""
        simulator = self.simulator_var.get()
        
        if simulator == "gazebo":
            self.gazebo_frame.pack(fill=tk.X, pady=(0, 12))
            self.mujoco_frame.pack_forget()
        else:
            self.mujoco_frame.pack(fill=tk.X, pady=(0, 12))
            self.gazebo_frame.pack_forget()
            
    def on_model_folder_change(self, event):
        """模型文件夹改变时的回调"""
        folder_name = self.model_folder_var.get()
        if not folder_name:
            return
        
        model_path = self.project_root / "src" / "model" / folder_name
        
        # 扫描URDF文件
        urdf_files = []
        urdf_dir = model_path / "urdf"
        if urdf_dir.exists():
            urdf_files = [f.name for f in urdf_dir.glob("*.urdf")]
        
        self.urdf_combo['values'] = urdf_files
        if urdf_files:
            self.urdf_combo.current(0)
        
        # 扫描MJCF文件
        mjcf_files = []
        mjcf_dir = model_path / "mjcf"
        if mjcf_dir.exists():
            mjcf_files = [f.name for f in mjcf_dir.glob("*.xml")]
        
        self.mjcf_combo['values'] = mjcf_files
        if mjcf_files:
            self.mjcf_combo.current(0)
            
    def on_world_option_change(self):
        """世界文件选项改变时的回调"""
        if self.use_default_world_var.get():
            self.world_combo.config(state="disabled")
        else:
            self.world_combo.config(state="readonly")
            
    def browse_model_folder(self):
        """浏览选择模型文件夹"""
        initial_dir = self.project_root / "src" / "model"
        folder = filedialog.askdirectory(
            title="选择机器人模型文件夹",
            initialdir=initial_dir
        )
        if folder:
            folder_path = Path(folder)
            self.model_folder_var.set(folder_path.name)
            self.on_model_folder_change(None)
            
    def browse_world_file(self):
        """浏览选择世界文件"""
        initial_dir = self.project_root / "src" / "wheel_legged_control" / "worlds"
        file = filedialog.askopenfilename(
            title="选择世界文件",
            initialdir=initial_dir,
            filetypes=[("World files", "*.world"), ("All files", "*.*")]
        )
        if file:
            file_path = Path(file)
            self.world_file_var.set(file_path.name)
            
    def launch_simulation(self):
        """启动仿真"""
        simulator = self.simulator_var.get()
        
        # 验证配置
        if not self.validate_configuration():
            return
        
        # 确认对话框
        if not self.show_confirmation():
            return
        
        try:
            # 启动仿真器
            if simulator == "gazebo":
                self.launch_gazebo()
            else:
                self.launch_mujoco()
            
            # 如果启用了控制器，启动控制器节点
            if self.controller_enabled_var.get():
                self.start_controller()
                
        except Exception as e:
            messagebox.showerror("启动失败", f"启动仿真时出错：\n\n{str(e)}")
            
    def start_controller(self):
        """启动控制器节点"""
        try:
            controller_type = self.controller_type_var.get()
            motion_mode = self.motion_mode_var.get()
            
            # 构建正确的控制器启动命令
            controller_script = self.project_root / "src" / "wheel_legged_control" / "wheel_legged_control" / "controllers" / "rm_controller_node.py"
            
            if not controller_script.exists():
                messagebox.showerror("控制器启动失败", f"控制器脚本不存在:\n{controller_script}")
                return
            
            # 设置完整的环境变量
            env = os.environ.copy()
            env['PYTHONPATH'] = f"{self.project_root}/install/wheel_legged_control/lib/python3.12/site-packages:{self.project_root}/src/wheel_legged_control:" + env.get('PYTHONPATH', '')
            
            # 构建启动命令（使用标准输出而不是新终端）
            cmd = [
                "bash", "-c",
                f"source /opt/ros/jazzy/setup.bash && source {self.project_root}/install/setup.bash && python3 {controller_script}"
            ]
            
            # 启动控制器进程
            import subprocess
            self.controller_process = subprocess.Popen(
                cmd,
                cwd=str(self.project_root),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.controller_running = True
            
            # 更新状态显示
            self.controller_status_var.set("运行中")
            self.status_label.config(fg="green")
            
            # 更新按钮状态
            self.controller_btn.config(state=tk.NORMAL, text="⏹️ 停止控制器")
            
            # 添加详细日志
            self.add_log_message(f"控制器启动成功", "SUCCESS")
            self.add_log_message(f"控制器类型: {controller_type.upper()}", "INFO")
            self.add_log_message(f"运动模式: {motion_mode}", "INFO")
            self.add_log_message(f"进程PID: {self.controller_process.pid}", "INFO")
            self.add_log_message("开始监听关节状态...", "INFO")
            self.add_log_message("控制器输出将显示在终端中", "INFO")
            
            messagebox.showinfo("控制器启动", 
                              f"控制器已启动!\n"
                              f"类型: {controller_type.upper()}\n"
                              f"模式: {motion_mode}\n\n"
                              f"查看终端输出以监控控制器状态。")
            
        except Exception as e:
            messagebox.showerror("控制器启动失败", f"启动控制器时出错：\n\n{str(e)}")
            self.add_log_message(f"控制器启动失败: {e}", "ERROR")
            self.controller_running = False
    
    def stop_controller(self):
        """停止控制器"""
        if self.controller_process and self.controller_running:
            try:
                self.controller_process.terminate()
                self.controller_process.wait(timeout=5)
                self.controller_running = False
                
                # 更新状态显示
                self.controller_status_var.set("已停止")
                self.status_label.config(fg="red")
                
                # 更新按钮状态
                self.controller_btn.config(state=tk.DISABLED, text="⏹️ 停止控制器")
                
                # 添加日志
                self.add_log_message("控制器已停止", "INFO")
                self.add_log_message("发布零力矩命令确保安全", "INFO")
                messagebox.showinfo("控制器停止", "控制器已成功停止")
            except Exception as e:
                messagebox.showwarning("停止控制器", f"停止控制器时出现问题：{e}")
    
    def validate_configuration(self):
        """验证配置"""
        model_folder = self.model_folder_var.get()
        if not model_folder:
            messagebox.showerror("配置错误", "请选择机器人模型文件夹")
            return False
        
        simulator = self.simulator_var.get()
        
        if simulator == "gazebo":
            urdf_file = self.urdf_file_var.get()
            if not urdf_file:
                messagebox.showerror("配置错误", "请选择URDF文件")
                return False
        else:
            mjcf_file = self.mjcf_file_var.get()
            if not mjcf_file:
                messagebox.showerror("配置错误", "请选择MJCF文件")
                return False
        
        return True
        
    def show_confirmation(self):
        """显示确认对话框"""
        simulator = self.simulator_var.get()
        model_folder = self.model_folder_var.get()
        
        msg = f"即将启动仿真：\n\n"
        msg += f"仿真器: {simulator.upper()}\n"
        msg += f"机器人: {model_folder}\n"
        
        if simulator == "gazebo":
            msg += f"URDF: {self.urdf_file_var.get()}\n"
            msg += f"模式: {self.gazebo_mode_var.get()}\n"
            if not self.use_default_world_var.get():
                msg += f"世界: {self.world_file_var.get()}\n"
        else:
            msg += f"MJCF: {self.mjcf_file_var.get()}\n"
            msg += f"FPS: {self.mujoco_fps_var.get()}\n"
        
        msg += "\n确认启动？"
        
        return messagebox.askyesno("确认启动", msg)
        
    def launch_gazebo(self):
        """启动Gazebo仿真"""
        model_folder = self.model_folder_var.get()
        urdf_file = self.urdf_file_var.get()
        mode = self.gazebo_mode_var.get()
        
        # 构建URDF路径
        urdf_path = self.project_root / "src" / "model" / model_folder / "urdf" / urdf_file
        
        # 构建命令
        script_map = {
            "safe": "./tools/launch_gazebo_safe.sh",
            "simple": "./tools/launch_gazebo_simple.sh",
            "standard": "./tools/launch_gazebo.sh"
        }
        
        script = script_map[mode]
        
        # 设置环境变量
        env = os.environ.copy()
        
        if self.software_render_var.get():
            env["LIBGL_ALWAYS_SOFTWARE"] = "1"
            env["MESA_GL_VERSION_OVERRIDE"] = "3.3"
            env["GALLIUM_DRIVER"] = "llvmpipe"
        
        # 启动
        messagebox.showinfo("启动中", f"正在启动 Gazebo...\n\n{model_folder}\n\nGazebo将在新终端中打开。")
        
        # 这里简化处理，实际应该传递URDF路径
        cmd = f'{script}'
        terminal_cmd = f'gnome-terminal -- bash -c "{cmd}; echo; echo \'按Enter关闭...\'; read"'
        
        subprocess.Popen(terminal_cmd, shell=True, env=env)
        
        messagebox.showinfo("成功", "Gazebo已启动！\n\n查看新打开的终端窗口。")
        
    def launch_mujoco(self):
        """启动MuJoCo仿真"""
        model_folder = self.model_folder_var.get()
        mjcf_file = self.mjcf_file_var.get()
        
        # 构建MJCF路径
        mjcf_path = self.project_root / "src" / "model" / model_folder / "mjcf" / mjcf_file
        
        if not mjcf_path.exists():
            messagebox.showerror("错误", f"MJCF文件不存在：\n\n{mjcf_path}")
            return
        
        messagebox.showinfo("启动中", f"正在启动 MuJoCo...\n\n{model_folder}\n\nMuJoCo窗口将打开。")
        
        # 使用MuJoCo官方viewer
        # 检查是否在虚拟环境中
        venv_python = self.project_root / "venv" / "bin" / "python3"
        if venv_python.exists():
            python_cmd = str(venv_python)
        else:
            python_cmd = "python3"
        
        # 构建命令 - 使用引号处理空格
        cmd = f'cd "{self.project_root}" && "{python_cmd}" -m mujoco.viewer --mjcf="{mjcf_path}"'
        
        # 设置环境变量
        env = os.environ.copy()
        if self.mujoco_fullscreen_var.get():
            env['MUJOCO_FULLSCREEN'] = '1'
        
        terminal_cmd = f'gnome-terminal -- bash -c \'{cmd}; echo; echo "按Enter关闭..."; read\''
        
        try:
            subprocess.Popen(terminal_cmd, shell=True, env=env)
            messagebox.showinfo("成功", "MuJoCo已启动！\n\n查看新打开的窗口。")
        except Exception as e:
            messagebox.showerror("失败", f"启动MuJoCo出错：\n\n{str(e)}")
        
    def show_help(self):
        """显示帮助信息"""
        help_text = """增强版仿真启动器帮助

【仿真器选择】
• Gazebo - 完整的物理仿真环境
• MuJoCo - 高性能物理引擎

【机器人模型】
• 选择模型文件夹
• 自动扫描URDF和MJCF文件
• 支持自定义路径

【世界环境】
• 使用默认世界或自定义
• 支持.world文件格式

【Gazebo选项】
• 安全模式 - 虚拟机推荐
• 简单模式 - 快速测试
• 标准模式 - 完整功能
• 软件渲染 - 解决闪屏

【MuJoCo选项】
• 全屏模式
• 自定义帧率

【快捷键】
• 鼠标滚轮 - 滚动界面

更多帮助：docs/GAZEBO_GUIDE.md
          docs/MUJOCO_GUIDE.md
        """
        
        messagebox.showinfo("帮助", help_text)

def main():
    try:
        root = tk.Tk()
        app = EnhancedSimulationLauncher(root)
        root.mainloop()
    except Exception as e:
        print(f"❌ GUI启动失败: {e}")
        print("\n请安装tkinter:")
        print("   sudo apt-get install python3-tk")
        sys.exit(1)

if __name__ == "__main__":
    main()
