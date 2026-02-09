#!/usr/bin/env python3
"""
并行MuJoCo仿真后端

支持批量并行仿真的MuJoCo后端实现，专为强化学习训练优化。
提供向量化环境接口，支持多个仿真实例同时运行。
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Any
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp

from .simulation_manager import SimulationConfig, SimulationBackend
from .mujoco_backend import MuJoCoSimulationBackend

# MuJoCo导入
try:
    import mujoco
    MUJOCO_AVAILABLE = True
except ImportError:
    mujoco = None
    MUJOCO_AVAILABLE = False


class ParallelMuJoCoBackend:
    """并行MuJoCo仿真后端 - 支持批量仿真"""
    
    def __init__(self, config: SimulationConfig, num_envs: int = 4, use_multiprocessing: bool = False):
        """
        初始化并行仿真后端
        
        Args:
            config: 仿真配置
            num_envs: 并行环境数量
            use_multiprocessing: 是否使用多进程（True）或多线程（False）
        """
        self.config = config
        self.num_envs = num_envs
        self.use_multiprocessing = use_multiprocessing
        self.logger = logging.getLogger(__name__)
        
        if not MUJOCO_AVAILABLE:
            raise ImportError("MuJoCo不可用，无法创建并行后端")
        
        # 环境实例列表
        self.envs: List[MuJoCoSimulationBackend] = []
        self.is_initialized = False
        
        # 执行器
        self.executor = None
        
        # 性能统计
        self.total_steps = 0
        self.total_time = 0.0
        
        self.logger.info(f"并行MuJoCo后端初始化: {num_envs}个环境, "
                        f"{'多进程' if use_multiprocessing else '多线程'}模式")
    
    def initialize(self, model_path: str) -> bool:
        """初始化所有并行环境"""
        try:
            # 创建环境实例
            for i in range(self.num_envs):
                env = MuJoCoSimulationBackend(self.config)
                if not env.initialize(model_path):
                    self.logger.error(f"环境 {i} 初始化失败")
                    return False
                self.envs.append(env)
            
            # 创建执行器
            if self.use_multiprocessing:
                # 多进程模式（更好的并行性，但开销更大）
                self.executor = ProcessPoolExecutor(max_workers=self.num_envs)
            else:
                # 多线程模式（开销小，但受GIL限制）
                self.executor = ThreadPoolExecutor(max_workers=self.num_envs)
            
            self.is_initialized = True
            self.logger.info(f"✅ {self.num_envs}个并行环境初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 并行环境初始化失败: {e}")
            return False
    
    def reset(self, env_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """
        重置指定的环境
        
        Args:
            env_ids: 要重置的环境ID列表，None表示重置所有环境
            
        Returns:
            每个环境的初始状态列表
        """
        if not self.is_initialized:
            return []
        
        if env_ids is None:
            env_ids = list(range(self.num_envs))
        
        # 并行重置
        states = []
        for env_id in env_ids:
            if 0 <= env_id < self.num_envs:
                self.envs[env_id].reset()
                states.append(self.envs[env_id].get_state())
        
        return states
    
    def step(self, actions: List[Dict[str, float]]) -> Tuple[List[Dict], List[bool]]:
        """
        并行执行仿真步
        
        Args:
            actions: 每个环境的动作列表
            
        Returns:
            (states, dones): 状态列表和完成标志列表
        """
        if not self.is_initialized:
            return [], []
        
        import time
        start_time = time.time()
        
        # 确保动作数量匹配
        if len(actions) != self.num_envs:
            self.logger.warning(f"动作数量({len(actions)})与环境数量({self.num_envs})不匹配")
            actions = actions[:self.num_envs] + [{}] * (self.num_envs - len(actions))
        
        # 并行执行步进
        states = []
        dones = []
        
        for i, (env, action) in enumerate(zip(self.envs, actions)):
            success = env.step(action)
            states.append(env.get_state())
            dones.append(not success)  # 简化的完成判断
        
        # 更新性能统计
        step_time = time.time() - start_time
        self.total_steps += self.num_envs
        self.total_time += step_time
        
        return states, dones
    
    def get_states(self) -> List[Dict[str, Any]]:
        """获取所有环境的当前状态"""
        if not self.is_initialized:
            return []
        
        return [env.get_state() for env in self.envs]
    
    def set_joint_positions_batch(self, positions_list: List[Dict[str, float]]) -> List[bool]:
        """批量设置关节位置"""
        if not self.is_initialized:
            return [False] * self.num_envs
        
        results = []
        for env, positions in zip(self.envs, positions_list):
            results.append(env.set_joint_positions(positions))
        
        return results
    
    def render(self, env_id: int = 0, mode: str = 'human') -> Optional[np.ndarray]:
        """渲染指定环境"""
        if not self.is_initialized or env_id >= self.num_envs:
            return None
        
        return self.envs[env_id].render(mode)
    
    def get_performance_stats(self) -> Dict[str, float]:
        """获取性能统计"""
        if self.total_time > 0:
            avg_step_time = self.total_time / self.total_steps
            steps_per_second = self.total_steps / self.total_time
            envs_per_second = steps_per_second * self.num_envs
        else:
            avg_step_time = 0.0
            steps_per_second = 0.0
            envs_per_second = 0.0
        
        return {
            'total_steps': self.total_steps,
            'total_time': self.total_time,
            'avg_step_time': avg_step_time,
            'steps_per_second': steps_per_second,
            'envs_per_second': envs_per_second,
            'num_envs': self.num_envs
        }
    
    def close(self):
        """关闭所有环境"""
        for env in self.envs:
            env.close()
        
        if self.executor:
            self.executor.shutdown(wait=True)
            self.executor = None
        
        self.envs.clear()
        self.is_initialized = False
        self.logger.info("并行MuJoCo后端已关闭")


class VectorizedMuJoCoEnvironment:
    """
    向量化MuJoCo环境 - 符合强化学习框架的向量化接口
    
    提供类似gym.vector.VectorEnv的接口，支持批量操作
    """
    
    def __init__(self, config: SimulationConfig, num_envs: int = 4, 
                 model_path: str = None, use_multiprocessing: bool = False):
        """
        初始化向量化环境
        
        Args:
            config: 仿真配置
            num_envs: 并行环境数量
            model_path: 模型文件路径
            use_multiprocessing: 是否使用多进程
        """
        self.config = config
        self.num_envs = num_envs
        self.model_path = model_path
        self.logger = logging.getLogger(__name__)
        
        # 创建并行后端
        self.backend = ParallelMuJoCoBackend(config, num_envs, use_multiprocessing)
        
        # 环境状态
        self.current_steps = np.zeros(num_envs, dtype=np.int32)
        self.episode_rewards = np.zeros(num_envs, dtype=np.float32)
        
        # 初始化
        if model_path:
            self.backend.initialize(model_path)
    
    def reset(self, env_ids: Optional[np.ndarray] = None) -> np.ndarray:
        """
        重置环境
        
        Args:
            env_ids: 要重置的环境ID数组，None表示重置所有环境
            
        Returns:
            观测数组 shape=(num_envs, obs_dim)
        """
        if env_ids is None:
            env_ids = list(range(self.num_envs))
        else:
            env_ids = env_ids.tolist()
        
        # 重置后端
        states = self.backend.reset(env_ids)
        
        # 重置统计
        for env_id in env_ids:
            self.current_steps[env_id] = 0
            self.episode_rewards[env_id] = 0.0
        
        # 转换为观测数组
        observations = self._states_to_observations(states)
        
        return observations
    
    def step(self, actions: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, List[Dict]]:
        """
        执行动作
        
        Args:
            actions: 动作数组 shape=(num_envs, action_dim)
            
        Returns:
            (observations, rewards, dones, infos)
        """
        # 转换动作格式
        action_dicts = self._actions_to_dicts(actions)
        
        # 执行步进
        states, dones = self.backend.step(action_dicts)
        
        # 更新统计
        self.current_steps += 1
        
        # 计算奖励（简化版本）
        rewards = self._compute_rewards(states)
        self.episode_rewards += rewards
        
        # 转换为观测
        observations = self._states_to_observations(states)
        
        # 构建信息字典
        infos = []
        for i in range(self.num_envs):
            info = {
                'episode_step': self.current_steps[i],
                'episode_reward': self.episode_rewards[i],
                'base_position': states[i]['base_position']
            }
            infos.append(info)
        
        return observations, rewards, np.array(dones), infos
    
    def _states_to_observations(self, states: List[Dict]) -> np.ndarray:
        """将状态字典列表转换为观测数组"""
        observations = []
        
        for state in states:
            obs = []
            
            # 关节位置
            if 'joint_positions' in state:
                obs.extend(state['joint_positions'].values())
            
            # 关节速度
            if 'joint_velocities' in state:
                obs.extend(state['joint_velocities'].values())
            
            # 基座位置和方向
            if 'base_position' in state:
                obs.extend(state['base_position'])
            if 'base_orientation' in state:
                obs.extend(state['base_orientation'])
            
            observations.append(obs)
        
        return np.array(observations, dtype=np.float32)
    
    def _actions_to_dicts(self, actions: np.ndarray) -> List[Dict[str, float]]:
        """将动作数组转换为字典列表"""
        action_dicts = []
        
        # 假设动作对应关节电机
        joint_names = ['lf0_motor', 'lf1_motor', 'rf0_motor', 'rf1_motor', 
                      'l_wheel_motor', 'r_wheel_motor']
        
        for action in actions:
            action_dict = {}
            for i, joint_name in enumerate(joint_names):
                if i < len(action):
                    action_dict[joint_name] = float(action[i])
            action_dicts.append(action_dict)
        
        return action_dicts
    
    def _compute_rewards(self, states: List[Dict]) -> np.ndarray:
        """计算奖励（简化版本）"""
        rewards = np.zeros(self.num_envs, dtype=np.float32)
        
        for i, state in enumerate(states):
            # 基于高度的简单奖励
            if 'base_position' in state:
                height = state['base_position'][2]
                rewards[i] = 1.0 if height > 0.2 else -1.0
            else:
                rewards[i] = 0.0
        
        return rewards
    
    def get_performance_stats(self) -> Dict[str, float]:
        """获取性能统计"""
        return self.backend.get_performance_stats()
    
    def close(self):
        """关闭环境"""
        self.backend.close()


if __name__ == "__main__":
    # 测试并行MuJoCo后端
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 测试并行MuJoCo仿真后端")
    print("=" * 50)
    
    if not MUJOCO_AVAILABLE:
        print("❌ MuJoCo不可用，跳过测试")
        exit(1)
    
    # 创建配置
    config = SimulationConfig(
        backend=SimulationBackend.MUJOCO,
        enable_rendering=False,
        dt=0.001
    )
    
    try:
        # 测试并行后端
        print("\n📦 测试并行后端...")
        num_envs = 4
        parallel_backend = ParallelMuJoCoBackend(config, num_envs=num_envs)
        
        # 创建测试模型
        from .mujoco_backend import URDFToMJCFConverter
        converter = URDFToMJCFConverter()
        test_mjcf = converter._create_simple_mjcf("test_parallel_model.xml")
        
        # 初始化
        success = parallel_backend.initialize(test_mjcf)
        print(f"初始化: {'✅' if success else '❌'}")
        
        if success:
            # 重置所有环境
            states = parallel_backend.reset()
            print(f"✅ 重置 {len(states)} 个环境")
            
            # 执行批量步进
            print("\n🏃 执行批量仿真...")
            for step in range(100):
                # 随机动作
                actions = []
                for _ in range(num_envs):
                    action = {
                        'lf0_motor': np.random.uniform(-1, 1),
                        'rf0_motor': np.random.uniform(-1, 1),
                        'l_wheel_motor': np.random.uniform(-1, 1),
                        'r_wheel_motor': np.random.uniform(-1, 1)
                    }
                    actions.append(action)
                
                states, dones = parallel_backend.step(actions)
                
                if step % 25 == 0:
                    print(f"步骤 {step}: {len(states)} 个环境状态已更新")
            
            # 显示性能统计
            print("\n📊 性能统计:")
            stats = parallel_backend.get_performance_stats()
            for key, value in stats.items():
                print(f"  {key}: {value:.4f}")
            
            parallel_backend.close()
        
        # 测试向量化环境
        print("\n🎯 测试向量化环境...")
        vec_env = VectorizedMuJoCoEnvironment(config, num_envs=4, model_path=test_mjcf)
        
        # 重置
        obs = vec_env.reset()
        print(f"✅ 向量化环境重置，观测形状: {obs.shape}")
        
        # 执行步进
        for step in range(50):
            actions = np.random.uniform(-1, 1, size=(num_envs, 6))
            obs, rewards, dones, infos = vec_env.step(actions)
            
            if step % 10 == 0:
                print(f"步骤 {step}: 平均奖励={rewards.mean():.3f}")
        
        # 显示性能
        print("\n📊 向量化环境性能:")
        stats = vec_env.get_performance_stats()
        for key, value in stats.items():
            print(f"  {key}: {value:.4f}")
        
        vec_env.close()
        
        # 清理
        import os
        if os.path.exists("test_parallel_model.xml"):
            os.remove("test_parallel_model.xml")
        
        print("\n🎉 并行MuJoCo后端测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
