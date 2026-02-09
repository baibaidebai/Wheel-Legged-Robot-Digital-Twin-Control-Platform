# CI/CD 流水线指南

## 概述

本项目使用GitHub Actions实现持续集成和持续部署(CI/CD)，确保代码质量和系统稳定性。

## 工作流程

### 1. 主CI/CD流水线 (ci.yml)

每次推送到`develop`或`main`分支，或创建Pull Request时自动触发。

#### 检查项目

1. **代码质量检查 (code-quality)**
   - Python代码风格检查 (flake8)
   - 代码格式化检查 (black)
   - 导入排序检查 (isort)

2. **C++代码质量 (cpp-quality)**
   - 静态代码分析 (cppcheck)
   - 代码规范检查

3. **Python单元测试 (python-tests)**
   - 运行所有Python单元测试
   - 生成代码覆盖率报告
   - 支持并行测试执行

4. **ROS2构建测试 (build-ros2)**
   - 编译ROS2工作空间
   - 运行ROS2包测试
   - 验证依赖关系

5. **集成测试 (integration-tests)**
   - 运行系统集成测试
   - 验证模块间协作

6. **文档检查 (documentation)**
   - 验证文档完整性
   - 检查TODO和FIXME标记

7. **安全扫描 (security-scan)**
   - Python代码安全漏洞扫描 (bandit)
   - 依赖安全检查

### 2. 主分支保护 (main-branch-protection.yml)

仅在向`main`分支创建Pull Request时触发。

#### 检查项目

1. **合并前验证 (pre-merge-checks)**
   - 确保PR来自develop分支
   - 检查版本标签
   - 验证无合并冲突
   - 验证提交消息格式

2. **变更日志检查 (changelog-check)**
   - 验证CHANGELOG.md更新

3. **文档完整性 (documentation-check)**
   - 检查README和关键文档
   - 验证API文档

4. **发布就绪检查 (release-readiness)**
   - 综合评估发布准备情况

## 代码质量标准

### Python代码规范

- **最大行长度**: 127字符
- **最大复杂度**: 10
- **代码格式化**: 使用black
- **导入排序**: 使用isort
- **静态检查**: 使用flake8和pylint

配置文件:
- `.flake8` - flake8配置
- `.pylintrc` - pylint配置
- `pyproject.toml` - black和isort配置

### C++代码规范

- 使用cppcheck进行静态分析
- 遵循ROS2 C++编码规范
- 启用所有警告级别

### 提交消息规范

使用Conventional Commits格式:

```
<type>(<scope>): <subject>

<body>

<footer>
```

类型 (type):
- `feat`: 新功能
- `fix`: 错误修复
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具链更新
- `perf`: 性能优化
- `ci`: CI/CD配置更新
- `build`: 构建系统更新
- `revert`: 回滚提交

示例:
```
feat(simulation): 添加并行MuJoCo仿真支持

实现ParallelMuJoCoBackend类，支持批量并行仿真。
提供4-8x训练加速。

Closes #123
```

## 分支策略

### 分支类型

1. **main** - 生产分支
   - 仅包含稳定的可发布版本
   - 受保护，需要PR和审查
   - 所有CI检查必须通过

2. **develop** - 开发分支
   - 日常开发集成分支
   - 功能分支合并目标
   - 定期合并到main

3. **feature/** - 功能分支
   - 从develop创建
   - 命名: `feature/功能名称`
   - 完成后合并回develop

4. **hotfix/** - 热修复分支
   - 从main创建
   - 紧急修复生产问题
   - 合并到main和develop

### 工作流程

```
feature/xxx → develop → main
                ↓
            hotfix/xxx → main
```

## 本地开发

### 运行代码质量检查

```bash
# Python代码检查
flake8 src/wheel_legged_control/wheel_legged_control
black --check src/wheel_legged_control/wheel_legged_control
isort --check-only src/wheel_legged_control/wheel_legged_control
pylint src/wheel_legged_control/wheel_legged_control

# C++代码检查
cppcheck --enable=all src/wheel_legged_control/src/

# 安全扫描
bandit -r src/wheel_legged_control/wheel_legged_control
```

### 运行测试

```bash
# Python单元测试
pytest test/python/ -v

# 带覆盖率
pytest test/python/ --cov=src/wheel_legged_control/wheel_legged_control --cov-report=html

# 集成测试
pytest test/integration/ -v

# ROS2测试
colcon test --packages-select wheel_legged_control
```

### 自动格式化代码

```bash
# 格式化Python代码
black src/wheel_legged_control/wheel_legged_control
isort src/wheel_legged_control/wheel_legged_control
```

## GitHub Actions配置

### 必需的Secrets

目前不需要配置secrets，所有检查都在公开环境中运行。

### 分支保护规则

建议为`main`分支配置以下保护规则:

1. **要求Pull Request审查**
   - 至少1个审查者批准
   - 驳回过时的审查

2. **要求状态检查通过**
   - 所有CI检查必须通过
   - 分支必须是最新的

3. **要求线性历史**
   - 禁止合并提交
   - 使用squash或rebase

4. **限制推送权限**
   - 仅管理员可直接推送

## 故障排除

### CI失败常见原因

1. **代码风格问题**
   - 运行`black`和`isort`自动修复
   - 检查flake8输出

2. **测试失败**
   - 本地运行失败的测试
   - 检查依赖是否完整

3. **构建失败**
   - 检查CMakeLists.txt配置
   - 验证ROS2依赖

4. **合并冲突**
   - 从目标分支拉取最新代码
   - 解决冲突后重新推送

### 跳过CI检查

在特殊情况下（如文档更新），可以在提交消息中添加`[skip ci]`跳过CI:

```bash
git commit -m "docs: 更新README [skip ci]"
```

**注意**: 向main分支的PR不能跳过CI检查。

## 性能优化

### 加速CI执行

1. **缓存依赖**
   - Python包缓存
   - ROS2构建缓存

2. **并行执行**
   - 多个job并行运行
   - pytest使用pytest-xdist

3. **选择性测试**
   - 仅运行受影响的测试
   - 使用测试标记

## 监控和报告

### CI状态徽章

在README.md中添加CI状态徽章:

```markdown
![CI](https://github.com/username/repo/workflows/CI%2FCD%20Pipeline/badge.svg)
```

### 代码覆盖率

- 使用pytest-cov生成覆盖率报告
- 目标: 保持80%以上覆盖率
- 查看HTML报告: `htmlcov/index.html`

## 最佳实践

1. **频繁提交**: 小而频繁的提交更容易审查和回滚
2. **清晰的提交消息**: 遵循Conventional Commits规范
3. **本地测试**: 推送前在本地运行所有检查
4. **及时修复**: CI失败后立即修复，不要累积问题
5. **代码审查**: 认真审查每个PR，提供建设性反馈
6. **文档同步**: 代码变更时同步更新文档

## 参考资源

- [GitHub Actions文档](https://docs.github.com/en/actions)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Python代码风格指南 (PEP 8)](https://pep8.org/)
- [ROS2开发指南](https://docs.ros.org/en/humble/Contributing.html)
