#!/usr/bin/env python3
"""
PPO (Proximal Policy Optimization) 训练器

为轮腿机器人实现PPO强化学习算法，支持CPU训练，适用于AMD APU等非NVIDIA硬件。
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.distributions import Normal
import time
import logging
import json
import os
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import deque
import matplotlib.pyplot as plt

# 导入我们的强化学习环境
from wheel_legged_control.algorithms.rl_environment import (
    create_wheel_legged_environment, EnvironmentConfig, RewardType
)


@dataclass
class PPOConfig:
    """PPO算法配置参数"""
    # 网络架构
    hidden_dim: int = 256
    num_layers: int = 3
    activation: str = "tanh"  # "tanh", "relu", "elu"
    
    # PPO超参数
    learning_rate: float = 3e-4
    gamma: float = 0.99          # 折扣因子
    gae_lambda: float = 0.95     # GAE参数
    clip_epsilon: float = 0.2    # PPO裁剪参数
    entropy_coef: float = 0.01   # 熵正则化系数
    value_coef: float = 0.5      # 价值函数损失系数
    max_grad_norm: float = 0.5   # 梯度裁剪
    
    # 训练参数
    batch_size: int = 64
    mini_batch_size: int = 32
    ppo_epochs: int = 10         # 每次更新的PPO轮数
    max_episodes: int = 1000     # 最大训练回合数
    max_steps_per_episode: int = 1000
    
    # 经验收集
    rollout_steps: int = 2048    # 每次收集的步数
    num_envs: int = 1            # 并行环境数量（CPU训练建议1-4）
    
    # 评估和保存
    eval_frequency: int = 50     # 评估频率
    save_frequency: int = 100    # 模型保存频率
    log_frequency: int = 10      # 日志记录频率
    
    # 设备设置
    device: str = "cpu"          # 强制使用CPU，适合AMD APU
    num_threads: int = 4         # CPU线程数
    
    # 早停和学习率调度
    early_stopping_patience: int = 100
    lr_schedule: bool = True
    lr_decay_factor: float = 0.99


class PolicyNetwork(nn.Module):
    """策略网络（Actor）"""
    
    def __init__(self, obs_dim: int, action_dim: int, config: PPOConfig):
        super().__init__()
        self.config = config
        
        # 选择激活函数
        if config.activation == "tanh":
            activation = nn.Tanh
        elif config.activation == "relu":
            activation = nn.ReLU
        elif config.activation == "elu":
            activation = nn.ELU
        else:
            activation = nn.Tanh
        
        # 构建网络层
        layers = []
        input_dim = obs_dim
        
        for i in range(config.num_layers):
            layers.append(nn.Linear(input_dim, config.hidden_dim))
            layers.append(activation())
            input_dim = config.hidden_dim
        
        self.shared_layers = nn.Sequential(*layers)
        
        # 策略头：输出动作均值
        self.action_mean = nn.Linear(config.hidden_dim, action_dim)
        
        # 策略头：输出动作标准差（对数）
        self.action_log_std = nn.Parameter(torch.zeros(action_dim))
        
        # 初始化权重
        self.apply(self._init_weights)
    
    def _init_weights(self, module):
        """初始化网络权重"""
        if isinstance(module, nn.Linear):
            nn.init.orthogonal_(module.weight, gain=np.sqrt(2))
            nn.init.constant_(module.bias, 0)
    
    def forward(self, obs: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """前向传播"""
        features = self.shared_layers(obs)
        action_mean = self.action_mean(features)
        action_std = torch.exp(self.action_log_std.clamp(-20, 2))  # 限制标准差范围
        return action_mean, action_std
    
    def get_action_and_log_prob(self, obs: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """获取动作和对数概率"""
        action_mean, action_std = self.forward(obs)
        dist = Normal(action_mean, action_std)
        action = dist.sample()
        log_prob = dist.log_prob(action).sum(dim=-1)
        return action, log_prob
    
    def evaluate_actions(self, obs: torch.Tensor, actions: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """评估动作的对数概率和熵"""
        action_mean, action_std = self.forward(obs)
        dist = Normal(action_mean, action_std)
        log_prob = dist.log_prob(actions).sum(dim=-1)
        entropy = dist.entropy().sum(dim=-1)
        return log_prob, entropy


class ValueNetwork(nn.Module):
    """价值网络（Critic）"""
    
    def __init__(self, obs_dim: int, config: PPOConfig):
        super().__init__()
        self.config = config
        
        # 选择激活函数
        if config.activation == "tanh":
            activation = nn.Tanh
        elif config.activation == "relu":
            activation = nn.ReLU
        elif config.activation == "elu":
            activation = nn.ELU
        else:
            activation = nn.Tanh
        
        # 构建网络层
        layers = []
        input_dim = obs_dim
        
        for i in range(config.num_layers):
            layers.append(nn.Linear(input_dim, config.hidden_dim))
            layers.append(activation())
            input_dim = config.hidden_dim
        
        # 输出层
        layers.append(nn.Linear(config.hidden_dim, 1))
        
        self.network = nn.Sequential(*layers)
        
        # 初始化权重
        self.apply(self._init_weights)
    
    def _init_weights(self, module):
        """初始化网络权重"""
        if isinstance(module, nn.Linear):
            nn.init.orthogonal_(module.weight, gain=np.sqrt(2))
            nn.init.constant_(module.bias, 0)
    
    def forward(self, obs: torch.Tensor) -> torch.Tensor:
        """前向传播"""
        return self.network(obs).squeeze(-1)


class PPOTrainer:
    """PPO训练器"""
    
    def __init__(self, env_config: EnvironmentConfig, ppo_config: PPOConfig):
        self.env_config = env_config
        self.config = ppo_config
        self.logger = logging.getLogger(__name__)
        
        # 设置设备和线程
        self.device = torch.device(ppo_config.device)
        if ppo_config.device == "cpu":
            torch.set_num_threads(ppo_config.num_threads)
        
        # 创建环境
        self.env = create_wheel_legged_environment(env_config)
        
        # 获取环境信息
        self.obs_dim = self.env.observation_space.shape[0]
        self.action_dim = self.env.action_space.shape[0]
        
        # 创建网络
        self.policy_net = PolicyNetwork(self.obs_dim, self.action_dim, ppo_config).to(self.device)
        self.value_net = ValueNetwork(self.obs_dim, ppo_config).to(self.device)
        
        # 创建优化器
        self.policy_optimizer = optim.Adam(self.policy_net.parameters(), lr=ppo_config.learning_rate)
        self.value_optimizer = optim.Adam(self.value_net.parameters(), lr=ppo_config.learning_rate)
        
        # 学习率调度器
        if ppo_config.lr_schedule:
            self.policy_scheduler = optim.lr_scheduler.ExponentialLR(
                self.policy_optimizer, gamma=ppo_config.lr_decay_factor
            )
            self.value_scheduler = optim.lr_scheduler.ExponentialLR(
                self.value_optimizer, gamma=ppo_config.lr_decay_factor
            )
        
        # 训练统计
        self.episode_rewards = deque(maxlen=100)
        self.episode_lengths = deque(maxlen=100)
        self.training_stats = {
            'episode': 0,
            'total_steps': 0,
            'policy_loss': [],
            'value_loss': [],
            'entropy': [],
            'rewards': [],
            'episode_lengths': []
        }
        
        # 早停
        self.best_reward = -np.inf
        self.patience_counter = 0
        
        self.logger.info(f"PPO训练器初始化完成")
        self.logger.info(f"观测维度: {self.obs_dim}, 动作维度: {self.action_dim}")
        self.logger.info(f"设备: {self.device}, 线程数: {ppo_config.num_threads}")
    
    def collect_rollouts(self) -> Dict[str, torch.Tensor]:
        """收集经验数据"""
        observations = []
        actions = []
        rewards = []
        values = []
        log_probs = []
        dones = []
        
        obs = self.env.reset()
        
        for step in range(self.config.rollout_steps):
            obs_tensor = torch.FloatTensor(obs).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                # 获取动作和价值
                action, log_prob = self.policy_net.get_action_and_log_prob(obs_tensor)
                value = self.value_net(obs_tensor)
            
            # 执行动作
            next_obs, reward, done, info = self.env.step(action.cpu().numpy().flatten())
            
            # 存储数据
            observations.append(obs)
            actions.append(action.cpu().numpy().flatten())
            rewards.append(reward)
            values.append(value.cpu().item())
            log_probs.append(log_prob.cpu().item())
            dones.append(done)
            
            obs = next_obs
            
            if done:
                obs = self.env.reset()
                self.episode_rewards.append(info.get('episode_reward', reward))
                self.episode_lengths.append(info.get('current_step', 1))
        
        # 计算最后一个状态的价值
        obs_tensor = torch.FloatTensor(obs).unsqueeze(0).to(self.device)
        with torch.no_grad():
            next_value = self.value_net(obs_tensor).cpu().item()
        
        # 转换为张量
        rollout_data = {
            'observations': torch.FloatTensor(observations).to(self.device),
            'actions': torch.FloatTensor(actions).to(self.device),
            'rewards': torch.FloatTensor(rewards).to(self.device),
            'values': torch.FloatTensor(values).to(self.device),
            'log_probs': torch.FloatTensor(log_probs).to(self.device),
            'dones': torch.FloatTensor(dones).to(self.device),
            'next_value': next_value
        }
        
        return rollout_data
    
    def compute_gae(self, rollout_data: Dict[str, torch.Tensor]) -> Tuple[torch.Tensor, torch.Tensor]:
        """计算广义优势估计（GAE）"""
        rewards = rollout_data['rewards']
        values = rollout_data['values']
        dones = rollout_data['dones']
        next_value = rollout_data['next_value']
        
        advantages = torch.zeros_like(rewards)
        returns = torch.zeros_like(rewards)
        
        gae = 0
        for t in reversed(range(len(rewards))):
            if t == len(rewards) - 1:
                next_value_t = next_value
                next_non_terminal = 1.0 - dones[t]
            else:
                next_value_t = values[t + 1]
                next_non_terminal = 1.0 - dones[t]
            
            delta = rewards[t] + self.config.gamma * next_value_t * next_non_terminal - values[t]
            gae = delta + self.config.gamma * self.config.gae_lambda * next_non_terminal * gae
            advantages[t] = gae
            returns[t] = advantages[t] + values[t]
        
        # 标准化优势
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        return advantages, returns
    
    def update_policy(self, rollout_data: Dict[str, torch.Tensor], advantages: torch.Tensor, returns: torch.Tensor):
        """更新策略和价值网络"""
        observations = rollout_data['observations']
        actions = rollout_data['actions']
        old_log_probs = rollout_data['log_probs']
        values = rollout_data['values']
        
        # 创建数据集
        dataset_size = len(observations)
        indices = np.arange(dataset_size)
        
        policy_losses = []
        value_losses = []
        entropies = []
        
        for epoch in range(self.config.ppo_epochs):
            # 随机打乱数据
            np.random.shuffle(indices)
            
            for start in range(0, dataset_size, self.config.mini_batch_size):
                end = start + self.config.mini_batch_size
                batch_indices = indices[start:end]
                
                batch_obs = observations[batch_indices]
                batch_actions = actions[batch_indices]
                batch_old_log_probs = old_log_probs[batch_indices]
                batch_advantages = advantages[batch_indices]
                batch_returns = returns[batch_indices]
                batch_old_values = values[batch_indices]
                
                # 计算新的对数概率和熵
                new_log_probs, entropy = self.policy_net.evaluate_actions(batch_obs, batch_actions)
                
                # 计算比率
                ratio = torch.exp(new_log_probs - batch_old_log_probs)
                
                # PPO损失
                surr1 = ratio * batch_advantages
                surr2 = torch.clamp(ratio, 1 - self.config.clip_epsilon, 1 + self.config.clip_epsilon) * batch_advantages
                policy_loss = -torch.min(surr1, surr2).mean()
                
                # 熵损失
                entropy_loss = -entropy.mean()
                
                # 总策略损失
                total_policy_loss = policy_loss + self.config.entropy_coef * entropy_loss
                
                # 更新策略网络
                self.policy_optimizer.zero_grad()
                total_policy_loss.backward()
                nn.utils.clip_grad_norm_(self.policy_net.parameters(), self.config.max_grad_norm)
                self.policy_optimizer.step()
                
                # 价值函数损失
                new_values = self.value_net(batch_obs)
                value_loss = F.mse_loss(new_values, batch_returns)
                
                # 更新价值网络
                self.value_optimizer.zero_grad()
                value_loss.backward()
                nn.utils.clip_grad_norm_(self.value_net.parameters(), self.config.max_grad_norm)
                self.value_optimizer.step()
                
                # 记录损失
                policy_losses.append(policy_loss.item())
                value_losses.append(value_loss.item())
                entropies.append(entropy.mean().item())
        
        # 更新学习率
        if self.config.lr_schedule:
            self.policy_scheduler.step()
            self.value_scheduler.step()
        
        return np.mean(policy_losses), np.mean(value_losses), np.mean(entropies)
    
    def evaluate(self, num_episodes: int = 5) -> Tuple[float, float]:
        """评估当前策略"""
        eval_rewards = []
        eval_lengths = []
        
        for _ in range(num_episodes):
            obs = self.env.reset()
            episode_reward = 0
            episode_length = 0
            done = False
            
            while not done:
                obs_tensor = torch.FloatTensor(obs).unsqueeze(0).to(self.device)
                with torch.no_grad():
                    action_mean, _ = self.policy_net(obs_tensor)
                    action = action_mean  # 使用确定性策略进行评估
                
                obs, reward, done, info = self.env.step(action.cpu().numpy().flatten())
                episode_reward += reward
                episode_length += 1
                
                if episode_length >= self.config.max_steps_per_episode:
                    break
            
            eval_rewards.append(episode_reward)
            eval_lengths.append(episode_length)
        
        return np.mean(eval_rewards), np.mean(eval_lengths)
    
    def save_model(self, filepath: str):
        """保存模型"""
        torch.save({
            'policy_net': self.policy_net.state_dict(),
            'value_net': self.value_net.state_dict(),
            'policy_optimizer': self.policy_optimizer.state_dict(),
            'value_optimizer': self.value_optimizer.state_dict(),
            'config': self.config,
            'training_stats': self.training_stats
        }, filepath)
        self.logger.info(f"模型已保存到: {filepath}")
    
    def load_model(self, filepath: str):
        """加载模型"""
        checkpoint = torch.load(filepath, map_location=self.device)
        self.policy_net.load_state_dict(checkpoint['policy_net'])
        self.value_net.load_state_dict(checkpoint['value_net'])
        self.policy_optimizer.load_state_dict(checkpoint['policy_optimizer'])
        self.value_optimizer.load_state_dict(checkpoint['value_optimizer'])
        self.training_stats = checkpoint.get('training_stats', self.training_stats)
        self.logger.info(f"模型已从 {filepath} 加载")
    
    def train(self, save_dir: str = "models"):
        """开始训练"""
        os.makedirs(save_dir, exist_ok=True)
        
        self.logger.info("开始PPO训练")
        self.logger.info(f"最大回合数: {self.config.max_episodes}")
        self.logger.info(f"每次收集步数: {self.config.rollout_steps}")
        
        start_time = time.time()
        
        for episode in range(self.config.max_episodes):
            # 收集经验
            rollout_data = self.collect_rollouts()
            
            # 计算优势和回报
            advantages, returns = self.compute_gae(rollout_data)
            
            # 更新网络
            policy_loss, value_loss, entropy = self.update_policy(rollout_data, advantages, returns)
            
            # 更新统计信息
            self.training_stats['episode'] = episode
            self.training_stats['total_steps'] += self.config.rollout_steps
            self.training_stats['policy_loss'].append(policy_loss)
            self.training_stats['value_loss'].append(value_loss)
            self.training_stats['entropy'].append(entropy)
            
            # 记录奖励
            if self.episode_rewards:
                avg_reward = np.mean(self.episode_rewards)
                avg_length = np.mean(self.episode_lengths)
                self.training_stats['rewards'].append(avg_reward)
                self.training_stats['episode_lengths'].append(avg_length)
                
                # 早停检查
                if avg_reward > self.best_reward:
                    self.best_reward = avg_reward
                    self.patience_counter = 0
                    # 保存最佳模型
                    self.save_model(os.path.join(save_dir, "best_model.pth"))
                else:
                    self.patience_counter += 1
            
            # 日志记录
            if episode % self.config.log_frequency == 0:
                elapsed_time = time.time() - start_time
                if self.episode_rewards:
                    self.logger.info(
                        f"Episode {episode:4d} | "
                        f"Avg Reward: {np.mean(self.episode_rewards):8.2f} | "
                        f"Avg Length: {np.mean(self.episode_lengths):6.1f} | "
                        f"Policy Loss: {policy_loss:8.4f} | "
                        f"Value Loss: {value_loss:8.4f} | "
                        f"Entropy: {entropy:8.4f} | "
                        f"Time: {elapsed_time:6.1f}s"
                    )
            
            # 评估
            if episode % self.config.eval_frequency == 0 and episode > 0:
                eval_reward, eval_length = self.evaluate()
                self.logger.info(f"评估 - 平均奖励: {eval_reward:.2f}, 平均长度: {eval_length:.1f}")
            
            # 保存模型
            if episode % self.config.save_frequency == 0 and episode > 0:
                self.save_model(os.path.join(save_dir, f"model_episode_{episode}.pth"))
            
            # 早停
            if self.patience_counter >= self.config.early_stopping_patience:
                self.logger.info(f"早停触发，在第 {episode} 回合停止训练")
                break
        
        # 保存最终模型
        self.save_model(os.path.join(save_dir, "final_model.pth"))
        
        # 保存训练统计
        with open(os.path.join(save_dir, "training_stats.json"), 'w') as f:
            json.dump(self.training_stats, f, indent=2)
        
        self.logger.info("训练完成")
        return self.training_stats
    
    def plot_training_curves(self, save_path: str = None):
        """绘制训练曲线"""
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        
        # 奖励曲线
        if self.training_stats['rewards']:
            axes[0, 0].plot(self.training_stats['rewards'])
            axes[0, 0].set_title('平均奖励')
            axes[0, 0].set_xlabel('Episode')
            axes[0, 0].set_ylabel('Reward')
            axes[0, 0].grid(True)
        
        # 策略损失
        if self.training_stats['policy_loss']:
            axes[0, 1].plot(self.training_stats['policy_loss'])
            axes[0, 1].set_title('策略损失')
            axes[0, 1].set_xlabel('Update')
            axes[0, 1].set_ylabel('Policy Loss')
            axes[0, 1].grid(True)
        
        # 价值损失
        if self.training_stats['value_loss']:
            axes[1, 0].plot(self.training_stats['value_loss'])
            axes[1, 0].set_title('价值损失')
            axes[1, 0].set_xlabel('Update')
            axes[1, 0].set_ylabel('Value Loss')
            axes[1, 0].grid(True)
        
        # 熵
        if self.training_stats['entropy']:
            axes[1, 1].plot(self.training_stats['entropy'])
            axes[1, 1].set_title('策略熵')
            axes[1, 1].set_xlabel('Update')
            axes[1, 1].set_ylabel('Entropy')
            axes[1, 1].grid(True)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"训练曲线已保存到: {save_path}")
        
        try:
            plt.show()
        except:
            print("无法显示图表，但已保存到文件")


def create_default_configs() -> Tuple[EnvironmentConfig, PPOConfig]:
    """创建默认配置"""
    # 环境配置
    env_config = EnvironmentConfig(
        max_episode_steps=1000,
        dt=0.02,
        reward_type=RewardType.SHAPED,
        action_type="continuous",
        randomize_initial_state=True,
        target_position=[2.0, 0.0, 0.1],
        position_tolerance=0.2,
        velocity_penalty_weight=0.01,
        effort_penalty_weight=0.001,
        stability_reward_weight=1.0
    )
    
    # PPO配置（针对CPU优化）
    ppo_config = PPOConfig(
        hidden_dim=128,          # 较小的网络，适合CPU
        num_layers=2,
        learning_rate=3e-4,
        batch_size=32,           # 较小的批次大小
        mini_batch_size=16,
        rollout_steps=1024,      # 适中的收集步数
        max_episodes=500,        # 适中的训练回合数
        device="cpu",
        num_threads=4,           # 根据您的AMD APU调整
        eval_frequency=25,
        save_frequency=50,
        log_frequency=5
    )
    
    return env_config, ppo_config


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 PPO强化学习训练器 - 适用于AMD APU")
    print("=" * 60)
    
    # 创建配置
    env_config, ppo_config = create_default_configs()
    
    print(f"🖥️  设备: {ppo_config.device}")
    print(f"🧵 线程数: {ppo_config.num_threads}")
    print(f"🎯 目标位置: {env_config.target_position}")
    print(f"📊 网络结构: {ppo_config.num_layers}层 x {ppo_config.hidden_dim}神经元")
    print(f"🔄 最大回合数: {ppo_config.max_episodes}")
    
    try:
        # 创建训练器
        trainer = PPOTrainer(env_config, ppo_config)
        
        # 开始训练
        print("\n开始训练...")
        stats = trainer.train(save_dir="ppo_models")
        
        # 绘制训练曲线
        trainer.plot_training_curves("ppo_models/training_curves.png")
        
        print("\n🎉 训练完成！")
        print(f"📁 模型保存在: ppo_models/")
        print(f"📈 训练曲线: ppo_models/training_curves.png")
        
    except KeyboardInterrupt:
        print("\n⏹️  训练被用户中断")
    except Exception as e:
        print(f"\n❌ 训练过程中发生错误: {e}")
        import traceback
        traceback.print_exc()