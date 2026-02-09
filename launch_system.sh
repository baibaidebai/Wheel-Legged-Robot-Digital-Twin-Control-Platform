#!/bin/bash
# 系统启动脚本包装器
# 提供便捷的命令行接口启动完整系统

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    cat << EOF
轮腿机器人孪生控制系统启动脚本

用法: $0 [选项]

选项:
    -m, --mode MODE         仿真模式: gazebo, mujoco, none (默认: gazebo)
    -g, --gui               启用控制面板GUI (默认: true)
    -r, --rviz              启用RViz可视化 (默认: false)
    -d, --record            启用数据记录 (默认: false)
    -a, --algorithm         启用算法管理器 (默认: false)
    -l, --log-level LEVEL   日志级别: debug, info, warn, error (默认: info)
    -q, --quick             快速启动模式（最小配置）
    -h, --help              显示此帮助信息

示例:
    # 使用Gazebo仿真启动完整系统
    $0 --mode gazebo --gui --rviz

    # 使用MuJoCo仿真，启用数据记录
    $0 --mode mujoco --record

    # 快速启动（开发模式）
    $0 --quick

    # 硬件模式（无仿真）
    $0 --mode none --gui

环境要求:
    - ROS2 Humble已安装并source
    - 工作空间已编译
    - 必要的Python依赖已安装

EOF
}

# 检查ROS2环境
check_ros2_env() {
    if [ -z "$ROS_DISTRO" ]; then
        print_error "ROS2环境未设置。请先source ROS2 setup文件。"
        print_info "例如: source /opt/ros/humble/setup.bash"
        exit 1
    fi
    print_success "ROS2环境已设置: $ROS_DISTRO"
}

# 检查工作空间
check_workspace() {
    if [ ! -d "install" ]; then
        print_warning "工作空间未编译。正在编译..."
        colcon build --packages-select wheel_legged_control
        if [ $? -ne 0 ]; then
            print_error "工作空间编译失败"
            exit 1
        fi
        print_success "工作空间编译完成"
    fi
    
    # Source工作空间
    if [ -f "install/setup.bash" ]; then
        source install/setup.bash
        print_success "工作空间已source"
    else
        print_error "找不到install/setup.bash"
        exit 1
    fi
}

# 默认参数
SIM_MODE="gazebo"
ENABLE_GUI="true"
ENABLE_RVIZ="false"
ENABLE_RECORDING="false"
ENABLE_ALGORITHM="false"
LOG_LEVEL="info"
QUICK_MODE=false

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--mode)
            SIM_MODE="$2"
            shift 2
            ;;
        -g|--gui)
            ENABLE_GUI="true"
            shift
            ;;
        -r|--rviz)
            ENABLE_RVIZ="true"
            shift
            ;;
        -d|--record)
            ENABLE_RECORDING="true"
            shift
            ;;
        -a|--algorithm)
            ENABLE_ALGORITHM="true"
            shift
            ;;
        -l|--log-level)
            LOG_LEVEL="$2"
            shift 2
            ;;
        -q|--quick)
            QUICK_MODE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 显示启动信息
print_info "=========================================="
print_info "轮腿机器人孪生控制系统"
print_info "=========================================="
print_info "仿真模式: $SIM_MODE"
print_info "GUI: $ENABLE_GUI"
print_info "RViz: $ENABLE_RVIZ"
print_info "数据记录: $ENABLE_RECORDING"
print_info "算法管理器: $ENABLE_ALGORITHM"
print_info "日志级别: $LOG_LEVEL"
print_info "=========================================="

# 检查环境
check_ros2_env
check_workspace

# 启动系统
print_info "正在启动系统..."

if [ "$QUICK_MODE" = true ]; then
    # 快速启动模式
    print_info "使用快速启动模式"
    ros2 launch wheel_legged_control quick_start.launch.py \
        sim_mode:=$SIM_MODE \
        enable_gui:=$ENABLE_GUI
else
    # 完整启动模式
    ros2 launch wheel_legged_control complete_system.launch.py \
        sim_mode:=$SIM_MODE \
        enable_gui:=$ENABLE_GUI \
        enable_rviz:=$ENABLE_RVIZ \
        enable_recording:=$ENABLE_RECORDING \
        enable_algorithm_manager:=$ENABLE_ALGORITHM \
        log_level:=$LOG_LEVEL
fi

# 捕获退出信号
trap 'print_info "正在关闭系统..."; exit 0' SIGINT SIGTERM

print_success "系统已启动"
