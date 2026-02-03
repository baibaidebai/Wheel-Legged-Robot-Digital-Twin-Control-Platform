# 轮腿机器人孪生控制系统

## 项目简介

轮腿机器人孪生控制系统是一个基于ROS2的仿真控制平台，用于《轮腿机器人孪生控制方法的研究》大创项目。系统通过数字孪生技术实现对串联轮腿机器人的仿真控制，为后续硬件集成和强化学习算法研究提供基础平台。

## 核心特性

- 🤖 **基于URDF的轮腿混合运动数字孪生映射器** - 核心创新功能
- 🎮 **PyQt5图形控制界面** - 直观的机器人控制面板
- 📊 **实时IMU数据仿真与可视化** - 支持姿态控制算法开发
- 🔄 **虚实状态同步模拟** - 为硬件集成做准备
- 🧠 **多算法验证平台** - 支持强化学习、LQR等控制算法
- 📹 **数据记录与回放** - ROS2 bag格式数据管理

## 系统架构

```
用户交互层    │  控制面板 (PyQt5) │ 命令行接口
应用服务层    │  控制管理器 │ 数据管理器 │ 算法管理器  
核心业务层    │  数字孪生映射器 │ 关节控制器 │ 状态同步器
仿真环境层    │  Gazebo仿真 │ URDF模型 │ IMU传感器
ROS2通信层   │  话题通信 │ 服务调用 │ 动作服务
```

## 技术栈

- **ROS2**: Humble/Foxy
- **仿真**: Gazebo Classic
- **编程语言**: Python 3.8+ (主要) + C++ (性能关键模块)
- **GUI框架**: PyQt5
- **测试框架**: pytest + Hypothesis (属性测试)
- **版本控制**: Git (GitFlow工作流)

## 快速开始

### 环境要求

- Ubuntu 20.04/22.04
- ROS2 Humble 或 Foxy
- Python 3.8+
- Gazebo Classic
- PyQt5

### 安装依赖

```bash
# 安装ROS2依赖
sudo apt update
sudo apt install ros-humble-desktop ros-humble-gazebo-ros-pkgs
sudo apt install python3-colcon-common-extensions

# 安装Python依赖
pip3 install PyQt5 numpy scipy matplotlib hypothesis pytest

# 安装C++依赖
sudo apt install libeigen3-dev pybind11-dev
```

### 构建项目

```bash
# 克隆项目
git clone <repository-url>
cd wheel-legged-robot-twin-control

# 构建ROS2工作空间
colcon build --symlink-install

# 设置环境
source install/setup.bash
```

### 运行系统

```bash
# 启动完整系统
ros2 launch wheel_legged_control system_launch.py

# 或分别启动各组件
ros2 run wheel_legged_control gazebo_simulator
ros2 run wheel_legged_control control_panel
```

## 项目结构

```
wheel-legged-robot-twin-control/
├── src/                          # 源代码
│   ├── wheel_legged_control/      # 主要ROS2包
│   │   ├── wheel_legged_control/  # Python模块
│   │   │   ├── core/             # 核心业务逻辑
│   │   │   ├── gui/              # PyQt5界面
│   │   │   ├── algorithms/       # 控制算法
│   │   │   └── utils/            # 工具函数
│   │   ├── src/                  # C++源码
│   │   │   └── digital_twin_mapper/ # 数字孪生映射器
│   │   ├── launch/               # 启动文件
│   │   ├── config/               # 配置文件
│   │   └── urdf/                 # 机器人模型
│   └── robot/                    # 机器人相关文件
│       └── urdf/                 # URDF模型文件
├── test/                         # 测试文件
├── docs/                         # 文档
├── .kiro/specs/                  # 项目规范文档
└── README.md
```

## 开发指南

### 分支策略

- `main`: 稳定发布版本
- `develop`: 开发集成分支  
- `feature/*`: 功能开发分支

### 贡献流程

1. 从develop分支创建feature分支
2. 开发并测试新功能
3. 提交Pull Request到develop分支
4. 代码审查通过后合并
5. 定期将develop合并到main发布

### 代码规范

- Python: 遵循PEP 8规范
- C++: 遵循Google C++风格指南
- 提交信息: 使用约定式提交格式

## 测试

```bash
# 运行所有测试
colcon test

# 运行Python测试
python -m pytest test/

# 运行属性测试
python -m pytest test/ -m property_test

# 生成测试覆盖率报告
python -m pytest test/ --cov=wheel_legged_control --cov-report=html
```

## 文档

- [需求文档](.kiro/specs/wheel-legged-robot-twin-control/requirements.md)
- [设计文档](.kiro/specs/wheel-legged-robot-twin-control/design.md)
- [实施计划](.kiro/specs/wheel-legged-robot-twin-control/tasks.md)
- [API文档](docs/api.md)
- [用户手册](docs/user_guide.md)

## 许可证

本项目采用MIT许可证 - 详见 [LICENSE](LICENSE) 文件

## 致谢

本项目是《轮腿机器人孪生控制方法的研究》大创项目的成果，感谢所有贡献者的努力。

## 联系方式

- 项目负责人: [姓名]
- 邮箱: [email]
- 项目主页: [GitHub链接]

---

**【软著提示】**: 本项目的核心创新在于"基于URDF的轮腿混合运动数字孪生映射器"，解决了轮腿机器人闭环机构在URDF中的表达与控制映射问题，具备申请计算机软件著作权的技术独创性。