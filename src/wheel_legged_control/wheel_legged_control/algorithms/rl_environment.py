#!/usr/bin/env python3
"""
强化学习环境接口

实现符合OpenAI Gym规范的轮腿机器人控制环境，支持强化学习算法训练。
"""

import numpy as np
import time
import logging
from typing import Dict, List, Tuple, Optional, Any, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
# import gym
# from gym import spaces
# from gym.utils import seeding

# 简化的空间定义（不依赖gym）
class Box:
    """简化的连续空间"""
    def __init__(self, low, high, shape=None, dtype=np.float32):
        self.low = np.array(low, dtype=dtype)
        self.high = np.array(high, dtype=dtype)
        self.shape = shape if shape is not None else self.low.shape
        self.dtype = dtype
    
    def sample(self):
        """随机采样"""
        return np.random.uniform(self.low, self.high).astype(self.dtype)

class Discrete:
    """简化的离散空间"""
    def __init__(self, n):
        self.n = n
        self.shape = ()
    
    def sample(self):
        """随机采样"""
        return np.random.randint(0, self.n)

class spaces:
    """简化的空间模块"""
    Box = Box
    Discrete = Discrete

def np_random(seed=None):
    """简化的随机数生成器"""
    if seed is not None:
        np.random.seed(seed)
    return np.random, seed

# 导入项目模块（可选）
try:
    from wheel_legged_control.core.urdf_loader import URDFLoader
    from wheel_legged_control.core.digital_twin_mapper_wrapper import DigitalTwinMapperWrapper
    from wheel_legged_control.sensors.imu_simulator import IMUSimulator
    COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  部分组件不可用: {e}")
    URDFLoader = None
    DigitalTwinMapperWrapper = None
    IMUSimulator = None
    COMPONENTS_AVAILABLE = False


class RewardType(Enum):
    """奖励函数类型"""
    SPARSE = "sparse"           # 稀疏奖励
    DENSE = "dense"            # 密集奖励
    SHAPED = "shaped"          # 形状奖励
    CUSTOM = "custom"          # 自定义奖励


@dataclass
class EnvironmentConfig:
    """环境配置参数"""
    # 基本配置
    max_episode_steps: int = 1000
    dt: float = 0.01  # 时间步长
    
    # 状态空间配置
    include_joint_positions: bool = True
    include_joint_velocities: bool = True
    include_joint_efforts: bool = False
    include_imu_data: bool = True
    include_base_pose: bool = True
    
    # 动作空间配置
    action_type: str = "continuous"  # "continuous" or "discrete"
    max_joint_velocity: float = 10.0  # rad/s
    max_joint_effort: float = 30.0    # N·m
    
    # 奖励配置
    reward_type: RewardType = RewardType.DENSE
    target_position: List[float] = None  # 目标位置
    position_tolerance: float = 0.1      # 位置容差
    velocity_penalty_weight: float = 0.01
    effort_penalty_weight: float = 0.001
    stability_reward_weight: float = 1.0
    
    # 安全限制
    joint_position_limits: Dict[str, Tuple[float, float]] = None
    joint_velocity_limits: Dict[str, float] = None
    joint_effort_limits: Dict[str, float] = None
    
    # 随机化配置
    randomize_initial_state: bool = True
    randomize_dynamics: bool = False
    noise_level: float = 0.01


class BaseRLEnvironment(ABC):
    """强化学习环境基类"""
    
    def __init__(self, config: EnvironmentConfig):
        super().__init__()
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 环境状态
        self.current_step = 0
        self.episode_reward = 0.0
        self.done = False
        
        # 机器人状态
        self.joint_positions = {}
        self.joint_velocities = {}
        self.joint_efforts = {}
        self.base_position = np.zeros(3)
        self.base_orientation = np.zeros(4)  # 四元数
        self.base_linear_velocity = np.zeros(3)
        self.base_angular_velocity = np.zeros(3)
        
        # 目标状态
        self.target_position = np.array(config.target_position) if config.target_position else np.zeros(3)
        
        # 随机数生成器
        self.np_random = np.random
        self.seed()
        
        # 初始化环境
        self._setup_environment()
        
    @abstractmethod
    def _setup_environment(self):
        """设置环境（子类实现）"""
        pass
    
    @abstractmethod
    def _get_observation(self) -> np.ndarray:
        """获取观测值（子类实现）"""
        pass
    
    @abstractmethod
    def _compute_reward(self, action: np.ndarray) -> float:
        """计算奖励（子类实现）"""
        pass
    
    @abstractmethod
    def _is_done(self) -> bool:
        """判断是否结束（子类实现）"""
        pass
    
    @abstractmethod
    def _apply_action(self, action: np.ndarray):
        """应用动作（子类实现）"""
        pass
    
    def seed(self, seed=None):
        """设置随机种子"""
        if seed is not None:
            np.random.seed(seed)
        self.np_random = np.random
        return [seed]
    
    def reset(self) -> np.ndarray:
        """重置环境"""
        self.current_step = 0
        self.episode_reward = 0.0
        self.done = False
        
        # 重置机器人状态
        self._reset_robot_state()
        
        # 返回初始观测
        return self._get_observation()
    
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, Dict]:
        """执行一步"""
        # 更新步数（在开始时更新）
        self.current_step += 1
        
        # 应用动作
        self._apply_action(action)
        
        # 更新环境状态
        self._update_environment()
        
        # 计算奖励
        reward = self._compute_reward(action)
        self.episode_reward += reward
        
        # 检查是否结束
        self.done = self._is_done()
        
        # 获取观测
        observation = self._get_observation()
        
        # 构建信息字典
        info = {
            'episode_reward': self.episode_reward,
            'current_step': self.current_step,
            'base_position': self.base_position.copy(),
            'target_position': self.target_position.copy(),
            'distance_to_target': np.linalg.norm(self.base_position - self.target_position)
        }
        
        return observation, reward, self.done, info
    
    def render(self, mode='human'):
        """渲染环境"""
        if mode == 'human':
            print(f"Step: {self.current_step}, Reward: {self.episode_reward:.3f}")
            print(f"Base Position: {self.base_position}")
            print(f"Target Position: {self.target_position}")
            print(f"Distance: {np.linalg.norm(self.base_position - self.target_position):.3f}")
        elif mode == 'rgb_array':
            # 返回RGB数组（如果有可视化）
            return np.zeros((480, 640, 3), dtype=np.uint8)
    
    def close(self):
        """关闭环境"""
        pass
    
    @abstractmethod
    def _reset_robot_state(self):
        """重置机器人状态（子类实现）"""
        pass
    
    @abstractmethod
    def _update_environment(self):
        """更新环境状态（子类实现）"""
        pass


class WheelLeggedRobotEnvironment(BaseRLEnvironment):
    """轮腿机器人强化学习环境"""
    
    def __init__(self, config: EnvironmentConfig, urdf_path: str = None):
        self.urdf_path = urdf_path or "src/model/RM_Serial_Wheeled-leg_Robot/urdf/RM_Serial_Wheeled-leg_Robot.urdf"
        
        # 初始化机器人组件
        self.urdf_loader = None
        self.digital_twin_mapper = None
        self.imu_simulator = None
        
        super().__init__(config)
        
    def _setup_environment(self):
        """设置轮腿机器人环境"""
        try:
            # 检查组件可用性
            if not COMPONENTS_AVAILABLE:
                self.logger.warning("部分组件不可用，使用简化模式")
                self.joint_names = ['lf0_joint', 'lf1_joint', 'rf0_joint', 'rf1_joint', 'l_wheel_joint', 'r_wheel_joint']
                self.num_joints = len(self.joint_names)
                self._setup_spaces()
                return
            
            # 加载URDF模型
            if URDFLoader:
                self.urdf_loader = URDFLoader()
                if not self.urdf_loader.load_urdf(self.urdf_path):
                    self.logger.warning(f"无法加载URDF文件: {self.urdf_path}，使用默认关节")
                    self.joint_names = ['lf0_joint', 'lf1_joint', 'rf0_joint', 'rf1_joint', 'l_wheel_joint', 'r_wheel_joint']
                else:
                    # 获取关节信息
                    self.joint_names = list(self.urdf_loader.joints.keys())
            else:
                self.joint_names = ['lf0_joint', 'lf1_joint', 'rf0_joint', 'rf1_joint', 'l_wheel_joint', 'r_wheel_joint']
            
            self.num_joints = len(self.joint_names)
            
            # 初始化数字孪生映射器
            if DigitalTwinMapperWrapper:
                self.digital_twin_mapper = DigitalTwinMapperWrapper()
            else:
                self.digital_twin_mapper = None
            
            # 初始化IMU仿真器
            if IMUSimulator:
                self.imu_simulator = IMUSimulator()
            else:
                self.imu_simulator = None
            
            # 设置动作空间和观测空间
            self._setup_spaces()
            
            self.logger.info(f"轮腿机器人环境初始化成功，关节数量: {self.num_joints}")
            
        except Exception as e:
            self.logger.error(f"环境初始化失败: {e}")
            # 使用默认配置
            self.joint_names = ['lf0_joint', 'lf1_joint', 'rf0_joint', 'rf1_joint', 'l_wheel_joint', 'r_wheel_joint']
            self.num_joints = len(self.joint_names)
            self.digital_twin_mapper = None
            self.imu_simulator = None
            self._setup_spaces()
    
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
            self.action_space = spaces.Discrete(self.num_joints * 3)  # 每个关节3个动作：停止、正向、反向
        
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
        obs = []
        
        # 关节位置
        if self.config.include_joint_positions:
            positions = [self.joint_positions.get(name, 0.0) for name in self.joint_names]
            obs.extend(positions)
        
        # 关节速度
        if self.config.include_joint_velocities:
            velocities = [self.joint_velocities.get(name, 0.0) for name in self.joint_names]
            obs.extend(velocities)
        
        # 关节力矩
        if self.config.include_joint_efforts:
            efforts = [self.joint_efforts.get(name, 0.0) for name in self.joint_names]
            obs.extend(efforts)
        
        # 基座位姿
        if self.config.include_base_pose:
            obs.extend(self.base_position)
            obs.extend(self.base_orientation)
        
        # IMU数据
        if self.config.include_imu_data:
            if self.imu_simulator:
                imu_data = self.imu_simulator.generate_imu_data(
                    position=self.base_position,
                    orientation=self.base_orientation,
                    linear_velocity=self.base_linear_velocity,
                    angular_velocity=self.base_angular_velocity
                )
                obs.extend(imu_data['linear_acceleration'])
                obs.extend(imu_data['angular_velocity'])
                obs.extend(imu_data['orientation'][:3])  # 只取前3个分量
            else:
                # 使用模拟IMU数据
                obs.extend([0.0, 0.0, 9.81])  # 线性加速度
                obs.extend([0.0, 0.0, 0.0])   # 角速度
                obs.extend([0.0, 0.0, 0.0])   # 方向
        
        # 目标位置
        obs.extend(self.target_position)
        
        return np.array(obs, dtype=np.float32)
    
    def _compute_reward(self, action: np.ndarray) -> float:
        """计算奖励函数"""
        reward = 0.0
        
        # 距离奖励
        distance = np.linalg.norm(self.base_position - self.target_position)
        
        if self.config.reward_type == RewardType.SPARSE:
            # 稀疏奖励：只在到达目标时给奖励
            if distance < self.config.position_tolerance:
                reward += 100.0
        
        elif self.config.reward_type == RewardType.DENSE:
            # 密集奖励：基于距离的连续奖励
            max_distance = 10.0  # 假设最大距离
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
            velocity_penalty = np.sum(np.square(list(self.joint_velocities.values())))
            reward -= velocity_penalty * self.config.velocity_penalty_weight
            
            # 力矩惩罚
            effort_penalty = np.sum(np.square(action))
            reward -= effort_penalty * self.config.effort_penalty_weight
            
            # 稳定性奖励（基于IMU数据）
            angular_velocity_magnitude = np.linalg.norm(self.base_angular_velocity)
            stability_reward = np.exp(-angular_velocity_magnitude)
            reward += stability_reward * 0.1
        
        # 生存奖励
        reward += 0.1
        
        # 碰撞惩罚（简化）
        if self.base_position[2] < 0.1:  # 假设地面高度为0
            reward -= 10.0
        
        return reward
    
    def _is_done(self) -> bool:
        """判断回合是否结束"""
        # 达到最大步数
        if self.current_step >= self.config.max_episode_steps:
            return True
        
        # 到达目标
        distance = np.linalg.norm(self.base_position - self.target_position)
        if distance < self.config.position_tolerance:
            return True
        
        # 机器人倒下或碰撞
        if self.base_position[2] < 0.05:  # 高度过低
            return True
        
        # 关节超出限制
        for joint_name in self.joint_names:
            position = self.joint_positions.get(joint_name, 0.0)
            if abs(position) > np.pi:  # 简化的关节限制
                return True
        
        return False
    
    def _apply_action(self, action: np.ndarray):
        """应用动作到机器人"""
        if self.config.action_type == "continuous":
            # 连续动作：直接设置关节速度或力矩
            for i, joint_name in enumerate(self.joint_names):
                if i < len(action):
                    if hasattr(self.config, 'control_mode') and self.config.control_mode == 'effort':
                        # 力矩控制
                        self.joint_efforts[joint_name] = np.clip(
                            action[i], 
                            -self.config.max_joint_effort, 
                            self.config.max_joint_effort
                        )
                    else:
                        # 速度控制
                        target_velocity = np.clip(
                            action[i], 
                            -self.config.max_joint_velocity, 
                            self.config.max_joint_velocity
                        )
                        # 简化的速度控制
                        self.joint_velocities[joint_name] = target_velocity
        else:
            # 离散动作
            joint_idx = action // 3
            action_type = action % 3
            
            if joint_idx < len(self.joint_names):
                joint_name = self.joint_names[joint_idx]
                if action_type == 0:  # 停止
                    self.joint_velocities[joint_name] = 0.0
                elif action_type == 1:  # 正向
                    self.joint_velocities[joint_name] = self.config.max_joint_velocity * 0.5
                else:  # 反向
                    self.joint_velocities[joint_name] = -self.config.max_joint_velocity * 0.5
    
    def _reset_robot_state(self):
        """重置机器人状态"""
        # 重置关节状态
        for joint_name in self.joint_names:
            if self.config.randomize_initial_state:
                # 随机初始位置
                self.joint_positions[joint_name] = np.random.uniform(-0.5, 0.5)
                self.joint_velocities[joint_name] = np.random.uniform(-0.1, 0.1)
            else:
                # 固定初始位置
                self.joint_positions[joint_name] = 0.0
                self.joint_velocities[joint_name] = 0.0
            
            self.joint_efforts[joint_name] = 0.0
        
        # 重置基座状态
        if self.config.randomize_initial_state:
            self.base_position = np.random.uniform([-1, -1, 0.2], [1, 1, 0.5])
            self.base_orientation = np.array([0, 0, 0, 1])  # 单位四元数
        else:
            self.base_position = np.array([0.0, 0.0, 0.3])
            self.base_orientation = np.array([0, 0, 0, 1])
        
        self.base_linear_velocity = np.zeros(3)
        self.base_angular_velocity = np.zeros(3)
        
        # 随机化目标位置
        if self.config.randomize_initial_state:
            self.target_position = np.random.uniform([-2, -2, 0.1], [2, 2, 0.1])
        else:
            self.target_position = np.array([1.0, 0.0, 0.1])
    
    def _update_environment(self):
        """更新环境物理状态"""
        # 简化的物理仿真
        dt = self.config.dt
        
        # 更新关节位置（基于速度积分）
        for joint_name in self.joint_names:
            velocity = self.joint_velocities[joint_name]
            self.joint_positions[joint_name] += velocity * dt
            
            # 应用关节限制
            self.joint_positions[joint_name] = np.clip(
                self.joint_positions[joint_name], -np.pi, np.pi
            )
        
        # 使用数字孪生映射器更新基座位置（如果可用）
        if self.digital_twin_mapper:
            try:
                joint_positions_list = [self.joint_positions[name] for name in self.joint_names]
                result = self.digital_twin_mapper.forward_kinematics(joint_positions_list)
                if result:
                    # 更新基座位置（简化）
                    self.base_position[0] += self.base_linear_velocity[0] * dt
                    self.base_position[1] += self.base_linear_velocity[1] * dt
            except Exception as e:
                self.logger.debug(f"数字孪生映射器更新失败: {e}")
        
        # 简化的基座运动学
        # 基于轮子速度估算基座运动
        if 'l_wheel_joint' in self.joint_velocities and 'r_wheel_joint' in self.joint_velocities:
            left_wheel_vel = self.joint_velocities['l_wheel_joint']
            right_wheel_vel = self.joint_velocities['r_wheel_joint']
            
            # 简化的差分驱动模型
            wheel_radius = 0.05  # 轮子半径
            wheel_base = 0.3     # 轮距
            
            linear_vel = (left_wheel_vel + right_wheel_vel) * wheel_radius / 2
            angular_vel = (right_wheel_vel - left_wheel_vel) * wheel_radius / wheel_base
            
            self.base_linear_velocity[0] = linear_vel
            self.base_angular_velocity[2] = angular_vel
        
        # 添加噪声
        if self.config.noise_level > 0:
            noise = np.random.normal(0, self.config.noise_level, 3)
            self.base_position += noise * dt


def create_wheel_legged_environment(config: EnvironmentConfig = None, **kwargs) -> WheelLeggedRobotEnvironment:
    """创建轮腿机器人环境的工厂函数"""
    if config is None:
        config = EnvironmentConfig()
    
    # 从kwargs更新配置
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    return WheelLeggedRobotEnvironment(config)


# 注册环境（简化版本，不依赖gym）
def register_environments():
    """注册自定义环境（简化版本）"""
    try:
        # 创建环境注册表
        _env_registry = {
            'WheelLeggedRobot-v0': {
                'entry_point': WheelLeggedRobotEnvironment,
                'max_episode_steps': 1000,
                'kwargs': {}
            },
            'WheelLeggedRobotSparse-v0': {
                'entry_point': WheelLeggedRobotEnvironment,
                'max_episode_steps': 1000,
                'kwargs': {'config': EnvironmentConfig(reward_type=RewardType.SPARSE)}
            },
            'WheelLeggedRobotDense-v0': {
                'entry_point': WheelLeggedRobotEnvironment,
                'max_episode_steps': 1000,
                'kwargs': {'config': EnvironmentConfig(reward_type=RewardType.DENSE)}
            }
        }
        
        print("✅ 强化学习环境已注册（简化版本）")
        return _env_registry
        
    except Exception as e:
        print(f"⚠️  环境注册警告: {e}")
        return {}


if __name__ == "__main__":
    # 测试环境
    print("🧪 测试轮腿机器人强化学习环境")
    
    # 创建环境配置
    config = EnvironmentConfig(
        max_episode_steps=100,
        reward_type=RewardType.DENSE,
        randomize_initial_state=True,
        action_type="continuous"
    )
    
    try:
        # 创建环境
        env = create_wheel_legged_environment(config)
        print(f"✅ 环境创建成功")
        print(f"📊 观测空间: {env.observation_space}")
        print(f"🎮 动作空间: {env.action_space}")
        
        # 测试环境
        obs = env.reset()
        print(f"🔄 环境重置，初始观测维度: {obs.shape}")
        
        total_reward = 0
        for step in range(10):
            # 随机动作
            action = env.action_space.sample()
            obs, reward, done, info = env.step(action)
            total_reward += reward
            
            print(f"步骤 {step+1}: 奖励={reward:.3f}, 累计奖励={total_reward:.3f}, 结束={done}")
            
            if done:
                print("🏁 回合结束")
                break
        
        env.close()
        print("🎉 环境测试完成")
        
        # 注册环境
        register_environments()
        
    except Exception as e:
        print(f"❌ 环境测试失败: {e}")
        import traceback
        traceback.print_exc()