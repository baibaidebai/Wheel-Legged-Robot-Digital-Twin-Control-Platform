# CI/CD使用指南（更新版）

## 📋 概述

本项目使用GitHub Actions实现CI/CD。**采用宽松策略**：只有严重的语法错误会导致构建失败，其他问题仅作为建议。

## 🎯 设计理念

### 为什么选择宽松策略？
1. **不阻碍开发**: 风格问题不应该阻止你的工作
2. **渐进改进**: 允许逐步提高代码质量
3. **快速反馈**: 简化的CI提供更快的反馈
4. **开发友好**: 专注于功能，而不是完美的风格

## 🔍 CI检查项目

### 1. 语法检查 ✓ (必须通过)
- Python语法错误
- 未定义的变量
- 严重的导入错误

**失败条件**: 只有严重语法错误

### 2. 代码风格 ⚠️ (建议性)
- Flake8风格检查
- Black格式检查
- isort导入排序

**失败条件**: 永不失败

### 3. 基础测试 ⚠️ (建议性)
- 导入测试
- 基本单元测试

**失败条件**: 永不失败

### 4. 文档检查 ⚠️ (建议性)
- 关键文档存在性

**失败条件**: 永不失败

## 🚀 本地运行CI检查

### 快速检查
```bash
# 只检查严重错误
flake8 src/wheel_legged_control/wheel_legged_control --select=E9,F63,F7,F82
```

### 完整风格检查
```bash
# 运行flake8
flake8 src/wheel_legged_control/wheel_legged_control

# 检查格式
black --check src/wheel_legged_control/wheel_legged_control --line-length=127

# 检查导入
isort --check-only src/wheel_legged_control/wheel_legged_control --profile black
```

### 自动修复
```bash
# 自动格式化
black src/wheel_legged_control/wheel_legged_control --line-length=127

# 自动排序导入
isort src/wheel_legged_control/wheel_legged_control --profile black
```

## ⚙️ 配置文件

### .github/workflows/ci.yml
主CI配置，所有检查都设置了 `continue-on-error: true`

### .flake8
宽松的代码风格配置：
- 行长度: 127
- 复杂度: 15
- 忽略常见风格问题

## 🔧 自定义CI

### 更严格的CI
编辑 `.github/workflows/ci.yml`：
```yaml
continue-on-error: false  # 改为false
```

### 禁用某些检查
注释掉不需要的job

### 跳过CI
在commit消息中添加：
```bash
git commit -m "feat: add feature [skip ci]"
```

## 📊 CI状态

查看CI状态：
- GitHub Actions页面
- PR中的检查状态
- Commit旁边的✓或✗标记

## 🎯 最佳实践

### 开发时
- 专注功能实现
- 不用担心小的风格问题

### 提交前
- 运行快速语法检查
- 确保没有严重错误

### PR时
- 查看CI建议
- 考虑修复重要问题

## 📚 更多信息

详细配置说明: [CI_CD_CONFIGURATION.md](CI_CD_CONFIGURATION.md)

---

**记住**: CI是帮助工具，不是障碍！
