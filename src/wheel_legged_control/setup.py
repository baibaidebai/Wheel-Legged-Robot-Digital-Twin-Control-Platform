from setuptools import setup, find_packages
import os
from glob import glob

package_name = 'wheel_legged_control'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Launch文件
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')),
        # 配置文件
        (os.path.join('share', package_name, 'config'),
            glob('config/*.yaml')),
        # URDF文件
        (os.path.join('share', package_name, 'urdf'),
            glob('urdf/*.urdf')),
        (os.path.join('share', package_name, 'urdf'),
            glob('urdf/*.xacro')),
        # 世界文件
        (os.path.join('share', package_name, 'worlds'),
            glob('worlds/*.world')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='项目开发团队',
    maintainer_email='developer@example.com',
    description='轮腿机器人孪生控制系统 - 基于ROS2的仿真控制平台',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'control_panel = wheel_legged_control.gui.control_panel:main',
            'gazebo_simulator = wheel_legged_control.core.gazebo_simulator:main',
            'joint_controller = wheel_legged_control.controllers.joint_controller:main',
            'joint_controller_node = wheel_legged_control.core.joint_controller_node:main',
            'imu_simulator_node = wheel_legged_control.core.imu_simulator_node:main',
            'state_synchronizer_node = wheel_legged_control.core.state_synchronizer_node:main',
        ],
    },
)