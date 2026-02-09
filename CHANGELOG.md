# 变更日志

本文档记录项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [未发布]

### 新增
- CI/CD流水线配置
  - GitHub Actions自动化测试
  - 代码质量检查 (flake8, pylint, black, isort)
  - C++代码检查 (cppcheck)
  - 主分支保护规则
  - 安全扫描 (bandit)

- 并行仿真支持 (任务3.5)
  - ParallelMuJoCoBackend: 批量并行仿真
  - VectorizedMuJoCoEnvironment: 向量化环境接口
  - SimulationBenchmark: 性能基准测试工具
  - 4-8x训练加速

- 仿真架构增强
  - ConfigManager: 配置管理器
  - BackendRegistry: 后端注册表
  - 多后端无缝切换支持

### 变更
- 更新任务状态: 任务2.3和11.1标记为已完成

### 文档
- CI/CD流水线使用指南
- 并行仿真完整文档
- 任务3.5实现总结

## [0.1.0-alpha] - 2024-02-08

### 新增
- 增强GUI启动器
  - 支持自定义模型文件夹选择
  - 支持世界文件选择
  - 支持Gazebo和MuJoCo仿真器切换
  - 完整参数配置界面

- MuJoCo集成修复
  - 使用官方MuJoCo viewer
  - 虚拟环境路径自动检测
  - 显示问题诊断工具

### 修复
- 修复路径处理中的空格问题
- 修复GUI按钮布局问题
- 修复MuJoCo启动器显示问题

### 文档
- 增强GUI使用指南
- MuJoCo故障排除文档
- 启动器对比文档

## [0.0.1] - 初始版本

### 新增
- 项目基础设施
  - Git仓库和分支策略
  - ROS2工作空间结构
  - Python和C++混合开发环境

- URDF加载器
  - URDFLoader类实现
  - 关节和链接信息提取
  - 错误处理和验证

- 数字孪生映射器 (C++)
  - DigitalTwinMapper核心功能
  - 约束识别算法
  - 运动学求解器
  - Python绑定接口

- 仿真管理器
  - SimulationManager基类
  - GazeboSimulationBackend
  - MuJoCoSimulationBackend
  - 后端切换功能

- 关节控制系统
  - JointControllerNode
  - PID控制算法
  - ROS2通信接口

- IMU传感器仿真
  - IMUSimulator类
  - 传感器噪声模拟
  - ROS2数据发布

- 状态同步系统
  - StateSynchronizerNode
  - 状态历史记录
  - 网络延迟模拟

- 算法管理平台
  - AlgorithmManager
  - 强化学习环境接口
  - LQR控制器

- 数据记录与回放
  - DataRecorder类
  - DataPlayer类
  - ROS2 bag和CSV格式支持

- 用户控制界面
  - PyQt5主控制面板
  - 关节控制滑块
  - IMU数据可视化
  - ROS2集成

### 文档
- README和贡献指南
- 项目结构文档
- API使用示例

---

## 版本说明

### 版本号格式: MAJOR.MINOR.PATCH[-PRERELEASE]

- **MAJOR**: 不兼容的API变更
- **MINOR**: 向后兼容的功能新增
- **PATCH**: 向后兼容的问题修复
- **PRERELEASE**: 预发布版本标识 (alpha, beta, rc)

### 变更类型

- **新增**: 新功能
- **变更**: 现有功能的变更
- **弃用**: 即将移除的功能
- **移除**: 已移除的功能
- **修复**: 错误修复
- **安全**: 安全相关的修复
- **文档**: 文档更新
- **性能**: 性能改进
