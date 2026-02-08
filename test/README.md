# 测试目录说明

本目录包含轮腿机器人孪生控制系统的所有测试文件。

## 目录结构

```
test/
├── run_tests.py              # 统一测试运行器
├── README.md                 # 本文件
├── cpp/                      # C++测试
│   └── test_digital_twin_mapper.cpp
├── python/                   # Python单元测试
│   ├── test_basic.py
│   ├── test_digital_twin_mapper_bindings.py
│   ├── test_imu_simulator.py
│   ├── test_joint_controller.py
│   └── test_urdf_loader.py
├── integration/              # 集成测试
│   ├── test_ros2_gui_integration.py      # ROS2 GUI集成测试
│   ├── test_imu_system.py               # IMU系统测试
│   ├── test_imu_publisher_basic.py      # IMU发布器测试
│   ├── test_joint_controller_basic.py   # 关节控制器测试
│   ├── test_ros2_interface_basic.py     # ROS2接口测试
│   ├── test_gazebo_integration.py       # Gazebo集成测试
│   └── test_gazebo_urdf.py              # Gazebo URDF测试
├── gui/                      # GUI测试
│   └── test_gui_launch.py               # GUI启动测试
└── deprecated/               # 过时的测试文件
    ├── test_basic_bindings_only.py
    ├── test_bindings_safe.py
    ├── test_complete_bindings.py
    ├── test_core_functionality.py
    ├── test_final_bindings.py
    ├── test_minimal_binding.py
    ├── test_simple_binding.py
    └── test_step_by_step.py
```

## 测试类型

### 1. C++测试 (`cpp/`)
- 使用gtest框架
- 测试C++核心模块（数字孪生映射器等）
- 通过colcon test运行

### 2. Python单元测试 (`python/`)
- 使用pytest框架
- 测试Python模块的单个功能
- 包含属性测试（Hypothesis）

### 3. 集成测试 (`integration/`)
- 测试多个模块间的协作
- ROS2节点间通信测试
- 系统级功能验证

### 4. GUI测试 (`gui/`)
- PyQt5界面测试
- 用户交互测试
- 界面启动和基本功能验证

### 5. 过时测试 (`deprecated/`)
- 开发过程中的临时测试文件
- 已被更好的测试替代
- 保留用于参考，不在CI中运行

## 运行测试

### 运行所有测试
```bash
python3 test/run_tests.py --all
```

### 运行特定类型测试
```bash
# GUI测试
python3 test/run_tests.py --gui

# 集成测试
python3 test/run_tests.py --integration

# Python单元测试
python3 test/run_tests.py --python

# C++测试
python3 test/run_tests.py --cpp
```

### 手动运行单个测试
```bash
# 运行特定集成测试
python3 test/integration/test_ros2_gui_integration.py

# 运行Python单元测试
python3 -m pytest test/python/test_joint_controller.py -v

# 运行C++测试
colcon test --packages-select wheel_legged_control
```

## 测试环境要求

### 基本要求
- Ubuntu 20.04/22.04
- ROS2 Jazzy
- Python 3.8+
- PyQt5

### 构建要求
```bash
# 构建项目
colcon build --symlink-install

# 设置环境
source install/setup.bash
```

### Python依赖
```bash
pip3 install pytest hypothesis numpy scipy matplotlib PyQt5
```

## 测试开发指南

### 添加新测试

1. **单元测试**: 添加到 `python/` 目录
2. **集成测试**: 添加到 `integration/` 目录
3. **GUI测试**: 添加到 `gui/` 目录
4. **C++测试**: 添加到 `cpp/` 目录

### 测试命名规范

- 文件名: `test_<模块名>.py` 或 `test_<功能名>.py`
- 测试函数: `test_<具体功能>()`
- 测试类: `Test<模块名>`

### 测试文档

每个测试文件应包含：
- 文件头部的功能说明
- 测试用例的详细注释
- 预期结果的说明

## CI/CD集成

测试运行器支持CI/CD集成：

```yaml
# GitHub Actions示例
- name: Run Tests
  run: |
    source install/setup.bash
    python3 test/run_tests.py --all
```

## 故障排除

### 常见问题

1. **ROS2环境未设置**
   ```bash
   source /opt/ros/jazzy/setup.bash
   source install/setup.bash
   ```

2. **PyQt5显示问题**
   ```bash
   export QT_QPA_PLATFORM=offscreen  # 无头模式
   ```

3. **权限问题**
   ```bash
   chmod +x test/run_tests.py
   ```

### 调试模式

启用详细输出：
```bash
python3 test/run_tests.py --all --verbose
```