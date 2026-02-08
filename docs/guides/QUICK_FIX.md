# 🚨 快速修复：Gazebo窗口没有打开

## 问题
运行 `./launch_gazebo.sh` 后，Gazebo窗口没有打开。

## 原因
缺少Gazebo仿真器（gz-sim）。

## 解决（1分钟）

### 运行这个命令：

```bash
./install_gazebo.sh
```

按 `y` 确认，等待3分钟。

### 或者手动安装：

```bash
sudo apt-get update && sudo apt-get install -y ros-jazzy-ros-gz-sim
```

## 验证

```bash
gz sim --version
```

看到版本号 = 成功 ✅

## 启动

```bash
./launch_gazebo.sh
```

Gazebo窗口会打开！🎉

---

## 详细文档

- [为什么没有打开？](WHY_GAZEBO_DIDNT_OPEN.md) - 详细解释
- [简单安装指南](GAZEBO_INSTALL_SIMPLE.md) - 3分钟安装
- [完整安装指南](INSTALL_GAZEBO.md) - 详细步骤
- [诊断工具](check_gazebo.sh) - 检查状态

---

**现在就运行：**

```bash
./install_gazebo.sh
```
