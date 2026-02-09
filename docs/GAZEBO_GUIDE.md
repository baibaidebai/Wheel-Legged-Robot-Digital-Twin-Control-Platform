# Gazebo 仿真完整指南

## 📋 目录

1. [快速开始](#快速开始)
2. [安装 Gazebo](#安装-gazebo)
3. [启动仿真](#启动仿真)
4. [常见问题](#常见问题)
5. [故障排除](#故障排除)

---

## 快速开始

### 一键启动（推荐）

```bash
# 方法 1：GUI 启动器
./launch.sh

# 方法 2：命令行启动（安全模式）
./tools/launch_gazebo_safe.sh
```

---

## 安装 Gazebo

### 自动安装（推荐）

```bash
./tools/install_gazebo.sh
```

### 手动安装

```bash
# 安装 Gazebo Harmonic
sudo apt-get update
sudo apt-get install gz-harmonic

# 或安装 ROS2 集成版本
sudo apt-get install ros-jazzy-ros-gz
```

### 验证安装

```bash
./tools/check_gazebo.sh
```

---

## 启动仿真

### 方法 1：GUI 启动器（推荐）⭐

```bash
./launch.sh
```

**功能**：
- 选择机器人模型（RM 或 DM）
- 选择仿真器（Gazebo 或 MuJoCo）
- 选择启动模式（安全/简单/标准）
- 配置高级选项

### 方法 2：命令行启动

```bash
# 安全模式（推荐虚拟机）
./tools/launch_gazebo_safe.sh

# 简单模式
./tools/launch_gazebo_simple.sh

# 标准模式
./tools/launch_gazebo.sh
```

### 方法 3：Python 脚本

```bash
python3 tools/launch_gazebo_gui.py
```

---

## 常见问题

### Q1: Gazebo 窗口没有打开？

**快速修复**：
```bash
# 1. 检查 Gazebo 安装
./tools/check_gazebo.sh

# 2. 使用安全模式启动
./tools/launch_gazebo_safe.sh
```

**详细排查**：
1. 检查 Gazebo 是否安装
2. 检查 OpenGL 支持
3. 尝试不同的启动模式

### Q2: Gazebo 闪屏/看不到模型？

**原因**：虚拟机 OpenGL 兼容性问题

**解决方案**：
```bash
# 使用安全模式（禁用硬件加速）
./tools/launch_gazebo_safe.sh
```

**或在 VMware 中**：
1. 虚拟机设置 → 显示
2. 启用"加速 3D 图形"
3. 分配足够的显存（建议 2GB+）

### Q3: DM 机器人无法加载？

**解决方案**：
```bash
python3 tools/fix_dm_urdf.py
```

---

## 故障排除

### 问题 1：Gazebo 未安装

**错误信息**：
```
gz: command not found
```

**解决方案**：
```bash
./tools/install_gazebo.sh
```

### 问题 2：OpenGL 错误

**错误信息**：
```
OpenGL error: ...
```

**解决方案**：
```bash
# 检查 OpenGL
./tools/check_opengl.sh

# 使用安全模式
./tools/launch_gazebo_safe.sh
```

### 问题 3：URDF 加载失败

**错误信息**：
```
Failed to load URDF
```

**解决方案**：
```bash
# 修复 DM 机器人
python3 tools/fix_dm_urdf.py

# 验证 URDF
python3 scripts/validate_urdf_models.py
```

---

## 启动模式对比

| 模式 | 特点 | 适用场景 |
|------|------|---------|
| **安全模式** | 禁用硬件加速 | 虚拟机、兼容性问题 |
| **简单模式** | 基础功能 | 快速测试 |
| **标准模式** | 完整功能 | 物理机、正常使用 |

---

## 工具说明

### 安装工具

- **`install_gazebo.sh`** - 自动安装 Gazebo
- **`check_gazebo.sh`** - 检查 Gazebo 安装状态
- **`check_opengl.sh`** - 检查 OpenGL 支持

### 启动工具

- **`launch.sh`** - GUI 启动器（推荐）
- **`launch_gazebo_safe.sh`** - 安全模式启动
- **`launch_gazebo_simple.sh`** - 简单模式启动
- **`launch_gazebo.sh`** - 标准模式启动
- **`launch_gazebo_gui.py`** - Python GUI 启动器

### 修复工具

- **`fix_dm_urdf.py`** - 修复 DM 机器人 URDF
- **`validate_urdf_models.py`** - 验证 URDF 模型

---

## 系统要求

- **操作系统**：Ubuntu 24.04 LTS
- **ROS2**：Jazzy
- **Gazebo**：Harmonic
- **Python**：3.12+

---

## 参考资料

- [Gazebo 官方文档](https://gazebosim.org/docs)
- [ROS2 Gazebo 集成](https://github.com/ros-simulation/gazebo_ros_pkgs)

---

## 更新日志

### 2026-02-09

- ✅ 整合 Gazebo 相关文档
- ✅ 简化安装流程
- ✅ 统一启动方式

---

**提示**：本指南整合了以下文档的内容：
- `guides/GAZEBO_QUICKSTART.md`
- `guides/INSTALL_GAZEBO.md`
- `guides/GAZEBO_INSTALL_SIMPLE.md`
- `guides/QUICK_FIX.md`
- `guides/GAZEBO_FLICKERING_FIX.md`
- `guides/WHY_GAZEBO_DIDNT_OPEN.md`
