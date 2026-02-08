# ROS2 GUI集成使用指南

## 概述

ROS2集成控制面板是轮腿机器人孪生控制系统的图形用户界面，提供了与ROS2系统的完整集成。通过这个界面，用户可以实时监控机器人状态、控制关节运动、查看IMU数据，并与ROS2节点进行交互。

## 功能特性

### 🎮 关节控制
- **实时关节控制**: 通过滑块直接控制机器人关节
- **自动指令发送**: 可选择自动发送关节指令到ROS2系统
- **关节状态监控**: 实时显示指令角度、实际角度和误差
- **安全限制**: 关节运动范围限制和安全检查

### 📊 数据可视化
- **机器人可视化**: 2D机器人模型实时显示
- **IMU数据显示**: 姿态、角速度、加速度实时可视化
- **数据表格**: 详细的关节数据表格显示
- **状态监控**: 系统连接状态和运行状态

### 🔧 系统控制
- **紧急停止**: 一键紧急停止所有运动
- **关节复位**: 将所有关节复位到零位
- **控制器使能**: 启用/禁用关节控制器
- **步态演示**: 预设步态序列演示

### 📡 ROS2集成
- **话题通信**: 关节状态发布、指令订阅、IMU数据订阅
- **服务调用**: 紧急停止、复位、使能服务
- **实时通信**: 100Hz高频数据交换
- **连接监控**: ROS2连接状态实时监控

## 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GUI控制面板   │◄──►│  ROS2通信层     │◄──►│  机器人控制器   │
│                 │    │                 │    │                 │
│ • 关节控制滑块  │    │ • 话题发布/订阅 │    │ • 关节控制器    │
│ • 状态显示      │    │ • 服务调用      │    │ • IMU发布器     │
│ • IMU可视化     │    │ • QoS配置       │    │ • 状态同步器    │
│ • 系统监控      │    │ • 多线程执行    │    │ • 安全监控      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 安装和配置

### 依赖要求

```bash
# ROS2 Jazzy
sudo apt install ros-jazzy-desktop

# Python依赖
pip3 install PyQt5 numpy scipy matplotlib

# 构建工具
sudo apt install python3-colcon-common-extensions
```

### 构建项目

```bash
# 进入工作空间
cd wheel-legged-robot-twin-control

# 构建项目
colcon build --symlink-install

# 设置环境
source install/setup.bash
```

## 使用方法

### 方法1: 使用Launch文件（推荐）

```bash
# 启动完整系统
ros2 launch wheel_legged_control ros2_control_panel.launch.py

# 自定义参数启动
ros2 launch wheel_legged_control ros2_control_panel.launch.py \
    use_sim_time:=true \
    robot_name:=my_robot
```

### 方法2: 分步启动

```bash
# 终端1: 启动关节控制器
ros2 run wheel_legged_control joint_controller_node

# 终端2: 启动IMU发布器
ros2 run wheel_legged_control imu_publisher_node

# 终端3: 启动GUI控制面板
ros2 run wheel_legged_control ros2_control_panel
```

### 方法3: 直接运行Python脚本

```bash
# 启动GUI（需要先启动ROS2节点）
python3 src/wheel_legged_control/wheel_legged_control/gui/ros2_control_panel.py
```

## 界面说明

### 左侧控制面板

#### ROS2连接状态
- **🟢 已连接**: ROS2通信正常
- **🔴 未连接**: ROS2通信断开
- **自动发送关节指令**: 勾选后自动发送滑块变化

#### 关节控制区域
- **关节滑块**: 每个关节对应一个滑块控制器
- **角度显示**: 实时显示当前设置角度
- **范围限制**: 根据URDF文件自动设置关节限制

#### 控制操作按钮
- **复位关节**: 将所有关节设置为0度
- **演示步态**: 执行预设的步态序列
- **启用/禁用控制器**: 切换控制器使能状态
- **紧急停止**: 立即停止所有运动并复位

### 中间显示面板

#### 机器人可视化
- **2D机器人模型**: 实时显示机器人姿态
- **关节连线**: 显示腿部连接关系
- **轮子显示**: 显示轮子位置和状态

#### 关节数据表格
- **关节名称**: 显示所有关节名称
- **指令角度**: 用户设置的目标角度
- **实际角度**: 从ROS2接收的实际角度
- **误差**: 指令与实际的差值
- **状态**: 正常/偏差/异常状态指示

### 右侧状态面板

#### IMU传感器显示
- **姿态角度**: Roll, Pitch, Yaw角度
- **角速度**: 三轴角速度数据
- **线性加速度**: 三轴加速度数据

#### 系统状态
- **仿真状态**: 显示仿真运行状态
- **控制模式**: 当前控制模式
- **关节数量**: 加载的关节总数

#### 系统日志
- **实时日志**: 显示系统操作和状态信息
- **时间戳**: 每条日志带有时间戳
- **颜色编码**: 不同类型消息使用不同颜色

## ROS2话题和服务

### 订阅的话题

| 话题名称 | 消息类型 | 频率 | 描述 |
|---------|---------|------|------|
| `/joint_states` | `sensor_msgs/JointState` | 100Hz | 关节状态数据 |
| `/imu/data` | `sensor_msgs/Imu` | 100Hz | IMU传感器数据 |
| `/joint_controller_state` | `control_msgs/JointTrajectoryControllerState` | 10Hz | 控制器状态 |

### 发布的话题

| 话题名称 | 消息类型 | 频率 | 描述 |
|---------|---------|------|------|
| `/joint_commands` | `std_msgs/Float64MultiArray` | 变化时 | 关节位置指令 |

### 调用的服务

| 服务名称 | 服务类型 | 描述 |
|---------|---------|------|
| `/joint_controller/emergency_stop` | `std_srvs/Trigger` | 紧急停止 |
| `/joint_controller/reset` | `std_srvs/Trigger` | 复位关节 |
| `/joint_controller/enable` | `std_srvs/SetBool` | 使能控制器 |

## 测试和验证

### 基本功能测试

```bash
# 运行集成测试
python3 test_ros2_gui_integration.py

# 运行GUI启动测试
python3 test_gui_launch.py
```

### 手动测试步骤

1. **启动系统**
   ```bash
   ros2 launch wheel_legged_control ros2_control_panel.launch.py
   ```

2. **验证连接状态**
   - 检查左上角连接状态显示为"🟢 已连接"
   - 查看系统日志确认ROS2节点启动成功

3. **测试关节控制**
   - 移动关节滑块
   - 观察机器人可视化更新
   - 检查数据表格中的角度变化

4. **测试IMU数据**
   - 观察右侧IMU数据显示
   - 验证姿态角度和加速度数据

5. **测试服务调用**
   - 点击"复位关节"按钮
   - 点击"紧急停止"按钮
   - 切换"启用/禁用控制器"

### 性能监控

```bash
# 监控话题频率
ros2 topic hz /joint_states
ros2 topic hz /imu/data

# 监控系统资源
htop
```

## 故障排除

### 常见问题

#### 1. GUI无法启动
```bash
# 检查PyQt5安装
python3 -c "from PyQt5.QtWidgets import QApplication; print('PyQt5 OK')"

# 检查ROS2环境
echo $ROS_DISTRO
```

#### 2. ROS2连接失败
```bash
# 检查ROS2节点
ros2 node list

# 检查话题
ros2 topic list

# 重启ROS2守护进程
ros2 daemon stop
ros2 daemon start
```

#### 3. 关节控制无响应
```bash
# 检查关节控制器节点
ros2 node info /joint_controller

# 检查关节指令话题
ros2 topic echo /joint_commands
```

#### 4. IMU数据异常
```bash
# 检查IMU发布器
ros2 node info /imu_publisher

# 检查IMU数据话题
ros2 topic echo /imu/data
```

### 调试模式

启用详细日志输出：

```bash
# 设置ROS2日志级别
export RCUTILS_LOGGING_SEVERITY=DEBUG

# 启动系统
ros2 launch wheel_legged_control ros2_control_panel.launch.py
```

## 扩展开发

### 添加新的控制功能

1. **修改GUI界面**
   ```python
   # 在ros2_control_panel.py中添加新的控件
   self.new_button = QPushButton("新功能")
   self.new_button.clicked.connect(self.new_function)
   ```

2. **添加ROS2通信**
   ```python
   # 在ROS2Worker中添加新的发布器或订阅器
   self.new_publisher = self.node.create_publisher(
       NewMessageType, '/new_topic', 10)
   ```

3. **实现业务逻辑**
   ```python
   def new_function(self):
       # 实现新功能逻辑
       pass
   ```

### 自定义机器人模型

1. **修改URDF文件路径**
   ```python
   robot_urdf = "path/to/your/robot.urdf"
   ```

2. **更新关节名称映射**
   ```python
   self.joint_names = ['joint1', 'joint2', 'joint3', 'joint4']
   ```

## 版本历史

- **v0.2.0**: ROS2集成控制面板首次发布
- **v0.1.0**: 基础PyQt5控制面板

## 贡献指南

欢迎提交Issue和Pull Request来改进这个项目。请遵循以下规范：

1. 使用约定式提交格式
2. 添加适当的测试
3. 更新相关文档
4. 确保代码风格一致

## 许可证

本项目采用MIT许可证，详见LICENSE文件。