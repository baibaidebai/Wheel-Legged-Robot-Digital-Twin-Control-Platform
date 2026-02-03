"""
轮腿机器人孪生控制系统

基于ROS2的仿真控制平台，用于轮腿机器人的数字孪生控制研究。
核心创新功能：基于URDF的轮腿混合运动数字孪生映射器。
"""

__version__ = "0.1.0"
__author__ = "轮腿机器人项目团队"
__email__ = "developer@example.com"

# 导出主要模块
from .core import *
from .utils import *

__all__ = [
    "core",
    "gui", 
    "algorithms",
    "utils"
]