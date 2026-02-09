# API参考文档

完整的Python API参考文档。

## 📖 目录

- [仿真模块 (simulation)](#仿真模块)
- [控制器模块 (controllers)](#控制器模块)
- [算法模块 (algorithms)](#算法模块)
- [数据模块 (data)](#数据模块)
- [传感器模块 (sensors)](#传感器模块)
- [核心模块 (core)](#核心模块)
- [工具模块 (utils)](#工具模块)

---

## 仿真模块

### wheel_legged_control.simulation.SimulationManager

统一的仿真管理接口。

**初始化**:
```python
SimulationManager(backend="mujoco", config=None)
```

**主要方法**:
- `load_robot(model_path)` - 加载机器人模型
- `start()` - 启动仿真
- `stop()` - 停止仿真
- `step()` - 执行一个仿真步骤
- `reset()` - 重置仿真状态
- `get_state()` - 获取当前状态
- `set_control(control)` - 设置控制输入
- `set_backend(backend)` - 切换仿真后端

**示例**:
```python
from wheel_legged_control.simulation import SimulationManager

sim = SimulationManager(backend="mujoco")
sim.load_robot("path/to/robot.urdf")
sim.start()

for i in range(1000):
    state = sim.get_state()
    control = compute_control(state)
    sim.set_control(control)
    sim.step()

sim.stop()
```

### wheel_legged_control.simulation.ParallelMuJoCoBackend

并行MuJoCo仿真后端，用于强化学习训练。

**初始化**:
```python
ParallelMuJoCoBackend(model_path, num_envs=4, use_multiprocessing=False)
```

**主要方法**:
- `reset_all()` - 重置所有环境
- `step_all(actions)` - 批量执行动作
- `get_states()` - 获取所有环境状态
- `close()` - 关闭所有环境

**示例**:
```python
from wheel_legged_control.simulation import ParallelMuJoCoBackend
import numpy as np

parallel_sim = ParallelMuJoCoBackend("robot.xml", num_envs=8)
parallel_sim.reset_all()

actions = np.random.randn(8, 6)
states, rewards, dones, infos = parallel_sim.step_all(actions)
```

---

## 控制器模块

### wheel_legged_control.controllers.JointController

关节空间控制器，支持PID控制和轨迹跟踪。

**初始化**:
```python
JointController(joint_names=None, control_frequency=100)
```

**主要方法**:
- `set_target_positions(positions)` - 设置目标位置
- `set_pid_gains(joint_name, kp, ki, kd)` - 设置PID参数
- `compute_control(current_state)` - 计算控制输出
- `reset()` - 重置控制器状态

**示例**:
```python
from wheel_legged_control.controllers import JointController

controller = JointController()
controller.set_pid_gains('joint1', kp=10.0, ki=0.1, kd=1.0)
controller.set_target_positions({'joint1': 0.5, 'joint2': -0.3})

control = controller.compute_control(current_state)
```

---

## 算法模块

### wheel_legged_control.algorithms.LQRController

线性二次调节器控制器。

**初始化**:
```python
LQRController(state_dim, control_dim)
```

**主要方法**:
- `set_system_matrices(A, B)` - 设置系统矩阵
- `set_cost_matrices(Q, R)` - 设置代价矩阵
- `compute_gains()` - 计算控制增益
- `compute_control(state, target_state)` - 计算控制输入

**示例**:
```python
from wheel_legged_control.algorithms import LQRController
import numpy as np

lqr = LQRController(state_dim=12, control_dim=6)
lqr.set_system_matrices(A, B)
lqr.set_cost_matrices(Q, R)
lqr.compute_gains()

control = lqr.compute_control(current_state, target_state)
```

### wheel_legged_control.algorithms.PPOTrainer

PPO强化学习训练器。

**初始化**:
```python
PPOTrainer(env, policy_network, value_network, learning_rate=3e-4)
```

**主要方法**:
- `train(total_timesteps, save_interval)` - 训练模型
- `evaluate(num_episodes)` - 评估模型
- `save(path)` - 保存模型
- `load(path)` - 加载模型

---

## 数据模块

### wheel_legged_control.data.DataRecorder

数据记录器，支持CSV和ROS bag格式。

**初始化**:
```python
DataRecorder(output_dir, experiment_name, format="csv")
```

**主要方法**:
- `start()` - 开始记录
- `stop()` - 停止记录
- `record_state(state)` - 记录状态
- `record_control(control)` - 记录控制
- `save()` - 保存数据

**示例**:
```python
from wheel_legged_control.data import DataRecorder

recorder = DataRecorder("data/experiments", "test_run")
recorder.start()

for i in range(1000):
    recorder.record_state(state)
    recorder.record_control(control)

recorder.stop()
recorder.save()
```

### wheel_legged_control.data.DataPlayer

数据回放器。

**主要方法**:
- `load(data_path)` - 加载数据
- `play(speed)` - 播放数据
- `pause()` - 暂停播放
- `resume()` - 继续播放
- `seek(time)` - 跳转到指定时间

---

## 传感器模块

### wheel_legged_control.sensors.IMUSimulator

IMU传感器仿真器。

**初始化**:
```python
IMUSimulator(noise_level=0.01, bias_level=0.001)
```

**主要方法**:
- `get_data(robot_state)` - 获取IMU数据
- `set_noise_level(level)` - 设置噪声水平
- `calibrate()` - 校准传感器

---

## 核心模块

### wheel_legged_control.core.DigitalTwinMapperWrapper

数字孪生映射器Python包装器。

**主要方法**:
- `load_urdf(urdf_path)` - 加载URDF模型
- `forward_kinematics(joint_positions)` - 正向运动学
- `inverse_kinematics(target_pose)` - 逆向运动学
- `identify_constraints()` - 识别约束

### wheel_legged_control.core.ExceptionHandler

系统异常处理器。

**主要方法**:
- `handle_exception(exception, context)` - 处理异常
- `register_recovery_strategy(exception_type, strategy)` - 注册恢复策略
- `attempt_recovery()` - 尝试恢复
- `get_system_state()` - 获取系统状态

### wheel_legged_control.core.SystemDiagnostics

系统诊断工具。

**主要方法**:
- `run_health_check()` - 运行健康检查
- `check_cpu_usage()` - 检查CPU使用率
- `check_memory_usage()` - 检查内存使用
- `generate_report()` - 生成诊断报告

---

## 工具模块

### wheel_legged_control.utils.PerformanceMonitor

性能监控器。

**主要方法**:
- `measure(func)` - 装饰器，测量函数性能
- `record(name, execution_time)` - 记录性能数据
- `get_metric(name)` - 获取性能指标
- `generate_report()` - 生成性能报告
- `get_slow_functions(threshold)` - 获取慢函数列表

**示例**:
```python
from wheel_legged_control.utils import PerformanceMonitor

monitor = PerformanceMonitor()

@monitor.measure
def my_function():
    # 函数逻辑
    pass

# 或使用上下文管理器
from wheel_legged_control.utils import PerformanceContext

with PerformanceContext('operation_name', monitor):
    # 操作逻辑
    pass

print(monitor.generate_report())
```

---

## 完整示例

### 基本仿真循环

```python
from wheel_legged_control.simulation import SimulationManager
from wheel_legged_control.controllers import JointController
from wheel_legged_control.data import DataRecorder

# 初始化
sim = SimulationManager(backend="mujoco")
sim.load_robot("path/to/robot.urdf")

controller = JointController()
controller.set_target_positions({'joint1': 0.5})

recorder = DataRecorder("data", "experiment1")

# 运行仿真
sim.start()
recorder.start()

for i in range(1000):
    state = sim.get_state()
    control = controller.compute_control(state)
    sim.set_control(control)
    sim.step()
    
    recorder.record_state(state)
    recorder.record_control(control)

recorder.stop()
recorder.save()
sim.stop()
```

### 强化学习训练

```python
from wheel_legged_control.simulation import ParallelMuJoCoBackend
from wheel_legged_control.algorithms import PPOTrainer, RLEnvironment

# 创建并行环境
parallel_sim = ParallelMuJoCoBackend("robot.xml", num_envs=8)
env = RLEnvironment(parallel_sim)

# 创建训练器
trainer = PPOTrainer(env, policy_net, value_net)

# 训练
trainer.train(total_timesteps=1000000, save_interval=10000)

# 评估
rewards = trainer.evaluate(num_episodes=10)
print(f"平均奖励: {np.mean(rewards)}")
```

---

**版本**: 1.0.0  
**最后更新**: 2026-02-09

更多详细信息，请参考源代码中的文档字符串。

