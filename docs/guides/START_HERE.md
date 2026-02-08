# 🚀 从这里开始

## 欢迎使用轮腿机器人孪生控制系统！

这是一个快速指南，帮助你在3分钟内启动Gazebo仿真。

---

## 📋 你需要做什么？

### 步骤1：安装Gazebo仿真器（首次使用必须）

运行这个命令：

```bash
./install_gazebo.sh
```

- 按 `y` 确认
- 等待3分钟安装完成
- 看到 "✅ Gazebo安装成功!" 就完成了

### 步骤2：验证安装

```bash
gz sim --version
```

如果显示版本号（例如：`Gazebo Sim, version 8.6.0`），说明安装成功！✅

### 步骤3：启动仿真

```bash
./launch_gazebo.sh
```

- 选择机器人模型（输入 `1` 或 `2`）
- Gazebo窗口会打开
- 你会看到3D仿真环境！

---

## 🎯 预期效果

安装成功后，你会看到：

1. **Gazebo窗口** - 一个3D仿真环境
2. **地面平面** - 灰色的地面
3. **光照效果** - 真实的阴影
4. **控制界面** - 可以控制视角

---

## 🚨 遇到问题？

### 问题1：Gazebo窗口没有打开

**原因**：缺少Gazebo仿真器

**解决**：运行 `./install_gazebo.sh`

**详细说明**：[WHY_GAZEBO_DIDNT_OPEN.md](WHY_GAZEBO_DIDNT_OPEN.md)

### 问题2：安装失败

**解决**：
```bash
sudo apt-get update
sudo apt-get install -f
sudo apt-get install ros-jazzy-ros-gz-sim
```

### 问题3：不确定是否安装成功

**运行诊断**：
```bash
./check_gazebo.sh
```

这会显示详细的安装状态。

---

## 📚 文档导航

### 快速参考
- [快速修复](QUICK_FIX.md) - 1分钟解决问题 ⭐
- [为什么没有打开？](WHY_GAZEBO_DIDNT_OPEN.md) - 详细解释

### 安装指南
- [简单安装](GAZEBO_INSTALL_SIMPLE.md) - 3分钟快速安装 ⭐
- [完整安装](INSTALL_GAZEBO.md) - 详细步骤和故障排除
- [下一步操作](NEXT_STEPS.md) - 安装后做什么

### 使用指南
- [Gazebo快速开始](GAZEBO_QUICKSTART.md) - 如何使用仿真器
- [项目README](README.md) - 完整项目文档
- [项目状态](PROJECT_STATUS.md) - 开发进度

### 工具
- [诊断脚本](check_gazebo.sh) - 检查安装状态
- [安装脚本](install_gazebo.sh) - 自动安装
- [启动脚本](launch_gazebo.sh) - 启动仿真

---

## 🎓 学习路径

### 第一天：安装和启动
1. 运行 `./install_gazebo.sh`
2. 运行 `./launch_gazebo.sh`
3. 熟悉Gazebo界面

### 第二天：探索功能
1. 查看机器人模型
2. 尝试控制视角
3. 了解仿真参数

### 第三天：运行演示
1. 运行 `python3 scripts/demo_lqr_controller.py`
2. 运行 `python3 scripts/demo_data_recorder.py`
3. 查看实验数据

---

## 💡 快速命令

```bash
# 诊断
./check_gazebo.sh

# 安装
./install_gazebo.sh

# 验证
gz sim --version

# 启动
./launch_gazebo.sh
```

---

## 🎉 现在就开始！

### 第一步：安装

```bash
./install_gazebo.sh
```

### 第二步：启动

```bash
./launch_gazebo.sh
```

### 第三步：享受仿真！

看到Gazebo窗口打开，你就成功了！🤖✨

---

## 📞 需要帮助？

- 查看 [快速修复](QUICK_FIX.md)
- 查看 [故障排除](WHY_GAZEBO_DIDNT_OPEN.md)
- 运行 `./check_gazebo.sh` 诊断
- 查看 [完整文档](README.md)

---

**祝你使用愉快！** 🚀
