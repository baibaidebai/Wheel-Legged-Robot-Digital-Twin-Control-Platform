# 故障排除指南

完整的问题诊断和解决方案。

## 📖 目录

1. [安装问题](#安装问题)
2. [仿真问题](#仿真问题)
3. [ROS2问题](#ros2问题)
4. [性能问题](#性能问题)
5. [数据问题](#数据问题)
6. [诊断工具](#诊断工具)

---

## 安装问题

### 问题: ROS2安装失败

**症状**: 无法安装ROS2 Jazzy

**解决方案**:
```bash
# 1. 检查Ubuntu版本
lsb_release -a  # 应该是24.04

# 2. 清理旧的ROS2源
sudo rm /etc/apt/sources.list.d/ros2*.list

# 3. 重新添加ROS2源
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

# 4. 更新并安装
sudo apt update
sudo apt install ros-jazzy-desktop
```

### 问题: Python依赖安装失败

**症状**: `pip install -r requirements.txt` 失败

**解决方案**:
```bash
# 1. 升级pip
pip install --upgrade pip

# 2. 安装系统依赖
sudo apt-get install python3-dev build-essential

# 3. 逐个安装依赖
pip install numpy
pip install scipy
pip install matplotlib
pip install PyQt5
pip install mujoco

# 4. 如果仍然失败，使用conda
conda create -n wheel_legged python=3.12
conda activate wheel_legged
pip install -r requirements.txt
```

### 问题: colcon build失败

**症状**: 构建ROS2包时出错

**解决方案**:
```bash
# 1. 清理构建文件
rm -rf build install log

# 2. 确保环境正确
source /opt/ros/jazzy/setup.bash

# 3. 安装构建依赖
sudo apt install python3-colcon-common-extensions

# 4. 重新构建
colcon build --symlink-install

# 5. 如果C++编译失败
sudo apt install cmake g++ libpython3-dev
```

---

## 仿真问题

### Gazebo问题

#### 问题: Gazebo窗口无法打开

**症状**: 运行启动脚本后Gazebo窗口不出现

**诊断**:
```bash
# 检查Gazebo安装
gz sim --version

# 检查Gazebo进程
ps aux | grep gz

# 查看错误日志
gz sim --verbose 4
```

**解决方案**:
```bash
# 方案1: 重新安装Gazebo
./tools/install_gazebo.sh

# 方案2: 使用安全模式
./tools/launch_gazebo_safe.sh

# 方案3: 检查显示设置
echo $DISPLAY  # 应该输出 :0 或类似值
export DISPLAY=:0

# 方案4: 检查OpenGL支持
./tools/check_opengl.sh
```

#### 问题: Gazebo闪屏或黑屏

**症状**: Gazebo窗口打开但显示异常

**解决方案**:
```bash
# 1. 禁用硬件加速
export LIBGL_ALWAYS_SOFTWARE=1
./tools/launch_gazebo_safe.sh

# 2. 更新显卡驱动
sudo ubuntu-drivers autoinstall

# 3. 使用简单模式
./tools/launch_gazebo_simple.sh

# 4. 检查虚拟机设置（如果使用虚拟机）
# - 启用3D加速
# - 增加显存到128MB+
```

#### 问题: 机器人模型不显示

**症状**: Gazebo打开但看不到机器人

**解决方案**:
```bash
# 1. 检查URDF文件
gz sdf -p path/to/robot.urdf

# 2. 检查mesh文件路径
ls -la src/model/*/meshes/

# 3. 修复DM机器人模型
python3 tools/fix_dm_urdf.py

# 4. 使用绝对路径
# 编辑URDF文件，将mesh路径改为绝对路径
```

### MuJoCo问题

#### 问题: MuJoCo无法加载模型

**症状**: `mujoco.FatalError` 或模型加载失败

**诊断**:
```bash
# 检查MuJoCo安装
python3 -c "import mujoco; print(mujoco.__version__)"

# 测试简单模型
python3 -c "
import mujoco
model = mujoco.MjModel.from_xml_string('<mujoco><worldbody><body><geom size=\"0.1\"/></body></worldbody></mujoco>')
print('MuJoCo工作正常')
"
```

**解决方案**:
```bash
# 1. 重新安装MuJoCo
pip uninstall mujoco
pip install mujoco

# 2. 转换URDF到MJCF
python3 tools/convert_urdf_to_mjcf.py --model rm

# 3. 使用Wiki-GRx-MJCF工具
cd ~/workspace
git clone https://github.com/FFTAI/Wiki-MJCF.git
pip install -e Wiki-GRx-MJCF
python3 tools/test_wiki_mjcf.py

# 4. 检查模型文件
# 确保XML格式正确，mesh文件存在
```

#### 问题: MuJoCo显示黑屏

**症状**: MuJoCo窗口打开但显示黑色

**解决方案**:
```bash
# 1. 检查OpenGL
./tools/check_opengl.sh

# 2. 使用软件渲染
export MUJOCO_GL=osmesa
python3 tools/launch_mujoco.py

# 3. 更新显卡驱动
sudo ubuntu-drivers autoinstall

# 4. 在虚拟机中
# - 启用3D加速
# - 使用SVGA II显卡
```

---

## ROS2问题

### 问题: 节点无法通信

**症状**: 节点启动但无法接收/发送消息

**诊断**:
```bash
# 检查节点
ros2 node list

# 检查话题
ros2 topic list

# 检查话题数据
ros2 topic echo /joint_states

# 检查节点信息
ros2 node info /joint_controller_node
```

**解决方案**:
```bash
# 1. 检查ROS2环境
source /opt/ros/jazzy/setup.bash
source install/setup.bash

# 2. 检查ROS_DOMAIN_ID
echo $ROS_DOMAIN_ID
# 如果多台机器，确保ID相同

# 3. 检查网络
# 禁用防火墙或添加ROS2规则
sudo ufw allow from 224.0.0.0/4
sudo ufw allow from 239.0.0.0/8

# 4. 使用localhost通信
export ROS_LOCALHOST_ONLY=1
```

### 问题: 消息类型不匹配

**症状**: `TypeError` 或消息发布/订阅失败

**解决方案**:
```bash
# 1. 重新构建消息包
cd src/wheel_legged_control_msgs
colcon build --packages-select wheel_legged_control_msgs

# 2. 重新source
source install/setup.bash

# 3. 检查消息定义
ros2 interface show wheel_legged_control_msgs/msg/JointCommand

# 4. 清理并重建
rm -rf build install log
colcon build
```

### 问题: Launch文件失败

**症状**: `ros2 launch` 命令失败

**解决方案**:
```bash
# 1. 检查launch文件语法
python3 -m py_compile src/wheel_legged_control/launch/complete_system.launch.py

# 2. 使用详细输出
ros2 launch wheel_legged_control complete_system.launch.py --debug

# 3. 检查依赖
ros2 pkg list | grep wheel_legged

# 4. 重新安装包
colcon build --packages-select wheel_legged_control
source install/setup.bash
```

---

## 性能问题

### 问题: 仿真运行缓慢

**症状**: 仿真帧率低，响应慢

**诊断**:
```python
from wheel_legged_control.utils import PerformanceMonitor

monitor = PerformanceMonitor()
# 运行仿真...
print(monitor.generate_report())
```

**解决方案**:
```bash
# 1. 使用MuJoCo而不是Gazebo
# MuJoCo通常更快

# 2. 减小仿真时间步长
# 在配置文件中设置更大的timestep

# 3. 禁用可视化
# 使用headless模式

# 4. 使用并行仿真
from wheel_legged_control.simulation import ParallelMuJoCoBackend
parallel_sim = ParallelMuJoCoBackend("robot.xml", num_envs=8)

# 5. 优化代码
# 使用性能监控器识别瓶颈
```

### 问题: 内存使用过高

**症状**: 系统内存不足，程序崩溃

**诊断**:
```python
from wheel_legged_control.core import SystemDiagnostics

diag = SystemDiagnostics()
print(diag.check_memory_usage())
```

**解决方案**:
```bash
# 1. 减少并行环境数量
# num_envs = 4 而不是 8

# 2. 清理数据记录
# 定期保存并清空记录器

# 3. 使用数据流而不是批量加载
# 逐步处理数据而不是一次性加载

# 4. 监控内存
watch -n 1 free -h
```

### 问题: CPU使用率100%

**症状**: CPU占用过高，系统卡顿

**解决方案**:
```bash
# 1. 限制仿真频率
# 在配置中设置合理的control_frequency

# 2. 使用多进程而不是多线程
parallel_sim = ParallelMuJoCoBackend(
    "robot.xml",
    num_envs=8,
    use_multiprocessing=True
)

# 3. 优化控制算法
# 减少不必要的计算

# 4. 使用nice降低优先级
nice -n 10 python3 scripts/demo_ppo_training.py
```

---

## 数据问题

### 问题: 数据记录失败

**症状**: 数据无法保存或文件损坏

**解决方案**:
```bash
# 1. 检查磁盘空间
df -h

# 2. 检查写入权限
ls -la data/

# 3. 使用绝对路径
recorder = DataRecorder("/absolute/path/to/data", "experiment")

# 4. 定期保存
# 不要等到最后才保存
recorder.save()  # 定期调用
```

### 问题: 数据回放不同步

**症状**: 回放数据与仿真不匹配

**解决方案**:
```python
# 1. 检查时间戳
player = DataPlayer("data/experiment")
player.load()
print(player.get_timestamps())

# 2. 使用固定时间步长
player.play(speed=1.0, use_timestamps=True)

# 3. 重新记录数据
# 确保记录时使用正确的时间戳
```

---

## 诊断工具

### 系统诊断

```bash
# 运行完整系统诊断
python3 -c "
from wheel_legged_control.core import SystemDiagnostics
diag = SystemDiagnostics()
print(diag.generate_report())
"
```

### Gazebo诊断

```bash
# 检查Gazebo
./tools/check_gazebo.sh

# 详细输出
gz sim --verbose 4 path/to/world.sdf
```

### OpenGL诊断

```bash
# 检查OpenGL支持
./tools/check_opengl.sh

# 查看显卡信息
glxinfo | grep "OpenGL version"
```

### ROS2诊断

```bash
# 检查ROS2环境
printenv | grep ROS

# 检查节点
ros2 node list
ros2 node info /node_name

# 检查话题
ros2 topic list
ros2 topic hz /topic_name
ros2 topic bw /topic_name

# 检查服务
ros2 service list
ros2 service type /service_name
```

### 性能诊断

```python
from wheel_legged_control.utils import PerformanceMonitor

monitor = PerformanceMonitor()

# 运行你的代码...

# 生成报告
print(monitor.generate_report())

# 查找慢函数
slow_funcs = monitor.get_slow_functions(threshold=0.1)
for func in slow_funcs:
    print(f"{func.name}: {func.avg_time*1000:.2f}ms")
```

---

## 获取帮助

如果以上方法都无法解决问题：

1. **查看日志**:
   ```bash
   # ROS2日志
   cat ~/.ros/log/latest/rosout.log
   
   # 系统日志
   journalctl -xe
   ```

2. **启用调试模式**:
   ```bash
   export ROS_LOG_LEVEL=DEBUG
   python3 scripts/demo_main_application.py --log-level DEBUG
   ```

3. **提交Issue**:
   - 访问GitHub Issues
   - 提供详细的错误信息
   - 包含系统信息和日志

4. **社区支持**:
   - 查看项目文档
   - 搜索已有的Issues
   - 参与讨论区

---

**版本**: 1.0.0  
**最后更新**: 2026-02-09
