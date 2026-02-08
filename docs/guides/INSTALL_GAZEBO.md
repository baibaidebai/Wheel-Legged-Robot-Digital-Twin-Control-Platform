# Gazebo完整安装指南

## 问题诊断

你的系统只安装了部分Gazebo组件，缺少仿真器 `gz-sim`。

## 🔧 解决方案：安装完整的Gazebo

### 方法1：安装Gazebo Harmonic（推荐）

```bash
# 添加Gazebo仓库
sudo wget https://packages.osrfoundation.org/gazebo.gpg -O /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null

# 更新并安装
sudo apt-get update
sudo apt-get install gz-harmonic
```

### 方法2：通过ROS2安装（简单）

```bash
sudo apt-get update
sudo apt-get install ros-jazzy-ros-gz-sim
```

### 方法3：安装所有ROS2 Gazebo包

```bash
sudo apt-get update
sudo apt-get install ros-jazzy-ros-gz
```

## ✅ 验证安装

安装完成后，验证：

```bash
# 检查gz sim命令
gz sim --version

# 应该显示类似：
# Gazebo Sim, version 8.x.x
```

## 🚀 安装后启动

```bash
./launch_gazebo.sh
```

## 📝 详细步骤

### 1. 安装Gazebo

选择上面的任一方法安装。推荐**方法2**（最简单）：

```bash
sudo apt-get update
sudo apt-get install ros-jazzy-ros-gz-sim
```

### 2. 验证安装

```bash
gz sim --version
```

如果显示版本号，说明安装成功。

### 3. 启动仿真

```bash
./launch_gazebo.sh
```

### 4. 查看机器人

Gazebo窗口会打开，显示3D世界和你的机器人模型。

## 🔍 故障排除

### 问题1：gz sim命令不存在

**解决**：
```bash
sudo apt-get install ros-jazzy-ros-gz-sim
```

### 问题2：仓库无法访问

**解决**：使用ROS2方法安装：
```bash
sudo apt-get install ros-jazzy-ros-gz
```

### 问题3：依赖问题

**解决**：
```bash
sudo apt-get update
sudo apt-get install -f
sudo apt-get install ros-jazzy-ros-gz-sim
```

## 💡 推荐安装命令（一键）

```bash
# 最简单的方法
sudo apt-get update && sudo apt-get install -y ros-jazzy-ros-gz-sim

# 验证
gz sim --version

# 启动
./launch_gazebo.sh
```

## 📚 更多信息

- [Gazebo官方文档](https://gazebosim.org/)
- [ROS2 Gazebo集成](https://github.com/gazebosim/ros_gz)

## 🎯 下一步

安装完成后：

1. 运行 `./launch_gazebo.sh`
2. 选择机器人模型
3. 享受仿真！

---

**现在就安装Gazebo吧！** 🚀
