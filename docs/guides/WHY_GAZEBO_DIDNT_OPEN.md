# 为什么Gazebo窗口没有打开？

## 🤔 你遇到的问题

运行 `./launch_gazebo.sh` 后，看到了很多输出信息，但**Gazebo窗口没有打开**。

最后显示的是 `gz` 命令的帮助信息，而不是仿真窗口。

## 🔍 问题原因

你的系统安装了**部分Gazebo组件**，但缺少**核心仿真器**。

### 技术细节

你的系统有这些包：
- ✅ `gz` 命令（Gazebo命令行工具）
- ✅ `gz-tools`（工具包）
- ✅ `gz-math`（数学库）
- ✅ `gz-utils`（实用工具）

但是缺少：
- ❌ `gz-sim`（**仿真器核心**）

这就像：
- 你有遥控器（gz命令）
- 你有说明书（gz-tools）
- 你有电池（gz-math, gz-utils）
- 但是**没有电视机**（gz-sim仿真器）

所以当你运行 `./launch_gazebo.sh` 时：
1. 脚本检测到 `gz` 命令存在 ✅
2. 脚本尝试运行 `gz sim` 启动仿真器
3. 但是 `gz sim` 不存在 ❌
4. 所以只显示了 `gz` 的帮助信息

## ✅ 解决方案

### 方法1：自动安装（最简单）⭐

```bash
./install_gazebo.sh
```

这个脚本会：
1. 检查是否已安装
2. 自动安装 `ros-jazzy-ros-gz-sim`（包含gz-sim）
3. 验证安装成功

### 方法2：手动安装

```bash
sudo apt-get update
sudo apt-get install ros-jazzy-ros-gz-sim
```

这会安装：
- `gz-sim`（仿真器核心）
- ROS2与Gazebo的集成包
- 所有必要的依赖

### 方法3：安装完整版（推荐用于开发）

```bash
sudo apt-get update
sudo apt-get install ros-jazzy-ros-gz
```

这会安装所有ROS2 Gazebo包，包括：
- 仿真器
- 传感器插件
- 控制器插件
- 可视化工具

## 🎯 验证安装

安装完成后，运行：

```bash
gz sim --version
```

**成功的输出**：
```
Gazebo Sim, version 8.6.0
Copyright (C) 2018 Open Source Robotics Foundation.
Released under the Apache 2.0 License.
```

**失败的输出**：
```
gz: command not found
```
或
```
gz: 'sim' is not a gz command. See 'gz help'.
```

## 🚀 安装后启动

```bash
./launch_gazebo.sh
```

现在你会看到：
1. ✅ 脚本检测到Gazebo已安装
2. ✅ 选择机器人模型
3. ✅ **Gazebo窗口打开**
4. ✅ 显示3D仿真环境

## 📊 安装前后对比

### 安装前
```bash
$ gz sim --version
gz: 'sim' is not a gz command. See 'gz help'.
```

### 安装后
```bash
$ gz sim --version
Gazebo Sim, version 8.6.0
```

## 🔧 故障排除

### 问题1：安装失败

```bash
# 更新软件源
sudo apt-get update

# 修复依赖
sudo apt-get install -f

# 重试安装
sudo apt-get install ros-jazzy-ros-gz-sim
```

### 问题2：网络问题

如果下载速度慢或失败：
1. 检查网络连接
2. 尝试更换软件源镜像
3. 使用代理（如果需要）

### 问题3：权限问题

确保：
1. 使用 `sudo` 命令
2. 输入正确的密码
3. 你的用户有管理员权限

## 💡 快速命令总结

```bash
# 1. 诊断（可选）
./check_gazebo.sh

# 2. 安装
./install_gazebo.sh

# 3. 验证
gz sim --version

# 4. 启动
./launch_gazebo.sh
```

## 📚 相关文档

- [简单安装指南](GAZEBO_INSTALL_SIMPLE.md) - 3分钟快速安装
- [完整安装指南](INSTALL_GAZEBO.md) - 详细步骤
- [下一步操作](NEXT_STEPS.md) - 安装后做什么
- [快速开始](GAZEBO_QUICKSTART.md) - 使用指南

## 🎉 总结

**问题**：缺少 `gz-sim` 仿真器

**解决**：运行 `./install_gazebo.sh`

**结果**：Gazebo窗口会打开，显示3D机器人仿真

---

## 现在就安装！

```bash
./install_gazebo.sh
```

3分钟后，你就可以看到Gazebo仿真窗口了！🤖✨
