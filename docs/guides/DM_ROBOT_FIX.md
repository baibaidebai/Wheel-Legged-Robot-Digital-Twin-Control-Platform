# DM机器人URDF修复说明

## 🚨 问题描述

运行DM_Wheel_leg_robot模型时出现错误：
```
Error Code 14: Msg: Parser configurations requested resolved uris, 
but uri [model://wheel_leg_description/meshes/base_link.STL] could not be resolved.
```

## 🔍 问题原因

DM机器人的URDF文件使用了ROS package协议的路径：
```xml
<mesh filename="package://wheel_leg_description/meshes/base_link.STL" />
```

但是：
1. Gazebo无法解析 `package://` 协议
2. 实际的meshes文件在 `src/model/DM_Wheel_leg_robot/meshes/` 目录
3. 需要使用相对路径

## ✅ 解决方案

### 自动修复（推荐）

运行修复脚本：
```bash
python3 fix_dm_urdf.py
```

这个脚本会：
1. 备份原URDF文件（.backup）
2. 将所有 `package://wheel_leg_description/meshes/` 替换为 `../meshes/`
3. 保存修复后的文件

### 手动修复

如果需要手动修复，编辑URDF文件：
```bash
nano src/model/DM_Wheel_leg_robot/urdf/wheel_legged_urdf_pkg.urdf
```

查找并替换：
- 查找：`package://wheel_leg_description/meshes/`
- 替换为：`../meshes/`

## 🎯 修复后的效果

### 修复前
```xml
<mesh filename="package://wheel_leg_description/meshes/base_link.STL" />
```

### 修复后
```xml
<mesh filename="../meshes/base_link.STL" />
```

## 🚀 使用修复后的模型

```bash
# 启动Gazebo
./launch_gazebo_safe.sh

# 选择模型 2 (DM_Wheel_leg_robot)
```

现在DM机器人应该可以正常加载和显示了！

## 📦 涉及的文件

修复脚本会处理以下15个STL文件的路径：
- base_link.STL
- imu_link.STL
- lidar_link.STL
- left_back_motor_link.STL
- left_front_motor_link.STL
- left_l1_link.STL
- left_l3_link.STL
- left_l4_link.STL
- left_wheel_motor_link.STL
- right_back_motor_link.STL
- right_front_motor_link.STL
- right_l1_link.STL
- right_l3_link.STL
- right_l4_link.STL
- right_wheel_motor_link.STL

## 🔧 故障排除

### 问题1：修复脚本失败

**解决**：
```bash
# 检查Python版本
python3 --version

# 手动运行
python3 fix_dm_urdf.py
```

### 问题2：仍然无法加载

**解决**：
```bash
# 检查meshes目录
ls -la src/model/DM_Wheel_leg_robot/meshes/

# 检查URDF文件
grep "filename=" src/model/DM_Wheel_leg_robot/urdf/wheel_legged_urdf_pkg.urdf | head -5
```

应该显示 `../meshes/` 路径。

### 问题3：想恢复原文件

**解决**：
```bash
# 恢复备份
cp src/model/DM_Wheel_leg_robot/urdf/wheel_legged_urdf_pkg.urdf.backup \
   src/model/DM_Wheel_leg_robot/urdf/wheel_legged_urdf_pkg.urdf
```

## 💡 为什么RM机器人可以工作？

RM_Serial_Wheeled-leg_Robot的URDF文件已经使用了正确的相对路径：
```xml
<mesh filename="../meshes/base_link.STL" />
```

所以不需要修复。

## 📚 相关文档

- [GAZEBO_FLICKERING_FIX.md](GAZEBO_FLICKERING_FIX.md) - 闪屏问题
- [START_HERE.md](START_HERE.md) - 快速开始
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - 快速参考

## 🎉 总结

**问题**：DM机器人URDF使用package://协议路径

**原因**：Gazebo无法解析package://协议

**解决**：运行 `python3 fix_dm_urdf.py` 转换为相对路径

**结果**：DM机器人可以正常加载！

---

**现在就试试DM机器人！** 🤖✨
