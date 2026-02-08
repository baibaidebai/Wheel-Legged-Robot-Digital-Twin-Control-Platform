#!/usr/bin/env python3
"""测试GUI是否能正常显示"""

import tkinter as tk
from tkinter import messagebox

def test_gui():
    root = tk.Tk()
    root.title("GUI测试")
    root.geometry("400x300")
    
    label = tk.Label(root, text="如果你能看到这个窗口，说明GUI可以工作！", font=("Arial", 12))
    label.pack(pady=50)
    
    def show_message():
        messagebox.showinfo("测试", "按钮点击成功！")
    
    button = tk.Button(
        root,
        text="🚀 点击测试",
        command=show_message,
        font=("Arial", 14, "bold"),
        bg="#27ae60",
        fg="white",
        padx=20,
        pady=10
    )
    button.pack(pady=20)
    
    quit_btn = tk.Button(
        root,
        text="❌ 退出",
        command=root.quit,
        font=("Arial", 12),
        bg="#e74c3c",
        fg="white",
        padx=20,
        pady=10
    )
    quit_btn.pack(pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    test_gui()
