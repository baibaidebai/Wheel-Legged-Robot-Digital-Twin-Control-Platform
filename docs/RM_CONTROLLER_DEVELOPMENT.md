# RM轮腿机器人控制器开发文档

## 🎯 项目概述

本文档介绍了为RM轮腿机器人开发的完整控制器解决方案，包括PID控制器、LQR控制器以及混合控制器的实现，并展示了在MuJoCo仿真环境中的应用。

## 🏗️ 系统架构

### 控制器层次结构

```
RMRobotController (基类)
├── PIDRMController (PID控制器)
├── LQRRMController (LQR控制器)
└── HybridRMController (混合控制器)
    ├── PIDRMController (子控制器)
    └── LQRRMController (子控制器)
```

### 核心组件

1. **基础控制器类** (`BaseRMController`)
   - 提供统一的接口和状态管理
   - 处理关节状态更新和查询

2. **PID控制器** (`PIDRMController`)
   - 经典比例-积分-微分控制
   - 支持关节级别的参数调整
   - 包含抗积分饱和和输出限幅

3. **LQR控制器** (`LQRRMController`)
   - 基于线性二次调节器的最优控制
   - 状态空间建模和Riccati方程求解
   - 自动稳定性分析

4. **混合控制器** (`HybridRMController`)
   - 结合PID和LQR的优势
   - 可调节的混合权重
   - 支持动态切换控制模式

## 🚀 快速开始

### 1. 安装依赖

```bash
# 确保已安装MuJoCo
pip install mujoco

# 安装其他依赖
pip install numpy matplotlib
```

### 2. 基本使用示例

```python
from wheel_legged_control.controllers.rm_robot_controller import (
    HybridRMController, PIDGains
)
from wheel_legged_control.algorithms.lqr_controller import LQRConfig

# 创建关节列表
joint_names = [
    'lf0_Joint', 'lf1_Joint', 'l_wheel_Joint',
    'rf0_Joint', 'rf1_Joint', 'r_wheel_Joint'
]

# 配置PID参数
pid_gains = {
    'lf0_Joint': PIDGains(kp=15.0, ki=0.2, kd=0.8),
    'lf1_Joint': PIDGains(kp=12.0, ki=0.15, kd=0.6),
    # ... 其他关节参数
}

# 配置LQR参数
lqr_config = LQRConfig(
    state_dim=12,
    control_dim=6,
    Q_weights=[10.0] * 6 + [1.0] * 6,
    R_weights=[0.1] * 6,
    dt=0.01
)

# 创建混合控制器
controller = HybridRMController(joint_names, pid_gains, lqr_config)

# 设置混合权重 (0=纯PID, 1=纯LQR)
controller.set_hybrid_weights({'lf0_Joint': 0.7, 'lf1_Joint': 0.3})

# 更新关节状态
controller.update_joint_state('lf0_Joint', current_position=0.1, current_velocity=0.0)

# 计算控制输出
target_positions = {'lf0_Joint': 0.5, 'lf1_Joint': -0.3}
control_outputs = controller.compute_control(target_positions, dt=0.01)

print(f"控制输出: {control_outputs}")
```

### 3. MuJoCo仿真使用

```python
from scripts.demo_rm_mujoco_control import RMRobotSimulator

# 创建仿真器
simulator = RMRobotSimulator()

# 设置控制模式
simulator.set_control_mode('hybrid')

# 设置运动模式
simulator.set_motion('walk_forward')

# 运行仿真
simulator.run_simulation(duration=30.0, show_viewer=True)
```

## 🎮 控制模式详解

### PID控制模式
- **适用场景**: 简单的位置控制任务
- **优点**: 实现简单，调试直观
- **缺点**: 对复杂动力学系统可能不够精确

### LQR控制模式
- **适用场景**: 需要最优控制性能的任务
- **优点**: 理论上最优，考虑系统全局性能
- **缺点**: 需要准确的系统模型，计算复杂度较高

### 混合控制模式
- **适用场景**: 复杂任务，需要平衡精度和稳定性
- **优点**: 结合两者优势，可动态调整权重
- **缺点**: 参数调节相对复杂

## 📊 性能测试

### 运行性能比较测试

```bash
python scripts/test_controller_performance.py
```

测试包括：
1. **位置跟踪测试** - 评估跟踪精度
2. **扰动抑制测试** - 评估鲁棒性
3. **轨迹跟随测试** - 评估动态响应
4. **能耗效率测试** - 评估能量消耗

### 测试结果示例

控制器性能指标：
- 平均跟踪误差
- 最大跟踪误差
- 平均控制努力
- 总能耗
- 扰动恢复时间

## 🔧 参数调优指南

### PID参数调节

```python
# 增加Kp：提高响应速度，但可能导致振荡
# 增加Ki：减少稳态误差，但可能引起积分饱和
# 增加Kd：提高稳定性，但对噪声敏感

pid_gains = {
    'lf0_Joint': PIDGains(
        kp=15.0,    # 根据系统响应调整
        ki=0.2,     # 通常较小
        kd=0.8      # 有助于稳定
    )
}
```

### LQR权重矩阵设计

```python
# Q矩阵：状态惩罚权重
# R矩阵：控制输入惩罚权重

lqr_config = LQRConfig(
    Q_weights=[20.0] * 6 + [2.0] * 6,  # 高位置权重，低速度权重
    R_weights=[0.05] * 6,              # 低控制权重（节能）
    dt=0.01
)
```

### 混合控制器权重设置

```python
# 动态任务：较高LQR权重（0.7-0.8）
# 稳定任务：较高PID权重（0.2-0.3）
# 平衡任务：中等权重（0.5）

controller.set_hybrid_weights({
    'lf0_Joint': 0.7,  # 动态关节
    'l_wheel_Joint': 0.3  # 稳定关节
})
```

## 🎭 运动控制示例

### 前进步行动作

```python
def walk_forward_pattern(time):
    cycle_time = 2.0
    normalized_time = (time % cycle_time) / cycle_time
    left_phase = normalized_time * 2 * np.pi
    right_phase = left_phase + np.pi
    
    return {
        'lf0_Joint': 0.3 * np.sin(left_phase),
        'lf1_Joint': -0.5 * np.abs(np.sin(left_phase)),
        'l_wheel_Joint': 0.1 * np.sin(time * 2),
        'rf0_Joint': 0.3 * np.sin(right_phase),
        'rf1_Joint': -0.5 * np.abs(np.sin(right_phase)),
        'r_wheel_Joint': -0.1 * np.sin(time * 2)
    }
```

### 跳跃动作

```python
def jump_pattern(time):
    jump_duration = 3.0
    phase = (time % jump_duration) / jump_duration
    
    if phase < 0.3:  # 蹲下
        leg_bend = -0.6 * (phase / 0.3)
    elif phase < 0.6:  # 起跳
        progress = (phase - 0.3) / 0.3
        leg_bend = -0.6 + 1.2 * progress
    else:  # 着陆
        progress = (phase - 0.6) / 0.4
        leg_bend = 0.6 * (1 - progress)
    
    return {joint: leg_bend for joint in joint_names}
```

## 📈 实时监控

### 状态查询

```python
# 获取当前关节位置
positions = controller.get_joint_positions()
print(f"当前位置: {positions}")

# 获取当前关节速度
velocities = controller.get_joint_velocities()
print(f"当前速度: {velocities}")
```

### 性能统计

```python
# 控制器内部统计
performance_data = {
    'control_updates': controller.performance_stats['control_updates'],
    'average_computation_time': controller.performance_stats['average_step_time']
}
```

## 🛠️ 故障排除

### 常见问题

1. **控制器输出过大**
   ```python
   # 检查PID参数是否过大
   # 减小Kp和Ki值
   # 检查输出限幅设置
   ```

2. **系统不稳定振荡**
   ```python
   # 增加Kd值提供阻尼
   # 检查系统模型是否准确
   # 考虑使用更保守的LQR权重
   ```

3. **跟踪精度不足**
   ```python
   # 增加PID的Kp值
   # 调整LQR的Q权重矩阵
   # 检查传感器反馈延迟
   ```

### 调试技巧

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 记录控制历史
control_history = []
state_history = []

# 在控制循环中记录数据
control_history.append(control_outputs.copy())
state_history.append(current_states.copy())
```

## 📚 API参考

### 主要类和方法

#### BaseRMController
```python
class BaseRMController:
    def compute_control(self, target_positions: Dict[str, float], dt: float) -> Dict[str, float]
    def update_joint_state(self, joint_name: str, position: float, velocity: float = 0.0, effort: float = 0.0)
    def get_joint_positions(self) -> Dict[str, float]
    def reset(self)
```

#### PIDRMController
```python
class PIDRMController(BaseRMController):
    def set_pid_gains(self, joint_name: str, gains: PIDGains)
```

#### LQRRMController
```python
class LQRRMController(BaseRMController):
    def set_reference_trajectory(self, target_positions: Dict[str, float])
```

#### HybridRMController
```python
class HybridRMController(BaseRMController):
    def set_control_mode(self, mode: str)  # 'pid', 'lqr', 'hybrid'
    def set_hybrid_weights(self, weights: Dict[str, float])
```

## 🎯 最佳实践

### 控制器选择建议

1. **简单任务** → 使用PID控制
2. **高精度要求** → 使用LQR控制
3. **复杂动态环境** → 使用混合控制

### 参数调节流程

1. 先调节PID参数获得基本稳定性
2. 根据需要调整LQR权重矩阵
3. 对于混合控制器，从小权重开始逐步调整
4. 在仿真环境中充分测试后再部署

### 性能优化

1. 合理设置控制频率（推荐100Hz）
2. 使用适当的状态预测
3. 实施有效的状态估计滤波
4. 考虑计算资源限制

## 📞 支持与贡献

如有问题或建议，请：
1. 查看日志输出定位问题
2. 运行测试脚本验证功能
3. 参考性能比较结果优化参数
4. 提交issue或pull request

---
*文档版本: 1.0*
*最后更新: 2026年2月*