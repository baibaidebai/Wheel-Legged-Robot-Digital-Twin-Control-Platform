#!/usr/bin/env python3
"""
MuJoCo简单启动器 - 使用简化模型
由于MuJoCo的URDF mesh路径解析问题，使用简化的MJCF模型
"""

import sys
import os

try:
    import mujoco
    import mujoco.viewer
except ImportError:
    print("❌ MuJoCo未安装")
    print("安装命令: pip install mujoco")
    sys.exit(1)

# 简化的轮腿机器人MJCF模型
SIMPLE_ROBOT_XML = '''
<mujoco model="wheel_legged_robot">
    <compiler angle="degree" />
    
    <option timestep="0.001" gravity="0 0 -9.81" />
    
    <asset>
        <texture name="grid" type="2d" builtin="checker" rgb1="0.1 0.2 0.3" rgb2="0.2 0.3 0.4" width="300" height="300"/>
        <material name="grid" texture="grid" texrepeat="8 8" reflectance="0.2"/>
    </asset>
    
    <worldbody>
        <geom name="ground" type="plane" size="10 10 0.1" material="grid"/>
        <light name="light" pos="0 0 3"/>
        
        <!-- 基座 -->
        <body name="base_link" pos="0 0 0.3">
            <inertial mass="8.8" pos="0 0 0" diaginertia="0.33 0.23 0.22"/>
            <geom name="base" type="box" size="0.2 0.15 0.05" rgba="0.8 0.2 0.2 1"/>
            
            <!-- 左前腿 -->
            <body name="lf0_link" pos="0.15 0.1 0">
                <inertial mass="0.16" pos="0.06 0 0.01" diaginertia="0.001 0.001 0.001"/>
                <joint name="lf0_Joint" type="hinge" axis="1 0 0" range="-90 90" damping="0.1"/>
                <geom name="lf0" type="capsule" size="0.02 0.08" rgba="0.2 0.8 0.2 1" fromto="0 0 0 0.12 0 0"/>
                
                <body name="lf1_link" pos="0.12 0 0">
                    <inertial mass="0.12" pos="0 0 -0.1" diaginertia="0.001 0.001 0.001"/>
                    <joint name="lf1_Joint" type="hinge" axis="1 0 0" range="-120 120" damping="0.1"/>
                    <geom name="lf1" type="capsule" size="0.015 0.1" rgba="0.2 0.8 0.2 1" fromto="0 0 0 0 0 -0.2"/>
                    
                    <body name="l_wheel" pos="0 0 -0.2">
                        <inertial mass="0.2" pos="0 0 0" diaginertia="0.005 0.005 0.005"/>
                        <joint name="l_wheel_Joint" type="hinge" axis="0 1 0" damping="0.05"/>
                        <geom name="l_wheel" type="cylinder" size="0.05 0.02" rgba="0.2 0.2 0.8 1"/>
                    </body>
                </body>
            </body>
            
            <!-- 右前腿 -->
            <body name="rf0_link" pos="0.15 -0.1 0">
                <inertial mass="0.16" pos="0.06 0 0.01" diaginertia="0.001 0.001 0.001"/>
                <joint name="rf0_Joint" type="hinge" axis="1 0 0" range="-90 90" damping="0.1"/>
                <geom name="rf0" type="capsule" size="0.02 0.08" rgba="0.2 0.8 0.2 1" fromto="0 0 0 0.12 0 0"/>
                
                <body name="rf1_link" pos="0.12 0 0">
                    <inertial mass="0.12" pos="0 0 -0.1" diaginertia="0.001 0.001 0.001"/>
                    <joint name="rf1_Joint" type="hinge" axis="1 0 0" range="-120 120" damping="0.1"/>
                    <geom name="rf1" type="capsule" size="0.015 0.1" rgba="0.2 0.8 0.2 1" fromto="0 0 0 0 0 -0.2"/>
                    
                    <body name="r_wheel" pos="0 0 -0.2">
                        <inertial mass="0.2" pos="0 0 0" diaginertia="0.005 0.005 0.005"/>
                        <joint name="r_wheel_Joint" type="hinge" axis="0 1 0" damping="0.05"/>
                        <geom name="r_wheel" type="cylinder" size="0.05 0.02" rgba="0.2 0.2 0.8 1"/>
                    </body>
                </body>
            </body>
        </body>
    </worldbody>
    
    <actuator>
        <motor name="lf0_motor" joint="lf0_Joint" gear="1" ctrllimited="true" ctrlrange="-10 10"/>
        <motor name="lf1_motor" joint="lf1_Joint" gear="1" ctrllimited="true" ctrlrange="-10 10"/>
        <motor name="rf0_motor" joint="rf0_Joint" gear="1" ctrllimited="true" ctrlrange="-10 10"/>
        <motor name="rf1_motor" joint="rf1_Joint" gear="1" ctrllimited="true" ctrlrange="-10 10"/>
        <motor name="l_wheel_motor" joint="l_wheel_Joint" gear="1" ctrllimited="true" ctrlrange="-10 10"/>
        <motor name="r_wheel_motor" joint="r_wheel_Joint" gear="1" ctrllimited="true" ctrlrange="-10 10"/>
    </actuator>
</mujoco>
'''

def main():
    print("🚀 启动MuJoCo仿真（简化模型）")
    print("=" * 50)
    print(f"MuJoCo版本: {mujoco.__version__}")
    print("=" * 50)
    print()
    
    print("💡 说明：由于MuJoCo的URDF mesh路径解析限制")
    print("   使用简化的几何体模型代替STL mesh文件")
    print()
    
    try:
        # 从XML字符串加载模型
        print("📦 加载简化机器人模型...")
        model = mujoco.MjModel.from_xml_string(SIMPLE_ROBOT_XML)
        data = mujoco.MjData(model)
        
        print(f"✅ 模型加载成功!")
        print(f"   自由度: {model.nv}")
        print(f"   关节数: {model.njnt}")
        print(f"   刚体数: {model.nbody}")
        print()
        
        # 打印关节信息
        print("🔧 关节信息:")
        for i in range(model.njnt):
            joint_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i)
            joint_type = model.jnt_type[i]
            type_names = {0: "free", 1: "ball", 2: "slide", 3: "hinge"}
            print(f"   {i}: {joint_name} ({type_names.get(joint_type, 'unknown')})")
        print()
        
        # 启动可视化
        print("🎨 启动MuJoCo可视化...")
        print()
        print("💡 控制说明:")
        print("   - 鼠标左键: 旋转视角")
        print("   - 鼠标右键: 平移视角")
        print("   - 鼠标滚轮: 缩放")
        print("   - 空格键: 暂停/继续")
        print("   - Backspace: 重置仿真")
        print("   - Ctrl+Q 或关闭窗口: 退出")
        print()
        print("=" * 50)
        
        # 启动交互式查看器
        with mujoco.viewer.launch_passive(model, data) as viewer:
            # 设置相机位置
            viewer.cam.distance = 2.0
            viewer.cam.azimuth = 45
            viewer.cam.elevation = -20
            
            # 仿真循环
            step = 0
            while viewer.is_running():
                # 步进仿真
                mujoco.mj_step(model, data)
                
                # 更新可视化（每10步更新一次）
                if step % 10 == 0:
                    viewer.sync()
                
                step += 1
        
        print()
        print("👋 MuJoCo仿真已退出")
        return 0
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
