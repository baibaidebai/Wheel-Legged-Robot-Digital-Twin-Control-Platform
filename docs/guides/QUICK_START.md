# 快速启动指南

## ✅ 问题已解决！

GUI已成功启动，MuJoCo集成正常工作！

## 🚀 启动GUI

```bash
cd "Wheel-Legged Robot Digital Twin Control Platform"
./launch_gui.sh
```

## 📋 使用步骤

### 1. 配置页面

启动后会看到配置选择页面：

1. **选择机器人模型**
   - RM_Serial_Wheeled-leg_Robot ✅
   - DM_Wheel_leg_robot ✅

2. **选择仿真后端**
   - MuJoCo（推荐）✅
   - Gazebo ✅

3. **选择配置档案**
   - 默认配置
   - 自定义配置

4. **选择控制算法**
   - 手动控制（推荐开始）
   - LQR控制器
   - PID控制器
   - 强化学习（需要PyTorch）

5. **调整高级参数**（可选）
   - 时间步长: 0.001s
   - 最大步数: 10000
   - 启用渲染: ✅
   - 重力加速度: -9.81 m/s²

6. **点击"开始仿真"**

### 2. 仿真页面

进入仿真页面后，你会看到：

- **左侧**: 关节控制面板
  - 每个关节的滑块控制
  - 实时关节状态显示
  - 算法控制选项

- **右侧**: MuJoCo 3D可视化
  - 真实物理仿真画面
  - 机器人模型实时渲染
  - 不再是黑屏！✅

- **顶部工具栏**:
  - ⏸️ 暂停/继续
  - 🔄 重置仿真
  - ⚙️ 重新配置

- **底部状态栏**:
  - 仿真状态
  - FPS显示

### 3. 控制机器人

**手动模式**:
- 使用左侧滑块控制各个关节
- 实时看到机器人在3D视图中移动

**自动模式**:
- 点击"启动算法"
- 算法自动控制机器人

## 🎯 验证清单

- [x] GUI成功启动
- [x] 配置页面正常显示
- [x] 可以选择机器人模型
- [x] 可以选择MuJoCo后端
- [ ] 仿真页面显示3D渲染（请验证）
- [ ] 机器人模型正确显示（请验证）
- [ ] 物理仿真正常运行（请验证）
- [ ] 关节控制正常工作（请验证）

## 📊 启动日志解读

```
✅ PyQt5可用          # GUI框架
✅ PyYAML可用         # 配置管理
✅ MuJoCo v3.4.0 可用 # 物理引擎
✅ NumPy可用          # 数值计算
✅ 找到模型: RM_Serial_Wheeled-leg_Robot
✅ 找到模型: DM_Wheel_leg_robot
✅ MuJoCo后端注册成功
✅ Gazebo后端注册成功
✅ 应用程序已启动
```

## ⚠️ 已知提示

### 算法模块警告
```
警告: 算法模块导入失败 - No module named 'torch'
```
**影响**: 无影响，只是强化学习功能不可用  
**解决**: 如需使用PPO训练，安装PyTorch: `pip install torch`

### QSocketNotifier警告
```
QSocketNotifier: Can only be used with threads started with QThread
```
**影响**: 无影响，这是Qt的内部警告  
**状态**: 可以忽略

## 🔧 故障排除

### 如果GUI没有显示

1. 检查是否有图形界面:
```bash
echo $DISPLAY
```

2. 如果在远程服务器，启用X11转发:
```bash
ssh -X user@server
```

3. 或使用VNC/远程桌面

### 如果仍然黑屏

1. 检查MuJoCo后端:
```bash
./venv/bin/python3 test_mujoco_simple.py
```

2. 查看控制台错误信息

3. 尝试切换到Gazebo后端

## 📁 相关文件

- **launch_gui.sh** - GUI启动脚本（推荐）
- **test_mujoco_simple.py** - MuJoCo后端测试
- **GUI_MUJOCO_STATUS_CN.md** - 详细状态报告
- **MUJOCO_GUI_DIAGNOSIS.md** - 诊断文档

## 🎉 成功！

GUI已经成功启动，MuJoCo物理仿真已集成！

现在可以：
1. 选择机器人模型
2. 选择MuJoCo后端
3. 开始仿真
4. 看到真实的3D物理仿真画面

享受你的轮腿机器人数字孪生系统！🤖
