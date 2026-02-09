# 增强版GUI启动器使用指南

## 📋 概述

增强版GUI启动器提供了更灵活的配置选项，支持：
- ✅ 选择任意模型文件夹
- ✅ 选择URDF/MJCF文件
- ✅ 选择世界文件
- ✅ 配置仿真器参数
- ✅ Gazebo和MuJoCo双支持

---

## 🚀 快速开始

### 启动增强版GUI

```bash
./launch_enhanced.sh
```

或直接运行Python脚本：

```bash
python3 tools/launch_gui_enhanced.py
```

---

## 🎮 功能特性

### 1. 仿真器选择

支持两种仿真器：

**Gazebo Harmonic**
- 完整的物理仿真环境
- 支持ROS2集成
- 适合完整系统测试

**MuJoCo**
- 高性能物理引擎
- 适合强化学习训练
- 交互式可视化

### 2. 机器人模型配置

**模型文件夹选择**
- 自动扫描 `src/model/` 目录
- 支持自定义路径浏览
- 下拉菜单快速选择

**URDF文件选择**（Gazebo）
- 自动扫描模型的 `urdf/` 目录
- 列出所有可用的URDF文件
- 实时更新文件列表

**MJCF文件选择**（MuJoCo）
- 自动扫描模型的 `mjcf/` 目录
- 列出所有可用的MJCF文件
- 优先显示Wiki-MJCF版本

### 3. 世界环境配置

**默认世界**
- 使用内置的默认世界环境
- 包含地面、光源等基本元素

**自定义世界**
- 选择自定义世界文件
- 支持 `.world` 格式
- 浏览器选择文件

### 4. Gazebo选项

**启动模式**
- 安全模式 - 虚拟机推荐，禁用硬件加速
- 简单模式 - 快速测试，基础功能
- 标准模式 - 完整功能，物理机使用

**渲染选项**
- 强制软件渲染 - 解决闪屏问题
- 详细输出 - 显示调试信息

### 5. MuJoCo选项

**显示选项**
- 全屏模式 - 沉浸式体验
- 窗口模式 - 默认选项

**性能选项**
- 帧率设置 - 30-120 FPS可调
- 默认60 FPS

---

## 📁 项目结构要求

增强版GUI要求以下目录结构：

```
src/model/
├── RM_Serial_Wheeled-leg_Robot/
│   ├── urdf/
│   │   └── *.urdf
│   ├── mjcf/
│   │   └── *.xml
│   └── meshes/
│       └── *.STL
│
└── DM_Wheel_leg_robot/
    ├── urdf/
    │   └── *.urdf
    ├── mjcf/
    │   └── *.xml
    └── meshes/
        └── *.STL

src/wheel_legged_control/worlds/
└── *.world
```

---

## 🎯 使用流程

### 步骤1：选择仿真器

1. 打开增强版GUI
2. 在"仿真器选择"区域选择 Gazebo 或 MuJoCo

### 步骤2：配置机器人模型

1. 在"机器人模型"区域选择模型文件夹
2. 选择对应的URDF（Gazebo）或MJCF（MuJoCo）文件
3. 或点击"浏览..."按钮选择自定义路径

### 步骤3：配置世界环境（可选）

1. 勾选"使用默认世界环境"使用默认设置
2. 或取消勾选，选择自定义世界文件

### 步骤4：配置仿真选项

**Gazebo：**
- 选择启动模式（安全/简单/标准）
- 勾选软件渲染（如果遇到闪屏）
- 勾选详细输出（如果需要调试）

**MuJoCo：**
- 勾选全屏模式（可选）
- 设置目标帧率

### 步骤5：启动仿真

1. 点击"🚀 启动仿真"按钮
2. 确认配置信息
3. 等待仿真器启动

---

## 💡 使用技巧

### 快速切换模型

1. 使用下拉菜单快速切换不同机器人
2. 文件列表会自动更新

### 保存常用配置

- 记住常用的模型和选项组合
- 下次启动时快速选择

### 调试模式

1. 勾选"详细输出"
2. 查看终端窗口的详细日志
3. 帮助定位问题

### 性能优化

**Gazebo：**
- 虚拟机使用安全模式
- 物理机使用标准模式
- 遇到闪屏启用软件渲染

**MuJoCo：**
- 降低FPS提高稳定性
- 提高FPS获得更流畅体验
- 根据硬件性能调整

---

## 🔧 命令行替代方案

如果不使用GUI，也可以直接使用命令行：

### Gazebo

```bash
# 安全模式
./tools/launch_gazebo_safe.sh

# 简单模式
./tools/launch_gazebo_simple.sh

# 标准模式
./tools/launch_gazebo.sh
```

### MuJoCo

```bash
# 使用预设模型
python3 tools/launch_mujoco.py --model rm
python3 tools/launch_mujoco.py --model dm

# 使用自定义MJCF
python3 tools/launch_mujoco.py --mjcf path/to/model.xml

# 全屏模式
python3 tools/launch_mujoco.py --model rm --fullscreen

# 自定义帧率
python3 tools/launch_mujoco.py --model rm --fps 120
```

---

## ❓ 常见问题

### Q1: GUI无法启动？

**解决方案：**
```bash
sudo apt-get install python3-tk
```

### Q2: 找不到模型文件？

**检查：**
1. 模型文件夹是否在 `src/model/` 目录下
2. URDF文件是否在 `urdf/` 子目录
3. MJCF文件是否在 `mjcf/` 子目录

### Q3: MuJoCo提示未安装？

**解决方案：**
```bash
source venv/bin/activate
pip install mujoco -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q4: Gazebo闪屏？

**解决方案：**
1. 选择"安全模式"
2. 勾选"强制软件渲染"
3. 重新启动

### Q5: 如何添加新模型？

**步骤：**
1. 在 `src/model/` 创建新文件夹
2. 添加 `urdf/` 和 `mjcf/` 子目录
3. 放入对应的模型文件
4. 重启GUI，新模型会自动出现

---

## 🆚 GUI版本对比

| 特性 | 标准版 | 增强版 |
|------|--------|--------|
| 预设模型 | ✅ | ✅ |
| 自定义模型 | ❌ | ✅ |
| 文件浏览 | ❌ | ✅ |
| 世界文件选择 | ❌ | ✅ |
| MuJoCo支持 | ✅ | ✅ |
| 参数配置 | 基础 | 完整 |
| 界面大小 | 600x480 | 800x700 |

---

## 📚 相关文档

- [Gazebo完整指南](GAZEBO_GUIDE.md)
- [MuJoCo完整指南](MUJOCO_GUIDE.md)
- [快速开始](guides/START_HERE.md)
- [项目结构](guides/FILE_ORGANIZATION.md)

---

## 🎉 开始使用

```bash
./launch_enhanced.sh
```

享受更灵活的仿真配置体验！🚀

---

**更新日期**: 2026-02-09
**版本**: v1.0
