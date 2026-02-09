#!/usr/bin/env python3
"""
强化学习环境单元测试

测试轮腿机器人强化学习环境的核心功能。
"""

import unittest
import numpy as np
import tempfile
import os

# 添加项目路径
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/wheel_legged_control'))

from wheel_legged_control.algorithms.rl_environment import (
    EnvironmentConfig, RewardType, BaseRLEnvironment, WheelLeggedRobotEnvironment,
    create_wheel_legged_environment, register_environments, spaces
)


class TestEnvironmentConfig(unittest.TestCase):
    """环境配置测试"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = EnvironmentConfig()
        
        self.assertEqual(config.max_episode_steps, 1000)
        self.assertEqual(config.dt, 0.01)
        self.assertTrue(config.include_joint_positions)
        self.assertTrue(config.include_joint_velocities)
        self.assertFalse(config.include_joint_efforts)
        self.assertTrue(config.include_imu_data)
        self.assertTrue(config.include_base_pose)
        self.assertEqual(config.action_type, "continuous")
        self.assertEqual(config.reward_type, RewardType.DENSE)
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = EnvironmentConfig(
            max_episode_steps=500,
            dt=0.02,
            reward_type=RewardType.SPARSE,
            action_type="discrete",
            target_position=[1.0, 2.0, 0.5]
        )
        
        self.assertEqual(config.max_episode_steps, 500)
        self.assertEqual(config.dt, 0.02)
        self.assertEqual(config.reward_type, RewardType.SPARSE)
        self.assertEqual(config.action_type, "discrete")
        self.assertEqual(config.target_position, [1.0, 2.0, 0.5])


class TestSpaces(unittest.TestCase):
    """空间类测试"""
    
    def test_box_space(self):
        """测试Box空间"""
        low = np.array([-1.0, -2.0])
        high = np.array([1.0, 2.0])
        space = spaces.Box(low=low, high=high)
        
        self.assertTrue(np.array_equal(space.low, low))
        self.assertTrue(np.array_equal(space.high, high))
        self.assertEqual(space.shape, (2,))
        
        # 测试采样
        sample = space.sample()
        self.assertEqual(sample.shape, (2,))
        self.assertTrue(np.all(sample >= low))
        self.assertTrue(np.all(sample <= high))
    
    def test_discrete_space(self):
        """测试Discrete空间"""
        space = spaces.Discrete(5)
        
        self.assertEqual(space.n, 5)
        self.assertEqual(space.shape, ())
        
        # 测试采样
        sample = space.sample()
        self.assertIsInstance(sample, (int, np.integer))
        self.assertGreaterEqual(sample, 0)
        self.assertLess(sample, 5)


class TestWheelLeggedRobotEnvironment(unittest.TestCase):
    """轮腿机器人环境测试"""
    
    def setUp(self):
        """测试前准备"""
        self.config = EnvironmentConfig(
            max_episode_steps=100,
            dt=0.01,
            reward_type=RewardType.DENSE,
            randomize_initial_state=False  # 固定初始状态便于测试
        )
        
    def test_environment_creation(self):
        """测试环境创建"""
        env = create_wheel_legged_environment(self.config)
        
        self.assertIsInstance(env, WheelLeggedRobotEnvironment)
        self.assertEqual(env.config.max_episode_steps, 100)
        self.assertEqual(env.config.dt, 0.01)
        self.assertIsNotNone(env.action_space)
        self.assertIsNotNone(env.observation_space)
    
    def test_action_space_continuous(self):
        """测试连续动作空间"""
        config = EnvironmentConfig(action_type="continuous")
        env = create_wheel_legged_environment(config)
        
        self.assertIsInstance(env.action_space, spaces.Box)
        self.assertEqual(env.action_space.shape[0], env.num_joints)
        
        # 测试动作采样
        action = env.action_space.sample()
        self.assertEqual(action.shape[0], env.num_joints)
    
    def test_action_space_discrete(self):
        """测试离散动作空间"""
        config = EnvironmentConfig(action_type="discrete")
        env = create_wheel_legged_environment(config)
        
        self.assertIsInstance(env.action_space, spaces.Discrete)
        self.assertEqual(env.action_space.n, env.num_joints * 3)
        
        # 测试动作采样
        action = env.action_space.sample()
        self.assertIsInstance(action, (int, np.integer))
        self.assertGreaterEqual(action, 0)
        self.assertLess(action, env.action_space.n)
    
    def test_observation_space(self):
        """测试观测空间"""
        env = create_wheel_legged_environment(self.config)
        
        self.assertIsInstance(env.observation_space, spaces.Box)
        
        # 计算期望的观测维度
        expected_dim = 0
        if self.config.include_joint_positions:
            expected_dim += env.num_joints
        if self.config.include_joint_velocities:
            expected_dim += env.num_joints
        if self.config.include_joint_efforts:
            expected_dim += env.num_joints
        if self.config.include_base_pose:
            expected_dim += 7  # 位置(3) + 四元数(4)
        if self.config.include_imu_data:
            expected_dim += 9  # 线性加速度(3) + 角速度(3) + 方向(3)
        expected_dim += 3  # 目标位置
        
        self.assertEqual(env.observation_space.shape[0], expected_dim)
    
    def test_reset(self):
        """测试环境重置"""
        env = create_wheel_legged_environment(self.config)
        
        obs = env.reset()
        
        self.assertIsInstance(obs, np.ndarray)
        self.assertEqual(obs.shape, env.observation_space.shape)
        self.assertEqual(env.current_step, 0)
        self.assertEqual(env.episode_reward, 0.0)
        self.assertFalse(env.done)
    
    def test_step(self):
        """测试环境步进"""
        env = create_wheel_legged_environment(self.config)
        
        obs = env.reset()
        action = env.action_space.sample()
        
        next_obs, reward, done, info = env.step(action)
        
        # 检查返回值类型和形状
        self.assertIsInstance(next_obs, np.ndarray)
        self.assertEqual(next_obs.shape, env.observation_space.shape)
        self.assertIsInstance(reward, (int, float))
        self.assertIsInstance(done, bool)
        self.assertIsInstance(info, dict)
        
        # 检查环境状态更新
        self.assertEqual(env.current_step, 1)
        self.assertEqual(env.episode_reward, reward)
        
        # 检查信息字典
        self.assertIn('episode_reward', info)
        self.assertIn('current_step', info)
        self.assertIn('base_position', info)
        self.assertIn('target_position', info)
        self.assertIn('distance_to_target', info)
    
    def test_multiple_steps(self):
        """测试多步执行"""
        env = create_wheel_legged_environment(self.config)
        
        obs = env.reset()
        total_reward = 0
        
        for step in range(10):
            action = env.action_space.sample()
            obs, reward, done, info = env.step(action)
            total_reward += reward
            
            self.assertEqual(env.current_step, step + 1)
            self.assertAlmostEqual(env.episode_reward, total_reward, places=5)
            
            if done:
                break
    
    def test_reward_types(self):
        """测试不同奖励类型"""
        reward_types = [RewardType.SPARSE, RewardType.DENSE, RewardType.SHAPED]
        
        for reward_type in reward_types:
            config = EnvironmentConfig(
                reward_type=reward_type,
                max_episode_steps=10,
                randomize_initial_state=False
            )
            env = create_wheel_legged_environment(config)
            
            obs = env.reset()
            action = env.action_space.sample()
            obs, reward, done, info = env.step(action)
            
            self.assertIsInstance(reward, (int, float))
            # 奖励应该是有限的数值
            self.assertTrue(np.isfinite(reward))
    
    def test_episode_termination(self):
        """测试回合终止条件"""
        config = EnvironmentConfig(
            max_episode_steps=5,  # 很短的回合
            randomize_initial_state=False
        )
        env = create_wheel_legged_environment(config)
        
        obs = env.reset()
        done = False
        step_count = 0
        
        while not done and step_count < 10:  # 防止无限循环
            action = env.action_space.sample()
            obs, reward, done, info = env.step(action)
            step_count += 1
        
        # 应该在最大步数时终止
        self.assertTrue(done)
        self.assertLessEqual(step_count, config.max_episode_steps)
    
    def test_seed_reproducibility(self):
        """测试随机种子的可重现性"""
        config = EnvironmentConfig(
            randomize_initial_state=False,  # 使用固定初始状态进行测试
            max_episode_steps=5
        )
        
        # 创建两个相同种子的环境
        env1 = create_wheel_legged_environment(config)
        env2 = create_wheel_legged_environment(config)
        
        env1.seed(42)
        env2.seed(42)
        
        obs1 = env1.reset()
        obs2 = env2.reset()
        
        # 初始观测应该相同（因为使用固定初始状态）
        np.testing.assert_array_almost_equal(obs1, obs2)
        
        # 执行相同的动作序列
        for _ in range(3):
            # 使用固定动作而不是随机动作
            action = np.array([0.1, -0.1, 0.2, -0.2, 0.05, -0.05])
            obs1, reward1, done1, info1 = env1.step(action)
            obs2, reward2, done2, info2 = env2.step(action)
            
            # 结果应该相同（允许小的数值误差）
            np.testing.assert_array_almost_equal(obs1, obs2, decimal=4)  # 降低精度要求
            self.assertAlmostEqual(reward1, reward2, places=4)
            self.assertEqual(done1, done2)
    
    def test_render(self):
        """测试渲染功能"""
        env = create_wheel_legged_environment(self.config)
        
        obs = env.reset()
        
        # 测试不同渲染模式
        try:
            env.render(mode='human')  # 应该打印信息
            rgb_array = env.render(mode='rgb_array')  # 应该返回数组
            self.assertIsInstance(rgb_array, np.ndarray)
            self.assertEqual(len(rgb_array.shape), 3)  # 高度x宽度x通道
        except Exception as e:
            self.fail(f"渲染功能失败: {e}")
    
    def test_close(self):
        """测试环境关闭"""
        env = create_wheel_legged_environment(self.config)
        
        # 关闭应该不抛出异常
        try:
            env.close()
        except Exception as e:
            self.fail(f"环境关闭失败: {e}")
    
    def test_joint_limits(self):
        """测试关节限制"""
        env = create_wheel_legged_environment(self.config)
        
        obs = env.reset()
        
        # 应用极大的动作
        large_action = np.full(env.num_joints, 1000.0)
        obs, reward, done, info = env.step(large_action)
        
        # 关节位置应该被限制
        for joint_name in env.joint_names:
            position = env.joint_positions[joint_name]
            self.assertGreaterEqual(position, -np.pi)
            self.assertLessEqual(position, np.pi)
    
    def test_different_configurations(self):
        """测试不同配置组合"""
        configs = [
            EnvironmentConfig(include_joint_efforts=True, include_imu_data=False),
            EnvironmentConfig(include_base_pose=False, action_type="discrete"),
            EnvironmentConfig(include_joint_positions=False, include_joint_velocities=False),
        ]
        
        for config in configs:
            try:
                env = create_wheel_legged_environment(config)
                obs = env.reset()
                action = env.action_space.sample()
                obs, reward, done, info = env.step(action)
                
                # 基本检查
                self.assertIsInstance(obs, np.ndarray)
                self.assertIsInstance(reward, (int, float))
                self.assertIsInstance(done, bool)
                
            except Exception as e:
                self.fail(f"配置 {config} 测试失败: {e}")


class TestEnvironmentFactory(unittest.TestCase):
    """环境工厂函数测试"""
    
    def test_create_with_default_config(self):
        """测试使用默认配置创建环境"""
        env = create_wheel_legged_environment()
        
        self.assertIsInstance(env, WheelLeggedRobotEnvironment)
        self.assertIsNotNone(env.config)
    
    def test_create_with_custom_config(self):
        """测试使用自定义配置创建环境"""
        config = EnvironmentConfig(max_episode_steps=200)
        env = create_wheel_legged_environment(config)
        
        self.assertEqual(env.config.max_episode_steps, 200)
    
    def test_create_with_kwargs(self):
        """测试使用关键字参数创建环境"""
        env = create_wheel_legged_environment(
            max_episode_steps=300,
            reward_type=RewardType.SPARSE,
            action_type="discrete"
        )
        
        self.assertEqual(env.config.max_episode_steps, 300)
        self.assertEqual(env.config.reward_type, RewardType.SPARSE)
        self.assertEqual(env.config.action_type, "discrete")


class TestEnvironmentRegistration(unittest.TestCase):
    """环境注册测试"""
    
    def test_register_environments(self):
        """测试环境注册"""
        registry = register_environments()
        
        self.assertIsInstance(registry, dict)
        self.assertIn('WheelLeggedRobot-v0', registry)
        self.assertIn('WheelLeggedRobotSparse-v0', registry)
        self.assertIn('WheelLeggedRobotDense-v0', registry)
        
        # 检查注册信息
        for env_id, env_spec in registry.items():
            self.assertIn('entry_point', env_spec)
            self.assertIn('max_episode_steps', env_spec)
            self.assertIn('kwargs', env_spec)


if __name__ == '__main__':
    # 配置日志
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    print("🧪 运行强化学习环境单元测试")
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestEnvironmentConfig,
        TestSpaces,
        TestWheelLeggedRobotEnvironment,
        TestEnvironmentFactory,
        TestEnvironmentRegistration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 输出结果
    if result.wasSuccessful():
        print("\n✅ 所有测试通过！")
        print("🎉 强化学习环境测试完成")
        exit(0)
    else:
        print(f"\n❌ 测试失败: {len(result.failures)} 个失败, {len(result.errors)} 个错误")
        exit(1)