# 🛠️ 工具脚本

这个目录包含所有可执行的工具和脚本。

## 启动脚本

### GUI启动器（推荐）⭐

```bash
# 从项目根目录运行
./launch.sh

# 或直接运行
python3 tools/launch_gazebo_gui.py
```

图形界面可以：
- 选择机器人模型
- 选择启动模式
- 配置高级选项

### 命令行启动

```bash
# 安全模式（推荐虚拟机）
./tools/launch_gazebo_safe.sh

# 简单模式
./tools/launch_gazebo_simple.sh

# 标准模式
./tools/launch_gazebo.sh
```

## 安装和诊断

```bash
# 安装Gazebo
./tools/install_gazebo.sh

# 检查Gazebo安装状态
./tools/check_gazebo.sh

# 检查OpenGL环境
./tools/check_opengl.sh
```

## 修复工具

```bash
# 修复DM机器人URDF
python3 tools/fix_dm_urdf.py

# 修复依赖
./tools/fix_dependencies.sh
```

## 脚本说明

| 脚本 | 功能 | 适用场景 |
|------|------|---------|
| `launch_gazebo_gui.py` | GUI启动器 | 所有用户（推荐）|
| `launch_gazebo_safe.sh` | 安全模式 | 虚拟机用户 |
| `launch_gazebo_simple.sh` | 简单模式 | 快速测试 |
| `launch_gazebo.sh` | 标准模式 | 物理机用户 |
| `install_gazebo.sh` | 安装Gazebo | 首次使用 |
| `check_gazebo.sh` | 诊断Gazebo | 故障排除 |
| `check_opengl.sh` | 诊断OpenGL | 渲染问题 |
| `fix_dm_urdf.py` | 修复DM机器人 | DM模型无法加载 |

## 使用建议

### 首次使用

1. 安装Gazebo：`./tools/install_gazebo.sh`
2. 启动GUI：`./launch.sh`（从根目录）
3. 选择模型和选项

### 遇到问题

1. 检查Gazebo：`./tools/check_gazebo.sh`
2. 检查OpenGL：`./tools/check_opengl.sh`
3. 查看文档：`docs/guides/`

### 虚拟机用户

使用安全模式：
```bash
./tools/launch_gazebo_safe.sh
```

或在GUI中选择"安全模式"。

## 更多信息

查看完整文档：
- [快速开始](../docs/guides/START_HERE.md)
- [文档索引](../docs/guides/DOCUMENTATION_INDEX.md)
- [文件组织](../docs/guides/FILE_ORGANIZATION.md)
