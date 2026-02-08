# 文件组织说明

## 📁 整理后的项目结构

### 主目录（根目录）

**保留的文件**：
- `launch_gazebo.sh` - Gazebo启动脚本（主要入口）⭐
- `README.md` - 项目主文档
- `GAZEBO_QUICKSTART.md` - Gazebo快速开始指南
- `CONTRIBUTING.md` - 贡献指南
- `PROJECT_STATUS.md` - 项目状态
- `QUICK_START.md` - 快速开始
- `requirements.txt` - Python依赖
- `pytest.ini` - 测试配置
- `fix_dependencies.sh` - 依赖修复脚本

### scripts/ 目录

**保留的文件**：
- `demo_*.py` - 各种演示脚本
- `launch_main_application.py` - 主应用启动
- `validate_urdf_models.py` - URDF验证
- `verify_*.py` - 验证脚本

**子目录**：
- `scripts/gazebo/` - Gazebo相关脚本（备用）
- `scripts/archive/` - 归档的MuJoCo相关脚本

### docs/ 目录

**保留的文件**：
- `GAZEBO_GUIDE.md` - Gazebo详细指南
- `SIMULATION_OPTIONS.md` - 仿真选项对比
- `START_HERE.md` - 开始指南
- `*.md` - 其他项目文档

**子目录**：
- `docs/archive/` - 归档的旧文档

### src/ 目录

**机器人模型**：
- `src/model/RM_Serial_Wheeled-leg_Robot/` - RM机器人
- `src/model/DM_Wheel_leg_robot/` - DM机器人

**控制系统**：
- `src/wheel_legged_control/` - 主要代码库

### test/ 目录

**测试文件**：
- `test/python/` - Python单元测试
- `test/integration/` - 集成测试

### data/ 目录

**实验数据**：
- `data/demo_recordings/` - 演示录制
- `data/advanced_recordings/` - 高级实验数据

## 🗑️ 已删除的文件

### 测试文件
- `test_*.py` - 临时测试脚本
- `test_*.sh` - 测试shell脚本
- `diagnose_black_screen.py` - 诊断脚本
- `test_fallback_render.py` - 渲染测试
- `test_render_output.png` - 测试图片
- `test_diagnose.xml` - 诊断XML

### 临时文件
- `MUJOCO_LOG.TXT` - MuJoCo日志
- `launch_gui.sh` - 有问题的GUI启动脚本

## 📦 归档的文件

### scripts/archive/
- MuJoCo相关启动脚本
- URDF修复工具
- 旧的仿真启动器

### docs/archive/
- 旧的GUI文档
- MuJoCo诊断文档
- OpenGL问题文档

## 🎯 推荐的工作流程

### 1. 开始仿真
```bash
./launch_gazebo.sh
```

### 2. 查看文档
- 快速开始：`GAZEBO_QUICKSTART.md`
- 详细指南：`docs/GAZEBO_GUIDE.md`
- 项目README：`README.md`

### 3. 运行演示
```bash
python3 scripts/demo_lqr_controller.py
python3 scripts/demo_ppo_training.py
```

### 4. 开发和测试
- 编辑代码：`src/wheel_legged_control/`
- 运行测试：`pytest test/`
- 记录数据：`data/`

## 📝 文件命名规范

### 脚本文件
- `launch_*.sh` - 启动脚本
- `demo_*.py` - 演示脚本
- `verify_*.py` - 验证脚本
- `validate_*.py` - 验证脚本

### 文档文件
- `*_GUIDE.md` - 指南文档
- `*_QUICKSTART.md` - 快速开始
- `README.md` - 主文档
- `CONTRIBUTING.md` - 贡献指南

## 🔄 维护建议

### 定期清理
1. 删除临时文件
2. 归档旧的实验数据
3. 更新文档

### 添加新功能
1. 代码放在 `src/wheel_legged_control/`
2. 测试放在 `test/`
3. 文档放在 `docs/`
4. 演示脚本放在 `scripts/`

### 版本控制
- 使用Git管理代码
- 忽略临时文件（`.gitignore`）
- 定期提交和推送

## ✅ 整理完成

项目文件已经整理完毕，结构清晰，易于维护和使用。

**主要入口**：`./launch_gazebo.sh`

**主要文档**：`GAZEBO_QUICKSTART.md`

开始你的仿真之旅吧！🚀
