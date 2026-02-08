#!/usr/bin/env python3
"""
基于MuJoCo的强化学习环境

使用MuJoCo物理引擎的高性能强化学习环境，专为轮腿机器人设计。
提供更精确的物理仿真和更好的训练性能。
"""

import numpy as np
import time
import logging
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass

# 导入基础环境
from .rl_environment import BaseRLEnvironment, EnvironmentConfig, RewardType, spaces

# 导入仿真管理器
try:
    from wheel_legged_control.simulation import (
        SimulationManager, SimulationBackend, SimulationConfig
    )
    SIMULATION_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  仿真模块不可用: {e}")
    SimulationManager = None
    SimulationBackend = None
    SimulationConfig = None
    SIMULATION_AVAILABLE = False


@dataclass
class MuJoCoEnvironmentConfig(EnvironmentConfig):
    """MuJoCo环境配置参数"""
    # MuJoCo特定配置
    mujoco_model_path: str = None
    solver_type: str = "Newton"  # "Newton", "CG", "PGS"
    solver_iterations: int = 100
    
    # 仿真精度
    simulation_dt: float = 0.001  # MuJoCo仿真时间步
    control_dt: float = 0.02      # 控制时间步
    
    # 渲染配置
    render_mode: str = "rgb_array"  # "human", "rgb_array"
    camera_id: int = -1  # -1为自由相机
    
    # 性能优化
    enable_contact_forces: bool = True
    enable_joint_limits: bool = True
    warmstart_solver: bool = True


class MuJoCoWheelLeggedEnvironment(BaseRLEnvironment):
    """基于MuJoCo的轮腿机器人强化学习环境"""
    
    def __init__(self, config: MuJoCoEnvironmentConfig, model_path: str = None):
        self.mujoco_config = config
        self.model_path = model_path or config.mujoco_model_path
        
        # 仿真管理器
        self.sim_manager = None
        self.simulation_config = None
        
        # 控制频率管理
        self.control_steps = int(config.control_dt / config.simulation_dt)
        self.sim_step_counter = 0
        
        # 性能统计
        self.step_times = []
        self.physics_times = []
        
        super().__init__(config)
    
    def _setup_environment(self):
        """设置MuJoCo环境"""
        try:
            if not SIMULATION_AVAILABLE:
                self.logger.warning("⚠️  仿真模块不可用，使用基础环境")
                super()._setup_environment()
                return
            
            # 创建仿真配置
            self.simulation_config = SimulationConfig(
                backend=SimulationBackend.MUJOCO,
                dt=self.mujoco_config.simulation_dt,
                enable_rendering=self.mujoco_config.enable_rendering,
                render_width=640,
                render_height=480,
                mujoco_solver=self.mujoco_config.solver_type,
                mujoco_iterations=self.mujoco_config.solver_iterations
            )
            
            # 创建仿真管理器
            self.sim_manager = SimulationManager(self.simulation_config)
            
            # 初始化仿真
            if self.model_path:
                success = self.sim_manager.initialize(self.model_path)
                if not success:
                    self.logger.error("❌ MuJoCo仿真初始化失败")
                    raise RuntimeError("MuJoCo仿真初始化失败")
            else:
                self.logger.warning("⚠️  未提供模型路径，使用默认模型")
                # 创建默认模型
                self._create_default_model()
            
            # 获取关节信息
            joint_states = self.sim_manager.get_joint_states()
            self.joint_names = list(joint_states.keys())
            self.num_joints = len(self.joint_names)
            
            # 设置动作空间和观测空间
            self._setup_spaces()
            
            self.logger.info(f"✅ MuJoCo环境初始化成功")
            self.logger.info(f"📊 关节数量: {self.num_joints}")
            self.logger.info(f"🎮 控制频率: {1/self.mujoco_config.control_dt:.1f} Hz")
            self.logger.info(f"⚙️  仿真频率: {1/self.mujoco_config.simulation_dt:.1f} Hz")
            
        except Exception as e:
            self.logger.error(f"❌ MuJoCo环境设置失败: {e}")
            # 回退到基础环境
            super()._setup_environment()
    
    def _create_default_model(self):
        """创建默认的轮腿机器人模型"""
        try:
            from wheel_legged_control.simulation.mujoco_backend import URDFToMJCFConverter
            
            converter = URDFToMJCFConverter()
            default_model_path = "default_wheel_legged_robot.xml"
            converter._create_simple_mjcf(default_model_path)
            
            success = self.sim_manager.initialize(default_model_path)
            if not success:
                raise RuntimeError("默认模型初始化失败")
            
            self.model_path = default_model_path
            self.logger.info("✅ 使用默认轮腿机器人模型")
            
        except Exception as e:
            self.logger.error(f"❌ 创建默认模型失败: {e}")
            raise
    
    def _setup_spaces(self):
        """设置动作空间和观测空间"""
        # 动作空间：关节速度或力矩控制
        if self.config.action_type == "continuous":
            if hasattr(self.config, 'control_mode') and self.config.control_mode == 'effort':
                # 力矩控制
                action_low = np.full(self.num_joints, -self.config.max_joint_effort)
                action_high = np.full(self.num_joints, self.config.max_joint_effort)
            else:
                # 速度控制
                action_low = np.full(self.num_joints, -self.config.max_joint_velocity)
                action_high = np.full(self.num_joints, self.config.max_joint_velocity)
            
            self.action_space = spaces.Box(
                low=action_low,
                high=action_high,
                dtype=np.float32
            )
        else:
            # 离散动作空间
            self.action_space = spaces.Discrete(self.num_joints * 3)
        
        # 观测空间
        obs_dim = 0
        
        if self.config.include_joint_positions:
            obs_dim += self.num_joints
        if self.config.include_joint_velocities:
            obs_dim += self.num_joints
        if self.config.include_joint_efforts:
            obs_dim += self.num_joints
        if self.config.include_base_pose:
            obs_dim += 7  # 位置(3) + 四元数(4)
        if self.config.include_imu_data:
            obs_dim += 9  # 线性加速度(3) + 角速度(3) + 方向(3)
        
        # 添加目标位置
        obs_dim += 3
        
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(obs_dim,),
            dtype=np.float32
        )
        
        self.logger.info(f"动作空间维度: {self.action_space.shape}")
        self.logger.info(f"观测空间维度: {self.observation_space.shape}")
    
    def _get_observation(self) -> np.ndarray:
        """获取当前观测值"""
        if not self.sim_manager:
            return super()._get_observation()
        
        obs = []
        
        # 获取仿真状态
        state = self.sim_manager.get_state()
        
        # 关节位置
        if self.config.include_joint_positions:
            positions = [state['joint_positions'].get(name, 0.0) for name in self.joint_names]
            obs.extend(positions)
        
        # 关节速度
        if self.config.include_joint_velocities:
            velocities = [state['joint_velocities'].get(name, 0.0) for name in self.joint_names]
            obs.extend(velocities)
        
        # 关节力矩
        if self.config.include_joint_efforts:
            efforts = [state['joint_efforts'].get(name, 0.0) for name in self.joint_names]
            obs.extend(efforts)
        
        # 基座位姿
        if self.config.include_base_pose:
            obs.extend(state['base_position'])
            obs.extend(state['base_orientation'])
        
        # IMU数据（从基座状态计算）
        if self.config.include_imu_data:
            # 线性加速度（简化计算）
            linear_accel = np.array([0.0, 0.0, 9.81])  # 重力
            obs.extend(linear_accel)
            
            # 角速度
            obs.extend(state['base_angular_velocity'])
            
            # 方向（从四元数提取欧拉角）
            quat = state['base_orientation']
            euler = self._quat_to_euler(quat)
            obs.extend(euler)
        
        # 目标位置
        obs.extend(self.target_position)
        
        return np.array(obs, dtype=np.float32)
    
    def _quat_to_euler(self, quat: np.ndarray) -> np.ndarray:
        """四元数转欧拉角"""
        w, x, y, z = quat
        
        # Roll (x-axis rotation)
        sinr_cosp = 2 * (w * x + y * z)
        cosr_cosp = 1 - 2 * (x * x + y * y)
        roll = np.arctan2(sinr_cosp, cosr_cosp)
        
        # Pitch (y-axis rotation)
        sinp = 2 * (w * y - z * x)
        if abs(sinp) >= 1:
            pitch = np.copysign(np.pi / 2, sinp)
        else:
            pitch = np.arcsin(sinp)
        
        # Yaw (z-axis rotation)
        siny_cosp = 2 * (w * z + x * y)
        cosy_cosp = 1 - 2 * (y * y + z * z)
        yaw = np.arctan2(siny_cosp, cosy_cosp)
        
        return np.array([roll, pitch, yaw])
    
    def _compute_reward(self, action: np.ndarray) -> float:
        """计算奖励函数"""
        if not self.sim_manager:
            return super()._compute_reward(action)
        
        reward = 0.0
        state = self.sim_manager.get_state()
        
        # 距离奖励
        current_position = state['base_position']
        distance = np.linalg.norm(current_position - self.target_position)
        
        if self.config.reward_type == RewardType.SPARSE:
            # 稀疏奖励：只在到达目标时给奖励
            if distance < self.config.position_tolerance:
                reward += 100.0
        
        elif self.config.reward_type == RewardType.DENSE:
            # 密集奖励：基于距离的连续奖励
            max_distance = 10.0
            distance_reward = (max_distance - distance) / max_distance
            reward += distance_reward * self.config.stability_reward_weight
            
            # 到达目标的额外奖励
            if distance < self.config.position_tolerance:
                reward += 50.0
        
        elif self.config.reward_type == RewardType.SHAPED:
            # 形状奖励：更复杂的奖励函数
            # 距离奖励（指数衰减）
            distance_reward = np.exp(-distance)
            reward += distance_reward * self.config.stability_reward_weight
            
            # 速度惩罚
            joint_velocities = list(state['joint_velocities'].values())
            velocity_penalty = np.sum(np.square(joint_velocities))
            reward -= velocity_penalty * self.config.velocity_penalty_weight
            
            # 力矩惩罚
            effort_penalty = np.sum(np.square(action))
            reward -= effort_penalty * self.config.effort_penalty_weight
            
            # 稳定性奖励
            angular_velocity = state['base_angular_velocity']
            angular_velocity_magnitude = np.linalg.norm(angular_velocity)
            stability_reward = np.exp(-angular_velocity_magnitude)
            reward += stability_reward * 0.1
            
            # 前进奖励
            forward_velocity = state['base_linear_velocity'][0]
            if forward_velocity > 0:
                reward += forward_velocity * 0.1
        
        # 生存奖励
        reward += 0.1
        
        # 碰撞惩罚
        if current_position[2] < 0.05:  # 高度过低
            reward -= 10.0
        
        return reward
    
    def _is_done(self) -> bool:
        """判断回合是否结束"""
        if not self.sim_manager:
            return super()._is_done()
        
        # 达到最大步数
        if self.current_step >= self.config.max_episode_steps:
            return True
        
        # 获取当前状态
        state = self.sim_manager.get_state()
        current_position = state['base_position']
        
        # 到达目标
        distance = np.linalg.norm(current_position - self.target_position)
        if distance < self.config.position_tolerance:
            return True
        
        # 机器人倒下或碰撞
        if current_position[2] < 0.05:  # 高度过低
            return True
        
        # 关节超出限制（如果启用）
        if self.mujoco_config.enable_joint_limits:
            joint_positions = state['joint_positions']
            for joint_name, position in joint_positions.items():
                if abs(position) > np.pi:  # 简化的关节限制
                    return True
        
        return False
    
    def _apply_action(self, action: np.ndarray):
        """应用动作到机器人"""
        if not self.sim_manager:
            super()._apply_action(action)
            return
        
        # 构建控制指令
        control_dict = {}
        
        if self.config.action_type == "continuous":
            # 连续动作
            for i, joint_name in enumerate(self.joint_names):
                if i < len(action):
                    motor_name = joint_name + '_motor'
                    if hasattr(self.config, 'control_mode') and self.config.control_mode == 'effort':
                        # 力矩控制
                        control_dict[motor_name] = np.clip(
                            action[i], 
                            -self.config.max_joint_effort, 
                            self.config.max_joint_effort
                        )
                    else:
                        # 速度控制
                        control_dict[motor_name] = np.clip(
                            action[i], 
                            -self.config.max_joint_velocity, 
                            self.config.max_joint_velocity
                        )
        else:
            # 离散动作
            joint_idx = action // 3
            action_type = action % 3
            
            if joint_idx < len(self.joint_names):
                joint_name = self.joint_names[joint_idx]
                motor_name = joint_name + '_motor'
                
                if action_type == 0:  # 停止
                    control_dict[motor_name] = 0.0
                elif action_type == 1:  # 正向
                    control_dict[motor_name] = self.config.max_joint_velocity * 0.5
                else:  # 反向
                    control_dict[motor_name] = -self.config.max_joint_velocity * 0.5
        
        # 应用控制指令
        self.sim_manager.step(control_dict)
    
    def _reset_robot_state(self):
        """重置机器人状态"""
        if not self.sim_manager:
            super()._reset_robot_state()
            return
        
        # 重置仿真
        self.sim_manager.reset()
        
        # 设置随机初始状态
        if self.config.randomize_initial_state:
            # 随机关节位置
            joint_positions = {}
            for joint_name in self.joint_names:
                joint_positions[joint_name] = np.random.uniform(-0.5, 0.5)
            
            self.sim_manager.set_joint_positions(joint_positions)
        
        # 随机化目标位置
        if self.config.randomize_initial_state:
            self.target_position = np.random.uniform([-2, -2, 0.1], [2, 2, 0.1])
        else:
            self.target_position = np.array([1.0, 0.0, 0.1])
        
        # 重置计数器
        self.sim_step_counter = 0
    
    def _update_environment(self):
        """更新环境状态"""
        if not self.sim_manager:
            super()._update_environment()
            return
        
        # 执行多个仿真步以匹配控制频率
        start_time = time.time()
        
        for _ in range(self.control_steps):
            self.sim_manager.step()
            self.sim_step_counter += 1
        
        physics_time = time.time() - start_time
        self.physics_times.append(physics_time)
        
        # 保持性能统计的合理大小
        if len(self.physics_times) > 1000:
            self.physics_times = self.physics_times[-500:]
    
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, Dict]:
        """执行一步（重写以添加性能统计）"""
        step_start_time = time.time()
        
        result = super().step(action)
        
        step_time = time.time() - step_start_time
        self.step_times.append(step_time)
        
        # 保持性能统计的合理大小
        if len(self.step_times) > 1000:
            self.step_times = self.step_times[-500:]
        
        # 添加性能信息到info
        if len(result) == 4:
            obs, reward, done, info = result
            info['step_time'] = step_time
            if self.physics_times:
                info['physics_time'] = self.physics_times[-1]
                info['avg_physics_time'] = np.mean(self.physics_times)
            result = (obs, reward, done, info)
        
        return result
    
    def render(self, mode='human'):
        """渲染环境"""
        if self.sim_manager:
            return self.sim_manager.render(mode)
        else:
            return super().render(mode)
    
    def close(self):
        """关闭环境"""
        if self.sim_manager:
            self.sim_manager.close()
            self.sim_manager = None
        
        # 清理临时文件
        if hasattr(self, 'model_path') and self.model_path and 'default_wheel_legged_robot.xml' in self.model_path:
            import os
            if os.path.exists(self.model_path):
                os.remove(self.model_path)
        
        super().close()
    
    def get_performance_stats(self) -> Dict[str, float]:
        """获取性能统计"""
        stats = {}
        
        if self.step_times:
            stats['avg_step_time'] = np.mean(self.step_times)
            stats['std_step_time'] = np.std(self.step_times)
            stats['max_step_time'] = np.max(self.step_times)
            stats['steps_per_second'] = 1.0 / np.mean(self.step_times)
        
        if self.physics_times:
            stats['avg_physics_time'] = np.mean(self.physics_times)
            stats['std_physics_time'] = np.std(self.physics_times)
            stats['physics_ratio'] = np.mean(self.physics_times) / np.mean(self.step_times) if self.step_times else 0
        
        stats['total_sim_steps'] = self.sim_step_counter
        stats['control_frequency'] = 1.0 / self.mujoco_config.control_dt
        stats['simulation_frequency'] = 1.0 / self.mujoco_config.simulation_dt
        
        return stats


def create_mujoco_wheel_legged_environment(
    config: MuJoCoEnvironmentConfig = None, 
    model_path: str = None,
    **kwargs
) -> MuJoCoWheelLeggedEnvironment:
    """创建基于MuJoCo的轮腿机器人环境的工厂函数"""
    if config is None:
        config = MuJoCoEnvironmentConfig()
    
    # 从kwargs更新配置
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    return MuJoCoWheelLeggedEnvironment(config, model_path)


if __name__ == "__main__":
    # 测试MuJoCo环境
    print("🧪 测试基于MuJoCo的强化学习环境")
    
    # 创建环境配置
    config = MuJoCoEnvironmentConfig(
        max_episode_steps=200,
        reward_type=RewardType.SHAPED,
        randomize_initial_state=True,
        action_type="continuous",
        simulation_dt=0.001,
        control_dt=0.02
    )
    
    try:
        # 创建环境
        env = create_mujoco_wheel_legged_environment(config)
        print(f"✅ 环境创建成功")
        print(f"📊 观测空间: {env.observation_space}")
        print(f"🎮 动作空间: {env.action_space}")
        
        # 测试环境
        obs = env.reset()
        print(f"🔄 环境重置，初始观测维度: {obs.shape}")
        
        total_reward = 0
        for step in range(20):
            # 随机动作
            action = env.action_space.sample()
            obs, reward, done, info = env.step(action)
            total_reward += reward
            
            print(f"步骤 {step+1:2d}: 奖励={reward:6.3f}, 累计={total_reward:6.3f}, "
                  f"步时间={info.get('step_time', 0)*1000:.1f}ms, 结束={done}")
            
            if done:
                print("🏁 回合结束")
                break
        
        # 性能统计
        stats = env.get_performance_stats()
        print("\n📈 性能统计:")
        for key, value in stats.items():
            if 'time' in key:
                print(f"   {key}: {value*1000:.2f}ms")
            elif 'frequency' in key:
                print(f"   {key}: {value:.1f}Hz")
            else:
                print(f"   {key}: {value:.2f}")
        
        env.close()
        print("🎉 环境测试完成")
        
    except Exception as e:
        print(f"❌ 环境测试失败: {e}")
        import traceback
        traceback.print_exc()