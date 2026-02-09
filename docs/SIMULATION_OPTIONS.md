# 仿真选项指南

## 🎯 你有三个选择

根据你的需求和环境，选择最适合的仿真方式：

---

## 选项1: Gazebo（推荐用于URDF模型）⭐

### ✅ 优势
- **完美支持URDF** - 直接加载你的机器人模型，无需转换
- **支持STL网格** - 显示真实的机器人外观
- **ROS标准** - 与ROS生态系统无缝集成
- **功能丰富** - 传感器、插件、物理引擎

### 📦 安装

```bash
sudo apt-get update
sudo apt-get install gazebo11 libgazebo11-dev
```

### 🚀 启动

```bash
./launch_gazebo.sh
```

### 📖 详细文档
查看 `GAZEBO_GUIDE.md`

---

## 选项2: MuJoCo（推荐用于强化学习）

### ✅ 优势
- **高性能** - 快速物理仿真
- **强化学习** - 专为RL优化
- **简洁** - 轻量级，易于使用

### ⚠️ 限制
- **URDF支持有限** - 对mesh路径处理严格
- **需要转换** - 复杂模型可能需要手动调整

### 🚀 启动

```bash
./launch_mujoco.sh
```

然后选择：
- **选项3**: 简化模型（推荐，可以正常显示）
- 选项1/2: URDF模型（可能只显示方块）

### 📖 详细文档
查看 `MUJOCO_DIRECT_GUIDE.md`

---

## 选项3: PyQt5 GUI（不推荐）

### ⚠️ 问题
- OpenGL渲染问题
- 黑屏
- 虚拟机环境不稳定

### 💡 建议
使用选项1（Gazebo）或选项2（MuJoCo）代替

---

## 🎯 快速决策

### 我想看到真实的机器人模型（STL网格）
→ **使用Gazebo**（选项1）

### 我想快速测试仿真功能
→ **使用MuJoCo简化模型**（选项2，选择3）

### 我要做强化学习训练
→ **使用MuJoCo**（选项2）

### 我要与ROS集成
→ **使用Gazebo**（选项1）

---

## 📊 详细对比

| 特性 | Gazebo | MuJoCo | PyQt5 GUI |
|------|--------|--------|-----------|
| URDF支持 | ✅ 完美 | ⚠️ 有限 | ⚠️ 有限 |
| STL网格 | ✅ 支持 | ⚠️ 需转换 | ❌ 不支持 |
| 性能 | 中等 | ⭐ 高 | 低 |
| ROS集成 | ✅ 原生 | ❌ 需桥接 | ⚠️ 有限 |
| 稳定性 | ✅ 高 | ✅ 高 | ❌ 低 |
| 学习曲线 | 平缓 | 中等 | 简单 |
| 虚拟机支持 | ✅ 好 | ✅ 好 | ❌ 差 |

---

## 🚀 立即开始

### 方案A: 使用Gazebo（推荐）

```bash
# 1. 安装Gazebo
sudo apt-get update
sudo apt-get install gazebo11 libgazebo11-dev

# 2. 启动仿真
./launch_gazebo.sh

# 3. 选择你的机器人模型（1或2）
```

### 方案B: 使用MuJoCo

```bash
# 1. 启动仿真
./launch_mujoco.sh

# 2. 选择简化模型（3）
```

---

## 💡 常见问题

### Q: 为什么MuJoCo不能正确显示我的URDF模型？

A: MuJoCo对URDF中的mesh路径处理比较严格。你的URDF使用相对路径`../meshes/`，MuJoCo解析时会有问题。建议：
- 使用Gazebo（完美支持）
- 或使用MuJoCo的简化模型

### Q: Gazebo和MuJoCo哪个更好？

A: 取决于你的需求：
- **开发和测试机器人** → Gazebo
- **强化学习训练** → MuJoCo
- **需要真实外观** → Gazebo
- **需要高性能** → MuJoCo

### Q: 可以同时使用两个吗？

A: 可以！它们各有优势：
- 用Gazebo开发和可视化
- 用MuJoCo训练强化学习
- 两者可以共享URDF模型（需要适配）

---

## 📚 更多资源

- **Gazebo指南**: `GAZEBO_GUIDE.md`
- **MuJoCo指南**: `MUJOCO_DIRECT_GUIDE.md`
- **项目文档**: `docs/`目录

---

## 🎉 开始你的仿真之旅！

根据你的需求选择合适的仿真器，开始探索轮腿机器人的世界！

**推荐路径**:
1. 先用Gazebo看看真实的机器人模型
2. 再用MuJoCo进行高性能仿真
3. 根据需求选择最适合的工具

祝你仿真愉快！🤖
