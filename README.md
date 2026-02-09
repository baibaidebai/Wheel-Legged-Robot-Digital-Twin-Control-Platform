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

### 方法1：增强版GUI启动器（推荐）⭐⭐

```bash
./launch_enhanced.sh
```

增强版图形界面支持：
- ✅ 选择任意模型文件夹
- ✅ 选择URDF/MJCF文件
- ✅ 选择世界文件
- ✅ 配置仿真器参数
- ✅ Gazebo和MuJoCo双支持

📚 详细说明：[增强版GUI使用指南](docs/ENHANCED_GUI_GUIDE.md)

### 方法1B：标准GUI启动器

```bash
./launch.sh
```

标准图形界面可以：
- 选择机器人模型（RM或DM）
- 选择仿真器（Gazebo或MuJoCo）
- 选择启动模式（安全/简单/标准）
- 配置高级选项
- 一键启动

### 方法2：命令行启动

#### Gazebo仿真

**第一步：安装Gazebo（首次使用必须）**

```bash
./tools/install_gazebo.sh
```

**第二步：启动仿真**

```bash
# 安全模式（推荐虚拟机）
./tools/launch_gazebo_safe.sh

# 简单模式
./tools/launch_gazebo_simple.sh

# 标准模式
./tools/launch_gazebo.sh
```

#### MuJoCo仿真（MJCF格式）⭐

**要求：** MuJoCo 2.3.0+（你的版本：3.4.0 ✅）

**第一步：转换URDF到MJCF（首次使用必须）**

我们提供两种转换方案：

**方案 A：Wiki-GRx-MJCF（推荐，保留真实外观）**
```bash
# 1. 安装工具（首次使用）
cd ~/workspace
git clone https://github.com/FFTAI/Wiki-MJCF.git
cd "Wheel-Legged Robot Digital Twin Control Platform"
source venv/bin/activate
pip install -e ~/workspace/Wiki-GRx-MJCF

# 2. 转换模型
python3 tools/test_wiki_mjcf.py
```

**方案 B：内置工具（简单可靠）**
```bash
# 转换RM机器人模型
python3 tools/convert_urdf_to_mjcf.py --model rm

# 转换DM机器人模型
python3 tools/convert_urdf_to_mjcf.py --model dm
```

📚 **详细对比**：查看 [docs/MUJOCO_GUIDE.md](docs/MUJOCO_GUIDE.md)

**第二步：启动仿真**

```bash
# 命令行启动
./tools/launch_mujoco.sh

# 或直接使用Python
python3 tools/launch_mujoco.py --model rm  # RM机器人
python3 tools/launch_mujoco.py --model dm  # DM机器人

# 使用 Wiki-GRx-MJCF 生成的文件（保留真实外观）
python3 tools/launch_mujoco.py --mjcf "src/model/RM_Serial_Wheeled-leg_Robot/mjcf/RM_Serial_Wheeled-leg_Robot_wiki.xml"
```

**MuJoCo优势：**
- ✅ 高性能物理仿真
- ✅ 适合强化学习训练
- ✅ 交互式可视化
- ✅ 两种转换方案可选（真实外观 vs 简单可靠）

📚 详细说明：
- [Gazebo 完整指南](docs/GAZEBO_GUIDE.md) - Gazebo 安装、启动和故障排除 ⭐
- [MuJoCo 完整指南](docs/MUJOCO_GUIDE.md) - MuJoCo 集成和使用 ⭐

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

### 快速开始
- [快速开始指南](docs/guides/START_HERE.md) - 立即开始 ⭐
- [快速参考](docs/guides/QUICK_REFERENCE.md) - 常用命令速查
- [增强版GUI使用指南](docs/ENHANCED_GUI_GUIDE.md) - 增强版启动器 ⭐⭐

### 仿真指南
- [Gazebo 完整指南](docs/GAZEBO_GUIDE.md) - Gazebo 仿真 ⭐
- [MuJoCo 完整指南](docs/MUJOCO_GUIDE.md) - MuJoCo 仿真 ⭐

### 其他文档
- [文档索引](docs/guides/DOCUMENTATION_INDEX.md) - 所有文档
- [项目状态](PROJECT_STATUS.md) - 开发进度
- [贡献指南](CONTRIBUTING.md) - 如何贡献代码
- [文件组织](docs/guides/FILE_ORGANIZATION.md) - 项目结构说明

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

**增强版GUI（推荐）：**
```bash
./launch_enhanced.sh
```

**标准GUI：**
```bash
./launch.sh
```

使用图形界面选择你的机器人模型，开始探索轮腿机器人的世界！🤖✨

或者使用命令行：

```bash
./tools/launch_gazebo_safe.sh
```
