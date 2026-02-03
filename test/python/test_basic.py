"""
基础Python模块测试
"""

import pytest
import sys
import os

# 添加源码路径到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/wheel_legged_control'))

def test_package_import():
    """测试包导入"""
    try:
        import wheel_legged_control
        assert wheel_legged_control.__version__ == "0.1.0"
    except ImportError as e:
        pytest.fail(f"Failed to import wheel_legged_control: {e}")

def test_submodules_import():
    """测试子模块导入"""
    try:
        from wheel_legged_control import core, gui, algorithms, utils
        # 基本导入测试通过即可，具体功能将在后续任务中测试
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import submodules: {e}")

if __name__ == "__main__":
    pytest.main([__file__])