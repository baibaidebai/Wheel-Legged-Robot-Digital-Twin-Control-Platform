# MuJoCo GUI黑屏问题诊断与解决方案

## 问题诊断

### 当前状态
✅ **GUI重构已完成** - 已移除假的2D可视化，集成真实MuJoCo物理仿真  
✅ **MuJoCo已安装** - v3.4.0 (在venv中)  
✅ **MuJoCo后端工作正常** - 测试通过，可以正常渲染  
❌ **GUI显示黑屏** - 因为依赖配置问题

### 根本原因

问题出在**Python环境依赖配置**上，而不是代码本身：

1. **MuJoCo已安装** - 在虚拟环境(venv)中正确安装
2. **PyQt5在系统Python中** - 未在venv中安装
3. **PyYAML在系统Python中** - 未在venv中安装  
4. **环境隔离** - venv无法访问系统包

当GUI启动时：
- 使用venv的Python → 有MuJoCo，但没有PyQt5
- 使用系统Python → 有PyQt5和PyYAML，但没有MuJoCo

## 解决方案

### 方案1：在venv中安装所有依赖（推荐）

```bash
# 激活虚拟环境
source venv/bin/activate

# 安装PyQt5
pip install PyQt5

# 安装PyYAML  
pip install PyYAML

# 验证所有依赖
python -c "import PyQt5; import yaml; import mujoco; print('✅ 所有依赖可用')"

# 启动GUI
python scripts/launch_main_application.py
```

### 方案2：使用系统Python + 添加venv包路径

```bash
# 设置Python路径包含venv的site-packages
export PYTHONPATH="$PWD/src/wheel_legged_control:$PWD/venv/lib/python3.12/site-packages:$PYTHONPATH"

# 使用系统Python启动
python3 scripts/launch_main_application.py
```

### 方案3：创建支持系统包的venv

```bash
# 删除现有venv
rm -rf venv

# 创建新venv，允许访问系统包
python3 -m venv --system-site-packages venv

# 激活并安装MuJoCo
source venv/bin/activate
pip install mujoco

# 启动GUI
python scripts/launch_main_application.py
```

## 验证步骤

### 1. 验证MuJoCo后端

```bash
./venv/bin/python3 test_mujoco_simple.py
```

预期输出：
```
✅ MuJoCo已安装: v3.4.0
✅ MuJoCo后端模块导入成功
✅ 创建测试模型: test_simple_robot.xml
✅ MuJoCo后端初始化成功
✅ 渲染成功! 图像尺寸: (480, 640, 3)
✅ 仿真步进成功
🎉 所有测试通过!
```

### 2. 验证GUI依赖

```bash
# 检查PyQt5
python3 -c "from PyQt5.QtWidgets import QApplication; print('✅ PyQt5可用')"

# 检查PyYAML
python3 -c "import yaml; print('✅ PyYAML可用')"

# 检查MuJoCo
./venv/bin/python3 -c "import mujoco; print('✅ MuJoCo可用')"
```

### 3. 启动GUI测试

```bash
# 使用测试脚本
./test_gui_mujoco.sh

# 或直接启动
python3 scripts/launch_main_application.py
```

## 技术细节

### MuJoCo渲染流程

1. **初始化** (`SimulationPage.__init__`)
   - 创建`SimulationManager`
   - 选择MuJoCo后端
   - 加载机器人URDF模型

2. **渲染循环** (`update_rendering()`)
   - 调用`simulation_manager.render(mode='rgb_array')`
   - MuJoCo后端执行离屏渲染
   - 返回RGB数组 (height, width, 3)
   - 转换为QPixmap显示在QLabel上

3. **仿真循环** (`step_simulation()`)
   - 调用`simulation_manager.step()`
   - 更新物理状态
   - 应用控制输入

### 关键代码位置

- **GUI主应用**: `src/wheel_legged_control/wheel_legged_control/gui/main_application.py`
- **MuJoCo后端**: `src/wheel_legged_control/wheel_legged_control/simulation/mujoco_backend.py`
- **仿真管理器**: `src/wheel_legged_control/wheel_legged_control/simulation/simulation_manager.py`
- **后端注册表**: `src/wheel_legged_control/wheel_legged_control/simulation/backend_registry.py`

### 渲染相关代码

```python
# main_application.py - SimulationPage类

def update_rendering(self):
    """更新渲染显示"""
    if self.simulation_manager and self.render_enabled:
        # 从仿真管理器获取渲染图像
        rgb_array = self.simulation_manager.render(mode='rgb_array')
        
        if rgb_array is not None and rgb_array.size > 0:
            # 转换为QPixmap并显示
            height, width, channel = rgb_array.shape
            bytes_per_line = 3 * width
            q_image = QImage(rgb_array.data, width, height, 
                           bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            
            # 缩放到标签大小
            scaled_pixmap = pixmap.scaled(
                self.render_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.render_label.setPixmap(scaled_pixmap)
```

## 已知问题

### OpenGL上下文警告

```
WARNING: ⚠️  渲染系统初始化失败: an OpenGL platform library has not been loaded
```

**影响**: 无实际影响，MuJoCo使用离屏渲染(EGL)，不需要显示OpenGL上下文  
**状态**: 渲染仍然正常工作，返回有效的RGB图像

### 网络超时

安装PyYAML时可能遇到网络超时：
```bash
# 使用更长的超时时间
pip install --default-timeout=100 pyyaml

# 或使用国内镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pyyaml
```

## 下一步

1. **选择并执行解决方案** - 推荐方案1（在venv中安装所有依赖）
2. **验证MuJoCo渲染** - 运行`test_mujoco_simple.py`
3. **启动GUI** - 运行`launch_main_application.py`
4. **测试功能**:
   - 选择机器人模型
   - 选择MuJoCo后端
   - 开始仿真
   - 验证3D可视化显示
   - 测试关节控制

## 参考文档

- **重构总结**: `docs/gui_mujoco_refactor_summary.md`
- **快速启动**: `docs/quick_start_mujoco_gui.md`
- **测试脚本**: `scripts/test_mujoco_gui.py`
- **验证脚本**: `scripts/verify_gui_refactor.py`

## 联系与支持

如果问题仍然存在，请提供：
1. 使用的解决方案编号
2. 完整的错误信息
3. Python版本和操作系统信息
4. 依赖验证步骤的输出
