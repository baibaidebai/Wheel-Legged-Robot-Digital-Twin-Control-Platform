# Gazebo仿真快速开始

## 🚀 一键启动

**首先确保Gazebo已安装**：

```bash
# 检查是否已安装
gz sim --version

# 如果未安装，运行：
sudo apt-get update
sudo apt-get install ros-jazzy-ros-gz-sim
```

**然后启动仿真**：

```bash
./launch_gazebo.sh
```

如果遇到安装问题，请查看：[INSTALL_GAZEBO.md](INSTALL_GAZEBO.md)

## 📋 步骤

### 1. 安装Gazebo（如果还没安装）

```bash
sudo apt-get update
sudo apt-get install ros-jazzy-ros-gz
```

或安装完整版：

```bash
sudo apt-get install gz-harmonic
```

### 2. 启动仿真

```bash
./launch_gazebo.sh
```

选择你的机器人模型：
- 1: RM_Serial_Wheeled-leg_Robot
- 2: DM_Wheel_leg_robot

### 3. 加载机器人

Gazebo窗口打开后，在**另一个终端**运行脚本显示的命令来加载机器人。

## 🎮 控制

| 操作 | 功能 |
|------|------|
| 鼠标左键拖动 | 旋转视角 |
| 鼠标滚轮 | 缩放 |
| Shift+鼠标左键 | 平移视角 |

## 📁 项目结构

```
Wheel-Legged Robot Digital Twin Control Platform/
├── launch_gazebo.sh          # Gazebo启动脚本
├── GAZEBO_QUICKSTART.md      # 本文档
├── src/
│   └── model/                 # 机器人模型
│       ├── RM_Serial_Wheeled-leg_Robot/
│       └── DM_Wheel_leg_robot/
├── scripts/
│   ├── gazebo/               # Gazebo相关脚本
│   └── archive/              # 归档的旧脚本
└── docs/                     # 文档
    ├── GAZEBO_GUIDE.md       # 详细指南
    └── archive/              # 归档的旧文档
```

## 💡 提示

- Gazebo对URDF有完美支持
- 可以直接加载STL网格文件
- 适合机器人开发和测试

## 📚 更多信息

查看详细文档：`docs/GAZEBO_GUIDE.md`

## 🔧 故障排除

### Gazebo未安装

```bash
sudo apt-get install ros-jazzy-ros-gz
```

### 模型不显示

检查URDF文件和mesh文件是否存在：

```bash
ls -la src/model/RM_Serial_Wheeled-leg_Robot/urdf/
ls -la src/model/RM_Serial_Wheeled-leg_Robot/meshes/
```

## 🎉 开始仿真

```bash
./launch_gazebo.sh
```

享受你的轮腿机器人仿真！🤖
