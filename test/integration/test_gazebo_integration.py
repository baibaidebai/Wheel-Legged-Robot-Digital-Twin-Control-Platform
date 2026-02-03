#!/usr/bin/env python3
"""
Gazebo集成测试

测试Gazebo仿真环境的集成功能，包括URDF加载、物理仿真等。
"""

import pytest
import sys
import os
import subprocess
import time
import signal
from pathlib import Path

# 添加源码路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/wheel_legged_control'))


class TestGazeboIntegration:
    """Gazebo集成测试类"""
    
    def setup_method(self):
        """测试前设置"""
        self.gazebo_process = None
        self.test_timeout = 30  # 30秒超时
        
    def teardown_method(self):
        """测试后清理"""
        if self.gazebo_process:
            try:
                self.gazebo_process.terminate()
                self.gazebo_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.gazebo_process.kill()
            except Exception:
                pass
    
    def test_urdf_files_exist(self):
        """测试URDF文件是否存在"""
        base_dir = Path("src/wheel_legged_control")
        
        # 检查URDF文件
        urdf_files = [
            base_dir / "urdf" / "wheel_legged_robot_base.urdf.xacro",
            base_dir / "urdf" / "wheel_legged_robot_gazebo.urdf"
        ]
        
        for urdf_file in urdf_files:
            assert urdf_file.exists(), f"URDF文件不存在: {urdf_file}"
            
    def test_world_file_exists(self):
        """测试世界文件是否存在"""
        world_file = Path("src/wheel_legged_control/worlds/wheel_legged_robot.world")
        assert world_file.exists(), f"世界文件不存在: {world_file}"
        
    def test_config_files_exist(self):
        """测试配置文件是否存在"""
        config_files = [
            Path("src/wheel_legged_control/config/wheel_legged_control.yaml")
        ]
        
        for config_file in config_files:
            assert config_file.exists(), f"配置文件不存在: {config_file}"
            
    def test_launch_files_exist(self):
        """测试启动文件是否存在"""
        launch_files = [
            Path("src/wheel_legged_control/launch/gazebo_simulation.launch.py"),
            Path("src/wheel_legged_control/launch/system_launch.py")
        ]
        
        for launch_file in launch_files:
            assert launch_file.exists(), f"启动文件不存在: {launch_file}"
            assert os.access(launch_file, os.X_OK), f"启动文件不可执行: {launch_file}"
    
    def test_urdf_xacro_processing(self):
        """测试URDF xacro处理"""
        urdf_file = "src/wheel_legged_control/urdf/wheel_legged_robot_base.urdf.xacro"
        
        if not Path(urdf_file).exists():
            pytest.skip("URDF文件不存在")
        
        try:
            # 尝试处理xacro文件
            result = subprocess.run(
                ['xacro', urdf_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # 检查是否成功处理
            assert result.returncode == 0, f"xacro处理失败: {result.stderr}"
            assert len(result.stdout) > 0, "xacro输出为空"
            assert '<robot' in result.stdout, "输出不包含robot标签"
            
        except FileNotFoundError:
            pytest.skip("xacro命令不可用")
        except subprocess.TimeoutExpired:
            pytest.fail("xacro处理超时")
    
    def test_gazebo_world_validation(self):
        """测试Gazebo世界文件验证"""
        world_file = "src/wheel_legged_control/worlds/wheel_legged_robot.world"
        
        if not Path(world_file).exists():
            pytest.skip("世界文件不存在")
        
        # 读取并验证世界文件内容
        with open(world_file, 'r') as f:
            content = f.read()
        
        # 检查基本SDF结构
        assert '<?xml version="1.0"' in content, "缺少XML声明"
        assert '<sdf version=' in content, "缺少SDF版本声明"
        assert '<world name=' in content, "缺少世界定义"
        assert '<physics' in content, "缺少物理引擎配置"
        assert '<gravity>' in content, "缺少重力设置"
        
    @pytest.mark.slow
    def test_gazebo_headless_startup(self):
        """测试Gazebo无头模式启动（慢速测试）"""
        world_file = "src/wheel_legged_control/worlds/wheel_legged_robot.world"
        
        if not Path(world_file).exists():
            pytest.skip("世界文件不存在")
        
        try:
            # 启动Gazebo服务器（无头模式）
            self.gazebo_process = subprocess.Popen(
                ['gzserver', '--verbose', world_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待Gazebo启动
            start_time = time.time()
            gazebo_started = False
            
            while time.time() - start_time < self.test_timeout:
                if self.gazebo_process.poll() is not None:
                    # 进程已退出
                    stdout, stderr = self.gazebo_process.communicate()
                    pytest.fail(f"Gazebo启动失败:\nstdout: {stdout}\nstderr: {stderr}")
                
                time.sleep(1)
                
                # 检查Gazebo是否响应
                try:
                    result = subprocess.run(
                        ['gz', 'world', '-l'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0 and 'wheel_legged_robot_world' in result.stdout:
                        gazebo_started = True
                        break
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
            
            assert gazebo_started, "Gazebo启动超时或失败"
            
        except FileNotFoundError:
            pytest.skip("Gazebo未安装或不在PATH中")
        except Exception as e:
            pytest.fail(f"Gazebo测试失败: {e}")
    
    def test_ros2_dependencies(self):
        """测试ROS2依赖是否可用"""
        required_packages = [
            'gazebo_ros',
            'robot_state_publisher',
            'joint_state_publisher',
            'controller_manager'
        ]
        
        for package in required_packages:
            try:
                result = subprocess.run(
                    ['ros2', 'pkg', 'list'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    assert package in result.stdout, f"ROS2包不可用: {package}"
                else:
                    pytest.skip("ROS2不可用")
                    
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pytest.skip("ROS2命令不可用")


def test_gazebo_simulator_script():
    """测试Gazebo仿真器脚本"""
    script_path = Path("src/wheel_legged_control/scripts/gazebo_simulator.py")
    
    assert script_path.exists(), "Gazebo仿真器脚本不存在"
    assert os.access(script_path, os.X_OK), "Gazebo仿真器脚本不可执行"
    
    # 检查脚本语法
    try:
        result = subprocess.run(
            ['python3', '-m', 'py_compile', str(script_path)],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, f"脚本语法错误: {result.stderr}"
    except subprocess.TimeoutExpired:
        pytest.fail("脚本语法检查超时")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not slow"])