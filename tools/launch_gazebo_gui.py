#!/usr/bin/env python3
"""
Gazebo启动器 - GUI版本
使用图形界面选择机器人模型和启动选项
"""

import sys
import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox

class GazeboLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Gazebo启动器")
        
        # 获取屏幕尺寸
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        # 设置窗口大小（不超过屏幕的80%）
        window_width = min(600, int(screen_width * 0.8))
        window_height = min(480, int(screen_height * 0.8))
        
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.resizable(True, True)
        
        # 设置工作目录为项目根目录
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        os.chdir(self.project_root)
        
        # 变量
        self.model_var = tk.StringVar(value="RM_Serial_Wheeled-leg_Robot")
        self.mode_var = tk.StringVar(value="safe")
        self.software_render_var = tk.BooleanVar(value=True)
        
        self.create_widgets()
        
    def create_widgets(self):
        # 标题
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="轮腿机器人 Gazebo 启动器",
            font=("Arial", 16, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(pady=15)
        
        # 创建可滚动的主内容区
        canvas = tk.Canvas(self.root)
        scrollbar = tk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 主内容
        main_frame = tk.Frame(scrollable_frame, padx=20, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 机器人模型选择
        model_frame = tk.LabelFrame(
            main_frame, 
            text="机器人模型", 
            font=("Arial", 11, "bold"), 
            padx=12, 
            pady=10
        )
        model_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Radiobutton(
            model_frame,
            text="RM串联轮腿机器人",
            variable=self.model_var,
            value="RM_Serial_Wheeled-leg_Robot",
            font=("Arial", 10)
        ).pack(anchor=tk.W, pady=3)
        
        tk.Radiobutton(
            model_frame,
            text="DM轮腿机器人",
            variable=self.model_var,
            value="DM_Wheel_leg_robot",
            font=("Arial", 10)
        ).pack(anchor=tk.W, pady=3)
        
        # 启动模式选择
        mode_frame = tk.LabelFrame(
            main_frame, 
            text="启动模式", 
            font=("Arial", 11, "bold"), 
            padx=12, 
            pady=10
        )
        mode_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Radiobutton(
            mode_frame,
            text="安全模式 (推荐虚拟机)",
            variable=self.mode_var,
            value="safe",
            font=("Arial", 10)
        ).pack(anchor=tk.W, pady=3)
        
        tk.Radiobutton(
            mode_frame,
            text="简单模式",
            variable=self.mode_var,
            value="simple",
            font=("Arial", 10)
        ).pack(anchor=tk.W, pady=3)
        
        tk.Radiobutton(
            mode_frame,
            text="标准模式",
            variable=self.mode_var,
            value="standard",
            font=("Arial", 10)
        ).pack(anchor=tk.W, pady=3)
        
        # 高级选项
        advanced_frame = tk.LabelFrame(
            main_frame, 
            text="高级选项", 
            font=("Arial", 11, "bold"), 
            padx=12, 
            pady=10
        )
        advanced_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Checkbutton(
            advanced_frame,
            text="强制软件渲染 (解决闪屏)",
            variable=self.software_render_var,
            font=("Arial", 10)
        ).pack(anchor=tk.W, pady=3)
        
        # 打包canvas和scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 底部按钮区（固定在底部）
        button_frame = tk.Frame(self.root, bg="#ecf0f1", pady=12)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 按钮容器
        btn_container = tk.Frame(button_frame, bg="#ecf0f1")
        btn_container.pack()
        
        # 启动按钮
        tk.Button(
            btn_container,
            text="启动 Gazebo",
            command=self.launch_gazebo,
            font=("Arial", 12, "bold"),
            bg="#27ae60",
            fg="white",
            padx=25,
            pady=10,
            cursor="hand2",
            relief=tk.RAISED,
            bd=2,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        # 帮助按钮
        tk.Button(
            btn_container,
            text="帮助",
            command=self.show_help,
            font=("Arial", 11),
            bg="#3498db",
            fg="white",
            padx=15,
            pady=10,
            cursor="hand2",
            relief=tk.RAISED,
            bd=2,
            width=8
        ).pack(side=tk.LEFT, padx=5)
        
        # 退出按钮
        tk.Button(
            btn_container,
            text="退出",
            command=self.root.quit,
            font=("Arial", 11),
            bg="#e74c3c",
            fg="white",
            padx=15,
            pady=10,
            cursor="hand2",
            relief=tk.RAISED,
            bd=2,
            width=8
        ).pack(side=tk.LEFT, padx=5)
        
    def launch_gazebo(self):
        """启动Gazebo"""
        model = self.model_var.get()
        mode = self.mode_var.get()
        software_render = self.software_render_var.get()
        
        # 确认对话框
        model_name = "RM串联轮腿机器人" if model == "RM_Serial_Wheeled-leg_Robot" else "DM轮腿机器人"
        mode_name = {"safe": "安全模式", "simple": "简单模式", "standard": "标准模式"}[mode]
        
        msg = f"即将启动Gazebo仿真：\n\n"
        msg += f"机器人：{model_name}\n"
        msg += f"模式：{mode_name}\n"
        msg += f"软件渲染：{'是' if software_render else '否'}\n\n"
        msg += "确认启动？"
        
        if not messagebox.askyesno("确认", msg):
            return
        
        # 构建命令
        script_map = {
            "safe": "./tools/launch_gazebo_safe.sh",
            "simple": "./tools/launch_gazebo_simple.sh",
            "standard": "./tools/launch_gazebo.sh"
        }
        
        script = script_map[mode]
        
        # 检查脚本是否存在
        if not os.path.exists(script):
            messagebox.showerror("错误", f"启动脚本不存在：{script}")
            return
        
        # 设置环境变量
        env = os.environ.copy()
        
        if software_render:
            env["LIBGL_ALWAYS_SOFTWARE"] = "1"
            env["MESA_GL_VERSION_OVERRIDE"] = "3.3"
            env["GALLIUM_DRIVER"] = "llvmpipe"
        
        # 准备命令
        model_choice = "1" if model == "RM_Serial_Wheeled-leg_Robot" else "2"
        
        try:
            messagebox.showinfo("启动中", f"正在启动 {model_name}...\n\nGazebo将在新终端中打开。")
            
            # 启动Gazebo
            cmd = f'echo "{model_choice}" | {script}'
            terminal_cmd = f'gnome-terminal -- bash -c "{cmd}; echo; echo \'按Enter关闭...\'; read"'
            
            subprocess.Popen(terminal_cmd, shell=True, env=env)
            
            messagebox.showinfo("成功", "Gazebo已启动！\n\n查看新打开的终端窗口。")
            
        except Exception as e:
            messagebox.showerror("失败", f"启动出错：\n\n{str(e)}")
    
    def show_help(self):
        """显示帮助信息"""
        help_text = """Gazebo启动器帮助

【机器人模型】
• RM串联轮腿机器人 - 推荐
• DM轮腿机器人 - 需先修复

【启动模式】
• 安全模式 - 虚拟机推荐
• 简单模式 - 快速测试
• 标准模式 - 物理机

【高级选项】
• 软件渲染 - 解决闪屏问题

【常见问题】
1. 闪屏 → 安全模式+软件渲染
2. DM无法加载 → 运行修复脚本
3. 窗口不开 → 检查Gazebo安装

更多帮助：docs/guides/
        """
        
        messagebox.showinfo("帮助", help_text)

def main():
    try:
        root = tk.Tk()
        app = GazeboLauncher(root)
        root.mainloop()
    except Exception as e:
        print(f"❌ GUI启动失败: {e}")
        print("\n请安装tkinter:")
        print("   sudo apt-get install python3-tk")
        sys.exit(1)

if __name__ == "__main__":
    main()
