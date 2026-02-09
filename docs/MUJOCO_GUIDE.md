# MuJoCo 仿真完整指南

## 📋 目录

1. [快速开始](#快速开始)
2. [安装配置](#安装配置)
3. [模型转换](#模型转换)
4. [启动仿真](#启动仿真)
5. [转换方案对比](#转换方案对比)
6. [故障排除](#故障排除)

---

## 快速开始

### 一键启动（推荐）

```bash
# 1. 安装 MuJoCo
source venv/bin/activate
pip install mujoco -i https://pypi.tuna.tsinghua.edu.cn/simple

# 2. 转换模型（已完成，可跳过）
python3 tools/test_wiki_mjcf.py

# 3. 启动仿真
python3 tools/launch_mujoco.py --model rm  # RM 机器人
python3 tools/launch_mujoco.py --model dm  # DM 机器人
```

---

## 安装配置

### 1. 安装 MuJoCo

```bash
# 激活虚拟环境
source venv/bin/activate

# 安装 MuJoCo
pip install mujoco -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2. 安装 Wiki-GRx-MJCF 工具（可选）

如果需要重新转换模型：

```bash
cd ~/workspace
git clone https://github.com/FFTAI/Wiki-MJCF.git
cd "Wheel-Legged Robot Digital Twin Control Platform"
source venv/bin/activate
pip install -e ~/workspace/Wiki-GRx-MJCF
```

---

## 模型转换

项目已包含转换好的 MJCF 文件，通常无需重新转换。

### 已转换的模型

```
src/model/
├── RM_Serial_Wheeled-leg_Robot/mjcf/
│   ├── RM_Serial_Wheeled-leg_Robot.xml       # 内置工具版本
│   └── RM_Serial_Wheeled-leg_Robot_wiki.xml  # Wiki-MJCF 版本 ⭐
│
└── DM_Wheel_leg_robot/mjcf/
    ├── wheel_legged_urdf_pkg.xml             # 内置工具版本
    └── wheel_legged_urdf_pkg_wiki.xml        # Wiki-MJCF 版本 ⭐
```

### 重新转换（如果需要）

#### 方法 A：Wiki-GRx-MJCF（保留真实外观）

```bash
python3 tools/test_wiki_mjcf.py
```

#### 方法 B：内置工具（简单可靠）

```bash
python3 tools/convert_urdf_to_mjcf.py --model rm
python3 tools/convert_urdf_to_mjcf.py --model dm
```

---

## 启动仿真

### 使用 Python 脚本

```bash
# RM 机器人（Wiki-MJCF 版本，真实外观）
python3 tools/launch_mujoco.py --mjcf "src/model/RM_Serial_Wheeled-leg_Robot/mjcf/RM_Serial_Wheeled-leg_Robot_wiki.xml"

# DM 机器人（Wiki-MJCF 版本，真实外观）
python3 tools/launch_mujoco.py --mjcf "src/model/DM_Wheel_leg_robot/mjcf/wheel_legged_urdf_pkg_wiki.xml"

# 或使用简化版本
python3 tools/launch_mujoco.py --model rm
python3 tools/launch_mujoco.py --model dm
```

### 使用 Shell 脚本

```bash
./tools/launch_mujoco.sh
```

### 控制说明

- **鼠标左键**：旋转视角
- **鼠标右键**：平移视角
- **鼠标滚轮**：缩放
- **空格键**：暂停/继续
- **Backspace**：重置仿真
- **Ctrl+Q**：退出

---

## 转换方案对比

### Wiki-GRx-MJCF（推荐用于演示）

**优势**：
- ✅ 保留 STL mesh 文件
- ✅ 完整的视觉效果
- ✅ 专业工具，社区维护

**劣势**：
- ❌ 需要额外安装
- ❌ 只支持 Binary STL
- ❌ 使用绝对路径

**适用场景**：
- 演示和展示
- 完整的物理仿真
- 专业开发和研究

### 内置转换工具（推荐用于开发）

**优势**：
- ✅ 无需额外安装
- ✅ 简单可靠
- ✅ 无 STL 格式限制
- ✅ 使用相对路径

**劣势**：
- ❌ 使用简单几何体
- ❌ 外观简化

**适用场景**：
- 快速原型开发
- 强化学习训练
- 算法测试

---

## 故障排除

### 问题 1：MJCF 文件不存在

**错误信息**：
```
❌ MJCF文件不存在
```

**解决方案**：
```bash
python3 tools/test_wiki_mjcf.py
```

### 问题 2：MuJoCo 未安装

**错误信息**：
```
❌ MuJoCo未安装
```

**解决方案**：
```bash
source venv/bin/activate
pip install mujoco -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题 3：MuJoCo 窗口无法显示 ⭐

**症状**：
- 窗口无法打开
- Wayland相关警告
- GLFW错误

**诊断**：
```bash
python3 tools/diagnose_mujoco.py
```

**解决方案**：

#### 方案 A：切换到 X11（推荐）

1. 运行修复脚本：
```bash
./tools/fix_mujoco_display.sh
```

2. 或手动切换：
   - 注销当前会话
   - 在登录界面点击右下角齿轮图标
   - 选择 "Ubuntu on Xorg"
   - 重新登录

#### 方案 B：使用软件渲染

```bash
# 临时设置
export MUJOCO_GL=osmesa
python3 tools/launch_mujoco.py --model rm --render osmesa

# 或直接使用参数
python3 tools/launch_mujoco.py --model rm --render osmesa
```

#### 方案 C：虚拟机配置

**VMware用户**：
1. 虚拟机 → 设置 → 显示
2. 启用"加速3D图形"
3. 图形内存设置为 2GB+
4. 安装VMware Tools

**VirtualBox用户**：
1. 设置 → 显示
2. 启用"3D加速"
3. 显存设置为 128MB+
4. 安装Guest Additions

### 问题 4：STL 文件格式错误

**错误信息**：
```
Error: perhaps this is an ASCII file?
```

**解决方案**：
```bash
python3 tools/fix_dm_stl.py
```

### 问题 5：三角面数超限

**错误信息**：
```
Error: number of faces should be between 1 and 200000
```

**解决方案**：
```bash
python3 tools/simplify_dm_mesh.py
```

---

## 工具说明

### 转换工具

- **`test_wiki_mjcf.py`** - Wiki-GRx-MJCF 转换测试
- **`convert_urdf_to_mjcf.py`** - 内置 URDF 到 MJCF 转换

### 修复工具

- **`fix_dm_stl.py`** - 修复 STL 文件格式
- **`simplify_dm_mesh.py`** - 简化复杂 mesh

### 启动工具

- **`launch_mujoco.py`** - MuJoCo 启动器
- **`launch_mujoco.sh`** - Shell 启动脚本

### 诊断工具

- **`diagnose_mujoco.py`** - MuJoCo 环境诊断
- **`fix_mujoco_display.sh`** - 显示问题修复

---

## 技术细节

### MuJoCo 版本

- **要求**：MuJoCo 2.3.0+
- **当前**：MuJoCo 3.4.0 ✅

### MJCF 格式

- **编译器**：angle="radian"
- **时间步长**：0.001s
- **重力**：0 0 -9.81

### Mesh 限制

- **格式**：Binary STL
- **最大三角面数**：200,000

---

## 参考资料

- [MuJoCo 官方文档](https://mujoco.readthedocs.io/)
- [MJCF 格式规范](https://mujoco.readthedocs.io/en/stable/XMLreference.html)
- [Wiki-GRx-MJCF GitHub](https://github.com/FFTAI/Wiki-MJCF)

---

## 更新日志

### 2026-02-09

- ✅ 集成 Wiki-GRx-MJCF 工具
- ✅ 成功转换 RM 和 DM 机器人
- ✅ 修复 STL 格式问题
- ✅ 简化复杂 mesh
- ✅ 创建完整文档

---

**提示**：本指南整合了以下文档的内容：
- `mujoco_integration_guide.md`
- `mujoco_conversion_comparison.md`
- `MUJOCO_SETUP_COMPLETE.md`
- `WIKI_MJCF_CONVERSION_SUCCESS.md`
