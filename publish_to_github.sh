#!/bin/bash

# 轮腿机器人孪生控制系统 - GitHub发布脚本
# 使用方法: ./publish_to_github.sh <GitHub仓库URL>

set -e

# 检查参数
if [ $# -eq 0 ]; then
    echo "❌ 错误: 请提供GitHub仓库URL"
    echo "使用方法: ./publish_to_github.sh <GitHub仓库URL>"
    echo "例如: ./publish_to_github.sh https://github.com/username/wheel-legged-robot-twin-control.git"
    exit 1
fi

REPO_URL=$1

echo "🚀 开始发布轮腿机器人孪生控制系统到GitHub"
echo "📍 仓库URL: $REPO_URL"

# 检查当前分支
CURRENT_BRANCH=$(git branch --show-current)
echo "📋 当前分支: $CURRENT_BRANCH"

# 添加远程仓库
echo "🔗 添加远程仓库..."
if git remote get-url origin >/dev/null 2>&1; then
    echo "⚠️  远程仓库已存在，更新URL..."
    git remote set-url origin "$REPO_URL"
else
    git remote add origin "$REPO_URL"
fi

# 验证远程仓库
echo "✅ 远程仓库配置:"
git remote -v

# 推送main分支
echo "📤 推送main分支..."
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "🔄 切换到main分支..."
    git checkout main 2>/dev/null || git checkout -b main
fi

# 推送到远程
echo "⬆️  推送main分支到远程仓库..."
git push -u origin main

# 推送develop分支
echo "📤 推送develop分支..."
git checkout develop
git push -u origin develop

# 推送所有标签
echo "🏷️  推送标签..."
git push origin --tags

# 显示仓库状态
echo ""
echo "🎉 发布完成！"
echo "📊 仓库状态:"
echo "  - 远程仓库: $REPO_URL"
echo "  - 主分支: main"
echo "  - 开发分支: develop"
echo "  - 当前分支: $(git branch --show-current)"

# 显示最近的提交
echo ""
echo "📝 最近的提交:"
git log --oneline -5

echo ""
echo "🌐 你现在可以访问GitHub仓库查看项目:"
echo "   $REPO_URL"
echo ""
echo "📋 项目特性:"
echo "   ✅ 基于URDF的轮腿混合运动数字孪生映射器"
echo "   ✅ Python绑定接口 (pybind11)"
echo "   ✅ IMU传感器仿真模块"
echo "   ✅ ROS2通信接口"
echo "   ✅ 关节控制系统"
echo "   ✅ PyQt5控制面板"
echo "   ✅ 完整的测试套件"
echo ""
echo "🚀 下一步: 继续开发剩余功能模块"