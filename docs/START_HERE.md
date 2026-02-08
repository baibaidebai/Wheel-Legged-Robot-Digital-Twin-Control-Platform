# 🚀 开始使用 - 轮腿机器人仿真

## ✅ 推荐方案：MuJoCo + 修复后的URDF

由于你的系统（Ubuntu 24.04）上Gazebo配置不完整，我为你准备了一个**完美的解决方案**：

### 🎯 一键启动（推荐）

```bash
./launch_mujoco_with_urdf.sh
```

这个脚本会：
1. ✅ 自动修复URDF文件的mesh路径
2. ✅ 使用MuJoCo加载你的真实机器人模型
3. ✅ 显示完整的STL网格（不是方块！）
4. ✅ 启动3D可视化查看器

---

## 📋 详细步骤

### 方法1：自动化脚本（最简单）

```bash
./launch_mujoco_with_urdf.sh
```

### 方法2：手动步骤

#### 步骤1：修复URDF

```bash
python3 fix_urdf_for_mujoco.py
# 选择 1 (RM模型) 或 2 (DM模型)
```

这会创建一个修复后的URDF文件：
- `RM_Serial_Wheeled-leg_Robot_mujoco_fixed.urdf`
- 或 `wheel_legged_urdf_pkg_mujoco_fixed.urdf`

#### 步骤2：启动MuJoCo

修改`launch_mujoco_direct.py`中的模型路径，或直接使用修复后的URDF。

---

## 🎮 使用说明

### MuJoCo查看器控制

| 操作 | 功能 |
|------|------|
| 鼠标左键拖动 | 旋转视角 |
| 鼠标右键拖动 | 平移视角 |
| 鼠标滚轮 | 缩放 |
| 空格键 | 暂停/继续仿真 |
| Ctrl+R | 重置仿真 |
| Esc | 退出 |

---

## 🔧 问题解决

### 问题：URDF修复失败

**检查**：
```bash
ls -la src/model/RM_Serial_Wheeled-leg_Robot/meshes/
```

确保mesh文件存在。

### 问题：MuJoCo加载失败

**检查MuJoCo**：
```bash
python3 -c "import sys; sys.path.insert(0, 'venv/lib/python3.12/site-packages'); import mujoco; print('MuJoCo版本:', mujoco.__version__)"
```

### 问题：仍然显示方块

**原因**：mesh文件路径仍然不正确

**解决**：
1. 检查修复后的URDF文件
2. 确认mesh文件路径是绝对路径
3. 手动验证文件存在

---

## 📊 你的选项对比

| 方案 | 状态 | 推荐度 |
|------|------|--------|
| **MuJoCo + 修复URDF** | ✅ 可用 | ⭐⭐⭐⭐⭐ |
| MuJoCo + 简化模型 | ✅ 可用 | ⭐⭐⭐ |
| Gazebo Classic | ❌ 不可用 | - |
| Gazebo Harmonic | ⚠️ 未完全配置 | ⭐⭐ |
| PyQt5 GUI | ❌ 黑屏问题 | - |

---

## 🎉 立即开始

运行这个命令，看到你的真实机器人模型：

```bash
./launch_mujoco_with_urdf.sh
```

**预期结果**：
- ✅ URDF自动修复
- ✅ MuJoCo窗口打开
- ✅ 显示完整的机器人模型（带STL网格）
- ✅ 流畅的3D可视化
- ✅ 实时物理仿真

---

## 📚 更多信息

- **MuJoCo指南**: `MUJOCO_DIRECT_GUIDE.md`
- **所有选项**: `SIMULATION_OPTIONS.md`
- **Gazebo指南**: `GAZEBO_GUIDE.md` (如果以后配置Gazebo)

---

## 💡 提示

### 如果你想尝试不同的模型

编辑 `fix_urdf_for_mujoco.py` 或运行时选择：
- 选项1: RM_Serial_Wheeled-leg_Robot
- 选项2: DM_Wheel_leg_robot

### 如果你想自定义控制

编辑 `launch_mujoco_with_urdf.sh` 中的控制逻辑：
```python
# 简单控制
if model.nu > 0:
    for i in range(min(4, model.nu)):
        data.ctrl[i] = 0.3 * np.sin(data.time * 1.5 + i * np.pi / 2)
```

---

## 🎯 总结

**最佳方案**：使用MuJoCo + 修复后的URDF

**一键启动**：
```bash
./launch_mujoco_with_urdf.sh
```

**享受你的轮腿机器人仿真！** 🤖✨
