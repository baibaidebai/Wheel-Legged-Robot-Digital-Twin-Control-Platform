# Gazebo仿真使用指南

## 🎯 为什么使用Gazebo？

**Gazebo是ROS的标准仿真器，对URDF有完美支持**

**优势**:
- ✅ 完美支持URDF格式（包括mesh文件）
- ✅ 不需要转换，直接加载你的机器人模型
- ✅ 完整的3D可视化
- ✅ 强大的物理引擎
- ✅ ROS集成
- ✅ 丰富的插件系统

## 🚀 快速启动

### 方法1：使用启动脚本（推荐）

```bash
./launch_gazebo.sh
```

### 方法2：直接运行Python脚本

```bash
python3 launch_gazebo.py
```

## 📋 使用流程

### 1. 启动脚本

```bash
cd "Wheel-Legged Robot Digital Twin Control Platform"
./launch_gazebo.sh
```

### 2. 选择机器人模型

程序会显示可用模型：

```
📦 可用的机器人模型:
  1. ✅ RM_Serial_Wheeled-leg_Robot - RM串联轮腿机器人
  2. ✅ DM_Wheel_leg_robot - DM轮腿机器人

请选择模型 (1-2) [默认: 1]:
```

输入数字选择，或直接按回车使用默认模型。

### 3. Gazebo自动启动

程序会：
1. 检查Gazebo是否安装
2. 创建仿真world
3. 启动Gazebo窗口
4. 显示如何加载机器人模型

### 4. 在Gazebo中加载模型

Gazebo窗口打开后，有两种方法加载模型：

#### 方法A：使用GUI（推荐）

1. 点击左侧的 **"Insert"** 标签
2. 点击 **"Add Path"** 按钮
3. 添加模型路径（脚本会显示具体路径）
4. 在模型列表中找到你的机器人
5. 拖动模型到场景中

#### 方法B：使用命令行

在另一个终端运行（脚本会显示具体命令）：

```bash
gz model --spawn-file=<urdf路径> --model-name=robot -x 0 -y 0 -z 0.5
```

## 🎮 Gazebo控制

### 视角控制

| 操作 | 功能 |
|------|------|
| 鼠标左键拖动 | 旋转视角 |
| 鼠标滚轮 | 缩放 |
| Shift+鼠标左键 | 平移视角 |
| 鼠标中键拖动 | 平移视角（备选） |

### 仿真控制

| 按钮/快捷键 | 功能 |
|------------|------|
| ▶️ 播放按钮 | 开始/暂停仿真 |
| ⏸️ 暂停按钮 | 暂停仿真 |
| ⏹️ 停止按钮 | 停止并重置仿真 |
| Ctrl+R | 重置世界 |

### 模型操作

| 工具 | 功能 |
|------|------|
| 选择工具 | 选择和移动模型 |
| 平移工具 | 平移模型位置 |
| 旋转工具 | 旋转模型 |
| 缩放工具 | 缩放模型 |

## 🎨 Gazebo功能

### 1. 完整的3D可视化

- 真实的机器人模型渲染（使用STL网格）
- 环境和地面
- 光照和阴影
- 碰撞检测可视化

### 2. 物理仿真

- 重力
- 碰撞
- 摩擦
- 关节约束
- 力和力矩

### 3. 传感器仿真

- 相机
- 激光雷达
- IMU
- 接触传感器
- GPS

### 4. 插件系统

可以添加各种插件：
- 控制器插件
- 传感器插件
- 世界插件
- 可视化插件

## 📊 与MuJoCo对比

| 特性 | Gazebo | MuJoCo |
|------|--------|--------|
| URDF支持 | ✅ 完美 | ⚠️ 有限 |
| Mesh文件 | ✅ 完美 | ⚠️ 需要转换 |
| ROS集成 | ✅ 原生 | ❌ 需要桥接 |
| 物理精度 | 高 | 非常高 |
| 性能 | 中等 | 高 |
| 强化学习 | 可用 | 优秀 |
| 学习曲线 | 平缓 | 陡峭 |

## 💡 使用建议

### 何时使用Gazebo

**推荐场景**:
- 使用现有的URDF模型
- 需要ROS集成
- 机器人开发和测试
- 教学和演示
- 传感器仿真

### 何时使用MuJoCo

**推荐场景**:
- 强化学习训练
- 需要极高性能
- 简化的物理模型
- 批量仿真

## 🔧 安装Gazebo

### Ubuntu 20.04

```bash
sudo apt-get update
sudo apt-get install gazebo11 libgazebo11-dev
```

### Ubuntu 22.04

```bash
sudo apt-get update
sudo apt-get install gazebo11 libgazebo11-dev
```

### 使用ROS2

```bash
# ROS2 Humble
sudo apt-get install ros-humble-gazebo-ros-pkgs

# ROS2 Foxy
sudo apt-get install ros-foxy-gazebo-ros-pkgs
```

### 验证安装

```bash
gazebo --version
```

应该显示类似：
```
Gazebo multi-robot simulator, version 11.x.x
```

## 🔍 故障排除

### 问题1：Gazebo无法启动

**症状**: 运行脚本后没有窗口

**解决**:
```bash
# 检查Gazebo是否安装
gazebo --version

# 尝试手动启动
gazebo

# 检查显示
echo $DISPLAY
```

### 问题2：模型不显示

**症状**: Gazebo打开但看不到机器人

**解决**:
1. 检查URDF文件路径是否正确
2. 检查mesh文件是否存在
3. 查看Gazebo终端输出的错误信息
4. 尝试手动插入模型

### 问题3：模型显示为方块

**症状**: 机器人显示为简单的几何体

**可能原因**:
- Mesh文件路径不正确
- Mesh文件格式不支持
- URDF中没有visual元素

**解决**:
1. 检查URDF中的mesh路径
2. 确认mesh文件存在
3. 尝试使用绝对路径

### 问题4：物理行为异常

**症状**: 机器人掉落、穿透地面等

**解决**:
1. 检查collision元素是否正确
2. 调整质量和惯性参数
3. 检查关节限制
4. 调整物理引擎参数

### 问题5：性能问题

**症状**: Gazebo运行缓慢

**解决**:
1. 降低实时因子
2. 简化mesh模型
3. 减少传感器数量
4. 关闭阴影和反射

## 📚 进一步学习

### Gazebo文档

- [Gazebo官方教程](http://gazebosim.org/tutorials)
- [Gazebo API文档](http://osrf-distributions.s3.amazonaws.com/gazebo/api/dev/index.html)
- [ROS-Gazebo集成](http://wiki.ros.org/gazebo_ros_pkgs)

### URDF教程

- [URDF官方文档](http://wiki.ros.org/urdf)
- [URDF教程](http://wiki.ros.org/urdf/Tutorials)
- [Xacro宏语言](http://wiki.ros.org/xacro)

## 🎉 总结

**Gazebo是使用URDF模型的最佳选择**:
- ✅ 完美支持URDF和mesh文件
- ✅ 不需要任何转换
- ✅ 完整的3D可视化
- ✅ 强大的功能
- ✅ ROS生态系统

**现在就试试吧**:
```bash
./launch_gazebo.sh
```

选择你的机器人模型，享受完整的3D仿真体验！🤖

## 🆚 选择指南

| 需求 | 推荐仿真器 |
|------|-----------|
| 使用URDF模型 | **Gazebo** ⭐ |
| ROS开发 | **Gazebo** ⭐ |
| 强化学习 | **MuJoCo** ⭐ |
| 快速原型 | **MuJoCo** ⭐ |
| 传感器仿真 | **Gazebo** ⭐ |
| 高性能计算 | **MuJoCo** ⭐ |

根据你的需求选择合适的仿真器！
