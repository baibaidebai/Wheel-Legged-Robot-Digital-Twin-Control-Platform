# MuJoCo 故障排除指南

## 🚨 常见问题

### 问题：MuJoCo窗口无法显示

这是虚拟机环境中最常见的问题。

#### 症状
- 程序运行但窗口不出现
- 看到Wayland相关警告
- GLFW错误信息

#### 原因
1. 使用Wayland而不是X11
2. 虚拟机3D加速未启用
3. 缺少必要的库

---

## 🔧 快速修复

### 步骤1：运行诊断工具

```bash
python3 tools/diagnose_mujoco.py
```

这会检查：
- MuJoCo安装
- 显示环境（X11/Wayland）
- OpenGL支持
- GLFW库
- 系统库

### 步骤2：运行修复脚本

```bash
./tools/fix_mujoco_display.sh
```

这会：
- 安装必要的库
- 检测会话类型
- 提供修复建议

---

## 💡 解决方案

### 方案A：切换到X11（推荐）⭐

**为什么？**
- MuJoCo在X11下工作最好
- Wayland支持不完整

**如何切换？**

1. 注销当前会话
2. 在登录界面点击右下角齿轮图标
3. 选择 "Ubuntu on Xorg"
4. 重新登录

**验证：**
```bash
echo $XDG_SESSION_TYPE
# 应该显示: x11
```

---

### 方案B：使用软件渲染

**适用场景：**
- 无法切换到X11
- 临时测试
- 虚拟机环境

**使用方法：**

```bash
# 方法1：环境变量
export MUJOCO_GL=osmesa
python3 tools/launch_mujoco.py --model rm

# 方法2：命令行参数
python3 tools/launch_mujoco.py --model rm --render osmesa
```

**注意：**
- 性能较低
- 适合测试，不适合长期使用

---

### 方案C：虚拟机配置

#### VMware用户

1. **启用3D加速**
   - 虚拟机 → 设置 → 显示
   - 勾选"加速3D图形"
   - 图形内存：2GB或更高

2. **安装VMware Tools**
   - 虚拟机 → 安装VMware Tools
   - 按照提示完成安装
   - 重启虚拟机

3. **验证**
   ```bash
   glxinfo | grep "OpenGL renderer"
   # 应该显示VMware相关信息
   ```

#### VirtualBox用户

1. **启用3D加速**
   - 设置 → 显示
   - 勾选"启用3D加速"
   - 显存：128MB或更高

2. **安装Guest Additions**
   - 设备 → 安装增强功能
   - 按照提示完成安装
   - 重启虚拟机

---

## 📋 检查清单

### 基础检查

- [ ] MuJoCo已安装
  ```bash
  python3 -c "import mujoco; print(mujoco.__version__)"
  ```

- [ ] 使用X11会话
  ```bash
  echo $XDG_SESSION_TYPE  # 应该是 x11
  ```

- [ ] 必要的库已安装
  ```bash
  sudo apt-get install libglfw3 libglew-dev mesa-utils
  ```

### 虚拟机检查

- [ ] 3D加速已启用
- [ ] 显存分配充足（2GB+）
- [ ] Guest Tools已安装
- [ ] OpenGL可用
  ```bash
  glxinfo -B
  ```

### 测试

- [ ] 诊断工具通过
  ```bash
  python3 tools/diagnose_mujoco.py
  ```

- [ ] 可以启动MuJoCo
  ```bash
  python3 tools/launch_mujoco.py --model rm
  ```

---

## 🎯 推荐配置

### 物理机
- ✅ 使用X11
- ✅ 硬件渲染（glfw）
- ✅ 高帧率（120 FPS）

```bash
python3 tools/launch_mujoco.py --model rm --fps 120
```

### 虚拟机
- ✅ 使用X11
- ✅ 启用3D加速
- ✅ 中等帧率（60 FPS）

```bash
python3 tools/launch_mujoco.py --model rm --fps 60
```

### 低配置/兼容模式
- ✅ 软件渲染（osmesa）
- ✅ 低帧率（30 FPS）

```bash
python3 tools/launch_mujoco.py --model rm --render osmesa --fps 30
```

---

## 🔍 详细诊断

### 检查显示环境

```bash
echo "DISPLAY: $DISPLAY"
echo "WAYLAND_DISPLAY: $WAYLAND_DISPLAY"
echo "XDG_SESSION_TYPE: $XDG_SESSION_TYPE"
```

**期望输出：**
```
DISPLAY: :0
WAYLAND_DISPLAY: 
XDG_SESSION_TYPE: x11
```

### 检查OpenGL

```bash
glxinfo -B
```

**期望输出：**
```
OpenGL vendor string: VMware, Inc.
OpenGL renderer string: SVGA3D; ...
OpenGL version string: 3.3 ...
```

### 检查GLFW

```bash
python3 -c "import glfw; print('GLFW:', glfw.init())"
```

**期望输出：**
```
GLFW: True
```

---

## 📚 相关资源

- [MuJoCo官方文档](https://mujoco.readthedocs.io/)
- [MuJoCo完整指南](MUJOCO_GUIDE.md)
- [增强版GUI指南](ENHANCED_GUI_GUIDE.md)

---

## 💬 仍然无法解决？

1. **运行完整诊断**
   ```bash
   python3 tools/diagnose_mujoco.py > mujoco_diagnosis.txt
   ```

2. **收集信息**
   - 操作系统版本
   - 虚拟机软件和版本
   - 诊断结果
   - 错误信息

3. **寻求帮助**
   - 提交Issue
   - 附上诊断结果
   - 描述具体问题

---

**更新日期**: 2026-02-09
**版本**: v1.0
