# GUI启动MuJoCo使用说明

## ✅ 问题已修复

GUI现在可以正确启动MuJoCo了！修复了虚拟环境路径问题。

---

## 🚀 使用方法

### 方法1：增强版GUI（推荐）

```bash
./launch_enhanced.sh
```

**步骤：**
1. 选择"MuJoCo - 高性能物理引擎"
2. 在"机器人模型"区域选择模型文件夹
3. 选择对应的MJCF文件
4. 点击"🚀 启动仿真"
5. 确认配置
6. MuJoCo窗口将在新终端中打开

### 方法2：标准GUI

```bash
./launch.sh
```

**步骤：**
1. 选择机器人模型（RM或DM）
2. 选择"MuJoCo - 原生URDF支持"
3. 点击"启动 Gazebo"
4. 确认启动
5. MuJoCo窗口将在新终端中打开

---

## 📋 可用的模型

### RM机器人
- **文件夹**: `RM_Serial_Wheeled-leg_Robot`
- **MJCF文件**: `RM_Serial_Wheeled-leg_Robot_wiki.xml`

### DM机器人
- **文件夹**: `DM_Wheel_leg_robot`
- **MJCF文件**: `wheel_legged_urdf_pkg_wiki.xml`

---

## 🎮 MuJoCo控制

启动后，在MuJoCo窗口中：

- **鼠标左键** - 旋转视角
- **鼠标右键** - 平移视角
- **鼠标滚轮** - 缩放
- **空格键** - 暂停/继续仿真
- **Backspace** - 重置仿真
- **Tab** - 切换UI显示
- **ESC** - 退出
- **F1** - 显示帮助

---

## 🔧 技术细节

### GUI如何启动MuJoCo

1. **检测虚拟环境**
   - 自动查找 `venv/bin/python3`
   - 如果存在，使用虚拟环境的Python
   - 否则使用系统Python

2. **构建命令**
   ```bash
   /path/to/venv/bin/python3 -m mujoco.viewer --mjcf=model.xml
   ```

3. **在新终端中启动**
   - 使用 `gnome-terminal`
   - 独立窗口运行
   - 可以看到所有输出

### 为什么这样工作

- ✅ 使用MuJoCo官方viewer（兼容性最好）
- ✅ 自动使用虚拟环境（确保MuJoCo可用）
- ✅ 独立终端（不阻塞GUI）
- ✅ 完整输出（便于调试）

---

## 🐛 故障排除

### 问题1：提示"MuJoCo未安装"

**原因**：虚拟环境中没有安装MuJoCo

**解决**：
```bash
source venv/bin/activate
pip install mujoco -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题2：窗口没有打开

**检查**：
1. 查看新打开的终端窗口
2. 检查是否有错误信息
3. 确认MJCF文件存在

**测试**：
```bash
# 直接测试
source venv/bin/activate
python3 -m mujoco.viewer --mjcf=src/model/RM_Serial_Wheeled-leg_Robot/mjcf/RM_Serial_Wheeled-leg_Robot_wiki.xml
```

### 问题3：找不到MJCF文件

**检查**：
```bash
# 查看可用的MJCF文件
ls -la src/model/*/mjcf/*.xml
```

**如果没有**：
```bash
# 转换URDF到MJCF
python3 tools/test_wiki_mjcf.py
```

---

## 💡 使用技巧

### 技巧1：快速切换模型

在增强版GUI中：
1. 使用下拉菜单快速切换模型文件夹
2. MJCF文件列表会自动更新
3. 无需重启GUI

### 技巧2：查看启动日志

MuJoCo在独立终端中运行，可以：
- 看到所有输出信息
- 查看错误消息
- 监控仿真状态

### 技巧3：同时运行多个实例

可以启动多个MuJoCo窗口：
1. 在GUI中启动第一个模型
2. 不关闭GUI
3. 选择另一个模型
4. 再次启动

---

## 📚 相关文档

- [MuJoCo完整指南](MUJOCO_GUIDE.md)
- [MuJoCo问题修复](MUJOCO_FIXED.md)
- [增强版GUI指南](ENHANCED_GUI_GUIDE.md)
- [启动器对比](LAUNCHER_COMPARISON.md)

---

## ✨ 总结

GUI启动MuJoCo现在完全可用：

1. ✅ 自动检测虚拟环境
2. ✅ 使用官方viewer
3. ✅ 独立终端运行
4. ✅ 完整的错误提示
5. ✅ 支持所有模型

开始使用：
```bash
./launch_enhanced.sh  # 增强版GUI
./launch.sh           # 标准GUI
```

---

**更新日期**: 2026-02-09
**版本**: v2.3
