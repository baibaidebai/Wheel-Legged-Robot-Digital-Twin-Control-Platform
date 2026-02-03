# 贡献指南

感谢您对轮腿机器人孪生控制系统项目的关注！本文档将指导您如何为项目做出贡献。

## 开发环境设置

### 1. 克隆仓库

```bash
git clone <repository-url>
cd wheel-legged-robot-twin-control
```

### 2. 安装依赖

请参考 [README.md](README.md) 中的环境要求和安装步骤。

### 3. 设置开发环境

```bash
# 安装开发工具
pip3 install flake8 black pytest-cov pre-commit

# 设置pre-commit钩子
pre-commit install
```

## 分支策略 (GitFlow)

我们使用GitFlow工作流进行版本控制：

- **main**: 生产就绪的稳定版本
- **develop**: 开发集成分支，包含最新的开发功能
- **feature/**: 功能开发分支 (从develop分出)
- **hotfix/**: 紧急修复分支 (从main分出)
- **release/**: 发布准备分支 (从develop分出)

### 功能开发流程

1. **创建功能分支**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   ```

2. **开发功能**
   - 编写代码
   - 添加测试
   - 更新文档

3. **提交代码**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

4. **推送分支**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **创建Pull Request**
   - 目标分支: develop
   - 填写PR模板
   - 等待代码审查

## 代码规范

### Python代码规范

- 遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 规范
- 使用 `black` 进行代码格式化
- 使用 `flake8` 进行代码检查
- 函数和类需要添加docstring

```python
def example_function(param1: str, param2: int) -> bool:
    """
    示例函数说明。
    
    Args:
        param1: 参数1说明
        param2: 参数2说明
        
    Returns:
        返回值说明
        
    Raises:
        ValueError: 异常说明
    """
    pass
```

### C++代码规范

- 遵循 [Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html)
- 使用 `clang-format` 进行代码格式化
- 头文件使用include guards或#pragma once

### 提交信息规范

使用 [约定式提交](https://www.conventionalcommits.org/zh-hans/v1.0.0/) 格式：

```
<类型>[可选的作用域]: <描述>

[可选的正文]

[可选的脚注]
```

**类型**:
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式化
- `refactor`: 代码重构
- `test`: 添加测试
- `chore`: 构建过程或辅助工具的变动

**示例**:
```
feat(digital-twin): add kinematic solver for wheel-leg coupling

- Implement forward kinematics calculation
- Add inverse kinematics solver with singularity handling
- Include unit tests for kinematic transformations

Closes #123
```

## 测试要求

### 单元测试

- 所有新功能必须包含单元测试
- 测试覆盖率应≥90%
- 使用pytest框架编写测试

```python
import pytest
from wheel_legged_control.core import JointController

class TestJointController:
    def test_set_joint_positions(self):
        controller = JointController()
        positions = {"joint1": 0.5, "joint2": -0.3}
        assert controller.set_joint_positions(positions) == True
```

### 属性测试

- 核心算法需要属性测试
- 使用Hypothesis库生成测试数据

```python
from hypothesis import given, strategies as st

@given(st.floats(min_value=-3.14, max_value=3.14))
def test_joint_angle_limits(angle):
    controller = JointController()
    # 测试关节角度限制属性
    assert controller.is_angle_valid(angle) == (-3.14 <= angle <= 3.14)
```

### 集成测试

- 测试ROS2节点间的通信
- 使用launch_testing框架

## 文档要求

### 代码文档

- 所有公共API需要docstring
- 复杂算法需要详细注释
- 使用Sphinx生成API文档

### 用户文档

- 新功能需要更新用户手册
- 提供使用示例和配置说明
- 更新README.md相关部分

## Pull Request流程

### PR检查清单

提交PR前请确认：

- [ ] 代码通过所有测试
- [ ] 代码符合规范要求
- [ ] 添加了必要的测试
- [ ] 更新了相关文档
- [ ] 提交信息符合约定式提交格式
- [ ] 解决了所有merge冲突

### PR模板

```markdown
## 变更类型
- [ ] 新功能
- [ ] Bug修复
- [ ] 文档更新
- [ ] 性能优化
- [ ] 代码重构

## 变更描述
简要描述本次变更的内容和目的。

## 测试
描述如何测试这些变更。

## 相关Issue
Closes #(issue编号)

## 检查清单
- [ ] 代码通过所有测试
- [ ] 添加了必要的测试
- [ ] 更新了文档
- [ ] 遵循了代码规范
```

## 发布流程

### 版本号规范

使用 [语义化版本](https://semver.org/lang/zh-CN/) 规范：

- **主版本号**: 不兼容的API修改
- **次版本号**: 向下兼容的功能性新增
- **修订号**: 向下兼容的问题修正

### 发布步骤

1. 从develop创建release分支
2. 更新版本号和CHANGELOG
3. 进行发布测试
4. 合并到main并打标签
5. 合并回develop

## 问题报告

### Bug报告

使用GitHub Issues报告bug，请包含：

- 问题描述
- 复现步骤
- 期望行为
- 实际行为
- 环境信息 (OS, ROS2版本等)
- 相关日志

### 功能请求

提交功能请求时请说明：

- 功能描述
- 使用场景
- 预期收益
- 实现建议

## 社区准则

- 保持友善和专业的交流
- 尊重不同的观点和经验水平
- 提供建设性的反馈
- 遵循开源社区最佳实践

## 获得帮助

如果您在贡献过程中遇到问题：

1. 查看现有的Issues和文档
2. 在GitHub Discussions中提问
3. 联系项目维护者

感谢您的贡献！🚀