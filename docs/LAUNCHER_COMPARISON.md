# 启动器对比指南

## 📋 概述

本项目提供多种启动方式，适合不同的使用场景。

---

## 🎮 GUI启动器

### 增强版GUI（推荐）⭐⭐

**启动命令：**
```bash
./launch_enhanced.sh
```

**特点：**
- ✅ 完全自定义配置
- ✅ 选择任意模型文件夹
- ✅ 选择URDF/MJCF文件
- ✅ 选择世界文件
- ✅ 配置所有参数
- ✅ 文件浏览器支持
- ✅ 实时文件扫描

**适用场景：**
- 需要灵活配置
- 测试自定义模型
- 开发新功能
- 高级用户

**界面大小：** 800x700

**文档：** [增强版GUI使用指南](ENHANCED_GUI_GUIDE.md)

---

### 标准GUI

**启动命令：**
```bash
./launch.sh
```

**特点：**
- ✅ 简单易用
- ✅ 预设模型选择
- ✅ 基础参数配置
- ✅ 快速启动
- ⚠️ 仅支持预设模型

**适用场景：**
- 快速测试
- 初学者
- 标准使用场景

**界面大小：** 600x480

---

## 🖥️ 命令行启动

### Gazebo启动脚本

#### 安全模式（推荐虚拟机）

```bash
./tools/launch_gazebo_safe.sh
```

**特点：**
- 禁用硬件加速
- 软件渲染
- 兼容性最好
- 性能较低

#### 简单模式

```bash
./tools/launch_gazebo_simple.sh
```

**特点：**
- 基础功能
- 快速启动
- 适合测试

#### 标准模式

```bash
./tools/launch_gazebo.sh
```

**特点：**
- 完整功能
- 硬件加速
- 性能最好
- 需要物理机

---

### MuJoCo启动脚本

#### Shell脚本

```bash
./tools/launch_mujoco.sh
```

**特点：**
- 交互式选择模型
- 自动检查依赖
- 简单易用

#### Python脚本（推荐）

```bash
# 预设模型
python3 tools/launch_mujoco.py --model rm
python3 tools/launch_mujoco.py --model dm

# 自定义MJCF
python3 tools/launch_mujoco.py --mjcf path/to/model.xml

# 全屏模式
python3 tools/launch_mujoco.py --model rm --fullscreen

# 自定义帧率
python3 tools/launch_mujoco.py --model rm --fps 120
```

**特点：**
- 完整参数支持
- 灵活配置
- 适合脚本调用

---

## 📊 功能对比表

| 功能 | 增强版GUI | 标准GUI | Gazebo脚本 | MuJoCo脚本 |
|------|-----------|---------|------------|------------|
| **易用性** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **灵活性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| **自定义模型** | ✅ | ❌ | ❌ | ✅ |
| **文件浏览** | ✅ | ❌ | ❌ | ❌ |
| **世界文件选择** | ✅ | ❌ | ❌ | N/A |
| **参数配置** | 完整 | 基础 | 固定 | 完整 |
| **Gazebo支持** | ✅ | ✅ | ✅ | ❌ |
| **MuJoCo支持** | ✅ | ✅ | ❌ | ✅ |
| **脚本调用** | ❌ | ❌ | ✅ | ✅ |

---

## 🎯 使用建议

### 场景1：日常使用

**推荐：** 标准GUI
```bash
./launch.sh
```

**原因：**
- 简单快速
- 满足大部分需求
- 界面友好

---

### 场景2：开发测试

**推荐：** 增强版GUI
```bash
./launch_enhanced.sh
```

**原因：**
- 灵活配置
- 支持自定义模型
- 快速切换文件

---

### 场景3：虚拟机环境

**推荐：** Gazebo安全模式
```bash
./tools/launch_gazebo_safe.sh
```

**原因：**
- 兼容性最好
- 解决闪屏问题
- 稳定可靠

---

### 场景4：强化学习训练

**推荐：** MuJoCo Python脚本
```bash
python3 tools/launch_mujoco.py --model rm --fps 120
```

**原因：**
- 高性能
- 可编程控制
- 适合批量运行

---

### 场景5：自动化脚本

**推荐：** 命令行脚本
```bash
# Gazebo
./tools/launch_gazebo_simple.sh

# MuJoCo
python3 tools/launch_mujoco.py --model rm
```

**原因：**
- 无需GUI
- 易于集成
- 支持参数传递

---

## 🔄 快速切换

### 从标准GUI升级到增强版

1. 关闭标准GUI
2. 运行 `./launch_enhanced.sh`
3. 享受更多功能

### 从GUI切换到命令行

1. 记住GUI中的配置
2. 使用对应的命令行参数
3. 编写脚本自动化

---

## 💡 高级技巧

### 技巧1：创建快捷方式

```bash
# 添加到 ~/.bashrc
alias sim-gui='cd ~/workspace/"Wheel-Legged Robot Digital Twin Control Platform" && ./launch_enhanced.sh'
alias sim-gazebo='cd ~/workspace/"Wheel-Legged Robot Digital Twin Control Platform" && ./tools/launch_gazebo_safe.sh'
alias sim-mujoco='cd ~/workspace/"Wheel-Legged Robot Digital Twin Control Platform" && python3 tools/launch_mujoco.py --model rm'
```

### 技巧2：批处理脚本

```bash
#!/bin/bash
# 批量测试脚本

# 测试RM机器人
python3 tools/launch_mujoco.py --model rm --fps 60 &
PID1=$!

# 等待5秒
sleep 5

# 测试DM机器人
python3 tools/launch_mujoco.py --model dm --fps 60 &
PID2=$!

# 等待用户输入
read -p "按Enter结束..."

# 关闭进程
kill $PID1 $PID2
```

### 技巧3：环境变量配置

```bash
# 设置默认仿真器
export DEFAULT_SIMULATOR="mujoco"

# 设置默认模型
export DEFAULT_MODEL="rm"

# 设置默认FPS
export DEFAULT_FPS="120"
```

---

## 📚 相关文档

- [增强版GUI使用指南](ENHANCED_GUI_GUIDE.md)
- [Gazebo完整指南](GAZEBO_GUIDE.md)
- [MuJoCo完整指南](MUJOCO_GUIDE.md)
- [快速开始](guides/START_HERE.md)

---

## 🆘 故障排除

### 问题1：GUI无法启动

**解决方案：**
```bash
sudo apt-get install python3-tk
```

### 问题2：找不到模型

**检查：**
1. 模型是否在 `src/model/` 目录
2. 是否有 `urdf/` 或 `mjcf/` 子目录
3. 文件扩展名是否正确

### 问题3：MuJoCo不可用

**解决方案：**
```bash
source venv/bin/activate
pip install mujoco -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题4：Gazebo闪屏

**解决方案：**
1. 使用安全模式
2. 启用软件渲染
3. 检查显卡驱动

---

## 🎉 总结

| 用户类型 | 推荐启动器 | 命令 |
|---------|-----------|------|
| 初学者 | 标准GUI | `./launch.sh` |
| 开发者 | 增强版GUI | `./launch_enhanced.sh` |
| 虚拟机用户 | Gazebo安全模式 | `./tools/launch_gazebo_safe.sh` |
| 研究人员 | MuJoCo脚本 | `python3 tools/launch_mujoco.py` |
| 自动化 | 命令行脚本 | 各种脚本 |

选择适合你的启动方式，开始探索轮腿机器人的世界！🚀

---

**更新日期**: 2026-02-09
**版本**: v1.0
