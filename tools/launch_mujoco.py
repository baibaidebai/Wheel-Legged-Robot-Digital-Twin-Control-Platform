#!/usr/bin/env python3
"""
MuJoCo仿真启动器
支持命令行参数和GUI调用
"""

import argparse
import sys
import os
from pathlib import Path

def check_mujoco():
    """检查MuJoCo是否安装"""
    try:
        import mujoco
        print(f"✅ MuJoCo版本: {mujoco.__version__}")
        return True
    except ImportError:
        print("❌ MuJoCo未安装")
        print("\n安装命令:")
        print("   pip install mujoco -i https://pypi.tuna.tsinghua.edu.cn/simple")
        return False

def find_mjcf_file(model_name):
    """查找MJCF文件"""
    project_root = Path(__file__).parent.parent
    
    model_map = {
        "rm": "RM_Serial_Wheeled-leg_Robot",
        "dm": "DM_Wheel_leg_robot"
    }
    
    folder_name = model_map.get(model_name.lower())
    if not folder_name:
        return None
    
    model_dir = project_root / "src" / "model" / folder_name / "mjcf"
    
    # 优先使用Wiki-MJCF版本
    wiki_file = model_dir / f"{folder_name}_wiki.xml"
    if wiki_file.exists():
        return wiki_file
    
    # 否则使用第一个找到的MJCF文件
    mjcf_files = list(model_dir.glob("*.xml"))
    if mjcf_files:
        return mjcf_files[0]
    
    return None

def launch_mujoco(mjcf_path, fullscreen=False, fps=60, render_backend="glfw"):
    """启动MuJoCo仿真"""
    import subprocess
    import sys
    
    print(f"\n🎨 启动MuJoCo Viewer...")
    print(f"   模型: {mjcf_path}")
    print(f"   渲染后端: {render_backend}")
    
    # 使用MuJoCo官方viewer
    cmd = [
        sys.executable,
        "-m",
        "mujoco.viewer",
        f"--mjcf={mjcf_path}"
    ]
    
    print(f"\n执行命令: {' '.join(cmd)}")
    print("\n控制说明:")
    print("  鼠标左键 - 旋转视角")
    print("  鼠标右键 - 平移视角")
    print("  鼠标滚轮 - 缩放")
    print("  空格键 - 暂停/继续")
    print("  Backspace - 重置仿真")
    print("  ESC/关闭窗口 - 退出")
    print("\n" + "="*50 + "\n")
    
    try:
        # 设置环境变量
        import os
        env = os.environ.copy()
        env['MUJOCO_GL'] = render_backend
        
        # 启动viewer
        result = subprocess.run(cmd, env=env)
        
        if result.returncode == 0:
            print("\n👋 MuJoCo仿真已关闭")
            return True
        else:
            print(f"\n❌ MuJoCo退出，返回码: {result.returncode}")
            return False
            
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        return True
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        print("\n可能的解决方案:")
        print("  1. 确认MuJoCo已安装:")
        print("     pip install mujoco")
        print("\n  2. 确认模型文件存在:")
        print(f"     ls -la {mjcf_path}")
        print("\n  3. 尝试直接启动:")
        print(f"     python3 -m mujoco.viewer --mjcf={mjcf_path}")
        print()
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(
        description="MuJoCo仿真启动器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用预设模型
  python3 launch_mujoco.py --model rm
  python3 launch_mujoco.py --model dm
  
  # 使用自定义MJCF文件
  python3 launch_mujoco.py --mjcf path/to/model.xml
  
  # 全屏模式
  python3 launch_mujoco.py --model rm --fullscreen
  
  # 自定义帧率
  python3 launch_mujoco.py --model rm --fps 120
        """
    )
    
    parser.add_argument(
        "--model",
        choices=["rm", "dm"],
        help="预设机器人模型 (rm=RM机器人, dm=DM机器人)"
    )
    
    parser.add_argument(
        "--mjcf",
        type=str,
        help="MJCF文件路径"
    )
    
    parser.add_argument(
        "--fullscreen",
        action="store_true",
        help="全屏模式"
    )
    
    parser.add_argument(
        "--fps",
        type=int,
        default=60,
        help="目标帧率 (默认: 60)"
    )
    
    parser.add_argument(
        "--render",
        choices=["glfw", "osmesa", "egl"],
        default="glfw",
        help="渲染后端 (glfw=硬件, osmesa=软件, egl=无头)"
    )
    
    args = parser.parse_args()
    
    # 检查MuJoCo
    if not check_mujoco():
        return 1
    
    # 确定MJCF文件
    mjcf_path = None
    
    if args.mjcf:
        mjcf_path = Path(args.mjcf)
        if not mjcf_path.exists():
            print(f"❌ MJCF文件不存在: {mjcf_path}")
            return 1
    elif args.model:
        mjcf_path = find_mjcf_file(args.model)
        if not mjcf_path:
            print(f"❌ 找不到模型 '{args.model}' 的MJCF文件")
            print("\n请先转换模型:")
            print("   python3 tools/test_wiki_mjcf.py")
            return 1
    else:
        print("❌ 请指定 --model 或 --mjcf 参数")
        parser.print_help()
        return 1
    
    # 启动MuJoCo
    success = launch_mujoco(mjcf_path, args.fullscreen, args.fps, args.render)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
