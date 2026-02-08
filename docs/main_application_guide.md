# 轮腿机器人孪生控制系统 - 主应用程序使用指南

## 概述

轮腿机器人孪生控制系统主应用程序提供了完整的用户界面流程：**配置选择页面** → **可视化仿真界面**。用户可以通过直观的图形界面配置系统参数，然后进入实时仿真环境进行机器人控制和算法验证。

## 功能特性

### 🔧 配置选择页面
- **机器人模型选择**: 支持多种URDF机器人模型
- **仿真后端选择**: 支持MuJoCo和Gazebo物理引擎
- **配置档案管理**: 预设和自定义配置档案
- **控制算法选择**: 手动控制、LQR、PID、强化学习
- **高级参数调整**: 时间步长、重力、渲染选项等
- **实时配置预览**: 显示当前配置状态
- **系统状态监控**: 检查组件可用性

### 🎮 可视化仿真界面
- **实时机器人可视化**: 2D机器人状态显示
- **关节控制面板**: 直观的滑块控制界面
- **算法控制面板**: 启动/停止控制算法
- **仿真控制**: 播放/暂停/重置仿真
- **状态监控**: 实时显示仿真状态和性能
- **灵活切换**: 可随时返回配置页面

## 安装要求

### 必需依赖
```bash
# Python GUI框架
pip install PyQt5

# 科学计算库
pip install numpy scipy

# 机器人相关
pip install urdfpy

# 可选：高性能仿真
pip install mujoco  # 用于MuJoCo后端
```

### 系统要求
- Python 3.8+
- Linux/Windows/macOS
- 图形界面支持

## 快速启动

### 方法1: 使用启动脚本
```bash
# 进入项目目录
cd "Wheel-Legged Robot Digital Twin Control Platform"

# 启动主应用程序
python scripts/launch_main_application.py
```

### 方法2: 直接运行
```bash
# 设置Python路径
export PYTHONPATH=src/wheel_legged_control:$PYTHONPATH

# 启动应用程序
python src/wheel_legged_control/wheel_legged_control/gui/main_application.py
```

### 方法3: 演示模式
```bash
# 运行功能演示
python scripts/demo_main_application.py
```

## 使用流程

### 第一步：配置选择
1. **选择机器人模型**
   - 从下拉菜单选择可用的URDF模型
   - 查看模型信息（关节数、链接数等）

2. **选择仿真后端**
   - MuJoCo: 高性能物理仿真，适合强化学习
   - Gazebo: 机器人仿真平台，与ROS2集成

3. **选择配置档案**
   - `mujoco_high_performance`: 高性能仿真配置
   - `mujoco_visualization`: 可视化仿真配置
   - `gazebo_standard`: Gazebo标准配置
   - `rl_training`: 强化学习训练配置
   - `debug`: 调试配置

4. **选择控制算法**
   - `手动控制`: 用户通过界面控制
   - `LQR控制器`: 线性二次调节器
   - `PID控制器`: 经典PID控制
   - `强化学习`: 基于PPO的智能控制

5. **调整高级参数**
   - 时间步长 (0.001-0.1s)
   - 最大仿真步数
   - 渲染选项
   - 重力加速度

6. **验证配置**
   - 查看配置预览
   - 检查系统状态
   - 确认所有选项正确

7. **开始仿真**
   - 点击"开始仿真"按钮
   - 系统将验证配置并切换到仿真界面

### 第二步：仿真控制
1. **界面布局**
   - 左侧：关节控制面板和算法控制
   - 右侧：机器人可视化显示
   - 顶部：仿真控制工具栏
   - 底部：状态信息栏

2. **关节控制**（手动模式）
   - 使用滑块调整各关节角度
   - 实时查看关节状态
   - 观察机器人可视化更新

3. **算法控制**（自动模式）
   - 点击"启动算法"开始自动控制
   - 监控算法运行状态
   - 随时停止算法切换到手动模式

4. **仿真控制**
   - ⏸️/▶️ 暂停/播放仿真
   - 🔄 重置仿真状态
   - ⚙️ 返回配置页面

## 配置档案详解

### 默认配置档案

| 档案名称 | 适用场景 | 特点 |
|---------|---------|------|
| `mujoco_high_performance` | 高性能计算 | 关闭渲染，小时间步长，适合批量仿真 |
| `mujoco_visualization` | 可视化演示 | 高分辨率渲染，适合展示和调试 |
| `gazebo_standard` | ROS2集成 | 标准Gazebo配置，与ROS2无缝集成 |
| `rl_training` | 强化学习 | 优化的训练参数，支持大规模训练 |
| `debug` | 开发调试 | 小规模仿真，便于问题排查 |

### 自定义配置档案
用户可以在配置页面调整参数后保存为自定义档案，便于重复使用。

## 控制算法说明

### 手动控制
- **适用场景**: 用户交互、演示、调试
- **操作方式**: 通过滑块直接控制关节角度
- **特点**: 实时响应，直观易用

### LQR控制器
- **适用场景**: 线性系统控制、稳定性控制
- **原理**: 线性二次调节器，最优控制理论
- **特点**: 数学严谨，适合已知系统模型

### PID控制器
- **适用场景**: 位置控制、速度控制
- **原理**: 比例-积分-微分控制
- **特点**: 经典控制方法，参数可调

### 强化学习
- **适用场景**: 复杂任务、自适应控制
- **原理**: 基于PPO的深度强化学习
- **特点**: 智能决策，适应性强

## 故障排除

### 常见问题

1. **应用程序无法启动**
   ```bash
   # 检查PyQt5安装
   pip install PyQt5
   
   # 检查Python路径
   export PYTHONPATH=src/wheel_legged_control:$PYTHONPATH
   ```

2. **未找到机器人模型**
   - 确保URDF文件存在于 `src/model/` 目录
   - 检查URDF文件格式是否正确

3. **仿真后端不可用**
   ```bash
   # 安装MuJoCo
   pip install mujoco
   
   # 检查ROS2环境（Gazebo后端）
   source /opt/ros/jazzy/setup.bash
   ```

4. **NumPy版本兼容性警告**
   ```bash
   # 降级NumPy版本
   pip install "numpy<2.0"
   
   # 或升级相关模块
   pip install --upgrade scipy
   ```

### 调试模式
```bash
# 启用详细日志
export PYTHONPATH=src/wheel_legged_control:$PYTHONPATH
python -u scripts/launch_main_application.py
```

## 开发扩展

### 添加新的机器人模型
1. 将URDF文件放入 `src/model/新模型名称/urdf/` 目录
2. 确保URDF文件格式正确
3. 重启应用程序，新模型将自动出现在选择列表中

### 添加新的控制算法
1. 在 `src/wheel_legged_control/wheel_legged_control/algorithms/` 中实现算法
2. 在 `main_application.py` 的 `load_control_algorithms()` 中添加算法选项
3. 在 `SimulationPage` 中实现算法启动逻辑

### 自定义配置档案
1. 在配置页面调整参数
2. 使用配置管理器保存档案
3. 档案将保存在 `~/.wheel_legged_control/simulation/profiles/` 目录

## 技术架构

### 主要组件
- `MainApplication`: 主应用程序窗口
- `ConfigurationPage`: 配置选择页面
- `SimulationPage`: 仿真界面页面
- `SimulationManager`: 仿真管理器
- `ConfigManager`: 配置管理器
- `BackendRegistry`: 后端注册表

### 数据流
```
用户配置 → 配置验证 → 仿真初始化 → 界面切换 → 实时控制
```

### 信号机制
- `configuration_complete`: 配置完成信号
- `back_to_config`: 返回配置信号
- `joint_changed`: 关节变化信号

## 性能优化

### 仿真性能
- 选择合适的时间步长
- 关闭不必要的渲染
- 使用高性能配置档案

### 界面响应
- 避免在主线程进行重计算
- 使用异步更新机制
- 合理设置更新频率

## 版本历史

- **v1.0.0**: 初始版本，完整的配置-仿真流程
- 支持多种机器人模型和仿真后端
- 集成配置管理和算法控制
- 提供直观的用户界面

## 贡献指南

欢迎贡献代码和建议！请参考项目的 `CONTRIBUTING.md` 文件。

## 许可证

本项目采用 MIT 许可证，详见 `LICENSE` 文件。