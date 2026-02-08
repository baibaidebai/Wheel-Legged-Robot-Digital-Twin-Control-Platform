# MuJoCo直接启动指南

## 🎯 为什么使用直接启动？

**问题**: PyQt5 GUI集成MuJoCo渲染容易出现OpenGL问题，导致黑屏

**解决方案**: 跳过GUI，直接使用MuJoCo的原生交互式查看器

**优势**:
- ✅ 避免GUI渲染问题
- ✅ 使用MuJoCo原生查看器（功能更强大）
- ✅ 更稳定可靠
- ✅ 更好的性能
- ✅ 完整的3D可视化
- ✅ 内置控制器和调试工具

## 🚀 快速启动

### 方法1：使用启动脚本（推荐）

```bash
./launch_mujoco.sh
```

### 方法2：直接运行Python脚本

```bash
python3 launch_mujoco_direct.py
```

## 📋 使用流程

### 1. 启动程序

```bash
cd "Wheel-Legged Robot Digital Twin Control Platform"
./launch_mujoco.sh
```

### 2. 选择机器人模型

程序会显示可用模型：

```
📦 可用的机器人模型:
  1. ✅ RM_Serial_Wheeled-leg_Robot - RM串联轮腿机器人
  2. ✅ DM_Wheel_leg_robot - DM轮腿机器人
  3. ✅ 简化测试模型 - 用于快速测试的简化模型

请选择模型 (1-3) [默认: 1]:
```

输入数字选择，或直接按回车使用默认模型。

### 3. 自动加载和启动

程序会：
1. 转换URDF到MJCF格式（如果需要）
2. 加载MuJoCo模型
3. 打开MuJoCo交互式查看器
4. 开始仿真

### 4. 使用MuJoCo查看器

查看器会自动打开，显示完整的3D机器人模型。

## 🎮 MuJoCo查看器控制

### 视角控制

| 操作 | 功能 |
|------|------|
| 鼠标左键拖动 | 旋转视角 |
| 鼠标右键拖动 | 平移视角 |
| 鼠标滚轮 | 缩放 |
| 双击 | 聚焦到点击的物体 |

### 仿真控制

| 按键 | 功能 |
|------|------|
| 空格键 | 暂停/继续仿真 |
| Ctrl+R | 重置仿真 |
| → | 单步前进 |
| ← | 单步后退（如果启用） |

### 显示选项

| 按键 | 功能 |
|------|------|
| Tab | 切换显示选项面板 |
| F1 | 显示帮助 |
| F2 | 显示/隐藏信息 |
| F3 | 显示/隐藏统计 |
| F4 | 显示/隐藏性能 |
| F5 | 显示/隐藏渲染选项 |

### 调试工具

| 按键 | 功能 |
|------|------|
| C | 显示/隐藏接触力 |
| F | 显示/隐藏力 |
| J | 显示/隐藏关节 |
| I | 显示/隐藏惯性 |
| T | 显示/隐藏透明度 |

### 退出

| 按键 | 功能 |
|------|------|
| Esc | 退出查看器 |
| Ctrl+C | 终止程序（在终端） |

## 🎨 查看器功能

### 1. 实时3D可视化

- 完整的机器人模型渲染
- 环境和地面
- 光照和阴影
- 碰撞检测可视化

### 2. 交互式控制

**关节控制**:
- 右侧面板可以调整每个关节
- 实时看到机器人响应
- 支持位置、速度、力矩控制

**外力施加**:
- Ctrl+鼠标左键：施加力
- Ctrl+鼠标右键：施加力矩
- 测试机器人的动态响应

### 3. 物理参数调整

可以实时修改：
- 重力
- 摩擦系数
- 阻尼
- 时间步长
- 求解器参数

### 4. 数据可视化

- 关节位置/速度/力矩曲线
- 接触力
- 能量
- 性能统计

## 📊 示例：控制机器人

程序内置了简单的正弦波控制示例：

```python
# 在launch_mujoco_direct.py中
if model.nu > 0:
    for i in range(min(4, model.nu)):
        data.ctrl[i] = 0.5 * np.sin(data.time * 2.0 + i * np.pi / 2)
```

你可以修改这部分代码来实现自己的控制算法。

## 🔧 自定义控制

### 修改控制逻辑

编辑`launch_mujoco_direct.py`，找到仿真循环：

```python
while viewer.is_running():
    # 执行仿真步
    mujoco.mj_step(model, data)
    
    # 在这里添加你的控制逻辑
    # 例如：
    # data.ctrl[0] = your_controller(data)
    
    viewer.sync()
```

### 添加传感器读取

```python
# 读取关节位置
joint_pos = data.qpos.copy()

# 读取关节速度
joint_vel = data.qvel.copy()

# 读取接触力
contact_forces = data.cfrc_ext.copy()
```

### 实现控制器

```python
class SimpleController:
    def __init__(self, model):
        self.model = model
        self.target_pos = np.zeros(model.nu)
    
    def compute_control(self, data):
        # PD控制器
        kp = 10.0
        kd = 1.0
        
        error = self.target_pos - data.qpos[:model.nu]
        error_dot = -data.qvel[:model.nu]
        
        return kp * error + kd * error_dot

# 使用控制器
controller = SimpleController(model)
while viewer.is_running():
    data.ctrl[:] = controller.compute_control(data)
    mujoco.mj_step(model, data)
    viewer.sync()
```

## 🎯 使用场景

### 1. 快速原型开发

```bash
# 选择简化模型（选项3）
./launch_mujoco.sh
# 输入: 3
```

快速测试控制算法，无需等待复杂模型加载。

### 2. 机器人调试

```bash
# 选择实际机器人模型
./launch_mujoco.sh
# 输入: 1 或 2
```

- 检查模型是否正确
- 验证关节范围
- 测试碰撞检测
- 调整物理参数

### 3. 算法验证

修改`launch_mujoco_direct.py`中的控制逻辑：
- 实现你的控制算法
- 实时看到效果
- 调整参数
- 记录数据

### 4. 演示和展示

- 完整的3D可视化
- 流畅的渲染
- 专业的外观
- 交互式演示

## 📈 性能对比

| 方式 | 启动时间 | 渲染质量 | 稳定性 | 功能 |
|------|---------|---------|--------|------|
| PyQt5 GUI | 慢 | 低（黑屏问题） | 低 | 有限 |
| MuJoCo直接 | 快 | 高（原生3D） | 高 | 完整 |

## ⚠️ 注意事项

### 显示要求

MuJoCo查看器需要：
- ✅ 图形界面（X11或Wayland）
- ✅ OpenGL支持
- ❌ 不支持纯终端环境

### 远程使用

**SSH X11转发**:
```bash
ssh -X user@server
cd "Wheel-Legged Robot Digital Twin Control Platform"
./launch_mujoco.sh
```

**VNC**:
1. 在服务器上启动VNC
2. 通过VNC客户端连接
3. 在VNC会话中运行

### 性能

- 需要一定的GPU性能
- 复杂模型可能较慢
- 可以调整渲染质量

## 🔍 故障排除

### 问题1：查看器无法打开

**症状**: 程序启动但没有窗口

**解决**:
```bash
# 检查显示
echo $DISPLAY

# 测试X11
xeyes

# 如果在远程，使用X11转发
ssh -X user@server
```

### 问题2：模型加载失败

**症状**: `❌ 模型加载失败`

**解决**:
1. 检查URDF文件是否存在
2. 尝试使用简化模型（选项3）
3. 查看详细错误信息

### 问题3：渲染很慢

**解决**:
1. 降低渲染质量（在查看器中按F5）
2. 使用简化模型
3. 关闭不必要的可视化选项

### 问题4：控制不响应

**检查**:
1. 确认模型有执行器
2. 检查控制信号范围
3. 查看关节限制

## 📚 进一步学习

### MuJoCo文档

- [MuJoCo官方文档](https://mujoco.readthedocs.io/)
- [Python绑定](https://mujoco.readthedocs.io/en/stable/python.html)
- [查看器使用](https://mujoco.readthedocs.io/en/stable/programming/simulation.html#visualization)

### 示例代码

查看`launch_mujoco_direct.py`中的注释，了解：
- 如何加载模型
- 如何控制仿真
- 如何读取传感器
- 如何实现控制器

## 🎉 总结

**MuJoCo直接启动方式**:
- ✅ 避免GUI渲染问题
- ✅ 完整的3D可视化
- ✅ 强大的交互功能
- ✅ 稳定可靠
- ✅ 适合开发和演示

**推荐使用场景**:
- 日常开发和调试
- 算法验证
- 演示和展示
- 教学和学习

现在就试试吧：
```bash
./launch_mujoco.sh
```

享受流畅的3D机器人仿真体验！🤖
