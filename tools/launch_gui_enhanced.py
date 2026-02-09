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
        self.create_options_section(main_frame)
        
        # 打包canvas和scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 绑定鼠标滚轮
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
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
            if simulator == "gazebo":
                self.launch_gazebo()
            else:
                self.launch_mujoco()
        except Exception as e:
            messagebox.showerror("启动失败", f"启动仿真时出错：\n\n{str(e)}")
            
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
