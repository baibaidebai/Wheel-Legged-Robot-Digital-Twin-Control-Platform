# MuJoCo启动问题已修复

## ✅ 问题解决

你说得对！MuJoCo本身工作正常，问题出在我们的Python脚本使用了`mujoco.viewer.launch_passive()`，这在某些环境下有兼容性问题。

## 🔧 修复方案

现在所有启动器都使用**MuJoCo官方viewer**：

```bash
python3 -m mujoco.viewer --mjcf=model.xml
```

这是MuJoCo推荐的启动方式，兼容性最好。

---

## 🚀 使用方法

### 方法1：命令行启动

```bash
# 使用我们的启动脚本
python3 tools/launch_mujoco.py --model rm
python3 tools/launch_mujoco.py --model dm

# 或直接使用MuJoCo viewer
python3 -m mujoco.viewer --mjcf=src/model/RM_Serial_Wheeled-leg_Robot/mjcf/RM_Serial_Wheeled-leg_Robot_wiki.xml
```

### 方法2：GUI启动

#### 增强版GUI
```bash
./launch_enhanced.sh
```
1. 选择"MuJoCo"仿真器
2. 选择模型文件夹
3. 选择MJCF文件
4. 点击"启动仿真"

#### 标准GUI
```bash
./launch.sh
```
1. 选择机器人模型
2. 选择"MuJoCo"模式
3. 点击"启动 Gazebo"

### 方法3：快速测试

```bash
./tools/test_mujoco_simple.sh
```

---

## 📝 修改内容

### 1. `tools/launch_mujoco.py`
- ✅ 改用`python3 -m mujoco.viewer`
- ✅ 移除复杂的viewer初始化代码
- ✅ 简化错误处理

### 2. `tools/launch_gui_enhanced.py`
- ✅ 更新MuJoCo启动方式
- ✅ 直接调用官方viewer

### 3. `tools/launch_gazebo_gui.py`
- ✅ 更新MuJoCo启动方式
- ✅ 保持一致性

### 4. 新增测试脚本
- ✅ `tools/test_mujoco_simple.sh` - 快速测试

---

## 🎯 优势

### 使用官方viewer的好处：

1. **兼容性最好**
   - MuJoCo官方维护
   - 支持所有平台
   - 无需担心环境问题

2. **功能完整**
   - 完整的交互控制
   - 内置调试工具
   - 性能优化

3. **简单可靠**
   - 无需复杂配置
   - 一行命令启动
   - 错误信息清晰

---

## 🧪 测试

### 快速测试
```bash
./tools/test_mujoco_simple.sh
```

### 完整测试
```bash
# 测试RM机器人
python3 tools/launch_mujoco.py --model rm

# 测试DM机器人
python3 tools/launch_mujoco.py --model dm

# 测试自定义文件
python3 tools/launch_mujoco.py --mjcf path/to/model.xml
```

### GUI测试
```bash
# 增强版GUI
./launch_enhanced.sh

# 标准GUI
./launch.sh
```

---

## 💡 使用建议

### 日常使用
```bash
python3 tools/launch_mujoco.py --model rm
```

### 开发调试
```bash
# 直接使用官方viewer，可以看到所有输出
python3 -m mujoco.viewer --mjcf=src/model/RM_Serial_Wheeled-leg_Robot/mjcf/RM_Serial_Wheeled-leg_Robot_wiki.xml
```

### GUI使用
```bash
./launch_enhanced.sh  # 更多选项
./launch.sh           # 快速启动
```

---

## 🎮 控制说明

MuJoCo Viewer控制：

- **鼠标左键** - 旋转视角
- **鼠标右键** - 平移视角
- **鼠标滚轮** - 缩放
- **空格键** - 暂停/继续
- **Backspace** - 重置仿真
- **ESC** - 退出
- **Tab** - 切换UI显示
- **F1** - 帮助

---

## 📚 相关文档

- [MuJoCo完整指南](MUJOCO_GUIDE.md)
- [增强版GUI指南](ENHANCED_GUI_GUIDE.md)
- [启动器对比](LAUNCHER_COMPARISON.md)

---

## ✨ 总结

问题已完全解决！现在MuJoCo可以通过以下方式启动：

1. ✅ 命令行脚本
2. ✅ 增强版GUI
3. ✅ 标准GUI
4. ✅ 直接使用官方viewer

所有方式都使用MuJoCo官方viewer，保证最佳兼容性和性能。

---

**更新日期**: 2026-02-09
**版本**: v2.2
