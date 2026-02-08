# PPO强化学习训练指南

## 概述

本指南介绍如何使用PPO (Proximal Policy Optimization) 算法训练轮腿机器人控制策略。PPO是一种先进的强化学习算法，特别适合连续控制任务。

## 系统要求

### 硬件要求
- **CPU**: 多核处理器（推荐4核以上）
- **内存**: 至少4GB RAM（推荐8GB以上）
- **存储**: 至少1GB可用空间用于模型和日志
- **GPU**: 可选，但本实现针对CPU优化，特别适合AMD APU

### 软件要求
- **Python**: 3.8或更高版本
- **PyTorch**: CPU版本（推荐）
- **NumPy**: 数值计算
- **Matplotlib**: 训练曲线可视化

## 安装依赖

### 安装PyTorch (CPU版本)
```bash
# 适用于AMD APU和其他CPU系统
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### 安装其他依赖
```bash
pip install numpy matplotlib
```

## 快速开始

### 1. 基本训练
```bash
# 运行默认配置的训练
python3 scripts/demo_ppo_training.py

# 短期训练测试
python3 scripts/demo_ppo_training.py --episodes 50

# 配置测试（不进行实际训练）
python3 scripts/demo_ppo_training.py --dry-run
```

### 2. 自定义训练参数
```bash
# 自定义网络结构和学习率
python3 scripts/demo_ppo_training.py \
    --episodes 200 \
    --hidden-dim 256 \
    --learning-rate 1e-4 \
    --threads 8

# 指定保存目录
python3 scripts/demo_ppo_training.py \
    --save-dir my_models \
    --episodes 100
```

## 配置说明

### 环境配置 (EnvironmentConfig)

```python
env_config = EnvironmentConfig(
    max_episode_steps=1000,     # 每回合最大步数
    dt=0.02,                    # 时间步长
    reward_type=RewardType.SHAPED,  # 奖励函数类型
    action_type="continuous",   # 动作空间类型
    randomize_initial_state=True,   # 随机初始状态
    target_position=[2.0, 0.0, 0.1],  # 目标位置
    position_tolerance=0.2,     # 位置容差
    velocity_penalty_weight=0.01,      # 速度惩罚权重
    effort_penalty_weight=0.001,       # 力矩惩罚权重
    stability_reward_weight=1.0        # 稳定性奖励权重
)
```

### PPO配置 (PPOConfig)

```python
ppo_config = PPOConfig(
    # 网络架构
    hidden_dim=128,             # 隐藏层维度
    num_layers=2,               # 网络层数
    activation="tanh",          # 激活函数
    
    # PPO超参数
    learning_rate=3e-4,         # 学习率
    gamma=0.99,                 # 折扣因子
    gae_lambda=0.95,            # GAE参数
    clip_epsilon=0.2,           # PPO裁剪参数
    entropy_coef=0.01,          # 熵正则化系数
    
    # 训练参数
    batch_size=32,              # 批次大小
    mini_batch_size=16,         # 小批次大小
    ppo_epochs=10,              # PPO更新轮数
    max_episodes=500,           # 最大训练回合数
    rollout_steps=1024,         # 经验收集步数
    
    # 设备设置
    device="cpu",               # 使用CPU
    num_threads=4,              # CPU线程数
)
```

## 奖励函数类型

### 1. 稀疏奖励 (SPARSE)
- 只在到达目标时给予奖励
- 训练难度较高，但策略更加精确
- 适合明确的目标导向任务

### 2. 密集奖励 (DENSE)
- 基于距离的连续奖励
- 训练相对容易，收敛较快
- 适合导航和跟踪任务

### 3. 形状奖励 (SHAPED)
- 复杂的多目标奖励函数
- 包含距离、速度、力矩、稳定性等多个因素
- 能够学习更加平滑和高效的控制策略

## 训练监控

### 训练日志
训练过程中会输出详细的日志信息：
```
Episode   50 | Avg Reward:   12.34 | Avg Length:  234.5 | Policy Loss:   0.0123 | Value Loss:   0.0456 | Entropy:   0.7890 | Time:   45.6s
```

### 训练曲线
训练完成后会自动生成训练曲线图：
- 平均奖励变化
- 策略损失变化
- 价值损失变化
- 策略熵变化

### 模型文件
训练过程中会保存以下文件：
- `best_model.pth`: 最佳性能模型
- `final_model.pth`: 最终训练模型
- `model_episode_X.pth`: 定期保存的检查点
- `training_stats.json`: 训练统计数据
- `training_curves.png`: 训练曲线图

## 性能优化

### CPU优化建议
1. **线程数设置**: 根据CPU核心数调整 `num_threads`
2. **批次大小**: 较小的批次大小减少内存使用
3. **网络结构**: 较小的网络结构提高训练速度
4. **收集步数**: 适中的 `rollout_steps` 平衡性能和内存

### AMD APU优化
```python
# 针对AMD APU的推荐配置
ppo_config = PPOConfig(
    hidden_dim=128,         # 适中的网络大小
    num_layers=2,           # 较少的层数
    batch_size=32,          # 适中的批次大小
    rollout_steps=512,      # 较少的收集步数
    device="cpu",           # 使用CPU
    num_threads=4,          # 根据APU核心数调整
)
```

## 故障排除

### 常见问题

#### 1. PyTorch安装问题
```bash
# 错误: ModuleNotFoundError: No module named 'torch'
# 解决: 安装PyTorch CPU版本
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

#### 2. 内存不足
```bash
# 错误: RuntimeError: out of memory
# 解决: 减少批次大小和网络大小
ppo_config.batch_size = 16
ppo_config.hidden_dim = 64
```

#### 3. 训练不收敛
- 检查奖励函数设计
- 调整学习率（通常减小）
- 增加训练回合数
- 检查环境设置

#### 4. 训练速度慢
- 减少网络大小
- 减少收集步数
- 增加CPU线程数
- 使用较小的批次大小

### 调试技巧

#### 1. 启用详细日志
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### 2. 监控训练指标
- 策略损失应该逐渐减小
- 价值损失应该逐渐减小
- 熵应该逐渐减小但不为零
- 平均奖励应该逐渐增加

#### 3. 可视化训练过程
```python
# 实时监控训练
trainer.plot_training_curves()
```

## 高级用法

### 自定义奖励函数
```python
class CustomEnvironment(WheelLeggedRobotEnvironment):
    def _compute_reward(self, action):
        # 自定义奖励逻辑
        reward = 0.0
        
        # 距离奖励
        distance = np.linalg.norm(self.base_position - self.target_position)
        reward += np.exp(-distance)
        
        # 自定义惩罚
        if self.base_position[2] < 0.1:
            reward -= 10.0
        
        return reward
```

### 多环境并行训练
```python
# 配置多个并行环境
ppo_config.num_envs = 4  # 4个并行环境
```

### 课程学习
```python
# 逐渐增加任务难度
def curriculum_learning(episode):
    if episode < 100:
        return easy_target
    elif episode < 300:
        return medium_target
    else:
        return hard_target
```

## API参考

### PPOTrainer类
```python
class PPOTrainer:
    def __init__(self, env_config, ppo_config)
    def train(self, save_dir="models")
    def evaluate(self, num_episodes=5)
    def save_model(self, filepath)
    def load_model(self, filepath)
    def plot_training_curves(self, save_path=None)
```

### 主要方法
- `collect_rollouts()`: 收集经验数据
- `compute_gae()`: 计算广义优势估计
- `update_policy()`: 更新策略和价值网络

## 示例代码

### 完整训练示例
```python
from wheel_legged_control.algorithms.ppo_trainer import PPOTrainer, create_default_configs

# 创建配置
env_config, ppo_config = create_default_configs()

# 自定义配置
ppo_config.max_episodes = 200
ppo_config.device = "cpu"
ppo_config.num_threads = 4

# 创建训练器
trainer = PPOTrainer(env_config, ppo_config)

# 开始训练
stats = trainer.train(save_dir="my_models")

# 绘制结果
trainer.plot_training_curves("training_results.png")
```

### 模型评估示例
```python
# 加载训练好的模型
trainer.load_model("my_models/best_model.pth")

# 评估性能
avg_reward, avg_length = trainer.evaluate(num_episodes=10)
print(f"平均奖励: {avg_reward:.2f}")
print(f"平均长度: {avg_length:.1f}")
```

## 最佳实践

1. **从小规模开始**: 先用少量回合测试配置
2. **监控训练指标**: 定期检查损失和奖励变化
3. **保存检查点**: 定期保存模型以防训练中断
4. **调整超参数**: 根据训练效果调整学习率等参数
5. **使用课程学习**: 逐渐增加任务难度
6. **验证环境**: 确保环境设置合理且可解

## 参考资料

- [PPO论文](https://arxiv.org/abs/1707.06347)
- [PyTorch文档](https://pytorch.org/docs/)
- [强化学习入门](https://spinningup.openai.com/)
- [轮腿机器人控制](docs/ros2_gui_integration_guide.md)

---

**更新时间**: 2026年2月8日  
**版本**: v1.0.0  
**作者**: 轮腿机器人孪生控制系统开发团队