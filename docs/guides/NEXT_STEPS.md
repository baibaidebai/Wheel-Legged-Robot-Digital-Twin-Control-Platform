# 下一步操作指南

## 🎯 当前问题

你运行 `./launch_gazebo.sh` 后Gazebo窗口没有打开，原因是：

**你的系统只安装了部分Gazebo组件（gz命令），但缺少核心仿真器（gz-sim）**

## 🔍 诊断（可选）

运行诊断脚本查看详细信息：

```bash
./check_gazebo.sh
```

## ✅ 解决方案（两步）

### 第一步：安装Gazebo仿真器

**方法A：自动安装（最简单）** ⭐

```bash
./install_gazebo.sh
```

这个脚本会：
1. 检查Gazebo是否已安装
2. 自动安装 `ros-jazzy-ros-gz-sim`
3. 验证安装是否成功

**方法B：手动安装**

```bash
sudo apt-get update
sudo apt-get install ros-jazzy-ros-gz-sim
```

**方法C：安装完整版（包含所有功能）**

```bash
sudo apt-get update
sudo apt-get install ros-jazzy-ros-gz
```

**验证安装**：
```bash
gz sim --version
```

应该显示：`Gazebo Sim, version 8.x.x`

如果显示版本号，说明安装成功！✅

---

### 第二步：启动仿真

```bash
./launch_gazebo.sh
```

选择你的机器人模型（1或2），Gazebo窗口会打开并显示3D机器人。

---

## 📚 详细文档

- **安装指南**: [INSTALL_GAZEBO.md](INSTALL_GAZEBO.md)
- **快速开始**: [GAZEBO_QUICKSTART.md](GAZEBO_QUICKSTART.md)
- **项目README**: [README.md](README.md)

---

## 🔧 故障排除

### 问题：安装失败

**解决**：
```bash
sudo apt-get update
sudo apt-get install -f
sudo apt-get install ros-jazzy-ros-gz-sim
```

### 问题：gz sim命令不存在

**解决**：
```bash
# 确保ROS2环境已加载
source /opt/ros/jazzy/setup.bash

# 重新安装
sudo apt-get install ros-jazzy-ros-gz-sim
```

### 问题：依赖冲突

**解决**：
```bash
sudo apt-get autoremove
sudo apt-get update
sudo apt-get install ros-jazzy-ros-gz-sim
```

---

## 🎉 完整流程

```
┌─────────────────────────────────────────┐
│  1️⃣  诊断（可选）                        │
│  ./check_gazebo.sh                      │
│  查看当前安装状态                        │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  2️⃣  安装Gazebo                          │
│  ./install_gazebo.sh                    │
│  或                                      │
│  sudo apt-get install ros-jazzy-ros-gz-sim │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  3️⃣  验证安装                            │
│  gz sim --version                       │
│  应该显示: Gazebo Sim, version 8.x.x    │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  4️⃣  启动仿真                            │
│  ./launch_gazebo.sh                     │
│  选择模型（1或2）                        │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  5️⃣  Gazebo窗口打开！                    │
│  🎉 看到3D机器人仿真环境                 │
└─────────────────────────────────────────┘
```

---

## 💡 提示

- 安装过程需要sudo权限
- 安装大约需要几分钟
- 确保网络连接正常
- 安装完成后可以立即使用

---

## 📞 需要帮助？

如果遇到问题：

1. 查看 [INSTALL_GAZEBO.md](INSTALL_GAZEBO.md)
2. 检查错误信息
3. 确认ROS2环境已加载
4. 尝试重新安装

---

## 🚀 现在就开始

```bash
./install_gazebo.sh
```

然后

```bash
./launch_gazebo.sh
```

**开始你的机器人仿真之旅！** 🤖✨
