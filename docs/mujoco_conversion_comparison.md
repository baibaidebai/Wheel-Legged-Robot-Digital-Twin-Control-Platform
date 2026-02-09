# MuJoCo URDF 转换方案对比

## 概述

本文档对比两种 URDF 到 MJCF 转换方案，帮助你选择最适合的工具。

## 方案对比

### 方案 A：Wiki-GRx-MJCF 工具 ⭐ 推荐

**来源**: https://github.com/FFTAI/Wiki-MJCF (傅利叶智能开源)

#### 优势
- ✅ **保留 STL mesh 文件** - 完整的视觉效果
- ✅ **专业工具** - 由机器人公司开发和维护
- ✅ **完整转换** - 保留所有 URDF 信息
- ✅ **自动路径处理** - 自动转换为绝对路径
- ✅ **支持传感器配置** - 可添加额外的传感器
- ✅ **可定制** - 支持自定义 MuJoCo 配置

#### 劣势
- ❌ **需要额外安装** - 需要克隆仓库并安装
- ❌ **STL 格式要求** - 只支持 Binary STL（不支持 ASCII STL）
- ❌ **绝对路径** - 生成的路径较长，不便于移植

#### 安装方法

```bash
# 1. 克隆仓库
cd ~/workspace
git clone https://github.com/FFTAI/Wiki-MJCF.git

# 2. 在虚拟环境中安装
cd "Wheel-Legged Robot Digital Twin Control Platform"
source venv/bin/activate
pip install -e ~/workspace/Wiki-GRx-MJCF
```

#### 使用方法

```bash
# 方法 1: 命令行
urdf2mjcf input.urdf output.xml --ground --lighting

# 方法 2: Python 脚本
python3 tools/test_wiki_mjcf.py
```

#### 测试结果

**RM 机器人**: ✅ 转换成功
- 保留了所有 STL mesh 文件
- 关节和惯性参数完整
- 可以在 MuJoCo 中正常加载

**DM 机器人**: ❌ 转换失败
- 原因：STL 文件是 ASCII 格式，MuJoCo 只支持 Binary 格式
- 解决方案：使用 Blender 或 MeshLab 转换 STL 格式

---

### 方案 B：自定义转换工具

**来源**: `tools/convert_urdf_to_mjcf.py` (项目内置)

#### 优势
- ✅ **无需额外安装** - 已集成到项目中
- ✅ **简单可靠** - 使用简单几何体，避免 mesh 问题
- ✅ **已测试通过** - 两个机器人都能成功转换
- ✅ **相对路径** - 便于项目移植
- ✅ **无 STL 格式限制** - 不依赖 mesh 文件

#### 劣势
- ❌ **简化外观** - 使用 box 代替 mesh，外观不真实
- ❌ **功能有限** - 只转换基本结构
- ❌ **手动调整** - 可能需要手动调整几何体尺寸

#### 使用方法

```bash
# 转换 RM 机器人
python3 tools/convert_urdf_to_mjcf.py --model rm

# 转换 DM 机器人
python3 tools/convert_urdf_to_mjcf.py --model dm

# 转换两个模型
python3 tools/convert_urdf_to_mjcf.py --model both
```

#### 测试结果

**RM 机器人**: ✅ 转换成功
**DM 机器人**: ✅ 转换成功

---

## 详细对比表

| 特性 | Wiki-GRx-MJCF | 自定义工具 |
|------|---------------|-----------|
| **外观质量** | ⭐⭐⭐⭐⭐ (真实 mesh) | ⭐⭐ (简单几何体) |
| **易用性** | ⭐⭐⭐ (需要安装) | ⭐⭐⭐⭐⭐ (内置) |
| **可靠性** | ⭐⭐⭐⭐ (依赖 STL 格式) | ⭐⭐⭐⭐⭐ (无依赖) |
| **转换完整性** | ⭐⭐⭐⭐⭐ (完整) | ⭐⭐⭐⭐ (基本完整) |
| **可移植性** | ⭐⭐⭐ (绝对路径) | ⭐⭐⭐⭐⭐ (相对路径) |
| **维护性** | ⭐⭐⭐⭐ (社区维护) | ⭐⭐⭐ (项目维护) |

---

## 推荐使用场景

### 使用 Wiki-GRx-MJCF 的场景

1. **需要真实外观** - 演示、展示、视频录制
2. **完整仿真** - 需要精确的碰撞检测
3. **专业开发** - 商业项目或研究论文
4. **STL 文件可用** - 且为 Binary 格式

### 使用自定义工具的场景

1. **快速原型** - 算法开发和测试
2. **强化学习训练** - 外观不重要，只需要物理特性
3. **简单项目** - 不需要复杂的视觉效果
4. **STL 文件问题** - ASCII 格式或文件损坏

---

## 转换流程图

```
URDF 文件
    |
    ├─→ Wiki-GRx-MJCF
    |       |
    |       ├─ 检查 STL 格式
    |       |   ├─ Binary ✅ → 转换成功 (保留 mesh)
    |       |   └─ ASCII ❌ → 转换失败
    |       |
    |       └─ 生成 MJCF (绝对路径)
    |
    └─→ 自定义工具
            |
            ├─ 忽略 mesh 文件
            ├─ 使用简单几何体
            └─ 生成 MJCF (相对路径) ✅
```

---

## 实际使用建议

### 推荐工作流程

1. **首先尝试 Wiki-GRx-MJCF**
   ```bash
   python3 tools/test_wiki_mjcf.py
   ```

2. **如果成功** → 使用 Wiki-GRx-MJCF 生成的文件
   - 文件位置：`mjcf/*_wiki.xml`
   - 启动：`python3 tools/launch_mujoco.py --mjcf path/to/*_wiki.xml`

3. **如果失败** → 使用自定义工具
   ```bash
   python3 tools/convert_urdf_to_mjcf.py --model rm
   python3 tools/launch_mujoco.py --model rm
   ```

### STL 格式转换（如果需要）

如果 Wiki-GRx-MJCF 因为 ASCII STL 失败，可以转换格式：

```bash
# 使用 MeshLab (需要安装)
meshlabserver -i input_ascii.stl -o output_binary.stl

# 或使用 Blender (需要安装)
# File → Import → STL → File → Export → STL (勾选 Binary)
```

---

## 文件对比示例

### Wiki-GRx-MJCF 生成的文件

```xml
<mujoco model="wl">
  <asset>
    <mesh name="base_link" file="/absolute/path/to/meshes/base_link.STL" />
  </asset>
  <worldbody>
    <body name="base_link">
      <geom type="mesh" mesh="base_link" />
    </body>
  </worldbody>
</mujoco>
```

**特点**：
- ✅ 使用真实 mesh
- ❌ 绝对路径
- ✅ 完整的视觉效果

### 自定义工具生成的文件

```xml
<mujoco model="wl">
  <compiler meshdir="../meshes" />
  <worldbody>
    <body name="base_link">
      <geom type="box" size="0.05 0.05 0.05" />
    </body>
  </worldbody>
</mujoco>
```

**特点**：
- ❌ 简单几何体
- ✅ 相对路径
- ❌ 简化的视觉效果

---

## 常见问题

### Q1: Wiki-GRx-MJCF 转换失败怎么办？

**A**: 检查错误信息：
- 如果是 "ASCII file" 错误 → STL 格式问题，需要转换
- 如果是 "file not found" → 路径问题，检查 mesh 文件位置
- 其他错误 → 使用自定义工具作为备选方案

### Q2: 生成的 MJCF 文件路径太长怎么办？

**A**: 可以手动编辑 MJCF 文件，将绝对路径改为相对路径：
```xml
<!-- 修改前 -->
<mesh file="/home/user/workspace/.../meshes/file.STL" />

<!-- 修改后 -->
<mesh file="../meshes/file.STL" />
```

### Q3: 两种工具生成的文件可以混用吗？

**A**: 可以！你可以：
1. 使用 Wiki-GRx-MJCF 生成基础文件
2. 手动编辑优化
3. 参考自定义工具的结构调整

### Q4: 哪个工具更适合强化学习训练？

**A**: 自定义工具更适合，因为：
- 简单几何体计算更快
- 不需要加载复杂的 mesh
- 物理特性足够准确

---

## 总结

- **追求真实外观** → 使用 Wiki-GRx-MJCF ⭐
- **追求简单可靠** → 使用自定义工具 ⭐
- **最佳实践** → 两者都尝试，选择最适合的

两种工具各有优势，根据你的具体需求选择即可！
