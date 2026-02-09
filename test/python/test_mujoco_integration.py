#!/usr/bin/env python3
"""
MuJoCo集成单元测试

测试MuJoCo物理引擎集成的各个组件，包括：
1. 仿真管理器功能
2. MuJoCo后端基本操作
3. URDF到MJCF转换
4. 性能和稳定性测试
"""

import unittest
import numpy as np
import os
import sys
import tempfile
import time

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

try:
    from wheel_legged_control.simulation import (
        SimulationManager, SimulationBackend, SimulationConfig,
        MuJoCoSimulationBackend
    )
    from wheel_legged_control.simulation.mujoco_backend import URDFToMJCFConverter
    SIMULATION_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  仿真模块不可用: {e}")
    SIMULATION_AVAILABLE = False

try:
    import mujoco
    MUJOCO_AVAILABLE = True
except ImportError:
    MUJOCO_AVAILABLE = False


class TestSimulationManager(unittest.TestCase):
    """测试仿真管理器"""
    
    def setUp(self):
        """测试前准备"""
        if not SIMULATION_AVAILABLE:
            self.skipTest("仿真模块不可用")
        
        self.config = SimulationConfig(
            backend=SimulationBackend.MUJOCO,
            dt=0.001,
            enable_rendering=False
        )
        self.sim_manager = SimulationManager(self.config)
    
    def tearDown(self):
        """测试后清理"""
        if hasattr(self, 'sim_manager'):
            self.sim_manager.close()
    
    def test_manager_initialization(self):
        """测试管理器初始化"""
        self.assertIsNotNone(self.sim_manager)
        self.assertEqual(self.sim_manager.config.backend, SimulationBackend.MUJOCO)
        
        # 检查可用后端
        available_backends = self.sim_manager.get_available_backends()
        self.assertIsInstance(available_backends, list)
        self.assertGreater(len(available_backends), 0)
    
    def test_backend_registration(self):
        """测试后端注册"""
        available_backends = self.sim_manager.get_available_backends()
        
        # 至少应该有一个后端可用
        self.assertGreater(len(available_backends), 0)
        
        # 检查后端类型
        for backend in available_backends:
            self.assertIsInstance(backend, SimulationBackend)
    
    @unittest.skipUnless(MUJOCO_AVAILABLE, "MuJoCo不可用")
    def test_mujoco_backend_availability(self):
        """测试MuJoCo后端可用性"""
        available_backends = self.sim_manager.get_available_backends()
        self.assertIn(SimulationBackend.MUJOCO, available_backends)


class TestURDFToMJCFConverter(unittest.TestCase):
    """测试URDF到MJCF转换器"""
    
    def setUp(self):
        """测试前准备"""
        if not SIMULATION_AVAILABLE:
            self.skipTest("仿真模块不可用")
        
        self.converter = URDFToMJCFConverter()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """测试后清理"""
        # 清理临时文件
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_converter_initialization(self):
        """测试转换器初始化"""
        self.assertIsNotNone(self.converter)
        self.assertTrue(hasattr(self.converter, 'convert_urdf_to_mjcf'))
    
    def test_create_simple_mjcf(self):
        """测试创建简化MJCF文件"""
        mjcf_path = os.path.join(self.temp_dir, 'test_simple.xml')
        
        result_path = self.converter._create_simple_mjcf(mjcf_path)
        
        self.assertEqual(result_path, mjcf_path)
        self.assertTrue(os.path.exists(mjcf_path))
        
        # 检查文件内容
        with open(mjcf_path, 'r') as f:
            content = f.read()
            self.assertIn('<mujoco', content)
            self.assertIn('wheel_legged_robot', content)
            self.assertIn('<actuator>', content)
    
    def test_urdf_conversion_with_nonexistent_file(self):
        """测试转换不存在的URDF文件"""
        nonexistent_urdf = os.path.join(self.temp_dir, 'nonexistent.urdf')
        mjcf_path = os.path.join(self.temp_dir, 'output.xml')
        
        with self.assertRaises(FileNotFoundError):
            self.converter.convert_urdf_to_mjcf(nonexistent_urdf, mjcf_path)
    
    def test_urdf_conversion_with_simple_urdf(self):
        """测试转换简单URDF文件"""
        # 创建简单的URDF文件
        urdf_content = '''<?xml version="1.0"?>
<robot name="test_robot">
  <link name="base_link">
    <inertial>
      <mass value="1.0"/>
      <inertia ixx="0.1" iyy="0.1" izz="0.1" ixy="0" ixz="0" iyz="0"/>
    </inertial>
    <visual>
      <geometry>
        <box size="0.2 0.2 0.1"/>
      </geometry>
    </visual>
  </link>
  
  <link name="wheel_link">
    <inertial>
      <mass value="0.5"/>
      <inertia ixx="0.05" iyy="0.05" izz="0.05" ixy="0" ixz="0" iyz="0"/>
    </inertial>
    <visual>
      <geometry>
        <cylinder radius="0.05" length="0.02"/>
      </geometry>
    </visual>
  </link>
  
  <joint name="wheel_joint" type="continuous">
    <parent link="base_link"/>
    <child link="wheel_link"/>
    <origin xyz="0 0 -0.1"/>
    <axis xyz="0 1 0"/>
  </joint>
</robot>'''
        
        urdf_path = os.path.join(self.temp_dir, 'test_robot.urdf')
        mjcf_path = os.path.join(self.temp_dir, 'test_robot.xml')
        
        with open(urdf_path, 'w') as f:
            f.write(urdf_content)
        
        # 转换
        result_path = self.converter.convert_urdf_to_mjcf(urdf_path, mjcf_path)
        
        self.assertTrue(os.path.exists(result_path))
        
        # 检查MJCF内容
        with open(result_path, 'r') as f:
            content = f.read()
            self.assertIn('<mujoco', content)
            self.assertIn('test_robot', content)


@unittest.skipUnless(MUJOCO_AVAILABLE, "MuJoCo不可用")
class TestMuJoCoBackend(unittest.TestCase):
    """测试MuJoCo后端"""
    
    def setUp(self):
        """测试前准备"""
        if not SIMULATION_AVAILABLE:
            self.skipTest("仿真模块不可用")
        
        self.config = SimulationConfig(
            backend=SimulationBackend.MUJOCO,
            dt=0.001,
            enable_rendering=False
        )
        self.backend = MuJoCoSimulationBackend(self.config)
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建测试模型
        self.test_model_path = os.path.join(self.temp_dir, 'test_model.xml')
        converter = URDFToMJCFConverter()
        converter._create_simple_mjcf(self.test_model_path)
    
    def tearDown(self):
        """测试后清理"""
        if hasattr(self, 'backend'):
            self.backend.close()
        
        # 清理临时文件
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_backend_initialization(self):
        """测试后端初始化"""
        self.assertIsNotNone(self.backend)
        self.assertFalse(self.backend.is_initialized)
    
    def test_model_loading(self):
        """测试模型加载"""
        success = self.backend.initialize(self.test_model_path)
        self.assertTrue(success)
        self.assertTrue(self.backend.is_initialized)
        self.assertIsNotNone(self.backend.model)
        self.assertIsNotNone(self.backend.data)
    
    def test_reset_functionality(self):
        """测试重置功能"""
        # 先初始化
        self.backend.initialize(self.test_model_path)
        
        # 重置
        success = self.backend.reset()
        self.assertTrue(success)
        self.assertEqual(self.backend.current_step, 0)
    
    def test_simulation_step(self):
        """测试仿真步进"""
        # 初始化
        self.backend.initialize(self.test_model_path)
        self.backend.reset()
        
        initial_step = self.backend.current_step
        
        # 执行步进
        success = self.backend.step()
        self.assertTrue(success)
        self.assertEqual(self.backend.current_step, initial_step + 1)
    
    def test_joint_control(self):
        """测试关节控制"""
        # 初始化
        self.backend.initialize(self.test_model_path)
        self.backend.reset()
        
        # 获取关节状态
        joint_states = self.backend.get_joint_states()
        self.assertIsInstance(joint_states, dict)
        self.assertGreater(len(joint_states), 0)
        
        # 设置关节位置
        if joint_states:
            joint_name = list(joint_states.keys())[0]
            test_position = 0.5
            
            success = self.backend.set_joint_positions({joint_name: test_position})
            self.assertTrue(success)
            
            # 检查设置是否生效
            updated_states = self.backend.get_joint_states()
            self.assertAlmostEqual(
                updated_states[joint_name]['position'], 
                test_position, 
                places=3
            )
    
    def test_state_retrieval(self):
        """测试状态获取"""
        # 初始化
        self.backend.initialize(self.test_model_path)
        self.backend.reset()
        
        # 获取状态
        state = self.backend.get_state()
        
        self.assertIsInstance(state, dict)
        self.assertIn('time', state)
        self.assertIn('step', state)
        self.assertIn('joint_positions', state)
        self.assertIn('joint_velocities', state)
        self.assertIn('base_position', state)
        self.assertIn('base_orientation', state)
        
        # 检查数据类型
        self.assertIsInstance(state['joint_positions'], dict)
        self.assertIsInstance(state['base_position'], np.ndarray)
        self.assertEqual(len(state['base_position']), 3)
        self.assertEqual(len(state['base_orientation']), 4)


class TestSimulationIntegration(unittest.TestCase):
    """测试仿真集成"""
    
    def setUp(self):
        """测试前准备"""
        if not SIMULATION_AVAILABLE:
            self.skipTest("仿真模块不可用")
        
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建测试模型
        self.test_model_path = os.path.join(self.temp_dir, 'integration_test.xml')
        converter = URDFToMJCFConverter()
        converter._create_simple_mjcf(self.test_model_path)
    
    def tearDown(self):
        """测试后清理"""
        # 清理临时文件
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @unittest.skipUnless(MUJOCO_AVAILABLE, "MuJoCo不可用")
    def test_full_simulation_workflow(self):
        """测试完整仿真工作流"""
        # 创建仿真管理器
        config = SimulationConfig(
            backend=SimulationBackend.MUJOCO,
            dt=0.001,
            enable_rendering=False
        )
        sim_manager = SimulationManager(config)
        
        try:
            # 初始化
            success = sim_manager.initialize(self.test_model_path)
            self.assertTrue(success)
            
            # 重置
            success = sim_manager.reset()
            self.assertTrue(success)
            
            # 执行仿真循环
            initial_state = sim_manager.get_state()
            
            for step in range(10):
                # 应用控制
                action = {
                    'lf0_motor': 0.1 * np.sin(step * 0.1),
                    'l_wheel_motor': 1.0
                }
                
                success = sim_manager.step(action)
                self.assertTrue(success)
            
            # 检查状态变化
            final_state = sim_manager.get_state()
            self.assertNotEqual(initial_state['step'], final_state['step'])
            self.assertGreater(final_state['time'], initial_state['time'])
            
        finally:
            sim_manager.close()
    
    def test_performance_benchmark(self):
        """测试性能基准"""
        if not MUJOCO_AVAILABLE:
            self.skipTest("MuJoCo不可用")
        
        config = SimulationConfig(
            backend=SimulationBackend.MUJOCO,
            dt=0.001,
            enable_rendering=False
        )
        sim_manager = SimulationManager(config)
        
        try:
            # 初始化
            sim_manager.initialize(self.test_model_path)
            sim_manager.reset()
            
            # 性能测试
            num_steps = 100
            start_time = time.time()
            
            for step in range(num_steps):
                action = {'l_wheel_motor': 1.0, 'r_wheel_motor': 1.0}
                sim_manager.step(action)
            
            elapsed_time = time.time() - start_time
            steps_per_second = num_steps / elapsed_time
            
            # 性能断言（应该能达到至少100 Hz）
            self.assertGreater(steps_per_second, 100)
            
            print(f"性能测试结果: {steps_per_second:.1f} steps/s")
            
        finally:
            sim_manager.close()


class TestErrorHandling(unittest.TestCase):
    """测试错误处理"""
    
    def setUp(self):
        """测试前准备"""
        if not SIMULATION_AVAILABLE:
            self.skipTest("仿真模块不可用")
    
    def test_invalid_model_path(self):
        """测试无效模型路径"""
        config = SimulationConfig(backend=SimulationBackend.MUJOCO)
        sim_manager = SimulationManager(config)
        
        try:
            # 尝试加载不存在的模型
            success = sim_manager.initialize("nonexistent_model.xml")
            self.assertFalse(success)
            
        finally:
            sim_manager.close()
    
    def test_operations_without_initialization(self):
        """测试未初始化时的操作"""
        config = SimulationConfig(backend=SimulationBackend.MUJOCO)
        sim_manager = SimulationManager(config)
        
        try:
            # 未初始化时的操作应该失败
            success = sim_manager.reset()
            self.assertFalse(success)
            
            success = sim_manager.step()
            self.assertFalse(success)
            
            state = sim_manager.get_state()
            self.assertEqual(state, {})
            
        finally:
            sim_manager.close()


def run_tests():
    """运行所有测试"""
    print("🧪 运行MuJoCo集成测试")
    print("=" * 50)
    
    # 检查依赖
    if not SIMULATION_AVAILABLE:
        print("❌ 仿真模块不可用，跳过测试")
        return
    
    if not MUJOCO_AVAILABLE:
        print("⚠️  MuJoCo不可用，部分测试将被跳过")
    
    # 创建测试套件
    test_classes = [
        TestSimulationManager,
        TestURDFToMJCFConverter,
        TestMuJoCoBackend,
        TestSimulationIntegration,
        TestErrorHandling
    ]
    
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出结果
    print("\n" + "=" * 50)
    print("🎉 测试完成")
    print(f"📊 运行测试: {result.testsRun}")
    print(f"✅ 成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ 失败: {len(result.failures)}")
    print(f"💥 错误: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ 失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")
    
    if result.errors:
        print("\n💥 错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('\\n')[-2]}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)