# 📁 文件组织说明

## 目录结构

项目已重新组织，文件按功能分类到不同目录。

### 根目录（简洁）

```
Wheel-Legged Robot Digital Twin Control Platform/
├── launch.sh              # 主启动脚本（GUI）⭐
├── README.md              # 项目说明
├── requirements.txt       # Python依赖
├── pytest.ini            # 测试配置
├── CONTRIBUTING.md        # 贡献指南
├── PROJECT_STATUS.md      # 项目状态
└── QUICK_START.md         # 快速开始
```

### tools/ - 工具脚本

所有可执行脚本和工具：

```
tools/
├── launch_gazebo_gui.py      # GUI启动器（Python）
├── launch_gazebo_safe.sh     # 安全模式启动
├── launch_gazebo_simple.sh   # 简单模式启动
├── launch_gazebo.sh          # 标准模式启动
├── install_gazebo.sh         # Gazebo安装
├── check_gazebo.sh           # Gazebo诊断
├── check_opengl.sh           # OpenGL诊断
├── fix_dm_urdf.py            # DM机器人修复
└── fix_dependencies.sh       # 依赖修复
```

### docs/guides/ - 使用指南

所有用户文档和指南：

```
docs/guides/
├── START_HERE.md                # 快速开始 ⭐
├── QUICK_FIX.md                 # 快速修复
├── QUICK_REFERENCE.md           # 快速参考
├── GAZEBO_QUICKSTART.md         # Gazebo快速开始
├── GAZEBO_INSTALL_SIMPLE.md     # 简单安装指南
├── INSTALL_GAZEBO.md            # 完整安装指南
├── NEXT_STEPS.md                # 下一步操作
├── GAZEBO_FLICKERING_FIX.md     # 闪屏问题修复
├── WHY_GAZEBO_DIDNT_OPEN.md     # 问题诊断
├── DM_ROBOT_FIX.md              # DM机器人修复
├── VISUAL_GUIDE.md              # 可视化指南
├── DOCUMENTATION_INDEX.md       # 文档索引
└── FILE_ORGANIZATION.md         # 本文件
```

### docs/ - 技术文档

技术文档和开发指南：

```
docs/
├── GAZEBO_GUIDE.md              # Gazebo详细指南
├── SIMULATION_OPTIONS.md        # 仿真选项
├── START_HERE.md                # 开发入门
├── project_structure.md         # 项目结构
├── ppo_implementation_summary.md # PPO实现
├── ppo_training_guide.md        # PPO训练指南
└── ...
```

### src/ - 源代码

```
src/
├── model/                       # 机器人模型
│   ├── RM_Serial_Wheeled-leg_Robot/
│   └── DM_Wheel_leg_robot/
└── wheel_legged_control/        # 控制系统
    └── wheel_legged_control/
        ├── algorithms/          # 算法
        ├── controllers/         # 控制器
        ├── simulation/          # 仿真
        ├── data/               # 数据
        └── sensors/            # 传感器
```

### scripts/ - 演示脚本

```
scripts/
├── demo_*.py                    # 演示脚本
└── gazebo/                      # Gazebo脚本
```

### test/ - 测试文件

```
test/
├── python/                      # Python测试
├── integration/                 # 集成测试
└── ...
```

### data/ - 实验数据

```
data/
├── demo_recordings/             # 演示数据
└── advanced_recordings/         # 高级数据
```

## 文件迁移对照表

### 启动脚本

| 旧位置 | 新位置 |
|--------|--------|
| `./launch_gazebo.sh` | `./tools/launch_gazebo.sh` |
| `./launch_gazebo_safe.sh` | `./tools/launch_gazebo_safe.sh` |
| `./launch_gazebo_simple.sh` | `./tools/launch_gazebo_simple.sh` |

**新增**：`./launch.sh` - GUI启动器（推荐）

### 工具脚本

| 旧位置 | 新位置 |
|--------|--------|
| `./install_gazebo.sh` | `./tools/install_gazebo.sh` |
| `./check_gazebo.sh` | `./tools/check_gazebo.sh` |
| `./check_opengl.sh` | `./tools/check_opengl.sh` |
| `./fix_dm_urdf.py` | `./tools/fix_dm_urdf.py` |
| `./fix_dependencies.sh` | `./tools/fix_dependencies.sh` |

### 文档

| 旧位置 | 新位置 |
|--------|--------|
| `./START_HERE.md` | `./docs/guides/START_HERE.md` |
| `./QUICK_FIX.md` | `./docs/guides/QUICK_FIX.md` |
| `./QUICK_REFERENCE.md` | `./docs/guides/QUICK_REFERENCE.md` |
| `./GAZEBO_QUICKSTART.md` | `./docs/guides/GAZEBO_QUICKSTART.md` |
| `./INSTALL_GAZEBO.md` | `./docs/guides/INSTALL_GAZEBO.md` |
| `./GAZEBO_FLICKERING_FIX.md` | `./docs/guides/GAZEBO_FLICKERING_FIX.md` |
| `./DM_ROBOT_FIX.md` | `./docs/guides/DM_ROBOT_FIX.md` |
| `./DOCUMENTATION_INDEX.md` | `./docs/guides/DOCUMENTATION_INDEX.md` |

## 使用新的文件位置

### 启动Gazebo

**推荐方式（GUI）：**
```bash
./launch.sh
```

**命令行方式：**
```bash
# 安全模式
./tools/launch_gazebo_safe.sh

# 简单模式
./tools/launch_gazebo_simple.sh

# 标准模式
./tools/launch_gazebo.sh
```

### 安装和诊断

```bash
# 安装Gazebo
./tools/install_gazebo.sh

# 检查Gazebo
./tools/check_gazebo.sh

# 检查OpenGL
./tools/check_opengl.sh

# 修复DM机器人
python3 tools/fix_dm_urdf.py
```

### 查看文档

```bash
# 快速开始
cat docs/guides/START_HERE.md

# 快速修复
cat docs/guides/QUICK_FIX.md

# 文档索引
cat docs/guides/DOCUMENTATION_INDEX.md
```

## 为什么重新组织？

### 之前的问题

- ❌ 根目录有20+个文件
- ❌ 脚本和文档混在一起
- ❌ 难以找到需要的文件
- ❌ 不专业的项目结构

### 现在的优势

- ✅ 根目录只有核心文件
- ✅ 文件按功能分类
- ✅ 清晰的目录结构
- ✅ 易于维护和扩展
- ✅ 专业的项目组织

## 兼容性

### 旧脚本仍然可用

如果你有使用旧路径的脚本，可以：

1. **更新路径**：将 `./script.sh` 改为 `./tools/script.sh`
2. **使用符号链接**（不推荐）：
   ```bash
   ln -s tools/launch_gazebo_safe.sh launch_gazebo_safe.sh
   ```

### 推荐做法

使用新的路径和GUI启动器：

```bash
# 最简单的方式
./launch.sh

# 或者使用新路径
./tools/launch_gazebo_safe.sh
```

## 总结

项目现在有清晰的目录结构：

- **根目录**：只有核心文件和主启动脚本
- **tools/**：所有工具和脚本
- **docs/guides/**：所有用户文档
- **docs/**：技术文档
- **src/**：源代码
- **scripts/**：演示脚本
- **test/**：测试文件
- **data/**：实验数据

这样的组织使项目更专业、更易于维护！🎉
