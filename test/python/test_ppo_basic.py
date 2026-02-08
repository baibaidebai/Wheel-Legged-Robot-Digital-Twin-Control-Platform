#!/usr/bin/env python3
"""
PPO训练器基础测试（不依赖PyTorch）

测试PPO模块的基本结构和导入。
"""

import unittest
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/wheel_legged_control'))


class TestPPOBasicStructure(unittest.TestCase):
    """测试PPO基础结构"""
    
    def test_ppo_module_import(self):
        """测试PPO模块导入"""
        try:
            from wheel_legged_control.algorithms import ppo_trainer
            self.assertTrue(hasattr(ppo_trainer, 'PPOConfig'))
            self.assertTrue(hasattr(ppo_trainer, 'create_default_configs'))
            print("✅ PPO模块导入成功")
        except ImportError as e:
            if 'torch' in str(e):
                print("⚠️  PyTorch未安装，跳过PyTorch相关测试")
                self.skipTest("PyTorch not available")
            else:
                raise
    
    def test_rl_environment_import(self):
        """测试强化学习环境导入"""
        try:
            from wheel_legged_control.algorithms import rl_environment
            self.assertTrue(hasattr(rl_environment, 'EnvironmentConfig'))
            self.assertTrue(hasattr(rl_environment, 'RewardType'))
            self.assertTrue(hasattr(rl_environment, 'create_wheel_legged_environment'))
            print("✅ 强化学习环境模块导入成功")
        except ImportError as e:
            self.fail(f"强化学习环境导入失败: {e}")
    
    def test_environment_creation_without_torch(self):
        """测试不依赖PyTorch的环境创建"""
        try:
            from wheel_legged_control.algorithms.rl_environment import (
                EnvironmentConfig, RewardType, create_wheel_legged_environment
            )
            
            # 创建环境配置
            config = EnvironmentConfig(
                max_episode_steps=10,
                reward_type=RewardType.DENSE,
                action_type="continuous"
            )
            
            # 创建环境
            env = create_wheel_legged_environment(config)
            
            # 基本验证
            self.assertIsNotNone(env)
            self.assertTrue(hasattr(env, 'reset'))
            self.assertTrue(hasattr(env, 'step'))
            self.assertTrue(hasattr(env, 'action_space'))
            self.assertTrue(hasattr(env, 'observation_space'))
            
            print("✅ 强化学习环境创建成功")
            
            # 测试环境重置
            obs = env.reset()
            self.assertIsNotNone(obs)
            print(f"✅ 环境重置成功，观测维度: {obs.shape}")
            
            # 测试一步交互
            action = env.action_space.sample()
            obs, reward, done, info = env.step(action)
            
            self.assertIsInstance(reward, (int, float))
            self.assertIsInstance(done, bool)
            self.assertIsInstance(info, dict)
            
            print(f"✅ 环境交互成功，奖励: {reward:.3f}")
            
        except Exception as e:
            self.fail(f"环境创建测试失败: {e}")
    
    def test_config_classes(self):
        """测试配置类"""
        try:
            from wheel_legged_control.algorithms.rl_environment import EnvironmentConfig, RewardType
            
            # 测试环境配置
            env_config = EnvironmentConfig()
            self.assertEqual(env_config.max_episode_steps, 1000)
            self.assertEqual(env_config.dt, 0.01)
            
            # 测试奖励类型枚举
            self.assertEqual(RewardType.SPARSE.value, "sparse")
            self.assertEqual(RewardType.DENSE.value, "dense")
            self.assertEqual(RewardType.SHAPED.value, "shaped")
            
            print("✅ 配置类测试通过")
            
        except Exception as e:
            self.fail(f"配置类测试失败: {e}")


class TestPPOWithoutTorch(unittest.TestCase):
    """测试不依赖PyTorch的PPO功能"""
    
    def test_ppo_config_creation(self):
        """测试PPO配置创建（不需要PyTorch）"""
        try:
            # 尝试导入配置类
            import importlib.util
            
            # 检查PPO模块文件是否存在
            ppo_file = os.path.join(
                os.path.dirname(__file__), 
                '../../src/wheel_legged_control/wheel_legged_control/algorithms/ppo_trainer.py'
            )
            
            self.assertTrue(os.path.exists(ppo_file), "PPO训练器文件不存在")
            
            # 读取文件内容检查结构
            with open(ppo_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # 检查关键类和函数是否存在
                self.assertIn('class PPOConfig', content)
                self.assertIn('class PolicyNetwork', content)
                self.assertIn('class ValueNetwork', content)
                self.assertIn('class PPOTrainer', content)
                self.assertIn('def create_default_configs', content)
                
            print("✅ PPO训练器文件结构验证通过")
            
        except Exception as e:
            self.fail(f"PPO配置测试失败: {e}")


if __name__ == '__main__':
    print("🧪 开始PPO基础测试（无PyTorch依赖）")
    print("=" * 50)
    
    # 运行测试
    unittest.main(verbosity=2)