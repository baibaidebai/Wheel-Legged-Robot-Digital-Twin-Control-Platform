# Gazebo闪屏问题解决方案

## 🚨 问题描述

Gazebo窗口打开后：
- 屏幕一直闪烁
- 看不到机器人模型
- 界面不稳定

## 🔍 问题原因

这是**虚拟机环境**中常见的OpenGL渲染问题：
- VMware虚拟机的3D加速不完全兼容Gazebo
- 硬件加速渲染导致闪屏
- 显存分配不足

## ✅ 解决方案

### 方案1：使用安全模式启动（推荐）⭐

```bash
./launch_gazebo_safe.sh
```

这个脚本会：
- 使用软件渲染（LIBGL_ALWAYS_SOFTWARE=1）
- 禁用硬件加速
- 关闭阴影效果
- 自动加载机器人模型

### 方案2：使用简单模式启动

```bash
./launch_gazebo_simple.sh
```

更简单的启动方式，直接加载机器人。

### 方案3：手动设置环境变量

```bash
# 设置软件渲染
export LIBGL_ALWAYS_SOFTWARE=1
export MESA_GL_VERSION_OVERRIDE=3.3
export GALLIUM_DRIVER=llvmpipe

# 启动Gazebo
./launch_gazebo.sh
```

### 方案4：增加虚拟机显存

1. 关闭虚拟机
2. 打开VMware设置
3. 显示器 → 3D图形 → 显存
4. 增加到至少 **2GB**
5. 启用 "加速3D图形"
6. 重启虚拟机

### 方案5：使用无头模式（仅后台仿真）

如果只需要物理仿真，不需要可视化：

```bash
gz sim robot_world.sdf --headless-rendering
```

## 🎯 推荐配置

### VMware虚拟机设置

1. **显存**: 2GB 或更多
2. **3D加速**: 启用
3. **显示器数量**: 1个
4. **分辨率**: 1920x1080 或更低

### Ubuntu设置

```bash
# 检查OpenGL版本
glxinfo | grep "OpenGL version"

# 应该显示至少 OpenGL 3.3
```

## 🔧 详细步骤

### 步骤1：尝试安全模式

```bash
./launch_gazebo_safe.sh
```

选择机器人模型，等待窗口打开。

### 步骤2：如果仍然闪屏

关闭Gazebo，增加虚拟机显存：

1. 关闭虚拟机
2. VMware → 虚拟机 → 设置
3. 硬件 → 显示器
4. 3D图形内存：2048 MB
5. 确定并重启

### 步骤3：重新启动

```bash
./launch_gazebo_safe.sh
```

应该不再闪屏。

## 📊 性能对比

### 硬件渲染（闪屏）
- ✅ 性能高
- ❌ 虚拟机中不稳定
- ❌ 闪屏问题

### 软件渲染（安全模式）
- ✅ 稳定，不闪屏
- ✅ 虚拟机兼容性好
- ⚠️  性能较低（可接受）

## 💡 使用技巧

### 如果机器人看不见

1. **缩小视角**：鼠标滚轮向后滚
2. **切换视图**：按数字键 `2`（正交视图）
3. **重置视角**：右键 → Reset View
4. **查找机器人**：左侧面板 → Entity Tree → robot

### 如果性能太慢

1. 关闭阴影：Edit → Preferences → Rendering → Shadows: Off
2. 降低分辨率：虚拟机设置 → 显示器 → 1280x720
3. 减少物理精度：修改world文件中的max_step_size

## 🚀 快速命令

```bash
# 方法1：安全模式（推荐）
./launch_gazebo_safe.sh

# 方法2：简单模式
./launch_gazebo_simple.sh

# 方法3：手动设置
export LIBGL_ALWAYS_SOFTWARE=1
./launch_gazebo.sh
```

## 🔍 故障排除

### 问题1：仍然闪屏

**解决**：
```bash
# 完全禁用硬件加速
export LIBGL_ALWAYS_SOFTWARE=1
export MESA_GL_VERSION_OVERRIDE=3.3
export GALLIUM_DRIVER=llvmpipe
export OGRE_RTT_MODE=Copy

./launch_gazebo_safe.sh
```

### 问题2：窗口黑屏

**解决**：
```bash
# 检查OpenGL支持
glxinfo | grep "OpenGL"

# 如果没有glxinfo，安装它
sudo apt-get install mesa-utils

# 重新启动
./launch_gazebo_safe.sh
```

### 问题3：性能太慢

**解决**：
- 增加虚拟机CPU核心数（至少2核）
- 增加虚拟机内存（至少4GB）
- 关闭其他应用程序

### 问题4：机器人不显示

**解决**：
```bash
# 使用简单模式，直接加载机器人
./launch_gazebo_simple.sh
```

## 📚 相关文档

- [START_HERE.md](START_HERE.md) - 快速开始
- [INSTALL_GAZEBO.md](INSTALL_GAZEBO.md) - 安装指南
- [GAZEBO_QUICKSTART.md](GAZEBO_QUICKSTART.md) - 使用指南

## 🎉 总结

**问题**：Gazebo闪屏，看不到模型

**原因**：虚拟机OpenGL渲染问题

**解决**：使用软件渲染模式

**命令**：
```bash
./launch_gazebo_safe.sh
```

---

**现在就试试安全模式！** 🚀
