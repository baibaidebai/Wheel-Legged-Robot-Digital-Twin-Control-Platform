# 轮腿机器人孪生控制系统 - 用户手册

## 📖 目录

1. [系统概述](#系统概述)
2. [安装指南](#安装指南)
3. [快速开始](#快速开始)
4. [核心功能](#核心功能)
5. [高级使用](#高级使用)
6. [配置管理](#配置管理)
7. [故障排除](#故障排除)
8. [最佳实践](#最佳实践)

---

## 系统概述

### 什么是轮腿机器人孪生控制系统？

轮腿机器人孪生控制系统是一个基于ROS2的仿真控制平台，用于研究和开发轮腿混合机器人的控制算法。系统通过数字孪生技术实现虚拟环境与物理机器人的状态同步，为算法验证和硬件集成提供完整的开发环境。

### 核心特性

- **多仿真后端支持**: Gazebo和MuJoCo双引擎支持
- **数字孪生映射**: 高性能C++实现的运动学映射器
- **控制算法库**: LQR、PPO等多种控制算法
- **数据管理**: 完整的实验数据记录和回放功能
- **可视化界面**: PyQt5图形界面和ROS2集成
- **性能监控**: 实时性能分析和优化工具

### 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    用户界面层                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  PyQt5 GUI   │  │  ROS2 Tools  │  │  CLI Scripts │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    控制层                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ 关节控制器    │  │ 算法管理器    │  │ 状态同步器    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    仿真层                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Gazebo     │  │   MuJoCo     │  │ 数字孪生映射  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    数据层                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ 数据记录器    │  │ 数据回放器    │  │ 配置管理器    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 安装指南

### 系统要求

#### 硬件要求
- CPU: 4核心以上（推荐8核心）
- 内存: 8GB以上（推荐16GB）
- 显卡: 支持OpenGL 3.3+
- 存储: 10GB可用空间

#### 软件要求
- 操作系统: Ubuntu 24.04 LTS
- ROS2: Jazzy Jalisco
- Python: 3.12+
- Gazebo: Harmonic (可选)
- MuJoCo: 3.0+ (可选)

### 安装步骤

#### 1. 安装ROS2 Jazzy

```bash
# 添加ROS2源
sudo apt update && sudo apt install software-properties-common
sudo add-apt-repository universe
sudo apt update && sudo apt install curl -y
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg

# 添加ROS2仓库
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

# 安装ROS2
sudo apt update
sudo apt install ros-jazzy-desktop
```

#### 2. 安装Gazebo（可选）

```bash
# 使用项目提供的安装脚本
./tools/install_gazebo.sh

# 或手动安装
sudo apt-get install ros-jazzy-ros-gz
sudo apt-get install gz-harmonic
```

#### 3. 克隆项目

```bash
cd ~/workspace
git clone https://github.com/baibaidebai/Wheel-Legged-Robot-Digital-Twin-Control-Platform.git
cd "Wheel-Legged Robot Digital Twin Control Platform"
```

#### 4. 创建Python虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate
```

#### 5. 安装Python依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 6. 安装MuJoCo（可选）

```bash
pip install mujoco
```

#### 7. 构建ROS2包

```bash
source /opt/ros/jazzy/setup.bash
colcon build
source install/setup.bash
```

### 验证安装

```bash
# 检查ROS2
ros2 --version

# 检查Gazebo
gz sim --version

# 检查Python包
python3 -c "import mujoco; print('MuJoCo版本:', mujoco.__version__)"

# 运行测试
pytest test/python/test_basic.py
```

---

## 快速开始

### 方法1: 使用增强版GUI启动器（推荐）

```bash
./launch_enhanced.sh
```

增强版GUI提供：
- 模型文件夹选择
- URDF/MJCF文件选择
- 世界文件配置
- 仿真参数设置
- Gazebo和MuJoCo支持

### 方法2: 使用标准GUI启动器

```bash
./launch.sh
```

标准GUI提供：
- 机器人模型选择（RM/DM）
- 仿真器选择（Gazebo/MuJoCo）
- 启动模式选择
- 高级选项配置

### 方法3: 命令行启动

#### Gazebo仿真

```bash
# 安全模式（推荐虚拟机）
./tools/launch_gazebo_safe.sh

# 简单模式
./tools/launch_gazebo_simple.sh

# 标准模式
./tools/launch_gazebo.sh
```

#### MuJoCo仿真

```bash
# 启动MuJoCo仿真
./tools/launch_mujoco.sh

# 或使用Python脚本
python3 tools/launch_mujoco.py --model rm
python3 tools/launch_mujoco.py --model dm
```

### 方法4: ROS2 Launch

```bash
source install/setup.bash

# 完整系统启动
ros2 launch wheel_legged_control complete_system.launch.py

# 快速启动
ros2 launch wheel_legged_control quick_start.launch.py

# 自定义启动
ros2 launch wheel_legged_control complete_system.launch.py \
    sim_mode:=mujoco \
    robot_model:=rm \
    enable_gui:=true
```

---

## 核心功能

### 1. 仿真管理

#### 启动仿真

```python
from wheel_legged_control.simulation import SimulationManager

# 创建仿真管理器
sim_manager = SimulationManager()

# 加载机器人模型
sim_manager.load_robot("path/to/robot.urdf")

# 启动仿真
sim_manager.start()

# 运行仿真步骤
for i in range(1000):
    sim_manager.step()
    state = sim_manager.get_state()
    # 处理状态...

# 停止仿真
sim_manager.stop()
```

#### 切换仿真后端

```python
# 使用Gazebo
sim_manager.set_backend("gazebo")

# 使用MuJoCo
sim_manager.set_backend("mujoco")

# 使用并行MuJoCo（用于强化学习）
sim_manager.enable_parallel_simulation(num_envs=8)
```

### 2. 关节控制

#### 基本关节控制

```python
from wheel_legged_control.controllers import JointController

# 创建关节控制器
controller = JointController()

# 设置目标位置
target_positions = {
    'joint1': 0.5,
    'joint2': -0.3,
    'joint3': 0.8
}
controller.set_target_positions(target_positions)

# 获取控制指令
control_cmd = controller.compute_control()

# 应用控制指令
sim_manager.apply_control(control_cmd)
```

#### PID参数调整

```python
# 设置PID参数
controller.set_pid_gains(
    joint_name='joint1',
    kp=10.0,
    ki=0.1,
    kd=1.0
)

# 批量设置
pid_params = {
    'joint1': {'kp': 10.0, 'ki': 0.1, 'kd': 1.0},
    'joint2': {'kp': 15.0, 'ki': 0.2, 'kd': 1.5},
}
controller.set_all_pid_gains(pid_params)
```

### 3. 控制算法

#### LQR控制器

```python
from wheel_legged_control.algorithms import LQRController

# 创建LQR控制器
lqr = LQRController(
    state_dim=12,
    control_dim=6
)

# 设置系统矩阵
lqr.set_system_matrices(A, B)

# 设置代价矩阵
lqr.set_cost_matrices(Q, R)

# 计算控制增益
lqr.compute_gains()

# 计算控制输入
state = sim_manager.get_state()
control = lqr.compute_control(state, target_state)
```

#### PPO强化学习

```python
from wheel_legged_control.algorithms import PPOTrainer, RLEnvironment

# 创建环境
env = RLEnvironment(sim_manager)

# 创建训练器
trainer = PPOTrainer(
    env=env,
    policy_network=policy_net,
    value_network=value_net
)

# 训练
trainer.train(
    total_timesteps=1000000,
    save_interval=10000
)

# 评估
rewards = trainer.evaluate(num_episodes=10)
```

### 4. 数据记录与回放

#### 数据记录

```python
from wheel_legged_control.data import DataRecorder

# 创建记录器
recorder = DataRecorder(
    output_dir="data/experiments",
    experiment_name="test_run"
)

# 开始记录
recorder.start()

# 记录数据
for i in range(1000):
    state = sim_manager.get_state()
    control = controller.compute_control()
    
    recorder.record_state(state)
    recorder.record_control(control)
    
    sim_manager.step()

# 停止记录
recorder.stop()
recorder.save()
```

#### 数据回放

```python
from wheel_legged_control.data import DataPlayer

# 创建回放器
player = DataPlayer("data/experiments/test_run")

# 加载数据
player.load()

# 回放数据
player.play(speed=1.0)

# 暂停/继续
player.pause()
player.resume()

# 跳转到特定时间
player.seek(time=5.0)
```

### 5. 传感器仿真

#### IMU传感器

```python
from wheel_legged_control.sensors import IMUSimulator

# 创建IMU仿真器
imu = IMUSimulator(
    noise_level=0.01,
    bias_level=0.001
)

# 获取IMU数据
imu_data = imu.get_data(robot_state)

# 访问数据
orientation = imu_data['orientation']
angular_velocity = imu_data['angular_velocity']
linear_acceleration = imu_data['linear_acceleration']
```

### 6. 数字孪生映射

#### 使用数字孪生映射器

```python
from wheel_legged_control.core import DigitalTwinMapperWrapper

# 创建映射器
mapper = DigitalTwinMapperWrapper()

# 加载机器人模型
mapper.load_urdf("path/to/robot.urdf")

# 正向运动学
joint_positions = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
end_effector_pose = mapper.forward_kinematics(joint_positions)

# 逆向运动学
target_pose = [0.5, 0.0, 0.3, 0.0, 0.0, 0.0]
joint_positions = mapper.inverse_kinematics(target_pose)

# 识别约束
constraints = mapper.identify_constraints()
```

---

## 高级使用

### 并行仿真（强化学习）

```python
from wheel_legged_control.simulation import ParallelMuJoCoBackend

# 创建并行仿真后端
parallel_sim = ParallelMuJoCoBackend(
    model_path="path/to/robot.xml",
    num_envs=8,
    use_multiprocessing=True
)

# 批量重置
parallel_sim.reset_all()

# 批量执行动作
actions = np.random.randn(8, 6)  # 8个环境，每个6个动作
states, rewards, dones, infos = parallel_sim.step_all(actions)

# 性能基准测试
from wheel_legged_control.simulation import SimulationBenchmark

benchmark = SimulationBenchmark()
results = benchmark.run_benchmark(
    backend='mujoco',
    num_steps=10000,
    num_envs=8
)
print(f"平均步频: {results['steps_per_second']:.2f} Hz")
```

### 性能监控

```python
from wheel_legged_control.utils import PerformanceMonitor, measure_performance

# 创建性能监控器
monitor = PerformanceMonitor()

# 使用装饰器
@monitor.measure
def my_control_function():
    # 控制逻辑
    pass

# 使用上下文管理器
from wheel_legged_control.utils import PerformanceContext

with PerformanceContext('simulation_step', monitor):
    sim_manager.step()

# 生成报告
print(monitor.generate_report())

# 获取慢函数
slow_functions = monitor.get_slow_functions(threshold=0.1)
for metric in slow_functions:
    print(f"{metric.name}: {metric.avg_time*1000:.2f}ms")
```

### 异常处理和恢复

```python
from wheel_legged_control.core import ExceptionHandler, SystemState

# 创建异常处理器
handler = ExceptionHandler()

# 注册恢复策略
handler.register_recovery_strategy(
    exception_type=ConnectionError,
    strategy='retry',
    max_retries=3
)

# 使用装饰器
@handler.handle_exceptions
def risky_operation():
    # 可能失败的操作
    pass

# 手动处理
try:
    risky_operation()
except Exception as e:
    handler.handle_exception(e, context={'operation': 'simulation'})

# 检查系统状态
if handler.get_system_state() == SystemState.ERROR:
    handler.attempt_recovery()
```

### 系统诊断

```python
from wheel_legged_control.core import SystemDiagnostics

# 创建诊断工具
diagnostics = SystemDiagnostics()

# 运行健康检查
health_status = diagnostics.run_health_check()
print(f"系统健康: {health_status['overall_health']}")

# 检查特定资源
cpu_usage = diagnostics.check_cpu_usage()
memory_usage = diagnostics.check_memory_usage()
disk_usage = diagnostics.check_disk_usage()

# 生成诊断报告
report = diagnostics.generate_report()
print(report)
```

---

## 配置管理

### 配置文件结构

配置文件位于 `src/wheel_legged_control/config/` 目录：

```
config/
├── wheel_legged_control.yaml    # 主配置文件
├── joint_controller.yaml        # 关节控制器配置
└── state_synchronizer.yaml      # 状态同步器配置
```

### 主配置文件示例

```yaml
# wheel_legged_control.yaml
simulation:
  backend: "mujoco"  # gazebo, mujoco
  timestep: 0.001
  realtime_factor: 1.0
  
robot:
  model: "rm"  # rm, dm
  urdf_path: "src/model/RM_Serial_Wheeled-leg_Robot/urdf/RM_Serial_Wheeled-leg_Robot.urdf"
  
control:
  frequency: 100  # Hz
  pid_gains:
    default:
      kp: 10.0
      ki: 0.1
      kd: 1.0
      
sensors:
  imu:
    enabled: true
    frequency: 200  # Hz
    noise_level: 0.01
    
data:
  recording:
    enabled: false
    output_dir: "data/recordings"
    format: "csv"  # csv, rosbag
```

### 使用配置管理器

```python
from wheel_legged_control.simulation import ConfigManager

# 加载配置
config = ConfigManager()
config.load("config/wheel_legged_control.yaml")

# 访问配置
sim_backend = config.get("simulation.backend")
control_freq = config.get("control.frequency")

# 修改配置
config.set("simulation.timestep", 0.002)

# 保存配置
config.save("config/my_config.yaml")

# 验证配置
is_valid = config.validate()
```

---

## 故障排除

### 常见问题

#### 1. Gazebo窗口无法打开

**症状**: 运行启动脚本后Gazebo窗口不出现

**解决方案**:
```bash
# 检查Gazebo安装
gz sim --version

# 重新安装Gazebo
./tools/install_gazebo.sh

# 使用安全模式
./tools/launch_gazebo_safe.sh
```

#### 2. MuJoCo显示错误

**症状**: MuJoCo无法加载模型或显示黑屏

**解决方案**:
```bash
# 检查MuJoCo安装
python3 -c "import mujoco; print(mujoco.__version__)"

# 重新安装MuJoCo
pip install --upgrade mujoco

# 检查OpenGL支持
./tools/check_opengl.sh
```

#### 3. ROS2节点无法通信

**症状**: 节点启动但无法接收/发送消息

**解决方案**:
```bash
# 检查ROS2环境
source /opt/ros/jazzy/setup.bash
source install/setup.bash

# 检查节点
ros2 node list

# 检查话题
ros2 topic list
ros2 topic echo /joint_states
```

#### 4. Python导入错误

**症状**: `ModuleNotFoundError` 或导入失败

**解决方案**:
```bash
# 激活虚拟环境
source venv/bin/activate

# 重新安装依赖
pip install -r requirements.txt

# 重新构建
colcon build
source install/setup.bash
```

### 诊断工具

```bash
# 检查Gazebo
./tools/check_gazebo.sh

# 检查OpenGL
./tools/check_opengl.sh

# 运行系统诊断
python3 -c "
from wheel_legged_control.core import SystemDiagnostics
diag = SystemDiagnostics()
print(diag.generate_report())
"
```

### 日志和调试

```bash
# 启用详细日志
export ROS_LOG_LEVEL=DEBUG

# 查看ROS2日志
ros2 run wheel_legged_control joint_controller_node --ros-args --log-level DEBUG

# 查看Python日志
python3 scripts/demo_main_application.py --log-level DEBUG
```

---

## 最佳实践

### 1. 开发工作流

```bash
# 1. 创建功能分支
git checkout -b feature/my-feature

# 2. 开发和测试
pytest test/python/

# 3. 提交更改
git add .
git commit -m "feat: add new feature"

# 4. 推送到远程
git push origin feature/my-feature

# 5. 创建Pull Request
```

### 2. 性能优化

- 使用MuJoCo进行大规模仿真
- 启用并行仿真加速强化学习训练
- 使用性能监控器识别瓶颈
- 调整仿真时间步长平衡精度和速度

### 3. 数据管理

- 为每个实验使用唯一的名称
- 定期备份重要数据
- 使用CSV格式便于分析
- 记录实验参数和配置

### 4. 代码质量

- 遵循PEP 8代码风格
- 编写单元测试
- 使用类型提示
- 添加文档字符串

### 5. 安全实践

- 始终检查关节限制
- 实现紧急停止机制
- 监控系统资源使用
- 定期运行健康检查

---

## 附录

### A. 快速参考

#### 常用命令

```bash
# 启动GUI
./launch_enhanced.sh

# Gazebo仿真
./tools/launch_gazebo_safe.sh

# MuJoCo仿真
./tools/launch_mujoco.sh

# ROS2启动
ros2 launch wheel_legged_control complete_system.launch.py

# 运行测试
pytest test/

# 构建项目
colcon build
```

#### 重要路径

- 配置文件: `src/wheel_legged_control/config/`
- 机器人模型: `src/model/`
- 演示脚本: `scripts/`
- 测试文件: `test/`
- 文档: `docs/`

### B. 相关文档

- [API参考](API_REFERENCE.md)
- [故障排除指南](TROUBLESHOOTING.md)
- [Gazebo指南](GAZEBO_GUIDE.md)
- [MuJoCo指南](MUJOCO_GUIDE.md)
- [性能优化指南](PERFORMANCE_OPTIMIZATION.md)
- [CI/CD指南](CI_CD_GUIDE.md)

### C. 支持和社区

- GitHub Issues: 报告问题和请求功能
- Pull Requests: 贡献代码
- 讨论区: 技术讨论和问答

---

**版本**: 1.0.0  
**最后更新**: 2026-02-09  
**维护者**: 轮腿机器人孪生控制系统开发团队
