#!/usr/bin/env python3
"""
MuJoCo诊断工具
检查MuJoCo环境和显示配置
"""

import sys
import os
import subprocess

def check_mujoco():
    """检查MuJoCo安装"""
    print("🔍 检查MuJoCo安装...")
    try:
        import mujoco
        print(f"  ✅ MuJoCo {mujoco.__version__} 已安装")
        return True
    except ImportError:
        print("  ❌ MuJoCo未安装")
        print("     安装: pip install mujoco")
        return False

def check_display():
    """检查显示环境"""
    print("\n🔍 检查显示环境...")
    
    display = os.environ.get('DISPLAY')
    wayland = os.environ.get('WAYLAND_DISPLAY')
    xdg_session = os.environ.get('XDG_SESSION_TYPE')
    
    print(f"  DISPLAY: {display or '未设置'}")
    print(f"  WAYLAND_DISPLAY: {wayland or '未设置'}")
    print(f"  XDG_SESSION_TYPE: {xdg_session or '未设置'}")
    
    if xdg_session == 'wayland':
        print("\n  ⚠️  检测到Wayland会话")
        print("     MuJoCo在Wayland下可能有显示问题")
        print("     建议切换到X11:")
        print("       1. 注销")
        print("       2. 在登录界面选择 'Ubuntu on Xorg'")
        return False
    elif xdg_session == 'x11':
        print("  ✅ 使用X11会话")
        return True
    else:
        print("  ⚠️  无法确定会话类型")
        return False

def check_opengl():
    """检查OpenGL支持"""
    print("\n🔍 检查OpenGL...")
    
    try:
        result = subprocess.run(
            ['glxinfo', '-B'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            output = result.stdout
            print("  ✅ glxinfo可用")
            
            # 提取关键信息
            for line in output.split('\n'):
                if 'OpenGL vendor' in line or 'OpenGL renderer' in line or 'OpenGL version' in line:
                    print(f"     {line.strip()}")
            
            # 检查是否使用软件渲染
            if 'llvmpipe' in output.lower() or 'software' in output.lower():
                print("\n  ⚠️  使用软件渲染")
                print("     性能可能较低")
                print("     建议启用硬件加速")
            
            return True
        else:
            print("  ❌ glxinfo执行失败")
            return False
            
    except FileNotFoundError:
        print("  ⚠️  glxinfo未安装")
        print("     安装: sudo apt-get install mesa-utils")
        return False
    except Exception as e:
        print(f"  ❌ 检查失败: {e}")
        return False

def check_glfw():
    """检查GLFW库"""
    print("\n🔍 检查GLFW...")
    
    try:
        import glfw
        print(f"  ✅ GLFW Python绑定已安装")
        
        # 尝试初始化GLFW
        if glfw.init():
            print("  ✅ GLFW初始化成功")
            glfw.terminate()
            return True
        else:
            print("  ❌ GLFW初始化失败")
            return False
            
    except ImportError:
        print("  ❌ GLFW Python绑定未安装")
        print("     安装: pip install glfw")
        return False
    except Exception as e:
        print(f"  ⚠️  GLFW测试失败: {e}")
        return False

def check_system_libs():
    """检查系统库"""
    print("\n🔍 检查系统库...")
    
    libs = [
        'libglfw.so.3',
        'libGL.so.1',
        'libGLEW.so'
    ]
    
    all_found = True
    for lib in libs:
        result = subprocess.run(
            ['ldconfig', '-p'],
            capture_output=True,
            text=True
        )
        
        if lib in result.stdout:
            print(f"  ✅ {lib}")
        else:
            print(f"  ❌ {lib} 未找到")
            all_found = False
    
    if not all_found:
        print("\n  安装缺失的库:")
        print("    sudo apt-get install libglfw3 libglew-dev")
    
    return all_found

def test_simple_render():
    """测试简单渲染"""
    print("\n🔍 测试MuJoCo渲染...")
    
    try:
        import mujoco
        import numpy as np
        
        # 创建简单模型
        xml = """
        <mujoco>
            <worldbody>
                <light diffuse=".5 .5 .5" pos="0 0 3" dir="0 0 -1"/>
                <geom type="plane" size="1 1 0.1" rgba=".9 0 0 1"/>
                <body pos="0 0 1">
                    <joint type="free"/>
                    <geom type="sphere" size=".1" rgba="0 .9 0 1"/>
                </body>
            </worldbody>
        </mujoco>
        """
        
        model = mujoco.MjModel.from_xml_string(xml)
        data = mujoco.MjData(model)
        
        print("  ✅ 模型创建成功")
        
        # 尝试离屏渲染
        try:
            renderer = mujoco.Renderer(model, 640, 480)
            mujoco.mj_forward(model, data)
            renderer.update_scene(data)
            pixels = renderer.render()
            
            print("  ✅ 离屏渲染成功")
            print(f"     图像尺寸: {pixels.shape}")
            return True
            
        except Exception as e:
            print(f"  ❌ 渲染失败: {e}")
            return False
            
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False

def print_recommendations(results):
    """打印建议"""
    print("\n" + "="*60)
    print("💡 建议")
    print("="*60)
    
    if not results['mujoco']:
        print("\n1. 安装MuJoCo:")
        print("   pip install mujoco -i https://pypi.tuna.tsinghua.edu.cn/simple")
    
    if not results['display']:
        print("\n2. 切换到X11:")
        print("   - 注销当前会话")
        print("   - 在登录界面选择 'Ubuntu on Xorg'")
        print("   - 重新登录")
    
    if not results['glfw']:
        print("\n3. 安装GLFW:")
        print("   pip install glfw")
    
    if not results['system_libs']:
        print("\n4. 安装系统库:")
        print("   sudo apt-get install libglfw3 libglew-dev mesa-utils")
    
    if results['display'] and 'wayland' in os.environ.get('XDG_SESSION_TYPE', '').lower():
        print("\n5. 临时解决方案（使用软件渲染）:")
        print("   export MUJOCO_GL=osmesa")
        print("   python3 tools/launch_mujoco.py --model rm --render osmesa")
    
    print("\n6. 虚拟机用户:")
    print("   - 启用3D加速（VMware/VirtualBox设置）")
    print("   - 分配足够的显存（建议2GB+）")
    print("   - 安装Guest Additions/VMware Tools")
    
    print("\n7. 测试启动:")
    print("   python3 tools/launch_mujoco.py --model rm")
    print("   python3 tools/launch_mujoco.py --model rm --render osmesa  # 软件渲染")

def main():
    print("="*60)
    print("🔧 MuJoCo环境诊断工具")
    print("="*60)
    
    results = {
        'mujoco': check_mujoco(),
        'display': check_display(),
        'opengl': check_opengl(),
        'glfw': check_glfw(),
        'system_libs': check_system_libs(),
        'render': test_simple_render()
    }
    
    print("\n" + "="*60)
    print("📊 诊断结果")
    print("="*60)
    
    for key, value in results.items():
        status = "✅" if value else "❌"
        print(f"{status} {key}")
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"\n通过: {passed}/{total}")
    
    if passed == total:
        print("\n✅ 所有检查通过！MuJoCo应该可以正常运行。")
    else:
        print_recommendations(results)
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
