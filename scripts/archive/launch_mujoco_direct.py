#!/usr/bin/env python3
"""
直接启动MuJoCo查看器 - 避免GUI渲染问题

配置后直接打开MuJoCo的原生交互式查看器
"""

import sys
import os
from pathlib import Path

# 保存原始工作目录
original_dir = os.getcwd()

# 设置路径
venv_site_packages = os.path.join(original_dir, 'venv/lib/python3.12/site-packages')
sys.path.insert(0, venv_site_packages)
sys.path.insert(0, os.path.join(original_dir, 'src/wheel_legged_control'))

import mujoco
import mujoco.viewer
import numpy as np
from wheel_legged_control.simulation.mujoco_backend import URDFToMJCFConverter

print("🚀 轮腿机器人MuJoCo直接启动")
print("=" * 60)

# 1. 选择机器人模型
print("\n📦 可用的机器人模型:")
models = {
    '1': {
        'name': 'RM_Serial_Wheeled-leg_Robot',
        'path': 'src/model/RM_Serial_Wheeled-leg_Robot/urdf/RM_Serial_Wheeled-leg_Robot.urdf',
        'description': 'RM串联轮腿机器人'
    },
    '2': {
        'name': 'DM_Wheel_leg_robot',
        'path': 'src/model/DM_Wheel_leg_robot/urdf/wheel_legged_urdf_pkg.urdf',
        'description': 'DM轮腿机器人'
    },
    '3': {
        'name': '简化测试模型',
        'path': None,
        'description': '用于快速测试的简化模型'
    }
}

for key, model in models.items():
    if model['path'] is None:
        status = "✅"
    else:
        full_path = os.path.join(original_dir, model['path'])
        status = "✅" if Path(full_path).exists() else "❌"
    print(f"  {key}. {status} {model['name']} - {model['description']}")

choice = input("\n请选择模型 (1-3) [默认: 1]: ").strip() or '1'

if choice not in models:
    print(f"❌ 无效选择: {choice}")
    sys.exit(1)

selected_model = models[choice]
print(f"\n✅ 已选择: {selected_model['name']}")

# 2. 准备模型
print("\n🔧 准备MuJoCo模型...")

model = None
data = None

if selected_model['path'] is None:
    # 使用简化测试模型
    converter = URDFToMJCFConverter()
    model_path = converter._create_simple_mjcf("robot_model.xml")
    print(f"✅ 创建简化模型: {model_path}")
    
    # 3. 加载MuJoCo模型
    print("\n📥 加载MuJoCo模型...")
    try:
        model = mujoco.MjModel.from_xml_path(model_path)
        data = mujoco.MjData(model)
        print(f"✅ 模型加载成功")
        print(f"   关节数量: {model.njnt}")
        print(f"   执行器数量: {model.nu}")
        print(f"   体数量: {model.nbody}")
        print(f"   网格数量: {model.nmesh}")
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
else:
    # 使用URDF文件 - 创建临时URDF修正mesh路径
    urdf_path = os.path.join(original_dir, selected_model['path'])
    if not Path(urdf_path).exists():
        print(f"❌ 模型文件不存在: {urdf_path}")
        sys.exit(1)
    
    print(f"✅ 使用URDF文件: {selected_model['path']}")
    print(f"   准备修正mesh路径...")
    
    # 读取URDF内容
    with open(urdf_path, 'r', encoding='utf-8') as f:
        urdf_content = f.read()
    
    # 修正mesh路径：将../meshes/替换为绝对路径
    model_dir = os.path.dirname(os.path.dirname(urdf_path))  # 模型根目录
    meshes_dir = os.path.join(model_dir, 'meshes')
    
    # 替换相对路径为绝对路径
    import re
    urdf_content = re.sub(
        r'filename="\.\.\/meshes\/',
        f'filename="{meshes_dir}/',
        urdf_content
    )
    # 也处理package://路径（DM模型）
    urdf_content = re.sub(
        r'filename="package://[^/]+/meshes/',
        f'filename="{meshes_dir}/',
        urdf_content
    )
    
    # 保存临时URDF
    temp_urdf_path = "temp_robot_model.urdf"
    with open(temp_urdf_path, 'w', encoding='utf-8') as f:
        f.write(urdf_content)
    
    print(f"   ✅ 创建临时URDF: {temp_urdf_path}")
    print(f"   Mesh目录: {meshes_dir}")
    
    # 3. 加载MuJoCo模型
    print("\n📥 加载MuJoCo模型...")
    try:
        model = mujoco.MjModel.from_xml_path(temp_urdf_path)
        data = mujoco.MjData(model)
        
        print(f"✅ 模型加载成功")
        print(f"   关节数量: {model.njnt}")
        print(f"   执行器数量: {model.nu}")
        print(f"   体数量: {model.nbody}")
        print(f"   网格数量: {model.nmesh}")
        
        if model.nmesh > 0:
            print(f"   ✅ 成功加载 {model.nmesh} 个网格文件")
        else:
            print(f"   ⚠️  警告: 没有加载到网格文件")
        
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        print(f"\n💡 提示: URDF文件可能存在以下问题:")
        print(f"   1. mesh文件路径不正确")
        print(f"   2. mesh文件不存在")
        print(f"   3. URDF格式有误")
        print(f"\n建议: 使用简化模型（选项3）进行测试")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# 4. 配置仿真参数
print("\n⚙️  仿真配置:")
print(f"   时间步长: {model.opt.timestep} s")
print(f"   重力: {model.opt.gravity}")
print(f"   求解器: Newton")

# 5. 启动MuJoCo交互式查看器
print("\n" + "=" * 60)
print("🎨 启动MuJoCo交互式查看器...")
print("=" * 60)
print("\n💡 使用说明:")
print("   - 鼠标左键拖动: 旋转视角")
print("   - 鼠标右键拖动: 平移视角")
print("   - 鼠标滚轮: 缩放")
print("   - 空格键: 暂停/继续仿真")
print("   - Ctrl+R: 重置仿真")
print("   - Tab: 切换显示选项")
print("   - F1: 显示帮助")
print("   - Esc: 退出")
print("\n🎮 控制器:")
print("   - 可以在查看器中实时调整关节位置")
print("   - 可以应用外力测试机器人响应")
print("   - 可以修改物理参数")
print("\n按 Ctrl+C 退出程序")
print("=" * 60)

try:
    # 启动被动查看器（允许外部控制）
    with mujoco.viewer.launch_passive(model, data) as viewer:
        # 设置相机
        viewer.cam.distance = 2.0
        viewer.cam.elevation = -20
        viewer.cam.azimuth = 45
        
        # 仿真循环
        step_count = 0
        while viewer.is_running():
            # 执行仿真步
            mujoco.mj_step(model, data)
            
            # 可以在这里添加控制逻辑
            # 例如：简单的正弦波控制
            if model.nu > 0:
                for i in range(min(4, model.nu)):
                    data.ctrl[i] = 0.5 * np.sin(data.time * 2.0 + i * np.pi / 2)
            
            # 同步查看器
            viewer.sync()
            
            step_count += 1
            
            # 每1000步打印一次状态
            if step_count % 1000 == 0:
                print(f"⏱️  仿真时间: {data.time:.2f}s, 步数: {step_count}")

except KeyboardInterrupt:
    print("\n\n⏹️  用户中断")
except Exception as e:
    print(f"\n\n❌ 运行错误: {e}")
    import traceback
    traceback.print_exc()
finally:
    print("\n🧹 清理资源...")
    # 确保回到原目录
    os.chdir(original_dir)
    # 清理临时文件
    if os.path.exists("robot_model.xml"):
        os.remove("robot_model.xml")
    if os.path.exists("temp_robot_model.urdf"):
        os.remove("temp_robot_model.urdf")
    print("✅ 清理完成")

print("\n👋 感谢使用！")
