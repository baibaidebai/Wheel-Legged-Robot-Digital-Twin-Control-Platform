#!/usr/bin/env python3
"""
RM轮腿机器人MuJoCo仿真演示
展示PID和LQR控制器在MuJoCo环境中的应用，实现机器人移动和跳跃控制
"""

import numpy as np
import time
import logging
from typing import Dict, List, Optional
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# 尝试导入MuJoCo
try:
    import mujoco
    import mujoco.viewer
    MUJOCO_AVAILABLE = True
except ImportError:
    MUJOCO_AVAILABLE = False
    print("❌ MuJoCo未安装，请先安装: pip install mujoco")

# 导入控制器
try:
    from wheel_legged_control.controllers.rm_robot_controller import (
        MujocoRMController, PIDGains, HybridRMController
    )
    from wheel_legged_control.algorithms.lqr_controller import LQRConfig
except ImportError:
    # 如果导入失败，创建简化版本用于演示
    print("⚠️  控制器模块导入失败，使用简化版本")
    
    class PIDGains:
        def __init__(self, kp=10.0, ki=0.1, kd=0.5, max_integral=1.0, max_output=30.0):
            self.kp = kp
            self.ki = ki
            self.kd = kd
            self.max_integral = max_integral
            self.max_output = max_output
    
    class LQRConfig:
        def __init__(self, **kwargs):
            self.state_dim = kwargs.get('state_dim', 12)
            self.control_dim = kwargs.get('control_dim', 6)
            self.Q_weights = kwargs.get('Q_weights', [10.0] * 6 + [1.0] * 6)
            self.R_weights = kwargs.get('R_weights', [0.1] * 6)
            self.dt = kwargs.get('dt', 0.01)
    
    class HybridRMController:
        def __init__(self, joint_names, pid_gains_dict=None, lqr_config=None):
            self.joint_names = joint_names
            self.control_mode = 'hybrid'
            
        def set_control_mode(self, mode):
            self.control_mode = mode
            
        def apply_control(self, target_positions, dt=0.01):
            # 简化的控制输出
            return {name: 0.0 for name in self.joint_names}

logger = logging.getLogger(__name__)


class RMMotionPlanner:
    """RM机器人运动规划器"""
    
    def __init__(self):
        self.motion_patterns = {
            'stand': self._stand_pose,
            'walk_forward': self._walk_forward_pattern,
            'jump': self._jump_pattern,
            'turn_left': self._turn_left_pattern,
            'turn_right': self._turn_right_pattern
        }
    
    def get_motion_pattern(self, motion_type: str, time: float) -> Dict[str, float]:
        """获取指定类型的运动模式"""
        if motion_type in self.motion_patterns:
            return self.motion_patterns[motion_type](time)
        else:
            raise ValueError(f"未知的运动类型: {motion_type}")
    
    def _stand_pose(self, time: float) -> Dict[str, float]:
        """站立姿态"""
        return {
            'lf0_Joint': 0.0,
            'lf1_Joint': 0.0,
            'l_wheel_Joint': 0.0,
            'rf0_Joint': 0.0,
            'rf1_Joint': 0.0,
            'r_wheel_Joint': 0.0
        }
    
    def _walk_forward_pattern(self, time: float) -> Dict[str, float]:
        """前进步行模式"""
        # 步行周期参数
        cycle_time = 2.0  # 2秒一个步行周期
        normalized_time = (time % cycle_time) / cycle_time
        
        # 腿部摆动相位差
        left_phase = normalized_time * 2 * np.pi
        right_phase = left_phase + np.pi  # 反相
        
        # 计算关节角度
        lf0_angle = 0.3 * np.sin(left_phase)  # 左前腿髋关节
        lf1_angle = -0.5 * np.abs(np.sin(left_phase))  # 左前腿膝关节
        rf0_angle = 0.3 * np.sin(right_phase)  # 右前腿髋关节
        rf1_angle = -0.5 * np.abs(np.sin(right_phase))  # 右前腿膝关节
        
        # 轮子主要用于支撑，小幅调整保持平衡
        wheel_adjust = 0.1 * np.sin(time * 2)  # 轻微摆动保持稳定
        
        return {
            'lf0_Joint': np.clip(lf0_angle, -0.3, 0.5),
            'lf1_Joint': np.clip(lf1_angle, -0.8, 0.2),
            'l_wheel_Joint': wheel_adjust,
            'rf0_Joint': np.clip(rf0_angle, -0.3, 0.5),
            'rf1_Joint': np.clip(rf1_angle, -0.8, 0.2),
            'r_wheel_Joint': -wheel_adjust
        }
    
    def _jump_pattern(self, time: float) -> Dict[str, float]:
        """跳跃模式"""
        # 跳跃分为三个阶段：蹲下 -> 起跳 -> 着陆
        jump_duration = 3.0
        phase = (time % jump_duration) / jump_duration
        
        if phase < 0.3:  # 蹲下阶段 (0-30%)
            squat_progress = phase / 0.3
            leg_bend = -0.6 * squat_progress  # 腿部弯曲
            return {
                'lf0_Joint': leg_bend * 0.5,
                'lf1_Joint': leg_bend,
                'l_wheel_Joint': 0.0,
                'rf0_Joint': leg_bend * 0.5,
                'rf1_Joint': leg_bend,
                'r_wheel_Joint': 0.0
            }
        elif phase < 0.6:  # 起跳阶段 (30-60%)
            jump_progress = (phase - 0.3) / 0.3
            # 快速伸展腿部
            leg_extend = -0.6 + 1.2 * jump_progress
            return {
                'lf0_Joint': leg_extend * 0.5,
                'lf1_Joint': leg_extend,
                'l_wheel_Joint': 0.0,
                'rf0_Joint': leg_extend * 0.5,
                'rf1_Joint': leg_extend,
                'r_wheel_Joint': 0.0
            }
        else:  # 着陆阶段 (60-100%)
            landing_progress = (phase - 0.6) / 0.4
            # 缓冲着陆
            leg_cushion = 0.6 * (1 - landing_progress)
            return {
                'lf0_Joint': leg_cushion * 0.3,
                'lf1_Joint': leg_cushion,
                'l_wheel_Joint': 0.0,
                'rf0_Joint': leg_cushion * 0.3,
                'rf1_Joint': leg_cushion,
                'r_wheel_Joint': 0.0
            }
    
    def _turn_left_pattern(self, time: float) -> Dict[str, float]:
        """左转模式"""
        cycle_time = 1.5
        normalized_time = (time % cycle_time) / cycle_time
        phase = normalized_time * 2 * np.pi
        
        # 左右腿不同步摆动实现转向
        left_swing = 0.4 * np.sin(phase)
        right_swing = 0.4 * np.sin(phase + np.pi * 0.7)  # 相位差产生转向效果
        
        return {
            'lf0_Joint': np.clip(left_swing, -0.4, 0.4),
            'lf1_Joint': -0.3 * np.abs(np.sin(phase)),
            'l_wheel_Joint': 0.2 * np.sin(time * 3),
            'rf0_Joint': np.clip(right_swing, -0.4, 0.4),
            'rf1_Joint': -0.3 * np.abs(np.sin(phase + np.pi * 0.7)),
            'r_wheel_Joint': -0.2 * np.sin(time * 3)
        }
    
    def _turn_right_pattern(self, time: float) -> Dict[str, float]:
        """右转模式"""
        cycle_time = 1.5
        normalized_time = (time % cycle_time) / cycle_time
        phase = normalized_time * 2 * np.pi
        
        # 与左转相反的相位关系
        left_swing = 0.4 * np.sin(phase + np.pi * 0.7)
        right_swing = 0.4 * np.sin(phase)
        
        return {
            'lf0_Joint': np.clip(left_swing, -0.4, 0.4),
            'lf1_Joint': -0.3 * np.abs(np.sin(phase + np.pi * 0.7)),
            'l_wheel_Joint': 0.2 * np.sin(time * 3),
            'rf0_Joint': np.clip(right_swing, -0.4, 0.4),
            'rf1_Joint': -0.3 * np.abs(np.sin(phase)),
            'r_wheel_Joint': -0.2 * np.sin(time * 3)
        }


class RMRobotSimulator:
    """RM机器人MuJoCo仿真器"""
    
    def __init__(self, model_path: str = None):
        if not MUJOCO_AVAILABLE:
            raise RuntimeError("MuJoCo不可用，请先安装")
        
        # 创建或加载模型
        if model_path and os.path.exists(model_path):
            self.model = mujoco.MjModel.from_xml_path(model_path)
        else:
            self.model = self._create_rm_model()
        
        self.data = mujoco.MjData(self.model)
        self.controller = MujocoRMController(self.model, self.data)
        self.motion_planner = RMMotionPlanner()
        
        # 仿真参数
        self.dt = 0.002  # 500Hz仿真
        self.control_dt = 0.01  # 100Hz控制
        self.sim_time = 0.0
        self.control_step_count = 0
        
        # 运动控制参数
        self.current_motion = 'stand'
        self.motion_start_time = 0.0
        self.control_mode = 'hybrid'  # 'pid', 'lqr', 'hybrid'
        
        # 性能监控
        self.performance_stats = {
            'simulation_steps': 0,
            'control_updates': 0,
            'average_step_time': 0.0
        }
        
        logger.info("✅ RM机器人仿真器初始化完成")
        logger.info(f"📊 仿真频率: {1/self.dt:.0f}Hz")
        logger.info(f"⚙️  控制频率: {1/self.control_dt:.0f}Hz")
    
    def _create_rm_model(self):
        """创建简化的RM机器人MuJoCo模型"""
        xml_string = '''
<mujoco model="rm_wheel_legged_robot">
    <compiler angle="radian" inertiafromgeom="true"/>
    <option timestep="0.002" iterations="50" solver="Newton" tolerance="1e-10"/>
    
    <asset>
        <texture type="skybox" builtin="gradient" rgb1="0.3 0.5 0.7" rgb2="0 0 0" width="512" height="512"/>
        <texture name="texplane" type="2d" builtin="checker" rgb1=".2 .3 .4" rgb2=".1 0.15 0.2" width="512" height="512" mark="cross" markrgb=".8 .8 .8"/>
        <material name="matplane" reflectance="0.3" texture="texplane" texrepeat="1 1" texuniform="true"/>
        <material name="robot_material" rgba="0.2 0.6 0.8 1"/>
    </asset>
    
    <worldbody>
        <!-- 地面 -->
        <geom name="floor" pos="0 0 -0.1" size="10 10 0.1" type="plane" material="matplane" condim="3"/>
        
        <!-- 机器人主体 -->
        <body name="base_link" pos="0 0 0.3">
            <freejoint name="root"/>
            <geom name="base" type="box" size="0.2 0.15 0.08" material="robot_material" mass="8.8"/>
            
            <!-- 左前腿 -->
            <body name="lf0_Link" pos="0.054 0.1705 0">
                <joint name="lf0_Joint" type="hinge" axis="0 0 1" range="-0.3363 1.3479"/>
                <geom name="lf0_geom" type="capsule" size="0.03 0.075" pos="0.075 0 0" material="robot_material" mass="0.16"/>
                
                <body name="lf1_Link" pos="0.15 0 0">
                    <joint name="lf1_Joint" type="hinge" axis="0 0 1" range="-1.0 1.25"/>
                    <geom name="lf1_geom" type="capsule" size="0.025 0.16" pos="0 0.16 0" material="robot_material" mass="0.36"/>
                    
                    <body name="l_wheel_Link" pos="0 0.32 0">
                        <joint name="l_wheel_Joint" type="hinge" axis="1 0 0" range="-10 10"/>
                        <geom name="l_wheel_geom" type="cylinder" size="0.08 0.02" material="robot_material" mass="1.22"/>
                    </body>
                </body>
            </body>
            
            <!-- 右前腿 (镜像) -->
            <body name="rf0_Link" pos="0.054 -0.1705 0">
                <joint name="rf0_Joint" type="hinge" axis="0 0 1" range="-0.3363 1.3479"/>
                <geom name="rf0_geom" type="capsule" size="0.03 0.075" pos="0.075 0 0" material="robot_material" mass="0.16"/>
                
                <body name="rf1_Link" pos="0.15 0 0">
                    <joint name="rf1_Joint" type="hinge" axis="0 0 1" range="-1.0 1.25"/>
                    <geom name="rf1_geom" type="capsule" size="0.025 0.16" pos="0 0.16 0" material="robot_material" mass="0.36"/>
                    
                    <body name="r_wheel_Link" pos="0 0.32 0">
                        <joint name="r_wheel_Joint" type="hinge" axis="1 0 0" range="-10 10"/>
                        <geom name="r_wheel_geom" type="cylinder" size="0.08 0.02" material="robot_material" mass="1.22"/>
                    </body>
                </body>
            </body>
        </body>
    </worldbody>
    
    <actuator>
        <motor name="lf0_motor" joint="lf0_Joint" gear="1" ctrllimited="true" ctrlrange="-30 30"/>
        <motor name="lf1_motor" joint="lf1_Joint" gear="1" ctrllimited="true" ctrlrange="-30 30"/>
        <motor name="l_wheel_motor" joint="l_wheel_Joint" gear="1" ctrllimited="true" ctrlrange="-30 30"/>
        <motor name="rf0_motor" joint="rf0_Joint" gear="1" ctrllimited="true" ctrlrange="-30 30"/>
        <motor name="rf1_motor" joint="rf1_Joint" gear="1" ctrllimited="true" ctrlrange="-30 30"/>
        <motor name="r_wheel_motor" joint="r_wheel_Joint" gear="1" ctrllimited="true" ctrlrange="-30 30"/>
    </actuator>
    
    <sensor>
        <accelerometer name="accelerometer" site="base_site"/>
        <gyro name="gyro" site="base_site"/>
        <velocimeter name="velocimeter" site="base_site"/>
    </sensor>
    
    <site name="base_site" pos="0 0 0"/>
</mujoco>
        '''
        
        # 从XML字符串创建模型
        assets = {}
        model = mujoco.MjModel.from_xml_string(xml_string, assets)
        return model
    
    def set_motion(self, motion_type: str):
        """设置运动模式"""
        if motion_type in self.motion_planner.motion_patterns:
            self.current_motion = motion_type
            self.motion_start_time = self.sim_time
            logger.info(f"🔄 切换到运动模式: {motion_type}")
        else:
            logger.warning(f"⚠️  未知运动模式: {motion_type}")
    
    def set_control_mode(self, mode: str):
        """设置控制模式"""
        if mode in ['pid', 'lqr', 'hybrid']:
            self.control_mode = mode
            self.controller.set_control_mode(mode)
            logger.info(f"🔧 控制模式设置为: {mode}")
        else:
            logger.warning(f"⚠️  无效控制模式: {mode}")
    
    def simulate_step(self):
        """执行一步仿真"""
        start_time = time.time()
        
        # 更新运动规划
        target_positions = self.motion_planner.get_motion_pattern(
            self.current_motion, 
            self.sim_time - self.motion_start_time
        )
        
        # 控制更新（每control_dt秒更新一次）
        if self.control_step_count % int(self.control_dt / self.dt) == 0:
            self.controller.apply_control(target_positions, self.control_dt)
            self.performance_stats['control_updates'] += 1
        
        # 物理仿真步进
        mujoco.mj_step(self.model, self.data)
        self.sim_time += self.dt
        self.control_step_count += 1
        self.performance_stats['simulation_steps'] += 1
        
        # 性能统计
        step_time = time.time() - start_time
        self.performance_stats['average_step_time'] = (
            self.performance_stats['average_step_time'] * 0.99 + 
            step_time * 0.01
        )
        
        return target_positions
    
    def get_robot_state(self):
        """获取机器人状态"""
        base_pos = self.data.qpos[:3].copy()
        base_quat = self.data.qpos[3:7].copy()
        joint_positions = self.controller.get_joint_positions()
        
        return {
            'base_position': base_pos,
            'base_orientation': base_quat,
            'joint_positions': joint_positions,
            'time': self.sim_time
        }
    
    def run_simulation(self, duration: float = 30.0, show_viewer: bool = True):
        """运行仿真"""
        if not show_viewer:
            # 无界面运行
            steps = int(duration / self.dt)
            for i in range(steps):
                self.simulate_step()
                if i % 1000 == 0:
                    state = self.get_robot_state()
                    logger.info(f"⏱️  仿真时间: {state['time']:.2f}s, "
                              f"位置: [{state['base_position'][0]:.2f}, "
                              f"{state['base_position'][1]:.2f}, "
                              f"{state['base_position'][2]:.2f}]")
        else:
            # 带可视化界面运行
            with mujoco.viewer.launch_passive(self.model, self.data) as viewer:
                viewer.cam.distance = 3.0
                viewer.cam.lookat[:] = [0, 0, 0.5]
                viewer.cam.elevation = -20
                
                steps = int(duration / self.dt)
                for i in range(steps):
                    # 仿真步骤
                    target_positions = self.simulate_step()
                    
                    # 更新viewer
                    viewer.sync()
                    
                    # 显示状态信息
                    if i % 500 == 0:  # 每秒显示一次
                        state = self.get_robot_state()
                        print(f"\n📊 仿真状态 (t={state['time']:.2f}s):")
                        print(f"   位置: x={state['base_position'][0]:.3f}, "
                              f"y={state['base_position'][1]:.3f}, "
                              f"z={state['base_position'][2]:.3f}")
                        print(f"   目标关节角度: {list(target_positions.values())}")
                        print(f"   当前关节角度: {list(state['joint_positions'].values())}")
                        print(f"   控制模式: {self.control_mode}")
                        print(f"   运动模式: {self.current_motion}")
                        
                        # 性能统计
                        avg_step_ms = self.performance_stats['average_step_time'] * 1000
                        print(f"   平均步进时间: {avg_step_ms:.2f}ms")
                    
                    # 检查用户交互
                    if viewer.is_running() == False:
                        break


def demonstrate_motions(simulator: RMRobotSimulator):
    """演示各种运动模式"""
    print("\n🎭 开始运动演示...")
    print("=" * 50)
    
    motions = [
        ('stand', 3.0, "站立稳定"),
        ('walk_forward', 8.0, "前进步行"),
        ('turn_left', 6.0, "左转"),
        ('turn_right', 6.0, "右转"),
        ('jump', 9.0, "跳跃动作"),
        ('stand', 3.0, "恢复站立")
    ]
    
    for motion_type, duration, description in motions:
        print(f"\n🚀 执行: {description} ({motion_type})")
        print(f"⏱️  持续时间: {duration}s")
        
        simulator.set_motion(motion_type)
        
        # 运行该动作
        steps = int(duration / simulator.dt)
        for i in range(steps):
            simulator.simulate_step()
            
            # 每2秒显示一次状态
            if i % int(2.0 / simulator.dt) == 0:
                state = simulator.get_robot_state()
                print(f"   t={state['time']:.1f}s - "
                      f"位置: [{state['base_position'][0]:.2f}, "
                      f"{state['base_position'][1]:.2f}, "
                      f"{state['base_position'][2]:.2f}]")
        
        print(f"✅ {description} 完成")


def main():
    """主函数"""
    print("🤖 RM轮腿机器人MuJoCo仿真演示")
    print("=" * 60)
    
    if not MUJOCO_AVAILABLE:
        print("❌ 错误: MuJoCo未安装")
        print("请运行: pip install mujoco")
        return
    
    try:
        # 创建仿真器
        print("🔧 初始化仿真环境...")
        simulator = RMRobotSimulator()
        
        # 设置控制模式
        simulator.set_control_mode('hybrid')  # 使用混合控制
        
        # 运行演示
        print("\n🎮 启动交互式仿真...")
        print("提示: 窗口打开后可以:")
        print("- 按空格键暂停/继续")
        print("- 拖拽视角观察机器人")
        print("- 程序会自动演示各种动作")
        
        # 先运行一段时间让用户熟悉界面
        print("\n👀 观察初始状态 (5秒)...")
        simulator.run_simulation(duration=5.0, show_viewer=True)
        
        # 运行运动演示
        demonstrate_motions(simulator)
        
        # 继续交互式仿真
        print("\n🎮 继续交互式仿真 (按ESC退出)...")
        simulator.run_simulation(duration=30.0, show_viewer=True)
        
        print("\n🎉 仿真演示完成!")
        print(f"📈 总仿真步数: {simulator.performance_stats['simulation_steps']}")
        print(f"⚙️  控制更新次数: {simulator.performance_stats['control_updates']}")
        
    except Exception as e:
        logger.error(f"❌ 仿真过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    main()