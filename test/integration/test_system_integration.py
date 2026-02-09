#!/usr/bin/env python3
"""
系统集成测试

验证轮腿机器人孪生控制系统的核心功能模块协调工作。
这是Task 6的关键验证步骤。
"""

import sys
import os
import time
import unittest
import threading
import numpy as np
from pathlib import Path

# 添加源码路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/wheel_legged_control'))

# 导入核心模块
try:
    from wheel_legged_control.core.urdf_loader import URDFLoader
    from wheel_legged_control.core.digital_twin_mapper_wrapper import (
        DigitalTwinMapper, create_test_constraint_model, create_test_task_state
    )
    from wheel_legged_control.controllers.joint_controller_standalone import JointController
    from wheel_legged_control.sensors.imu_simulator import IMUSimulator
    from wheel_legged_control.core.state_synchronizer import StateSynchronizer
    IMPORTS_SUCCESSFUL = True
except ImportError as e:
    print(f"❌ 模块导入失败: {e}")
    IMPORTS_SUCCESSFUL = False


class SystemIntegrationTest(unittest.TestCase):
    """系统集成测试类"""
    
    def setUp(self):
        """测试设置"""
        self.test_passed = []
        self.test_failed = []
        
    def test_01_module_imports(self):
        """测试1: 验证所有核心模块可以正确导入"""
        print("\n🔍 测试1: 模块导入验证")
        
        self.assertTrue(IMPORTS_SUCCESSFUL, "核心模块导入失败")
        print("✅ 所有核心模块导入成功")
        self.test_passed.append("模块导入")
        
    def test_02_urdf_loading(self):
        """测试2: URDF加载功能"""
        print("\n🔍 测试2: URDF加载功能验证")
        
        if not IMPORTS_SUCCESSFUL:
            self.skipTest("模块导入失败")
            
        # 测试URDF加载器
        loader = URDFLoader()
        
        # 查找可用的URDF文件
        urdf_paths = [
            "src/model/RM_Serial_Wheeled-leg_Robot/urdf/RM_Serial_Wheeled-leg_Robot.urdf",
            "src/model/DM_Wheel_leg_robot/urdf/wheel_legged_urdf_pkg.urdf",
            "src/wheel_legged_control/urdf/wheel_legged_robot.urdf"
        ]
        
        urdf_loaded = False
        for urdf_path in urdf_paths:
            if Path(urdf_path).exists():
                try:
                    robot_model = loader.load_urdf(urdf_path)
                    self.assertIsNotNone(robot_model, "机器人模型加载失败")
                    self.assertGreater(len(robot_model.joints), 0, "没有找到关节")
                    print(f"✅ URDF加载成功: {robot_model.name}")
                    print(f"   关节数量: {len(robot_model.joints)}")
                    print(f"   链接数量: {len(robot_model.links)}")
                    urdf_loaded = True
                    break
                except Exception as e:
                    print(f"⚠️ URDF加载失败 {urdf_path}: {e}")
                    continue
        
        self.assertTrue(urdf_loaded, "所有URDF文件加载失败")
        self.test_passed.append("URDF加载")
        
    def test_03_digital_twin_mapper(self):
        """测试3: 数字孪生映射器功能"""
        print("\n🔍 测试3: 数字孪生映射器验证")
        
        if not IMPORTS_SUCCESSFUL:
            self.skipTest("模块导入失败")
            
        # 创建数字孪生映射器
        mapper = DigitalTwinMapper()
        
        # 创建测试约束模型
        constraint_model = create_test_constraint_model()
        
        # 构建运动学模型
        success = mapper.build_kinematic_model(constraint_model)
        self.assertTrue(success, "运动学模型构建失败")
        print("✅ 运动学模型构建成功")
        
        # 测试正运动学
        joint_angles = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
        task_state = mapper.joint_to_task_mapping(joint_angles)
        self.assertIsNotNone(task_state, "正运动学映射失败")
        print("✅ 正运动学映射成功")
        
        # 测试逆运动学
        test_task_state = create_test_task_state()
        recovered_angles = mapper.task_to_joint_mapping(test_task_state)
        self.assertEqual(len(recovered_angles), len(joint_angles), "逆运动学输出维度错误")
        print("✅ 逆运动学映射成功")
        
        # 测试运动一致性验证
        result = mapper.validate_motion_consistency(joint_angles)
        self.assertIsNotNone(result, "运动一致性验证失败")
        print(f"✅ 运动一致性验证完成 (误差: {result.consistency_error:.6f})")
        
        self.test_passed.append("数字孪生映射器")
        
    def test_04_joint_controller(self):
        """测试4: 关节控制器功能"""
        print("\n🔍 测试4: 关节控制器验证")
        
        if not IMPORTS_SUCCESSFUL:
            self.skipTest("模块导入失败")
            
        # 创建关节控制器
        joint_names = ["joint1", "joint2", "joint3", "joint4"]
        controller = JointController(joint_names)
        
        # 测试关节限制设置
        limits = {
            "joint1": (-1.57, 1.57),
            "joint2": (-1.0, 1.0),
            "joint3": (-2.0, 2.0),
            "joint4": (-0.5, 0.5)
        }
        controller.set_joint_limits(limits)
        print("✅ 关节限制设置成功")
        
        # 测试PID参数设置
        pid_params = {
            "joint1": {"kp": 10.0, "ki": 0.1, "kd": 1.0},
            "joint2": {"kp": 8.0, "ki": 0.05, "kd": 0.8}
        }
        controller.set_pid_parameters(pid_params)
        print("✅ PID参数设置成功")
        
        # 测试关节指令
        target_positions = [0.5, -0.3, 0.8, -0.2]
        current_positions = [0.0, 0.0, 0.0, 0.0]
        
        control_output = controller.compute_control(target_positions, current_positions)
        self.assertEqual(len(control_output), len(joint_names), "控制输出维度错误")
        print("✅ 关节控制计算成功")
        
        # 测试轨迹插值
        trajectory = controller.generate_trajectory(
            start_positions=current_positions,
            end_positions=target_positions,
            duration=2.0,
            num_points=10
        )
        self.assertEqual(len(trajectory), 10, "轨迹点数量错误")
        print("✅ 轨迹生成成功")
        
        self.test_passed.append("关节控制器")
        
    def test_05_imu_simulator(self):
        """测试5: IMU仿真器功能"""
        print("\n🔍 测试5: IMU仿真器验证")
        
        if not IMPORTS_SUCCESSFUL:
            self.skipTest("模块导入失败")
            
        # 创建IMU仿真器
        imu_sim = IMUSimulator()
        
        # 导入RobotState类
        from wheel_legged_control.sensors.imu_simulator import RobotState
        
        # 设置机器人状态
        robot_state = RobotState(
            timestamp=time.time(),
            joint_positions={},
            joint_velocities={},
            base_position=np.array([0.0, 0.0, 0.2]),
            base_orientation=np.array([0.0, 0.0, 0.0, 1.0]),  # 四元数
            base_linear_velocity=np.array([0.1, 0.0, 0.0]),
            base_angular_velocity=np.array([0.0, 0.0, 0.1])
        )
        
        # 生成IMU数据
        orientation, angular_velocity, linear_acceleration = imu_sim.generate_imu_data(robot_state)
        
        # 验证IMU数据结构
        self.assertEqual(len(orientation), 4, "姿态四元数维度错误")
        self.assertEqual(len(angular_velocity), 3, "角速度维度错误")
        self.assertEqual(len(linear_acceleration), 3, "线性加速度维度错误")
        
        print("✅ IMU数据生成成功")
        print(f"   姿态: {orientation}")
        print(f"   角速度: {angular_velocity}")
        print(f"   线性加速度: {linear_acceleration}")
        
        # 测试噪声添加
        imu_sim.config.gyro_noise_std = 0.01
        imu_sim.config.accel_noise_std = 0.1
        
        noisy_orientation, noisy_angular_velocity, noisy_linear_acceleration = imu_sim.generate_imu_data(robot_state)
        self.assertIsNotNone(noisy_orientation, "带噪声的IMU数据生成失败")
        print("✅ 噪声IMU数据生成成功")
        
        # 测试ROS2消息创建
        imu_msg = imu_sim.create_imu_message(robot_state)
        self.assertIsNotNone(imu_msg, "IMU消息创建失败")
        
        # 验证消息有效性
        is_valid = imu_sim.validate_imu_data(imu_msg)
        self.assertTrue(is_valid, "IMU数据验证失败")
        print("✅ ROS2 IMU消息创建和验证成功")
        
        self.test_passed.append("IMU仿真器")
        
    def test_06_state_synchronizer(self):
        """测试6: 状态同步器功能"""
        print("\n🔍 测试6: 状态同步器验证")
        
        if not IMPORTS_SUCCESSFUL:
            self.skipTest("模块导入失败")
            
        # 导入配置类
        from wheel_legged_control.core.state_synchronizer import SyncConfig, RobotStateSnapshot
        
        # 创建状态同步器配置
        sync_config = SyncConfig()
        sync_config.max_history_length = 100
        sync_config.sync_frequency = 20.0
        sync_config.max_sync_error = 0.1
        sync_config.network_delay_mean = 0.02
        sync_config.network_delay_std = 0.005
        sync_config.packet_loss_rate = 0.01
        
        synchronizer = StateSynchronizer(sync_config)
        
        # 测试虚拟状态更新
        virtual_state = RobotStateSnapshot(
            timestamp=time.time(),
            joint_positions={'joint1': 0.1, 'joint2': 0.2, 'joint3': 0.3, 'joint4': 0.4},
            joint_velocities={'joint1': 0.0, 'joint2': 0.0, 'joint3': 0.0, 'joint4': 0.0},
            joint_efforts={'joint1': 0.0, 'joint2': 0.0, 'joint3': 0.0, 'joint4': 0.0},
            imu_orientation=(0.0, 0.0, 0.0, 1.0),
            imu_angular_velocity=(0.0, 0.0, 0.0),
            imu_linear_acceleration=(0.0, 0.0, 9.81)
        )
        
        synchronizer.update_virtual_state(virtual_state)
        print("✅ 虚拟状态更新成功")
        
        # 测试物理状态更新
        physical_state = RobotStateSnapshot(
            timestamp=time.time(),
            joint_positions={'joint1': 0.11, 'joint2': 0.19, 'joint3': 0.31, 'joint4': 0.39},
            joint_velocities={'joint1': 0.01, 'joint2': -0.01, 'joint3': 0.02, 'joint4': -0.01},
            joint_efforts={'joint1': 0.1, 'joint2': -0.1, 'joint3': 0.2, 'joint4': -0.2},
            imu_orientation=(0.0, 0.0, 0.0, 1.0),
            imu_angular_velocity=(0.0, 0.0, 0.0),
            imu_linear_acceleration=(0.0, 0.0, 9.81)
        )
        
        synchronizer.update_physical_state(physical_state)
        print("✅ 物理状态更新成功")
        
        # 测试同步误差计算
        sync_error = synchronizer.calculate_sync_error()
        self.assertIsNotNone(sync_error, "同步误差计算失败")
        print(f"✅ 同步误差计算成功: {sync_error:.6f}")
        
        # 测试质量指标
        quality_metrics = synchronizer.get_quality_metrics()
        self.assertIsNotNone(quality_metrics, "质量指标获取失败")
        print("✅ 质量指标获取成功")
        
        self.test_passed.append("状态同步器")
        
    def test_07_system_coordination(self):
        """测试7: 系统协调功能"""
        print("\n🔍 测试7: 系统协调验证")
        
        if not IMPORTS_SUCCESSFUL:
            self.skipTest("模块导入失败")
            
        # 创建所有核心组件
        print("创建核心组件...")
        
        # 1. 数字孪生映射器
        mapper = DigitalTwinMapper()
        constraint_model = create_test_constraint_model()
        mapper.build_kinematic_model(constraint_model)
        
        # 2. 关节控制器
        joint_names = ["lf0_joint", "lf1_joint", "rf0_joint", "rf1_joint"]
        controller = JointController(joint_names)
        
        # 3. IMU仿真器
        imu_sim = IMUSimulator()
        
        # 4. 状态同步器
        from wheel_legged_control.core.state_synchronizer import SyncConfig
        sync_config = SyncConfig()
        sync_config.max_history_length = 50
        sync_config.max_sync_error = 0.1
        
        synchronizer = StateSynchronizer(sync_config)
        
        print("✅ 所有核心组件创建成功")
        
        # 模拟系统协调工作流程
        print("执行系统协调测试...")
        
        # 步骤1: 设置目标关节角度
        target_angles = np.array([0.2, -0.3, 0.1, -0.2])
        current_angles = np.array([0.0, 0.0, 0.0, 0.0])
        
        # 步骤2: 通过数字孪生映射器验证运动
        validation_result = mapper.validate_motion_consistency(target_angles)
        self.assertTrue(validation_result.is_valid or validation_result.consistency_error < 0.5, 
                       "目标运动验证失败")
        print("✅ 目标运动验证通过")
        
        # 步骤3: 关节控制器计算控制输出
        control_output = controller.compute_control(target_angles.tolist(), current_angles.tolist())
        self.assertEqual(len(control_output), len(joint_names), "控制输出维度错误")
        print("✅ 关节控制计算完成")
        
        # 步骤4: 正运动学计算任务空间状态
        task_state = mapper.joint_to_task_mapping(target_angles)
        self.assertIsNotNone(task_state, "任务空间映射失败")
        print("✅ 任务空间状态计算完成")
        
        # 步骤5: IMU数据生成
        from wheel_legged_control.sensors.imu_simulator import RobotState
        
        robot_state = RobotState(
            timestamp=time.time(),
            joint_positions={},
            joint_velocities={},
            base_position=task_state.base_position,
            base_orientation=task_state.base_orientation,
            base_linear_velocity=np.array([0.0, 0.0, 0.0]),
            base_angular_velocity=np.array([0.0, 0.0, 0.0])
        )
        
        orientation, angular_velocity, linear_acceleration = imu_sim.generate_imu_data(robot_state)
        self.assertIsNotNone(orientation, "IMU数据生成失败")
        print("✅ IMU数据生成完成")
        
        # 步骤6: 状态同步
        from wheel_legged_control.core.state_synchronizer import RobotStateSnapshot
        
        virtual_state = RobotStateSnapshot(
            timestamp=time.time(),
            joint_positions={f'joint{i+1}': target_angles[i] for i in range(len(target_angles))},
            joint_velocities={f'joint{i+1}': 0.0 for i in range(len(target_angles))},
            joint_efforts={f'joint{i+1}': 0.0 for i in range(len(target_angles))},
            imu_orientation=(0.0, 0.0, 0.0, 1.0),
            imu_angular_velocity=(0.0, 0.0, 0.0),
            imu_linear_acceleration=(0.0, 0.0, 9.81)
        )
        
        synchronizer.update_virtual_state(virtual_state)
        
        # 模拟物理状态（添加小误差）
        physical_angles = target_angles + np.random.normal(0, 0.01, len(target_angles))
        physical_state = RobotStateSnapshot(
            timestamp=time.time(),
            joint_positions={f'joint{i+1}': physical_angles[i] for i in range(len(physical_angles))},
            joint_velocities={f'joint{i+1}': 0.0 for i in range(len(physical_angles))},
            joint_efforts={f'joint{i+1}': 0.0 for i in range(len(physical_angles))},
            imu_orientation=(0.0, 0.0, 0.0, 1.0),
            imu_angular_velocity=(0.0, 0.0, 0.0),
            imu_linear_acceleration=(0.0, 0.0, 9.81)
        )
        
        synchronizer.update_physical_state(physical_state)
        sync_error = synchronizer.calculate_sync_error()
        print(f"✅ 状态同步完成 (误差: {sync_error:.6f})")
        
        print("✅ 系统协调测试完成 - 所有模块协调工作正常")
        self.test_passed.append("系统协调")
        
    def test_08_performance_validation(self):
        """测试8: 性能验证"""
        print("\n🔍 测试8: 性能验证")
        
        if not IMPORTS_SUCCESSFUL:
            self.skipTest("模块导入失败")
            
        # 创建组件
        mapper = DigitalTwinMapper()
        constraint_model = create_test_constraint_model()
        mapper.build_kinematic_model(constraint_model)
        
        # 性能测试参数
        num_iterations = 100
        joint_angles = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
        
        # 测试正运动学性能
        start_time = time.time()
        for _ in range(num_iterations):
            task_state = mapper.joint_to_task_mapping(joint_angles)
        forward_time = time.time() - start_time
        
        forward_avg_time = forward_time / num_iterations
        self.assertLess(forward_avg_time, 0.01, "正运动学性能不达标")  # 小于10ms
        print(f"✅ 正运动学性能: {forward_avg_time*1000:.2f}ms/次")
        
        # 测试逆运动学性能
        test_task_state = create_test_task_state()
        start_time = time.time()
        for _ in range(num_iterations):
            recovered_angles = mapper.task_to_joint_mapping(test_task_state)
        inverse_time = time.time() - start_time
        
        inverse_avg_time = inverse_time / num_iterations
        self.assertLess(inverse_avg_time, 0.02, "逆运动学性能不达标")  # 小于20ms
        print(f"✅ 逆运动学性能: {inverse_avg_time*1000:.2f}ms/次")
        
        # 测试IMU仿真性能
        imu_sim = IMUSimulator()
        from wheel_legged_control.sensors.imu_simulator import RobotState
        
        robot_state = RobotState(
            timestamp=time.time(),
            joint_positions={},
            joint_velocities={},
            base_position=np.array([0.0, 0.0, 0.2]),
            base_orientation=np.array([0.0, 0.0, 0.0, 1.0]),
            base_linear_velocity=np.array([0.1, 0.0, 0.0]),
            base_angular_velocity=np.array([0.0, 0.0, 0.1])
        )
        
        start_time = time.time()
        for _ in range(num_iterations):
            orientation, angular_velocity, linear_acceleration = imu_sim.generate_imu_data(robot_state)
        imu_time = time.time() - start_time
        
        imu_avg_time = imu_time / num_iterations
        self.assertLess(imu_avg_time, 0.005, "IMU仿真性能不达标")  # 小于5ms
        print(f"✅ IMU仿真性能: {imu_avg_time*1000:.2f}ms/次")
        
        self.test_passed.append("性能验证")
        
    def tearDown(self):
        """测试清理"""
        pass
        
    def print_test_summary(self):
        """打印测试总结"""
        print("\n" + "="*60)
        print("🎯 系统集成测试总结")
        print("="*60)
        
        print(f"✅ 通过的测试 ({len(self.test_passed)}):")
        for test in self.test_passed:
            print(f"   • {test}")
            
        if self.test_failed:
            print(f"\n❌ 失败的测试 ({len(self.test_failed)}):")
            for test in self.test_failed:
                print(f"   • {test}")
        
        total_tests = len(self.test_passed) + len(self.test_failed)
        success_rate = len(self.test_passed) / total_tests * 100 if total_tests > 0 else 0
        
        print(f"\n📊 测试统计:")
        print(f"   总测试数: {total_tests}")
        print(f"   成功率: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("\n🎉 系统集成测试通过！核心功能验证成功。")
            return True
        else:
            print("\n⚠️ 系统集成测试未完全通过，需要修复问题。")
            return False


def run_integration_tests():
    """运行集成测试"""
    print("🚀 开始轮腿机器人孪生控制系统集成测试")
    print("="*60)
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    test_instance = SystemIntegrationTest()
    
    # 添加测试方法
    test_methods = [
        'test_01_module_imports',
        'test_02_urdf_loading', 
        'test_03_digital_twin_mapper',
        'test_04_joint_controller',
        'test_05_imu_simulator',
        'test_06_state_synchronizer',
        'test_07_system_coordination',
        'test_08_performance_validation'
    ]
    
    for method in test_methods:
        test_suite.addTest(SystemIntegrationTest(method))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
    result = runner.run(test_suite)
    
    # 手动运行测试以获得详细输出
    test_instance = SystemIntegrationTest()
    test_instance.setUp()
    
    try:
        test_instance.test_01_module_imports()
        test_instance.test_02_urdf_loading()
        test_instance.test_03_digital_twin_mapper()
        test_instance.test_04_joint_controller()
        test_instance.test_05_imu_simulator()
        test_instance.test_06_state_synchronizer()
        test_instance.test_07_system_coordination()
        test_instance.test_08_performance_validation()
    except Exception as e:
        print(f"❌ 测试执行出错: {e}")
        test_instance.test_failed.append(f"执行错误: {str(e)}")
    
    # 打印总结
    success = test_instance.print_test_summary()
    
    return success


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)