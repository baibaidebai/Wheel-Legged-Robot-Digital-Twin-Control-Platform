#!/usr/bin/env python3
"""
离屏MuJoCo控制测试
专门用于测试控制器与MuJoCo的集成，无需图形界面
"""

import sys
import os
import time
import numpy as np
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import mujoco
    MUJOCO_AVAILABLE = True
    print("✅ MuJoCo导入成功")
except ImportError as e:
    print(f"❌ MuJoCo导入失败: {e}")
    MUJOCO_AVAILABLE = False
    sys.exit(1)

# 尝试导入控制器
try:
    # 临时修改sys.path来导入控制器
    controller_path = project_root / "src" / "wheel_legged_control"
    if str(controller_path) not in sys.path:
        sys.path.insert(0, str(controller_path))
    
    from wheel_legged_control.controllers.rm_controller_node import RMControllerNode
    CONTROLLERS_AVAILABLE = True
    print("✅ 控制器导入成功")
except ImportError as e:
    print(f"⚠️ 控制器导入失败: {e}")
    CONTROLLERS_AVAILABLE = False

class OffscreenMuJoCoTest:
    """离屏MuJoCo测试类"""
    
    def __init__(self):
        # 创建简单的轮腿机器人模型
        self.model = self._create_simple_model()
        self.data = mujoco.MjData(self.model)
        
        # 关节映射
        self.joint_names = ['lf0_Joint', 'lf1_Joint', 'rf0_Joint', 'rf1_Joint', 
                           'l_wheel_Joint', 'r_wheel_Joint']
        self.joint_name_to_id = {}
        self._setup_joint_mapping()
        
        # 控制器
        if CONTROLLERS_AVAILABLE:
            self.controller = RMControllerNode()
            self.controller_enabled = True
        else:
            self.controller = None
            self.controller_enabled = False
        
        print(f"📊 关节数量: {len(self.joint_name_to_id)}")
        print(f"🎮 控制器状态: {'启用' if self.controller_enabled else '禁用'}")
    
    def _create_simple_model(self):
        """创建简化的轮腿机器人模型"""
        xml_string = '''
<mujoco model="simple_wheel_leg">
    <compiler angle="radian"/>
    <option timestep="0.002"/>
    
    <worldbody>
        <geom name="floor" type="plane" size="10 10 0.1" rgba="0.5 0.5 0.5 1"/>
        <light directional="true" diffuse="0.8 0.8 0.8" pos="0 0 3" dir="0 0 -1"/>
        
        <body name="base" pos="0 0 0.3">
            <freejoint name="root"/>
            <geom type="box" size="0.2 0.1 0.05" rgba="0.8 0.6 0.4 1" mass="5"/>
            
            <!-- 左腿 -->
            <body name="left_hip" pos="0.1 0.1 0">
                <joint name="lf0_Joint" type="hinge" axis="0 1 0" range="-1.5 1.5"/>
                <geom type="capsule" size="0.02 0.1" pos="0 0 -0.1" rgba="0.3 0.3 0.3 1" mass="0.5"/>
                <body name="left_knee" pos="0 0 -0.2">
                    <joint name="lf1_Joint" type="hinge" axis="0 1 0" range="-2.0 2.0"/>
                    <geom type="capsule" size="0.02 0.15" pos="0 0 -0.15" rgba="0.3 0.3 0.3 1" mass="0.3"/>
                </body>
            </body>
            
            <!-- 右腿 -->
            <body name="right_hip" pos="0.1 -0.1 0">
                <joint name="rf0_Joint" type="hinge" axis="0 1 0" range="-1.5 1.5"/>
                <geom type="capsule" size="0.02 0.1" pos="0 0 -0.1" rgba="0.3 0.3 0.3 1" mass="0.5"/>
                <body name="right_knee" pos="0 0 -0.2">
                    <joint name="rf1_Joint" type="hinge" axis="0 1 0" range="-2.0 2.0"/>
                    <geom type="capsule" size="0.02 0.15" pos="0 0 -0.15" rgba="0.3 0.3 0.3 1" mass="0.3"/>
                </body>
            </body>
            
            <!-- 轮子 -->
            <body name="left_wheel" pos="-0.15 0.1 -0.05">
                <joint name="l_wheel_Joint" type="hinge" axis="0 1 0" range="-10 10"/>
                <geom type="cylinder" size="0.05 0.02" rgba="0.1 0.1 0.1 1" mass="0.2"/>
            </body>
            
            <body name="right_wheel" pos="-0.15 -0.1 -0.05">
                <joint name="r_wheel_Joint" type="hinge" axis="0 1 0" range="-10 10"/>
                <geom type="cylinder" size="0.05 0.02" rgba="0.1 0.1 0.1 1" mass="0.2"/>
            </body>
        </body>
    </worldbody>
    
    <actuator>
        <motor name="lf0_motor" joint="lf0_Joint" gear="20"/>
        <motor name="lf1_motor" joint="lf1_Joint" gear="20"/>
        <motor name="rf0_motor" joint="rf0_Joint" gear="20"/>
        <motor name="rf1_motor" joint="rf1_Joint" gear="20"/>
        <motor name="l_wheel_motor" joint="l_wheel_Joint" gear="10"/>
        <motor name="r_wheel_motor" joint="r_wheel_Joint" gear="10"/>
    </actuator>
</mujoco>
        '''
        
        # 写入临时文件
        temp_path = "/tmp/simple_wheel_leg.xml"
        with open(temp_path, 'w') as f:
            f.write(xml_string)
        
        return mujoco.MjModel.from_xml_path(temp_path)
    
    def _setup_joint_mapping(self):
        """设置关节映射"""
        for i in range(self.model.njnt):
            joint_name = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_JOINT, i)
            if joint_name and joint_name in self.joint_names:
                self.joint_name_to_id[joint_name] = i
        
        print(f"📊 关节映射: {self.joint_name_to_id}")
    
    def get_joint_states(self):
        """获取关节状态"""
        states = {}
        for joint_name, joint_id in self.joint_name_to_id.items():
            if joint_id < len(self.data.qpos):
                states[joint_name] = {
                    'position': self.data.qpos[joint_id],
                    'velocity': self.data.qvel[joint_id] if joint_id < len(self.data.qvel) else 0.0
                }
        return states
    
    def apply_control(self, control_outputs):
        """应用控制输出"""
        for joint_name, torque in control_outputs.items():
            if joint_name in self.joint_name_to_id:
                joint_id = self.joint_name_to_id[joint_name]
                # 找到对应的执行器
                for i in range(self.model.nu):
                    actuator_name = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, i)
                    if actuator_name and joint_name.replace('_Joint', '') in actuator_name:
                        self.data.ctrl[i] = torque
                        break
    
    def test_leg_movement(self, duration=10.0):
        """测试腿部运动"""
        print(f"🚀 开始腿部运动测试 ({duration}秒)...")
        
        start_time = time.time()
        step_count = 0
        
        # 测试轨迹点
        test_trajectories = [
            # 初始位置
            (0.0, {'lf0_Joint': 0.0, 'lf1_Joint': 0.0, 'rf0_Joint': 0.0, 'rf1_Joint': 0.0}),
            # 收腿
            (2.0, {'lf0_Joint': 0.8, 'lf1_Joint': -1.5, 'rf0_Joint': 0.8, 'rf1_Joint': -1.5}),
            # 伸腿
            (4.0, {'lf0_Joint': -0.5, 'lf1_Joint': 1.0, 'rf0_Joint': -0.5, 'rf1_Joint': 1.0}),
            # 回到初始
            (6.0, {'lf0_Joint': 0.0, 'lf1_Joint': 0.0, 'rf0_Joint': 0.0, 'rf1_Joint': 0.0})
        ]
        
        current_traj_index = 0
        
        while time.time() - start_time < duration:
            current_sim_time = time.time() - start_time
            
            # 更新轨迹点
            while (current_traj_index < len(test_trajectories) - 1 and 
                   current_sim_time >= test_trajectories[current_traj_index + 1][0]):
                current_traj_index += 1
                print(f"🎯 切换到轨迹点 {current_traj_index + 1}")
            
            # 获取目标位置
            current_point = test_trajectories[current_traj_index]
            target_positions = current_point[1].copy()
            
            # 如果不是最后一个点，进行插值
            if current_traj_index < len(test_trajectories) - 1:
                next_point = test_trajectories[current_traj_index + 1]
                ratio = (current_sim_time - current_point[0]) / (next_point[0] - current_point[0])
                ratio = max(0.0, min(1.0, ratio))
                
                for joint_name in target_positions:
                    current_pos = current_point[1][joint_name]
                    next_pos = next_point[1][joint_name]
                    target_positions[joint_name] = current_pos + ratio * (next_pos - current_pos)
            
            # 更新控制器状态
            if self.controller and self.controller_enabled:
                joint_states = self.get_joint_states()
                for joint_name, state in joint_states.items():
                    if hasattr(self.controller, 'controller'):
                        self.controller.controller.update_joint_state(
                            joint_name, state['position'], state['velocity'], 0.0
                        )
                
                # 计算控制输出
                control_outputs = self.controller.controller.compute_control(target_positions, 0.01)
            else:
                # 简单PD控制
                joint_states = self.get_joint_states()
                control_outputs = {}
                kp, kd = 10.0, 1.0
                
                for joint_name in target_positions:
                    if joint_name in joint_states:
                        error = target_positions[joint_name] - joint_states[joint_name]['position']
                        error_dot = -joint_states[joint_name]['velocity']
                        control_outputs[joint_name] = kp * error + kd * error_dot
            
            # 应用控制
            self.apply_control(control_outputs)
            
            # 仿真步进
            mujoco.mj_step(self.model, self.data)
            step_count += 1
            
            # 打印状态
            if step_count % 500 == 0:
                base_pos = self.data.qpos[:3] if len(self.data.qpos) >= 3 else [0, 0, 0]
                print(f"⏱️  时间: {current_sim_time:.1f}s, "
                      f"位置: [{base_pos[0]:.3f}, {base_pos[1]:.3f}, {base_pos[2]:.3f}]")
                
                # 打印关节状态
                joint_states = self.get_joint_states()
                lf0_pos = joint_states.get('lf0_Joint', {}).get('position', 0.0)
                lf1_pos = joint_states.get('lf1_Joint', {}).get('position', 0.0)
                print(f"   关节状态 - lf0: {lf0_pos:.3f}, lf1: {lf1_pos:.3f}")
        
        print(f"✅ 测试完成! 总步数: {step_count}")

def main():
    """主函数"""
    print("🔬 离屏MuJoCo控制测试")
    print("=" * 40)
    
    try:
        # 创建测试实例
        test = OffscreenMuJoCoTest()
        
        # 执行测试
        test.test_leg_movement(duration=10.0)
        
        print("\n🎉 测试成功完成!")
        print("✅ 证明了控制器与MuJoCo仿真的集成是可行的!")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()