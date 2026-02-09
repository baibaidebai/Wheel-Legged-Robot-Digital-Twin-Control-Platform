# GitHub Actions 工作流

本目录包含项目的CI/CD自动化工作流配置。

## 工作流文件

### 1. ci.yml - 主CI/CD流水线

**触发条件**:
- 推送到 `develop` 或 `main` 分支
- 创建Pull Request到 `develop` 或 `main` 分支

**包含的检查**:
- ✅ Python代码质量 (flake8, black, isort)
- ✅ C++代码质量 (cppcheck)
- ✅ Python单元测试
- ✅ ROS2构建测试
- ✅ 集成测试
- ✅ 文档检查
- ✅ 安全扫描 (bandit)

### 2. main-branch-protection.yml - 主分支保护

**触发条件**:
- 创建Pull Request到 `main` 分支

**包含的检查**:
- ✅ 确保PR来自develop分支
- ✅ 检查版本标签
- ✅ 验证无合并冲突
- ✅ 验证提交消息格式
- ✅ 检查CHANGELOG更新
- ✅ 验证文档完整性
- ✅ 发布就绪检查

## 状态徽章

在README.md中添加以下徽章显示CI状态:

```markdown
![CI/CD Pipeline](https://github.com/YOUR_USERNAME/YOUR_REPO/workflows/CI%2FCD%20Pipeline/badge.svg)
![Main Branch Protection](https://github.com/YOUR_USERNAME/YOUR_REPO/workflows/Main%20Branch%20Protection/badge.svg)
```

## 本地测试

在推送代码前，建议在本地运行相同的检查:

```bash
# 代码质量检查
flake8 src/wheel_legged_control/wheel_legged_control
black --check src/wheel_legged_control/wheel_legged_control
isort --check-only src/wheel_legged_control/wheel_legged_control

# 运行测试
pytest test/python/ -v
pytest test/integration/ -v

# ROS2构建
colcon build --packages-select wheel_legged_control
colcon test --packages-select wheel_legged_control
```

## 配置文件

相关配置文件位于项目根目录:
- `.flake8` - flake8配置
- `.pylintrc` - pylint配置
- `pyproject.toml` - black, isort, pytest配置

## 故障排除

如果CI检查失败:

1. **查看详细日志**: 点击失败的检查查看完整输出
2. **本地复现**: 在本地运行相同的命令
3. **修复问题**: 根据错误信息修复代码
4. **重新推送**: 修复后推送，CI会自动重新运行

## 更多信息

详细的CI/CD使用指南请参考: [docs/CI_CD_GUIDE.md](../docs/CI_CD_GUIDE.md)
