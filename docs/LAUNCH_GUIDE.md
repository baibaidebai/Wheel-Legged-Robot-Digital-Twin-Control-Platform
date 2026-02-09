# 系统启动指南

## 概述

本文档介绍轮腿机器人孪生控制系统的各种启动方式和配置选项。

## 快速开始

### 方式1: 使用Shell脚本（推荐）

```bash
# 基本启动（Gazebo仿真 + GUI）
./launch_system.sh

# 使用MuJoCo仿真
./launch_system.sh --mode mujoco --gui

# 快速启动（开发模式）
./launch_system.sh --quick

# 完整功能启动
./launch_system.sh --mode gazebo --gui --rviz --record --algorithm
```

### 方式2: 直接使用ROS2 launch

```bash
# Source环境
source /opt/ros/humble/setup.bash
source install/setup.bash

# 完整系统启动
ros2 launch wheel_legged_control complete_system.launch.py

# 快速启动
ros2 launch wheel_legged_control quick_start.launch.py
```

## 启动模式

### 1. 完整系统模式

启动所有功能模块，适合完整测试和演示。

```bash
./launch_system.sh --mode gazebo --gui --rviz --record
```

**包含的节点**:
- Gazebo/MuJoCo仿真环境
- 关节控制器
- IMU仿真器
- 状态同步器
- 控制面板GUI
- RViz可视化
- 数据记录器

### 2. 快速启动模式

最小化配置，快速启动核心功能，适合开发和调试。

```bash
./launch_system.sh --quick
```

**包含的节点**:
- 关节控制器
- IMU仿真器

### 3. 硬件模式

连接真实硬件，不启动仿真环境。

```bash
./launch_system.sh --mode none --gui
```

## 启动参数

### Shell脚本参数

| 参数 | 说明 | 默认值 | 可选值 |
|------|------|--------|--------|
| `-m, --mode` | 仿真模式 | gazebo | gazebo, mujoco, none |
| `-g, --gui` | 启用GUI | true | - |
| `-r, --rviz` | 启用RViz | false | - |
| `-d, --record` | 启用数据记录 | false | - |
| `-a, --algorithm` | 启用算法管理器 | false | - |
| `-l, --log-level` | 日志级别 | info | debug, info, warn, error |
| `-q, --quick` | 快速启动模式 | false | - |
| `-h, --help` | 显示帮助 | - | - |

### ROS2 Launch参数

#### complete_system.launch.py

```bash
ros2 launch wheel_legged_control complete_system.launch.py \
    sim_mode:=gazebo \
    use_sim_time:=true \
    enable_gui:=true \
    enable_rviz:=false \
    robot_model:=wheel_legged_robot \
    log_level:=info \
    enable_recording:=false \
    enable_algorithm_manager:=false \
    x_pose:=0.0 \
    y_pose:=0.0 \
    z_pose:=0.2
```

**参数说明**:

- `sim_mode`: 仿真后端 (gazebo/mujoco/none)
- `use_sim_time`: 使用仿真时间
- `enable_gui`: 启用控制面板
- `enable_rviz`: 启用RViz可视化
- `robot_model`: 机器人模型名称
- `config_file`: 配置文件路径（可选）
- `log_level`: 日志级别
- `enable_recording`: 启用数据记录
- `enable_algorithm_manager`: 启用算法管理器
- `x_pose`, `y_pose`, `z_pose`: 机器人初始位置

#### quick_start.launch.py

```bash
ros2 launch wheel_legged_control quick_start.launch.py \
    sim_mode:=mujoco \
    enable_gui:=true
```

## 启动序列

完整系统启动按以下顺序执行:

### 阶段1: 仿真环境 (0秒)
- 启动Gazebo或MuJoCo仿真器
- 加载机器人模型
- 初始化物理引擎

### 阶段2: 核心控制节点 (延迟3秒)
- 关节控制器
- IMU仿真器
- 状态同步器

### 阶段3: 可选节点 (延迟5秒)
- 数据记录器
- 算法管理器

### 阶段4: 用户界面 (延迟7秒)
- 控制面板GUI
- RViz可视化

**延迟原因**: 确保依赖节点完全就绪后再启动后续节点。

## 节点依赖关系

```
仿真环境 (Gazebo/MuJoCo)
    ↓
关节控制器 ← IMU仿真器
    ↓
状态同步器
    ↓
控制面板GUI / RViz
```

## 常见启动场景

### 场景1: 开发调试

```bash
# 快速启动，无GUI
./launch_system.sh --quick
```

### 场景2: 功能演示

```bash
# 完整功能，带可视化
./launch_system.sh --mode gazebo --gui --rviz
```

### 场景3: 数据采集

```bash
# 启用数据记录
./launch_system.sh --mode gazebo --record
```

### 场景4: 强化学习训练

```bash
# 使用MuJoCo，启用算法管理器
./launch_system.sh --mode mujoco --algorithm --log-level warn
```

### 场景5: 硬件测试

```bash
# 连接真实硬件
./launch_system.sh --mode none --gui
```

## 环境要求

### 必需

- Ubuntu 22.04 LTS
- ROS2 Humble
- Python 3.10+
- 已编译的工作空间

### 可选

- Gazebo Classic (用于Gazebo仿真)
- MuJoCo (用于MuJoCo仿真)
- RViz2 (用于可视化)

## 环境设置

### 首次使用

```bash
# 1. Source ROS2环境
source /opt/ros/humble/setup.bash

# 2. 编译工作空间
cd /path/to/workspace
colcon build --packages-select wheel_legged_control

# 3. Source工作空间
source install/setup.bash

# 4. 启动系统
./launch_system.sh
```

### 日常使用

```bash
# 添加到~/.bashrc以自动设置环境
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
echo "source ~/workspace/Wheel-Legged\ Robot\ Digital\ Twin\ Control\ Platform/install/setup.bash" >> ~/.bashrc

# 重新加载
source ~/.bashrc

# 直接启动
./launch_system.sh
```

## 故障排除

### 问题1: ROS2环境未设置

**错误**: `ROS2环境未设置`

**解决**:
```bash
source /opt/ros/humble/setup.bash
```

### 问题2: 工作空间未编译

**错误**: `找不到install/setup.bash`

**解决**:
```bash
colcon build --packages-select wheel_legged_control
```

### 问题3: 节点启动失败

**错误**: 某个节点无法启动

**解决**:
1. 检查日志输出
2. 增加日志级别: `--log-level debug`
3. 单独测试节点:
```bash
ros2 run wheel_legged_control joint_controller_node
```

### 问题4: Gazebo无法启动

**错误**: Gazebo启动失败或黑屏

**解决**:
1. 检查显示设置:
```bash
echo $DISPLAY
```

2. 尝试软件渲染:
```bash
export LIBGL_ALWAYS_SOFTWARE=1
```

3. 检查Gazebo安装:
```bash
gazebo --version
```

### 问题5: 端口冲突

**错误**: 地址已被使用

**解决**:
1. 检查运行的ROS2节点:
```bash
ros2 node list
```

2. 清理僵尸进程:
```bash
killall -9 gzserver gzclient
```

## 性能优化

### 1. 减少启动时间

使用快速启动模式:
```bash
./launch_system.sh --quick
```

### 2. 降低资源使用

- 禁用GUI: 不使用 `--gui` 参数
- 禁用RViz: 不使用 `--rviz` 参数
- 降低日志级别: `--log-level warn`

### 3. 提高仿真性能

- 使用MuJoCo而非Gazebo
- 禁用渲染（无头模式）
- 调整物理引擎参数

## 高级配置

### 自定义配置文件

创建配置文件 `my_config.yaml`:

```yaml
simulation:
  backend: mujoco
  dt: 0.001
  
control:
  joint_controller:
    kp: 100.0
    kd: 10.0
    
recording:
  enabled: true
  output_dir: /tmp/recordings
```

使用配置文件启动:

```bash
ros2 launch wheel_legged_control complete_system.launch.py \
    config_file:=/path/to/my_config.yaml
```

### 多机器人仿真

启动多个机器人实例:

```bash
# 机器人1
ros2 launch wheel_legged_control complete_system.launch.py \
    robot_model:=robot1 \
    x_pose:=0.0 \
    y_pose:=0.0

# 机器人2
ros2 launch wheel_legged_control complete_system.launch.py \
    robot_model:=robot2 \
    x_pose:=2.0 \
    y_pose:=0.0
```

## 监控和调试

### 查看节点状态

```bash
# 列出所有节点
ros2 node list

# 查看节点信息
ros2 node info /joint_controller

# 查看话题
ros2 topic list

# 监听话题
ros2 topic echo /joint_states
```

### 查看日志

```bash
# 实时查看日志
ros2 run rqt_console rqt_console

# 查看特定节点日志
ros2 run rqt_logger_level rqt_logger_level
```

### 性能分析

```bash
# CPU和内存使用
top -p $(pgrep -d',' -f ros2)

# 话题频率
ros2 topic hz /joint_states

# 话题带宽
ros2 topic bw /joint_states
```

## 参考资料

- [ROS2 Launch文档](https://docs.ros.org/en/humble/Tutorials/Intermediate/Launch/Launch-Main.html)
- [Gazebo集成指南](./GAZEBO_GUIDE.md)
- [MuJoCo集成指南](./MUJOCO_GUIDE.md)
- [系统架构文档](./project_structure.md)
