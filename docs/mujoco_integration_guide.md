# MuJoCo集成指南

## 概述

本项目已成功集成MuJoCo物理仿真引擎，使用MJCF（MuJoCo XML）格式代替直接加载URDF文件。

## 为什么使用MJCF格式？

MuJoCo 3.4.0的URDF解析器对mesh文件路径有严格限制：
- ❌ 无法正确处理相对路径（如`../meshes/file.STL`）
- ❌ 符号链接方案不可靠
- ❌ 绝对路径转换也无法解决问题

**解决方案：** 使用MJCF格式，用简单几何体代替STL mesh文件。

## 快速开始

### 1. 安装MuJoCo

```bash
# 激活虚拟环境（如果使用）
source venv/bin/activate

# 安装MuJoCo
pip install mujoco -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2. 转换URDF到MJCF

我们提供两种转换方案：

#### 方案 A：Wiki-GRx-MJCF 工具（推荐，保留真实 mesh）⭐

```bash
# 1. 安装工具（首次使用）
cd ~/workspace
git clone https://github.com/FFTAI/Wiki-MJCF.git
cd "Wheel-Legged Robot Digital Twin Control Platform"
source venv/bin/activate
pip install -e ~/workspace/Wiki-GRx-MJCF

# 2. 转换模型
python3 tools/test_wiki_mjcf.py
```

**优势**：保留 STL mesh 文件，完整的视觉效果
**劣势**：只支持 Binary STL 格式

#### 方案 B：内置转换工具（简单可靠）

```bash
# 转换RM机器人模型
python3 tools/convert_urdf_to_mjcf.py --model rm

# 转换DM机器人模型
python3 tools/convert_urdf_to_mjcf.py --model dm

# 一次转换两个模型
python3 tools/convert_urdf_to_mjcf.py --model both
```

**优势**：无需额外安装，使用简单几何体避免 mesh 问题
**劣势**：外观简化

转换后的文件位置：
- Wiki-GRx-MJCF：`mjcf/*_wiki.xml`（保留 mesh）
- 内置工具：`mjcf/*.xml`（简单几何体）

📚 **详细对比**：查看 [转换方案对比文档](mujoco_conversion_comparison.md)

### 3. 启动MuJoCo仿真

```bash
# 使用Shell脚本（交互式选择）
./tools/launch_mujoco.sh

# 或直接使用Python
python3 tools/launch_mujoco.py --model rm  # RM机器人
python3 tools/launch_mujoco.py --model dm  # DM机器人
```

## 转换工具说明

### 功能特性

`tools/convert_urdf_to_mjcf.py` 转换工具提供：

1. **自动解析URDF结构**
   - 链接（links）和关节（joints）
   - 惯性参数（inertial properties）
   - 关节限制和轴向

2. **几何体转换**
   - STL mesh → 简单几何体（box, cylinder, sphere）
   - 保留原始尺寸和颜色信息
   - 自动生成合理的默认尺寸

3. **关节和执行器**
   - 保留所有关节名称和类型
   - 自动创建电机执行器
   - 转换关节限制（弧度→度）

4. **MJCF优化**
   - 添加地面和光源
   - 配置物理参数
   - 设置材质和纹理

### 使用选项

```bash
# 基本用法
python3 tools/convert_urdf_to_mjcf.py --model [rm|dm|both]

# 指定URDF文件
python3 tools/convert_urdf_to_mjcf.py --urdf path/to/robot.urdf

# 指定输出目录
python3 tools/convert_urdf_to_mjcf.py --model rm --output path/to/output
```

## MuJoCo启动器说明

### 功能特性

`tools/launch_mujoco.py` 启动器提供：

1. **模型加载**
   - 自动查找MJCF文件
   - 验证文件存在性
   - 显示模型信息

2. **交互式可视化**
   - 鼠标控制视角
   - 实时物理仿真
   - 关节和执行器信息显示

3. **控制说明**
   - 鼠标左键：旋转视角
   - 鼠标右键：平移视角
   - 鼠标滚轮：缩放
   - 空格键：暂停/继续
   - Backspace：重置仿真
   - Ctrl+Q：退出

## 文件结构

```
Wheel-Legged Robot Digital Twin Control Platform/
├── tools/
│   ├── convert_urdf_to_mjcf.py    # URDF到MJCF转换工具
│   ├── launch_mujoco.py            # MuJoCo启动器
│   ├── launch_mujoco.sh            # Shell启动脚本
│   └── launch_mujoco_simple.py     # 简化版启动器（内嵌模型）
├── src/model/
│   ├── RM_Serial_Wheeled-leg_Robot/
│   │   ├── urdf/                   # 原始URDF文件
│   │   └── mjcf/                   # 转换后的MJCF文件 ⭐
│   └── DM_Wheel_leg_robot/
│       ├── urdf/                   # 原始URDF文件
│       └── mjcf/                   # 转换后的MJCF文件 ⭐
└── docs/
    └── mujoco_integration_guide.md # 本文档
```

## 已知限制

1. **几何体简化**
   - 使用简单几何体代替STL mesh
   - 可能与原始模型外观不完全一致
   - 可以手动编辑MJCF文件调整几何体

2. **材质和纹理**
   - 基本颜色保留
   - 复杂材质可能丢失
   - 可以在MJCF中手动添加

3. **关节限制**
   - 自动转换弧度到度
   - 可能需要手动调整范围

## 手动调整MJCF

生成的MJCF文件可以手动编辑以优化：

```xml
<!-- 调整几何体尺寸 -->
<geom name="link_geom" type="box" size="0.1 0.1 0.1" />

<!-- 调整颜色 -->
<geom rgba="1 0 0 1" />  <!-- 红色 -->

<!-- 调整关节限制 -->
<joint range="-90 90" />

<!-- 调整执行器参数 -->
<motor gear="10" ctrlrange="-100 100" />
```

## 故障排除

### 问题：MJCF文件不存在

```
❌ MJCF文件不存在: .../mjcf/robot.xml
```

**解决方案：** 运行转换工具
```bash
python3 tools/convert_urdf_to_mjcf.py --model rm
```

### 问题：MuJoCo未安装

```
❌ MuJoCo未安装
```

**解决方案：** 安装MuJoCo
```bash
pip install mujoco -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题：模型加载失败

**可能原因：**
1. MJCF文件格式错误
2. 几何体参数无效
3. 关节配置问题

**解决方案：**
1. 重新运行转换工具
2. 检查MJCF文件语法
3. 手动调整参数

## 与Gazebo对比

| 特性 | MuJoCo | Gazebo |
|------|--------|--------|
| 物理精度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 仿真速度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 可视化 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| ROS2集成 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 强化学习 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 易用性 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

**推荐使用场景：**
- **MuJoCo**：强化学习训练、高性能仿真、批量实验
- **Gazebo**：ROS2集成、传感器仿真、完整系统测试

## 下一步

1. ✅ 基础MuJoCo集成完成
2. ✅ URDF到MJCF转换工具
3. ✅ 交互式可视化启动器
4. 🔄 集成到主GUI应用
5. 🔄 添加控制算法接口
6. 🔄 实现强化学习训练环境

## 参考资料

- [MuJoCo官方文档](https://mujoco.readthedocs.io/)
- [MJCF格式规范](https://mujoco.readthedocs.io/en/stable/XMLreference.html)
- [MuJoCo Python绑定](https://mujoco.readthedocs.io/en/stable/python.html)
