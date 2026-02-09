#!/usr/bin/env python3
"""
PPO强化学习训练演示脚本

演示如何使用PPO算法训练轮腿机器人控制策略。

注意：此脚本需要安装PyTorch。在AMD APU系统上，建议使用CPU版本：
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
"""

import os
import sys
import logging
import argparse
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src/wheel_legged_control'))

def check_pytorch():
    """检查PyTorch是否可用"""
    try:
        import torch
        print(f"✅ PyTorch版本: {torch.__version__}")
        print(f"🖥️  设备: {'CUDA' if torch.cuda.is_available() else 'CPU'}")
        if torch.cuda.is_available():
            print(f"🎮 GPU数量: {torch.cuda.device_count()}")
        else:
            print("💻 使用CPU训练（适合AMD APU）")
        return True
    except ImportError:
        print("❌ PyTorch未安装")
        print("请安装PyTorch CPU版本：")
        print("pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='PPO强化学习训练演示')
    parser.add_argument('--episodes', type=int, default=100, help='训练回合数')
    parser.add_argument('--save-dir', type=str, default='ppo_models', help='模型保存目录')
    parser.add_argument('--log-level', type=str, default='INFO', help='日志级别')
    parser.add_argument('--hidden-dim', type=int, default=128, help='隐藏层维度')
    parser.add_argument('--learning-rate', type=float, default=3e-4, help='学习率')
    parser.add_argument('--threads', type=int, default=4, help='CPU线程数')
    parser.add_argument('--dry-run', action='store_true', help='仅测试配置，不进行训练')
    
    args = parser.parse_args()
    
    # 配置日志
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 PPO强化学习训练演示")
    print("=" * 60)
    print(f"📅 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 训练回合数: {args.episodes}")
    print(f"💾 保存目录: {args.save_dir}")
    print(f"🧠 隐藏层维度: {args.hidden_dim}")
    print(f"📈 学习率: {args.learning_rate}")
    print(f"🧵 CPU线程数: {args.threads}")
    
    # 检查PyTorch
    if not check_pytorch():
        return 1
    
    try:
        # 导入PPO相关模块
        from wheel_legged_control.algorithms.ppo_trainer import (
            PPOTrainer, PPOConfig, create_default_configs
        )
        from wheel_legged_control.algorithms.rl_environment import (
            EnvironmentConfig, RewardType
        )
        
        print("\n📦 模块导入成功")
        
        # 创建配置
        env_config, ppo_config = create_default_configs()
        
        # 根据命令行参数调整配置
        ppo_config.max_episodes = args.episodes
        ppo_config.hidden_dim = args.hidden_dim
        ppo_config.learning_rate = args.learning_rate
        ppo_config.num_threads = args.threads
        ppo_config.device = "cpu"  # 强制使用CPU，适合AMD APU
        
        # 针对演示调整配置（更快的训练）
        if args.episodes <= 50:
            ppo_config.rollout_steps = 512
            ppo_config.batch_size = 32
            ppo_config.mini_batch_size = 16
            ppo_config.eval_frequency = max(1, args.episodes // 10)
            ppo_config.save_frequency = max(1, args.episodes // 5)
            ppo_config.log_frequency = max(1, args.episodes // 20)
        
        print(f"\n⚙️  配置信息:")
        print(f"   环境最大步数: {env_config.max_episode_steps}")
        print(f"   奖励类型: {env_config.reward_type.value}")
        print(f"   网络结构: {ppo_config.num_layers}层 x {ppo_config.hidden_dim}神经元")
        print(f"   批次大小: {ppo_config.batch_size}")
        print(f"   收集步数: {ppo_config.rollout_steps}")
        
        if args.dry_run:
            print("\n🧪 配置测试模式 - 不进行实际训练")
            
            # 创建训练器测试初始化
            trainer = PPOTrainer(env_config, ppo_config)
            print("✅ 训练器初始化成功")
            
            # 测试环境交互
            obs = trainer.env.reset()
            print(f"✅ 环境重置成功，观测维度: {obs.shape}")
            
            action = trainer.env.action_space.sample()
            obs, reward, done, info = trainer.env.step(action)
            print(f"✅ 环境交互成功，奖励: {reward:.3f}")
            
            print("🎉 配置测试完成！")
            return 0
        
        # 创建保存目录
        os.makedirs(args.save_dir, exist_ok=True)
        
        # 创建训练器
        print(f"\n🏗️  创建PPO训练器...")
        trainer = PPOTrainer(env_config, ppo_config)
        
        # 开始训练
        print(f"\n🎓 开始训练...")
        print(f"   目标: 学习轮腿机器人导航到目标位置")
        print(f"   策略: PPO (Proximal Policy Optimization)")
        print(f"   硬件: AMD APU CPU训练")
        
        stats = trainer.train(save_dir=args.save_dir)
        
        # 生成训练报告
        print(f"\n📊 训练完成统计:")
        print(f"   总回合数: {stats['episode']}")
        print(f"   总步数: {stats['total_steps']}")
        
        if stats['rewards']:
            final_reward = stats['rewards'][-1]
            best_reward = max(stats['rewards'])
            print(f"   最终平均奖励: {final_reward:.2f}")
            print(f"   最佳平均奖励: {best_reward:.2f}")
        
        # 绘制训练曲线
        try:
            curve_path = os.path.join(args.save_dir, "training_curves.png")
            trainer.plot_training_curves(save_path=curve_path)
            print(f"📈 训练曲线已保存: {curve_path}")
        except Exception as e:
            print(f"⚠️  训练曲线生成失败: {e}")
        
        # 保存配置
        import json
        config_path = os.path.join(args.save_dir, "config.json")
        with open(config_path, 'w') as f:
            config_data = {
                'env_config': env_config.__dict__,
                'ppo_config': ppo_config.__dict__,
                'args': vars(args)
            }
            json.dump(config_data, f, indent=2, default=str)
        print(f"⚙️  配置已保存: {config_path}")
        
        print(f"\n🎉 训练完成！")
        print(f"📁 所有文件保存在: {args.save_dir}/")
        print(f"🤖 可以使用训练好的模型进行机器人控制")
        
        return 0
        
    except ImportError as e:
        if 'torch' in str(e):
            print(f"\n❌ PyTorch导入失败: {e}")
            print("请安装PyTorch CPU版本以继续训练")
        else:
            print(f"\n❌ 模块导入失败: {e}")
        return 1
    
    except KeyboardInterrupt:
        print(f"\n⏹️  训练被用户中断")
        return 0
    
    except Exception as e:
        print(f"\n❌ 训练过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)