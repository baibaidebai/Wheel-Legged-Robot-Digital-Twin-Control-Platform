# Gazebo安装 - 简单版

## 🚨 问题

运行 `./launch_gazebo.sh` 后，Gazebo窗口没有打开。

## 🔍 原因

你的系统有 `gz` 命令，但**没有 `gz sim` 仿真器**。

就像你有一个遥控器（gz命令），但没有电视机（gz sim仿真器）。

## ✅ 解决方法（3分钟）

### 一键安装（推荐）

```bash
./install_gazebo.sh
```

按 `y` 确认，等待安装完成。

### 手动安装

```bash
sudo apt-get update
sudo apt-get install ros-jazzy-ros-gz-sim
```

输入密码，等待安装。

## 🎯 验证

安装完成后，运行：

```bash
gz sim --version
```

如果显示版本号（例如：`Gazebo Sim, version 8.6.0`），说明安装成功！✅

## 🚀 启动仿真

```bash
./launch_gazebo.sh
```

选择机器人模型（输入 `1` 或 `2`），Gazebo窗口会打开！

## 📸 预期效果

安装成功后，你会看到：

1. **Gazebo窗口打开** - 3D仿真环境
2. **地面平面** - 灰色的地面
3. **光照效果** - 真实的阴影和光照
4. **机器人模型** - 你的轮腿机器人（需要在另一个终端加载）

## 🔧 如果安装失败

### 错误1：网络问题

```bash
# 更新软件源
sudo apt-get update

# 重试安装
sudo apt-get install ros-jazzy-ros-gz-sim
```

### 错误2：依赖问题

```bash
# 修复依赖
sudo apt-get install -f

# 重试安装
sudo apt-get install ros-jazzy-ros-gz-sim
```

### 错误3：权限问题

确保使用 `sudo` 命令，并输入正确的密码。

## 💡 快速命令

```bash
# 1. 安装
./install_gazebo.sh

# 2. 验证
gz sim --version

# 3. 启动
./launch_gazebo.sh
```

## 📞 需要帮助？

- 查看详细文档：[INSTALL_GAZEBO.md](INSTALL_GAZEBO.md)
- 运行诊断：`./check_gazebo.sh`
- 查看快速开始：[GAZEBO_QUICKSTART.md](GAZEBO_QUICKSTART.md)

---

## 🎉 现在就安装

```bash
./install_gazebo.sh
```

3分钟后，你就可以看到3D机器人仿真了！🤖✨
