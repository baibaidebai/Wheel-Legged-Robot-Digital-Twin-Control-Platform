#!/usr/bin/env python3
"""
PPO训练器测试

测试PPO算法的各个组件和训练流程。
"""

import unittest
import numpy as np
import torch
import tempfile
import os
import shutil
from unittest.mock import patch, MagicMock

# 导入被测试的模块
from wheel_legged_control.algorithms.ppo_trainer import (
    PPOTrainer, PPOConfig, PolicyNetwork, ValueNetwork, create_default_configs
)
from wheel_legged_control.algorithms.rl_environment import (
    EnvironmentConfig, RewardType, create_wheel_legged_environment
)


class TestPolicyNetwork(unittest.TestCase):
    """测试策略网络"""
    
    def setUp(self):
        """设置测试环境"""
        self.config = PPOConfig(
            hidden_dim=64,
            num_layers=2,
            activation="tanh"
        )
        self.obs_dim = 10
        self.action_dim = 6
        self.policy_net = PolicyNetwork(self.obs_dim, self.action_dim, self.config)
    
    def test_network_initialization(self):
        """测试网络初始化"""
        self.assertIsInstance(self.policy_net, PolicyNetwork)
        self.assertEqual(len(self.policy_net.shared_layers), 4)  # 2层 * 2 (Linear + Activation)
    
    def test_forward_pass(self):
        """测试前向传播"""
        batch_size = 5
        obs = torch.randn(batch_size, self.obs_dim)
        
        action_mean, action_std = self.policy_net(obs)
        
        self.assertEqual(action_mean.shape, (batch_size, self.action_dim))
        self.assertEqual(action_std.shape, (self.action_dim,))
        self.assertTrue(torch.all(action_std > 0))  # 标准差应该为正
    
    def test_get_action_and_log_prob(self):
        """测试动作采样和对数概率计算"""
        batch_size = 3
        obs = torch.randn(batch_size, self.obs_dim)
        
        action, log_prob = self.policy_net.get_action_and_log_prob(obs)
        
        self.assertEqual(action.shape, (batch_size, self.action_dim))
        self.assertEqual(log_prob.shape, (batch_size,))
    
    def test_evaluate_actions(self):
        """测试动作评估"""
        batch_size = 4
        obs = torch.randn(batch_size, self.obs_dim)
        actions = torch.randn(batch_size, self.action_dim)
        
        log_prob, entropy = self.policy_net.evaluate_actions(obs, actions)
        
        self.assertEqual(log_prob.shape, (batch_size,))
        self.assertEqual(entropy.shape, (batch_size,))


class TestValueNetwork(unittest.TestCase):
    """测试价值网络"""
    
    def setUp(self):
        """设置测试环境"""
        self.config = PPOConfig(
            hidden_dim=64,
            num_layers=2,
            activation="relu"
        )
        self.obs_dim = 10
        self.value_net = ValueNetwork(self.obs_dim, self.config)
    
    def test_network_initialization(self):
        """测试网络初始化"""
        self.assertIsInstance(self.value_net, ValueNetwork)
    
    def test_forward_pass(self):
        """测试前向传播"""
        batch_size = 5
        obs = torch.randn(batch_size, self.obs_dim)
        
        values = self.value_net(obs)
        
        self.assertEqual(values.shape, (batch_size,))


class TestPPOConfig(unittest.TestCase):
    """测试PPO配置"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = PPOConfig()
        
        self.assertEqual(config.device, "cpu")
        self.assertEqual(config.hidden_dim, 256)
        self.assertEqual(config.learning_rate, 3e-4)
        self.assertEqual(config.gamma, 0.99)
        self.assertTrue(config.lr_schedule)
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = PPOConfig(
            hidden_dim=128,
            learning_rate=1e-3,
            device="cpu",
            num_threads=2
        )
        
        self.assertEqual(config.hidden_dim, 128)
        self.assertEqual(config.learning_rate, 1e-3)
        self.assertEqual(config.device, "cpu")
        self.assertEqual(config.num_threads, 2)


class TestPPOTrainer(unittest.TestCase):
    """测试PPO训练器"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建简化的配置用于快速测试
        self.env_config = EnvironmentConfig(
            max_episode_steps=50,
            dt=0.02,
            reward_type=RewardType.DENSE,
            action_type="continuous",
            randomize_initial_state=False
        )
        
        self.ppo_config = PPOConfig(
            hidden_dim=32,
            num_layers=2,
            learning_rate=1e-3,
            batch_size=16,
            mini_batch_size=8,
            ppo_epochs=2,
            max_episodes=5,
            rollout_steps=64,
            device="cpu",
            num_threads=1,
            eval_frequency=2,
            save_frequency=10,
            log_frequency=1
        )
        
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """清理测试环境"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_trainer_initialization(self):
        """测试训练器初始化"""
        trainer = PPOTrainer(self.env_config, self.ppo_config)
        
        self.assertIsInstance(trainer, PPOTrainer)
        self.assertIsInstance(trainer.policy_net, PolicyNetwork)
        self.assertIsInstance(trainer.value_net, ValueNetwork)
        self.assertEqual(trainer.device.type, "cpu")
    
    def test_collect_rollouts(self):
        """测试经验收集"""
        trainer = PPOTrainer(self.env_config, self.ppo_config)
        
        rollout_data = trainer.collect_rollouts()
        
        # 检查数据结构
        expected_keys = ['observations', 'actions', 'rewards', 'values', 'log_probs', 'dones', 'next_value']
        for key in expected_keys:
            self.assertIn(key, rollout_data)
        
        # 检查数据形状
        self.assertEqual(rollout_data['observations'].shape[0], self.ppo_config.rollout_steps)
        self.assertEqual(rollout_data['actions'].shape[0], self.ppo_config.rollout_steps)
        self.assertEqual(rollout_data['rewards'].shape[0], self.ppo_config.rollout_steps)
    
    def test_compute_gae(self):
        """测试GAE计算"""
        trainer = PPOTrainer(self.env_config, self.ppo_config)
        
        # 创建模拟数据
        rollout_steps = 10
        rollout_data = {
            'rewards': torch.randn(rollout_steps),
            'values': torch.randn(rollout_steps),
            'dones': torch.zeros(rollout_steps),
            'next_value': 0.5
        }
        
        advantages, returns = trainer.compute_gae(rollout_data)
        
        self.assertEqual(advantages.shape, (rollout_steps,))
        self.assertEqual(returns.shape, (rollout_steps,))
        
        # 检查优势标准化
        self.assertAlmostEqual(advantages.mean().item(), 0.0, places=5)
        self.assertAlmostEqual(advantages.std().item(), 1.0, places=5)
    
    def test_model_save_load(self):
        """测试模型保存和加载"""
        trainer = PPOTrainer(self.env_config, self.ppo_config)
        
        # 保存模型
        model_path = os.path.join(self.temp_dir, "test_model.pth")
        trainer.save_model(model_path)
        self.assertTrue(os.path.exists(model_path))
        
        # 修改网络参数
        original_param = trainer.policy_net.action_mean.weight.clone()
        trainer.policy_net.action_mean.weight.data.fill_(0.5)
        
        # 加载模型
        trainer.load_model(model_path)
        loaded_param = trainer.policy_net.action_mean.weight
        
        # 验证参数恢复
        self.assertTrue(torch.allclose(original_param, loaded_param))
    
    def test_evaluate(self):
        """测试策略评估"""
        trainer = PPOTrainer(self.env_config, self.ppo_config)
        
        avg_reward, avg_length = trainer.evaluate(num_episodes=2)
        
        self.assertIsInstance(avg_reward, float)
        self.assertIsInstance(avg_length, float)
        self.assertGreater(avg_length, 0)
    
    @patch('matplotlib.pyplot.show')
    def test_plot_training_curves(self, mock_show):
        """测试训练曲线绘制"""
        trainer = PPOTrainer(self.env_config, self.ppo_config)
        
        # 添加一些模拟统计数据
        trainer.training_stats['rewards'] = [1.0, 2.0, 3.0]
        trainer.training_stats['policy_loss'] = [0.1, 0.08, 0.06]
        trainer.training_stats['value_loss'] = [0.5, 0.4, 0.3]
        trainer.training_stats['entropy'] = [1.0, 0.9, 0.8]
        
        # 测试绘图（不显示）
        plot_path = os.path.join(self.temp_dir, "test_curves.png")
        trainer.plot_training_curves(save_path=plot_path)
        
        self.assertTrue(os.path.exists(plot_path))
    
    def test_short_training_run(self):
        """测试短期训练运行"""
        # 使用非常小的配置进行快速测试
        small_config = PPOConfig(
            hidden_dim=16,
            num_layers=1,
            max_episodes=2,
            rollout_steps=32,
            ppo_epochs=1,
            batch_size=8,
            mini_batch_size=4,
            device="cpu",
            num_threads=1,
            log_frequency=1,
            eval_frequency=1,
            save_frequency=1
        )
        
        trainer = PPOTrainer(self.env_config, small_config)
        
        # 运行短期训练
        stats = trainer.train(save_dir=self.temp_dir)
        
        # 验证训练统计
        self.assertIsInstance(stats, dict)
        self.assertIn('episode', stats)
        self.assertIn('total_steps', stats)
        
        # 验证模型文件生成
        model_files = [f for f in os.listdir(self.temp_dir) if f.endswith('.pth')]
        self.assertGreater(len(model_files), 0)


class TestDefaultConfigs(unittest.TestCase):
    """测试默认配置创建"""
    
    def test_create_default_configs(self):
        """测试默认配置创建"""
        env_config, ppo_config = create_default_configs()
        
        self.assertIsInstance(env_config, EnvironmentConfig)
        self.assertIsInstance(ppo_config, PPOConfig)
        
        # 验证环境配置
        self.assertEqual(env_config.reward_type, RewardType.SHAPED)
        self.assertEqual(env_config.action_type, "continuous")
        
        # 验证PPO配置
        self.assertEqual(ppo_config.device, "cpu")
        self.assertGreater(ppo_config.hidden_dim, 0)
        self.assertGreater(ppo_config.learning_rate, 0)


class TestPPOIntegration(unittest.TestCase):
    """测试PPO与环境的集成"""
    
    def test_ppo_environment_compatibility(self):
        """测试PPO与环境的兼容性"""
        env_config = EnvironmentConfig(
            max_episode_steps=10,
            action_type="continuous"
        )
        
        ppo_config = PPOConfig(
            hidden_dim=16,
            num_layers=1,
            rollout_steps=20,
            device="cpu"
        )
        
        # 创建训练器（这会创建环境）
        trainer = PPOTrainer(env_config, ppo_config)
        
        # 验证维度匹配
        self.assertEqual(trainer.policy_net.action_mean.out_features, trainer.action_dim)
        self.assertEqual(trainer.value_net.network[-1].out_features, 1)
        
        # 测试一步交互
        obs = trainer.env.reset()
        self.assertEqual(len(obs), trainer.obs_dim)
        
        action = trainer.env.action_space.sample()
        obs, reward, done, info = trainer.env.step(action)
        
        self.assertIsInstance(reward, (int, float))
        self.assertIsInstance(done, bool)
        self.assertIsInstance(info, dict)


if __name__ == '__main__':
    # 配置测试
    import logging
    logging.basicConfig(level=logging.WARNING)  # 减少测试期间的日志输出
    
    print("🧪 开始PPO训练器测试")
    print("=" * 50)
    
    # 运行测试
    unittest.main(verbosity=2)