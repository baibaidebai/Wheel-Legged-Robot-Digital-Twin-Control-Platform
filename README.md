# 轮腿机器人孪生控制系统

## 🚨 遇到问题？

**Gazebo窗口没有打开？** → 查看 [docs/guides/QUICK_FIX.md](docs/guides/QUICK_FIX.md)

**Gazebo闪屏/看不到模型？** → 查看 [docs/guides/GAZEBO_FLICKERING_FIX.md](docs/guides/GAZEBO_FLICKERING_FIX.md)

**DM机器人无法加载？** → 运行 `python3 tools/fix_dm_urdf.py`

**首次使用？** → 先阅读 [docs/guides/START_HERE.md](docs/guides/START_HERE.md)

**查找文档？** → 查看 [docs/guides/DOCUMENTATION_INDEX.md](docs/guides/DOCUMENTATION_INDEX.md)

## 项目简介

轮腿机器人孪生控制系统是一个基于ROS2和Gazebo的仿真控制平台，用于《轮腿机器人孪生控制方法的研究》大创项目。系统通过数字孪生技术实现对串联轮腿机器人的仿真控制，为后续硬件集成和强化学习算法研究提供基础平台。

## 🚀 快速开始

### 方法1：GUI启动器（推荐）⭐

```bash
./launch.sh
```

图形界面可以：
- 选择机器人模型（RM或DM）
- 选择启动模式（安全/简单/标准）
- 配置高级选项
- 一键启动Gazebo

### 方法2：命令行启动

#### 第一步：安装Gazebo（首次使用必须）

```bash
./tools/install_gazebo.sh
```

#### 第二步：启动仿真

```bash
# 安全模式（推荐虚拟机）
./tools/launch_gazebo_safe.sh

# 简单模式
./tools/launch_gazebo_simple.sh

# 标准模式
./tools/launch_gazebo.sh
```

📚 详细说明：
- [简单安装指南](docs/guides/GAZEBO_INSTALL_SIMPLE.md) - 3分钟快速安装 ⭐
- [完整安装指南](docs/guides/INSTALL_GAZEBO.md) - 详细步骤和故障排除
- [诊断工具](tools/check_gazebo.sh) - 检查安装状态

## 核心特性

- 🤖 **完整的URDF机器人模型** - 支持RM和DM轮腿机器人
- 🎮 **Gazebo物理仿真** - 真实的物理引擎和3D可视化
- 📊 **ROS2集成** - 标准的机器人操作系统
- 🔄 **多种控制算法** - LQR、PPO强化学习等
- 🧠 **数字孪生映射** - 虚实状态同步
- 📹 **数据记录与回放** - 完整的实验数据管理

## 📋 系统要求

- Ubuntu 24.04 LTS
- ROS2 Jazzy
- Gazebo Harmonic
- Python 3.12+

## 🔧 安装

### 1. 安装Gazebo

```bash
sudo apt-get update
sudo apt-get install ros-jazzy-ros-gz
```

或安装完整版：

```bash
sudo apt-get install gz-harmonic
```

### 2. 安装Python依赖

```bash
pip install -r requirements.txt
```

### 3. 构建ROS2包（可选）

```bash
colcon build
source install/setup.bash
```

## 📁 项目结构

```
Wheel-Legged Robot Digital Twin Control Platform/
├── launch.sh                     # GUI启动器（推荐）⭐
├── README.md                     # 项目说明
├── requirements.txt              # Python依赖
├── pytest.ini                    # 测试配置
│
├── tools/                        # 工具脚本
│   ├── launch_gazebo_gui.py     # GUI启动器
│   ├── launch_gazebo_safe.sh    # 安全模式启动
│   ├── launch_gazebo_simple.sh  # 简单模式启动
│   ├── launch_gazebo.sh         # 标准模式启动
│   ├── install_gazebo.sh        # Gazebo安装脚本
│   ├── check_gazebo.sh          # Gazebo诊断
│   ├── check_opengl.sh          # OpenGL诊断
│   └── fix_dm_urdf.py           # DM机器人修复
│
├── docs/                         # 文档
│   ├── guides/                  # 使用指南
│   │   ├── START_HERE.md        # 快速开始
│   │   ├── QUICK_FIX.md         # 快速修复
│   │   ├── QUICK_REFERENCE.md   # 快速参考
│   │   ├── GAZEBO_QUICKSTART.md # Gazebo快速开始
│   │   ├── INSTALL_GAZEBO.md    # 安装指南
│   │   ├── GAZEBO_FLICKERING_FIX.md # 闪屏修复
│   │   ├── DM_ROBOT_FIX.md      # DM机器人修复
│   │   └── DOCUMENTATION_INDEX.md # 文档索引
│   ├── GAZEBO_GUIDE.md          # Gazebo详细指南
│   └── *.md                     # 其他文档
│
├── src/                          # 源代码
│   ├── model/                   # 机器人URDF模型
│   │   ├── RM_Serial_Wheeled-leg_Robot/  # RM机器人
│   │   └── DM_Wheel_leg_robot/           # DM机器人
│   └── wheel_legged_control/    # 控制系统代码
│       └── wheel_legged_control/
│           ├── algorithms/      # 控制算法（LQR、PPO）
│           ├── controllers/     # 控制器实现
│           ├── simulation/      # 仿真后端
│           ├── data/           # 数据记录和回放
│           └── sensors/        # 传感器仿真
│
├── scripts/                     # 演示脚本
│   ├── demo_*.py               # 演示脚本
│   └── gazebo/                 # Gazebo相关脚本
│
├── test/                        # 测试文件
│   ├── python/                 # Python单元测试
│   └── integration/            # 集成测试
│
└── data/                       # 实验数据
    ├── demo_recordings/        # 演示录制
    └── advanced_recordings/    # 高级实验数据
```

## 🎮 功能特性

### 仿真系统
- ✅ Gazebo Harmonic物理仿真
- ✅ 完整的URDF模型支持
- ✅ STL网格文件渲染
- ✅ 实时3D可视化

### 控制算法
- ✅ LQR线性二次调节器
- ✅ PPO强化学习
- ✅ 关节空间控制
- ✅ 任务空间控制

### 数据管理
- ✅ 实验数据记录
- ✅ 数据回放功能
- ✅ CSV格式导出
- ✅ JSON元数据

### ROS2集成
- ✅ 标准ROS2消息
- ✅ 服务接口
- ✅ Launch文件
- ✅ 参数配置

## 📚 文档

- [快速开始](docs/guides/START_HERE.md) - 立即开始 ⭐
- [Gazebo快速开始](docs/guides/GAZEBO_QUICKSTART.md) - 仿真入门 ⭐
- [文档索引](docs/guides/DOCUMENTATION_INDEX.md) - 所有文档
- [Gazebo详细指南](docs/GAZEBO_GUIDE.md) - 完整使用说明
- [项目状态](PROJECT_STATUS.md) - 开发进度
- [贡献指南](CONTRIBUTING.md) - 如何贡献代码

## 🎯 使用示例

### 1. 启动Gazebo仿真（GUI）

```bash
./launch.sh
```

在图形界面中选择机器人模型和启动选项。

### 2. 启动Gazebo仿真（命令行）

```bash
# 安全模式（推荐虚拟机）
./tools/launch_gazebo_safe.sh

# 简单模式
./tools/launch_gazebo_simple.sh
```

### 3. 运行演示脚本

```bash
# LQR控制器演示
python3 scripts/demo_lqr_controller.py

# PPO训练演示
python3 scripts/demo_ppo_training.py

# 数据记录演示
python3 scripts/demo_data_recorder.py
```

### 3. 使用ROS2 Launch

```bash
source install/setup.bash
ros2 launch wheel_legged_control system_launch.py
```

## 🔬 研究方向

本项目支持以下研究方向：

1. **轮腿混合运动控制** - 研究轮式和腿式运动的协调控制
2. **强化学习算法** - 基于PPO的自主学习控制
3. **数字孪生技术** - 虚实映射和状态同步
4. **传感器融合** - IMU、编码器等多传感器融合
5. **鲁棒控制** - 应对不确定性和扰动的控制策略

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细信息。

## 📄 许可证

本项目采用开源许可证。

## 🙏 致谢

感谢所有贡献者和支持者！

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交Issue
- Pull Request
- 项目讨论区

---

## 🎉 开始你的仿真之旅

```bash
./launch.sh
```

使用图形界面选择你的机器人模型，开始探索轮腿机器人的世界！🤖✨

或者使用命令行：

```bash
./tools/launch_gazebo_safe.sh
```
