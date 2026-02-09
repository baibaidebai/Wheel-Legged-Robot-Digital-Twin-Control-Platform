# 增强版GUI - 快速总结

## ✨ 新功能

### 🎮 增强版GUI启动器
一个功能更强大的图形界面，支持完全自定义配置。

**启动命令：**
```bash
./launch_enhanced.sh
```

---

## 🆚 与标准版对比

| 特性 | 标准GUI | 增强版GUI |
|------|---------|-----------|
| 预设模型 | ✅ | ✅ |
| 自定义模型 | ❌ | ✅ |
| 文件浏览器 | ❌ | ✅ |
| 世界文件选择 | ❌ | ✅ |
| 完整参数配置 | ❌ | ✅ |
| 界面大小 | 600x480 | 800x700 |

---

## 📦 核心功能

### 1. 模型选择
- 📁 选择任意模型文件夹
- 📄 选择URDF文件（Gazebo）
- 📄 选择MJCF文件（MuJoCo）
- 🔍 文件浏览器支持

### 2. 世界环境
- 🌍 使用默认世界
- 🌍 选择自定义世界文件
- 🔍 浏览 `.world` 文件

### 3. 仿真器配置

**Gazebo：**
- 安全/简单/标准模式
- 软件渲染选项
- 详细输出选项

**MuJoCo：**
- 全屏模式
- 帧率设置（30-120 FPS）

---

## 🚀 快速开始

### 步骤1：启动GUI
```bash
./launch_enhanced.sh
```

### 步骤2：选择配置
1. 选择仿真器（Gazebo/MuJoCo）
2. 选择模型文件夹
3. 选择对应的文件（URDF/MJCF）
4. 配置选项

### 步骤3：启动仿真
点击"🚀 启动仿真"按钮

---

## 📚 完整文档

- [增强版GUI使用指南](ENHANCED_GUI_GUIDE.md) - 详细说明
- [启动器对比指南](LAUNCHER_COMPARISON.md) - 各版本对比
- [更新日志](CHANGELOG_ENHANCED_GUI.md) - 所有改进

---

## 💡 使用建议

### 日常使用
**推荐：** 标准GUI
```bash
./launch.sh
```

### 开发测试
**推荐：** 增强版GUI
```bash
./launch_enhanced.sh
```

### 虚拟机环境
**推荐：** Gazebo安全模式
```bash
./tools/launch_gazebo_safe.sh
```

### 强化学习
**推荐：** MuJoCo命令行
```bash
python3 tools/launch_mujoco.py --model rm --fps 120
```

---

## 🧪 测试

运行测试脚本验证安装：
```bash
python3 tools/test_enhanced_gui.py
```

---

## 🎉 开始使用

```bash
./launch_enhanced.sh
```

享受更灵活的仿真配置体验！🚀

---

**版本**: v2.1  
**日期**: 2026-02-09
