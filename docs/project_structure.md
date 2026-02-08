# 项目结构说明

## 概述

轮腿机器人孪生控制系统采用标准的ROS2工作空间结构，结合Python和C++混合开发模式。

## 目录结构

```
wheel-legged-robot-twin-control/
├── .git/                     # Git版本控制
├── .kiro/                    # Kiro规范文档
│   └── specs/
│       └── wheel-legged-robot-twin-control/
│           ├── requirements.md    # 需求文档
│           ├── design.md         # 设计文档
│           └── tasks.md          # 任务清单
├── src/                      # 源代码目录
│   ├── wheel_legged_control/     # 主要ROS2包
│   │   ├── wheel_legged_control/ # Python模块
│   │   │   ├── core/            # 核心业务逻辑
│   │   │   ├── controllers/     # 控制器模块
│   │   │   ├── gui/             # 图形用户界面
│   │   │   ├── interfaces/      # ROS2通信接口
│   │   │   ├── sensors/         # 传感器模块
│   │   │   └── utils/           # 工具函数
│   │   ├── src/                 # C++源码
│   │   │   ├── digital_twin_mapper/  # 数字孪生映射器
│   │   │   └── python_bindings/     # Python绑定
│   │   ├── include/             # C++头文件
│   │   ├── launch/              # 启动文件
│   │   ├── config/              # 配置文件
│   │   ├── urdf/                # 机器人模型
│   │   ├── worlds/              # Gazebo世界文件
│   │   ├── scripts/             # 可执行脚本
│   │   ├── CMakeLists.txt       # C++构建配置
│   │   ├── package.xml          # ROS2包配置
│   │   └── setup.py             # Python包配置
│   ├── wheel_legged_control_msgs/   # 自定义消息包
│   │   ├── msg/                 # 消息定义
│   │   ├── srv/                 # 服务定义
│   │   ├── CMakeLists.txt
│   │   └── package.xml
│   └── model/                   # 机器人模型文件
│       ├── RM_Serial_Wheeled-leg_Robot/  # RM轮腿机器人
│       └── DM_Wheel_leg_robot/           # DM轮腿机器人
├── test/                     # 测试目录
│   ├── cpp/                  # C++测试
│   ├── python/               # Python单元测试
│   ├── integration/          # 集成测试
│   ├── gui/                  # GUI测试
│   ├── deprecated/           # 过时测试文件
│   ├── run_tests.py          # 测试运行器
│   └── README.md             # 测试说明
├── docs/                     # 文档目录
│   ├── project_structure.md  # 项目结构说明
│   └── ros2_gui_integration_guide.md  # ROS2 GUI集成指南
├── scripts/                  # 项目脚本
│   └── verify_gazebo_integration.py
├── build/                    # 构建输出（Git忽略）
├── install/                  # 安装输出（Git忽略）
├── log/                      # 日志文件（Git忽略）
├── .gitignore               # Git忽略规则
├── pytest.ini              # pytest配置
├── README.md                # 项目说明
├── CONTRIBUTING.md          # 贡献指南
├── PROJECT_STATUS.md        # 项目状态
└── publish_to_github.sh     # GitHub发布脚本
```

## 核心模块说明

### 1. 源代码结构 (`src/`)

#### 主要ROS2包 (`wheel_legged_control/`)

**Python模块** (`wheel_legged_control/`)
- `core/`: 核心业务逻辑
  - `urdf_loader.py`: URDF文件加载器
  - `gazebo_simulator.py`: Gazebo仿真接口
- `controllers/`: 控制器模块
  - `joint_controller.py`: 关节控制器
- `gui/`: 图形用户界面
  - `control_panel.py`: 基础控制面板
  - `ros2_control_panel.py`: ROS2集成控制面板
- `interfaces/`: ROS2通信接口
  - `joint_interface.py`: 关节控制接口
- `sensors/`: 传感器模块
  - `imu_simulator.py`: IMU传感器仿真器
  - `imu_publisher_node.py`: IMU数据发布节点
- `utils/`: 工具函数

**C++模块** (`src/`)
- `digital_twin_mapper/`: 数字孪生映射器核心实现
- `python_bindings/`: pybind11 Python绑定

**配置和资源**
- `launch/`: ROS2启动文件
- `config/`: YAML配置文件
- `urdf/`: 机器人URDF模型
- `worlds/`: Gazebo世界文件
- `scripts/`: 可执行脚本

#### 自定义消息包 (`wheel_legged_control_msgs/`)
- `msg/`: 自定义消息类型
- `srv/`: 自定义服务类型

#### 机器人模型 (`model/`)
- 包含不同机器人的URDF模型和网格文件

### 2. 测试结构 (`test/`)

**测试类型**
- `cpp/`: C++单元测试（gtest）
- `python/`: Python单元测试（pytest）
- `integration/`: 系统集成测试
- `gui/`: 图形界面测试
- `deprecated/`: 过时的测试文件

**测试工具**
- `run_tests.py`: 统一测试运行器
- `README.md`: 测试使用说明

### 3. 文档结构 (`docs/`)

- 项目文档和使用指南
- API文档和技术说明

### 4. 规范文档 (`.kiro/specs/`)

- `requirements.md`: 详细需求规范
- `design.md`: 系统设计文档
- `tasks.md`: 实施任务清单

## 开发工作流

### 1. 构建系统

```bash
# 构建所有包
colcon build --symlink-install

# 构建特定包
colcon build --packages-select wheel_legged_control

# 设置环境
source install/setup.bash
```

### 2. 运行系统

```bash
# 使用launch文件启动
ros2 launch wheel_legged_control system_launch.py

# 启动ROS2集成控制面板
ros2 launch wheel_legged_control ros2_control_panel.launch.py
```

### 3. 测试

```bash
# 运行所有测试
python3 test/run_tests.py --all

# 运行特定类型测试
python3 test/run_tests.py --integration
```

## 编码规范

### Python代码
- 遵循PEP 8规范
- 使用类型提示
- 详细的文档字符串

### C++代码
- 遵循Google C++风格指南
- 使用现代C++特性（C++17）
- RAII资源管理

### ROS2规范
- 标准的包结构
- 规范的话题和服务命名
- 适当的QoS配置

## 依赖管理

### 系统依赖
- Ubuntu 20.04/22.04
- ROS2 Jazzy
- Gazebo Classic

### Python依赖
- PyQt5: GUI框架
- NumPy: 数值计算
- SciPy: 科学计算
- Matplotlib: 数据可视化
- Hypothesis: 属性测试

### C++依赖
- Eigen3: 线性代数
- pybind11: Python绑定
- tinyxml2: XML解析

## 版本控制

### 分支策略
- `main`: 稳定发布版本
- `develop`: 开发集成分支
- `feature/*`: 功能开发分支

### 提交规范
- 使用约定式提交格式
- 详细的提交信息
- 引用相关需求和任务

## 部署和发布

### 本地部署
```bash
# 构建和安装
colcon build --symlink-install
source install/setup.bash
```

### GitHub发布
```bash
# 使用发布脚本
./publish_to_github.sh <repository-url>
```

## 扩展开发

### 添加新模块
1. 在适当的目录创建模块文件
2. 更新CMakeLists.txt或setup.py
3. 添加相应的测试
4. 更新文档

### 添加新的ROS2包
1. 在src/目录创建新包
2. 配置package.xml和CMakeLists.txt
3. 添加到工作空间构建
4. 更新launch文件

这个项目结构支持：
- 模块化开发
- 混合语言编程
- 完整的测试覆盖
- 标准的ROS2工作流
- 清晰的文档组织