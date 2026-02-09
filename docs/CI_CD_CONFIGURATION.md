# CI/CD配置说明

## 📋 概述

本项目的CI/CD配置采用**宽松策略**，旨在提供代码质量反馈而不阻碍开发流程。

## 🎯 设计原则

### 1. 宽松优先
- **只有严重的语法错误会导致构建失败**
- 代码风格问题仅作为警告，不会阻止合并
- 测试失败会报告但不会阻止构建

### 2. 快速反馈
- CI流程简化，只运行必要的检查
- 避免耗时的完整测试套件
- 提供清晰的错误信息

### 3. 开发友好
- 不会因为小的风格问题阻止你的工作
- 允许渐进式改进代码质量
- 提供建议而不是强制要求

## 🔍 CI检查项目

### 1. 语法检查 (Syntax Check)
**状态**: 必须通过 ✓

检查内容：
- Python语法错误
- 未定义的变量
- 导入错误

**失败条件**：
- 只有严重的语法错误才会失败

### 2. 代码风格 (Code Style)
**状态**: 建议性 ⚠️

检查内容：
- Flake8代码风格
- Black代码格式化
- isort导入排序

**失败条件**：
- 永远不会失败，只提供建议

### 3. 基础测试 (Basic Tests)
**状态**: 建议性 ⚠️

检查内容：
- 基本导入测试
- 简单单元测试

**失败条件**：
- 测试失败会报告但不会阻止构建

### 4. 文档检查 (Documentation)
**状态**: 建议性 ⚠️

检查内容：
- 关键文档文件是否存在
- README.md
- 用户手册
- API文档

**失败条件**：
- 永远不会失败，只提供提醒

## 📝 配置文件

### .github/workflows/ci.yml
主CI配置文件，定义了所有检查流程。

关键设置：
```yaml
continue-on-error: true  # 允许失败但继续执行
```

### .flake8
Flake8配置文件，定义代码风格规则。

宽松设置：
- `max-line-length = 127` (较长的行长度)
- `max-complexity = 15` (较高的复杂度)
- 忽略常见的风格问题（E402, E731, F401等）

### .pylintrc
Pylint配置文件（如果使用）。

## 🚀 本地运行CI检查

### 语法检查
```bash
# 检查Python语法
python -m py_compile src/wheel_legged_control/wheel_legged_control/**/*.py

# 运行flake8（只检查严重错误）
flake8 src/wheel_legged_control/wheel_legged_control --select=E9,F63,F7,F82
```

### 代码风格检查
```bash
# 运行flake8（完整检查）
flake8 src/wheel_legged_control/wheel_legged_control

# 检查代码格式
black --check src/wheel_legged_control/wheel_legged_control --line-length=127

# 检查导入排序
isort --check-only src/wheel_legged_control/wheel_legged_control --profile black
```

### 自动修复风格问题
```bash
# 自动格式化代码
black src/wheel_legged_control/wheel_legged_control --line-length=127

# 自动排序导入
isort src/wheel_legged_control/wheel_legged_control --profile black
```

### 运行测试
```bash
# 运行基础测试
pytest test/python/test_basic.py -v

# 运行所有测试
pytest test/ -v
```

## ⚙️ 自定义CI配置

### 如果你想更严格的CI

编辑 `.github/workflows/ci.yml`，将：
```yaml
continue-on-error: true
```
改为：
```yaml
continue-on-error: false
```

### 如果你想禁用某些检查

在 `.github/workflows/ci.yml` 中注释掉相应的job：
```yaml
# code-style:  # 禁用代码风格检查
#   name: Code Style Check (Advisory)
#   ...
```

### 如果你想调整代码风格规则

编辑 `.flake8` 文件，添加或删除忽略规则：
```ini
ignore =
    E203,
    E501,
    # 添加你想忽略的规则
```

## 🔧 常见问题

### Q: CI失败了，但我的代码可以运行？
A: 检查是否是语法检查失败。如果是风格检查，可以忽略或修复。

### Q: 如何临时跳过CI检查？
A: 在commit消息中添加 `[skip ci]`：
```bash
git commit -m "feat: add feature [skip ci]"
```

### Q: CI太慢了怎么办？
A: 当前配置已经很简化了。如果还是太慢，可以：
1. 只在PR时运行CI
2. 禁用某些检查
3. 使用本地pre-commit hooks

### Q: 如何在本地设置pre-commit hooks？
A: 创建 `.git/hooks/pre-commit` 文件：
```bash
#!/bin/bash
# 运行基本检查
flake8 src/wheel_legged_control/wheel_legged_control --select=E9,F63,F7,F82
if [ $? -ne 0 ]; then
    echo "❌ 语法检查失败"
    exit 1
fi
echo "✓ 语法检查通过"
```

## 📊 CI状态徽章

在README.md中添加CI状态徽章：
```markdown
![CI](https://github.com/baibaidebai/Wheel-Legged-Robot-Digital-Twin-Control-Platform/workflows/CI%2FCD%20Pipeline/badge.svg)
```

## 🎯 最佳实践

### 开发时
1. 专注于功能实现，不用担心风格问题
2. 定期运行 `black` 和 `isort` 自动修复风格
3. 提交前运行基本语法检查

### 提交PR时
1. 确保没有严重的语法错误
2. 查看CI报告的风格建议
3. 根据需要修复重要问题

### 合并前
1. 确保语法检查通过
2. 考虑修复明显的风格问题
3. 确保基本功能测试通过

## 📚 相关文档

- [贡献指南](../CONTRIBUTING.md)
- [代码风格指南](CODE_STYLE.md)（如果有）
- [测试指南](TESTING.md)（如果有）

## 🔄 更新历史

- **2026-02-09**: 初始版本，采用宽松策略
- 未来可能根据项目需求调整

---

**记住**: CI是帮助你的工具，不是阻碍你的障碍。如果CI配置有问题，随时可以调整！
