#!/usr/bin/env python3
"""
集成式MuJoCo控制演示
将控制器与MuJoCo仿真器集成在一起，实现真正的闭环控制
"""

import sys
import os
import time
import threading
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import mujoco
    import numpy as np
    from scipy.spatial.transform import Rotation
    MUJOCO_AVAILABLE = True
    
    # 尝试导入viewer
    try:
        from mujoco import viewer
        VIEWER_AVAILABLE = True
    except ImportError:
        VIEWER_AVAILABLE = False
        print("⚠️  MuJoCo viewer不可用，将使用离屏渲染")
        
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    MUJOCO_AVAILABLE = False
    VIEWER_AVAILABLE = False

# 导入控制器
try:
    from wheel_legged_control.controllers.rm_controller_node import RMControllerNode
    CONTROLLERS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ 控制器导入失败: {e}")
    CONTROLLERS_AVAILABLE = False

class IntegratedMuJoCoController:
    """集成式MuJoCo控制器 - 将控制器与仿真器结合"""
    
    def __init__(self, model_path: str = None):
        if not MUJOCO_AVAILABLE:
            raise RuntimeError("MuJoCo不可用")
        
        # 初始化MuJoCo模型
        if model_path and os.path.exists(model_path):
            self.model = mujoco.MjModel.from_xml_path(model_path)
        else:
            # 创建默认模型
            self.model = self._create_default_model()
        
        self.data = mujoco.MjData(self.model)
        
        # 关节映射
        self.joint_name_to_id = {}
        self.joint_id_to_name = {}
        self._setup_joint_mapping()
        
        # 控制器状态
        self.is_running = False
        self.control_thread = None
        self.viewer = None
        
        # 控制器实例
        if CONTROLLERS_AVAILABLE:
            self.controller = RMControllerNode()
            self.controller_enabled = True
        else:
            self.controller = None
            self.controller_enabled = False
        
        print("✅ 集成控制器初始化完成")
        print(f"📊 关节数量: {len(self.joint_name_to_id)}")
        print(f"🎮 控制器状态: {'启用' if self.controller_enabled else '禁用'}")
    
    def _create_default_model(self):
        """创建默认的轮腿机器人模型"""
        xml_string = '''
<mujoco model="wheel_legged_robot">
    <compiler angle="radian" inertiafromgeom="true"/>
    <option timestep="0.002" iterations="50" solver="Newton"/>
    
    <asset>
        <material name="groundplane" rgba="0.5 0.5 0.5 1"/>
        <material name="robot" rgba="0.8 0.6 0.4 1"/>
    </asset>
    
    <worldbody>
        <light directional="true" diffuse=".8 .8 .8" pos="0 0 3" dir="0 0 -1"/>
        <geom name="floor" type="plane" size="10 10 0.1" material="groundplane"/>
        
        <!-- 机器人主体 -->
        <body name="base" pos="0 0 0.5">
            <freejoint name="floating_base"/>
            <geom type="box" size="0.2 0.15 0.05" material="robot"/>
            
            <!-- 左腿 -->
            <body name="left_hip" pos="0.1 0.1 0">
                <joint name="lf0_Joint" type="hinge" axis="0 1 0" range="-1.5 1.5"/>
                <geom type="capsule" size="0.03 0.1" pos="0 0 -0.1" material="robot"/>
                <body name="left_knee" pos="0 0 -0.2">
                    <joint name="lf1_Joint" type="hinge" axis="0 1 0" range="-2.0 2.0"/>
                    <geom type="capsule" size="0.03 0.15" pos="0 0 -0.15" material="robot"/>
                </body>
            </body>
            
            <!-- 右腿 -->
            <body name="right_hip" pos="0.1 -0.1 0">
                <joint name="rf0_Joint" type="hinge" axis="0 1 0" range="-1.5 1.5"/>
                <geom type="capsule" size="0.03 0.1" pos="0 0 -0.1" material="robot"/>
                <body name="right_knee" pos="0 0 -0.2">
                    <joint name="rf1_Joint" type="hinge" axis="0 1 0" range="-2.0 2.0"/>
                    <geom type="capsule" size="0.03 0.15" pos="0 0 -0.15" material="robot"/>
                </body>
            </body>
            
            <!-- 左轮 -->
            <body name="left_wheel" pos="-0.2 0.15 -0.05">
                <joint name="l_wheel_Joint" type="hinge" axis="0 1 0" range="-10 10"/>
                <geom type="cylinder" size="0.08 0.02" material="robot"/>
            </body>
            
            <!-- 右轮 -->
            <body name="right_wheel" pos="-0.2 -0.15 -0.05">
                <joint name="r_wheel_Joint" type="hinge" axis="0 1 0" range="-10 10"/>
                <geom type="cylinder" size="0.08 0.02" material="robot"/>
            </body>
        </body>
    </worldbody>
    
    <actuator>
        <motor name="lf0_motor" joint="lf0_Joint" gear="50"/>
        <motor name="lf1_motor" joint="lf1_Joint" gear="50"/>
        <motor name="rf0_motor" joint="rf0_Joint" gear="50"/>
        <motor name="rf1_motor" joint="rf1_Joint" gear="50"/>
        <motor name="l_wheel_motor" joint="l_wheel_Joint" gear="20"/>
        <motor name="r_wheel_motor" joint="r_wheel_Joint" gear="20"/>
    </actuator>
</mujoco>
        '''
        
        # 写入临时文件
        temp_path = "/tmp/default_wheel_legged_robot.xml"
        with open(temp_path, 'w') as f:
            f.write(xml_string)
        
        return mujoco.MjModel.from_xml_path(temp_path)
    
    def _setup_joint_mapping(self):
        """设置关节映射"""
        for i in range(self.model.njnt):
            joint_name = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_JOINT, i)
            if joint_name:
                self.joint_name_to_id[joint_name] = i
                self.joint_id_to_name[i] = joint_name
        
        print(f"📊 关节映射: {self.joint_name_to_id}")
    
    def update_joint_states(self):
        """更新关节状态到控制器"""
        if not self.controller:
            return
        
        for joint_name, joint_id in self.joint_name_to_id.items():
            if joint_id < len(self.data.qpos):
                position = self.data.qpos[joint_id]
                velocity = self.data.qvel[joint_id] if joint_id < len(self.data.qvel) else 0.0
                effort = 0.0  # MuJoCo中需要额外计算
                
                # 更新控制器状态
                if hasattr(self.controller, 'controller'):
                    self.controller.controller.update_joint_state(joint_name, position, velocity, effort)
    
    def apply_control(self):
        """应用控制器输出到仿真器"""
        if not self.controller or not self.controller_enabled:
            return
        
        # 获取当前关节位置作为目标（或者使用控制器的运动模式）
        current_time = time.time()
        
        if hasattr(self.controller, 'leg_test_active') and self.controller.leg_test_active:
            # 使用腿部测试轨迹
            target_positions = self.controller.get_current_leg_test_target(current_time)
        else:
            # 使用默认站立位置
            target_positions = {
                'lf0_Joint': 0.1,
                'lf1_Joint': -0.3,
                'l_wheel_Joint': 0.0,
                'rf0_Joint': 0.1,
                'rf1_Joint': -0.3,
                'r_wheel_Joint': 0.0
            }
        
        # 计算控制输出
        dt = 0.01
        control_outputs = self.controller.controller.compute_control(target_positions, dt)
        
        # 应用到执行器
        for joint_name, torque in control_outputs.items():
            if joint_name in self.joint_name_to_id:
                joint_id = self.joint_name_to_id[joint_name]
                # 找到对应的执行器
                for i in range(self.model.nu):
                    actuator_name = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, i)
                    if actuator_name and joint_name.replace('_Joint', '') in actuator_name:
                        self.data.ctrl[i] = torque
                        break
    
    def control_loop(self):
        """控制循环"""
        print("🎮 控制循环开始运行...")
        
        last_time = time.time()
        step_count = 0
        
        while self.is_running:
            current_time = time.time()
            dt = current_time - last_time
            
            if dt >= 0.01:  # 100Hz控制频率
                # 更新关节状态
                self.update_joint_states()
                
                # 应用控制
                self.apply_control()
                
                # 仿真步进
                mujoco.mj_step(self.model, self.data)
                
                step_count += 1
                if step_count % 500 == 0:  # 每5秒打印一次状态
                    print(f"⏱️  运行时间: {current_time - last_time:.1f}s, 步数: {step_count}")
                
                last_time = current_time
            
            time.sleep(0.001)  # 1ms睡眠避免占用过多CPU
    
    def start_control(self):
        """启动控制"""
        if self.is_running:
            print("⚠️  控制已经在运行")
            return
        
        self.is_running = True
        self.control_thread = threading.Thread(target=self.control_loop, daemon=True)
        self.control_thread.start()
        print("✅ 控制系统已启动")
    
    def stop_control(self):
        """停止控制"""
        self.is_running = False
        if self.control_thread:
            self.control_thread.join(timeout=1.0)
        print("⏹️  控制系统已停止")
    
    def run_with_viewer(self, duration: float = 30.0):
        """带可视化界面运行"""
        print(f"🎨 启动带可视化的仿真 (持续 {duration} 秒)...")
        
        # 启动控制
        self.start_control()
        
        if VIEWER_AVAILABLE:
            # 使用MuJoCo viewer
            with viewer.launch_passive(self.model, self.data) as viewer_obj:
                viewer_obj.cam.distance = 3.0
                viewer_obj.cam.lookat[:] = [0, 0, 0.5]
                viewer_obj.cam.elevation = -20
                
                start_time = time.time()
                while time.time() - start_time < duration and self.is_running:
                    # 更新viewer
                    viewer_obj.sync()
                    time.sleep(0.016)  # ~60 FPS
        else:
            # 离屏运行
            print("🖥️  离屏模式运行...")
            start_time = time.time()
            step_count = 0
            while time.time() - start_time < duration and self.is_running:
                time.sleep(0.01)
                step_count += 1
                if step_count % 500 == 0:
                    # 打印状态信息
                    base_pos = self.data.qpos[:3] if len(self.data.qpos) >= 3 else [0, 0, 0]
                    print(f"📊 仿真时间: {time.time() - start_time:.1f}s, "
                          f"位置: [{base_pos[0]:.2f}, {base_pos[1]:.2f}, {base_pos[2]:.2f}]")
        
        # 停止控制
        self.stop_control()
        print("👋 仿真结束")

def main():
    """主函数"""
    print("🚀 集成式MuJoCo控制演示")
    print("=" * 50)
    
    try:
        # 创建集成控制器
        controller = IntegratedMuJoCoController()
        
        # 运行仿真
        controller.run_with_viewer(duration=30.0)
        
        print("\n🎉 演示完成!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
    except Exception as e:
        print(f"\n❌ 运行错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()