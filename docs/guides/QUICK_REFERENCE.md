# 🚀 快速参考卡

## 常见问题快速解决

### 问题1：Gazebo窗口没有打开
```bash
./install_gazebo.sh
```

### 问题2：Gazebo闪屏/看不到模型（虚拟机）
```bash
./launch_gazebo_safe.sh
```

### 问题3：想快速测试
```bash
./launch_gazebo_simple.sh
```

### 问题4：DM机器人无法加载
```bash
python3 fix_dm_urdf.py
./launch_gazebo_safe.sh
# 选择模型 2
```

---

## 启动脚本对比

| 脚本 | 适用场景 | 特点 |
|------|---------|------|
| `launch_gazebo.sh` | 物理机 | 标准模式，硬件加速 |
| `launch_gazebo_safe.sh` ⭐ | 虚拟机 | 软件渲染，解决闪屏 |
| `launch_gazebo_simple.sh` | 快速测试 | 最简单，直接加载 |

---

## 诊断脚本

```bash
# 检查Gazebo安装
./check_gazebo.sh

# 检查OpenGL环境
./check_opengl.sh
```

---

## 环境变量（手动设置）

```bash
# 软件渲染模式（解决闪屏）
export LIBGL_ALWAYS_SOFTWARE=1
export MESA_GL_VERSION_OVERRIDE=3.3
export GALLIUM_DRIVER=llvmpipe

# 然后启动
./launch_gazebo.sh
```

---

## 文档快速链接

| 问题 | 文档 |
|------|------|
| 首次使用 | [START_HERE.md](START_HERE.md) |
| 窗口没打开 | [QUICK_FIX.md](QUICK_FIX.md) |
| 闪屏问题 | [GAZEBO_FLICKERING_FIX.md](GAZEBO_FLICKERING_FIX.md) |
| DM机器人 | [DM_ROBOT_FIX.md](DM_ROBOT_FIX.md) |
| 安装指南 | [GAZEBO_INSTALL_SIMPLE.md](GAZEBO_INSTALL_SIMPLE.md) |
| 所有文档 | [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) |

---

## 虚拟机用户（推荐流程）

```bash
# 1. 安装Gazebo
./install_gazebo.sh

# 2. 检查环境
./check_opengl.sh

# 3. 使用安全模式启动
./launch_gazebo_safe.sh
```

---

## 物理机用户（推荐流程）

```bash
# 1. 安装Gazebo
./install_gazebo.sh

# 2. 标准模式启动
./launch_gazebo.sh
```

---

## 故障排除流程

```
问题 → 查文档 → 运行诊断 → 尝试解决方案
  ↓        ↓          ↓            ↓
闪屏   FLICKERING  check_opengl  launch_safe
没打开  QUICK_FIX   check_gazebo  install
```

---

## 一键命令

```bash
# 虚拟机用户（最常用）
./launch_gazebo_safe.sh

# 物理机用户
./launch_gazebo.sh

# 快速测试
./launch_gazebo_simple.sh
```

---

**保存这个页面，随时查阅！** 📌
