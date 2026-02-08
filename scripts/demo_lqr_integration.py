#!/usr/bin/env python3
"""
LQR控制器与算法管理器集成演示

演示如何将LQR控制器集成到算法管理器中，实现多算法切换。
"""

import os
import sys
import logging
import numpy as np
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src/wheel_legged_control'))

def create_simple_lqr_algorithm():
    """创建简化的LQR算法（不依赖SciPy）"""
    from wheel_legged_control.algorithms.algorithm_manager import BaseAlgorithm, AlgorithmConfig, AlgorithmType
    
    class SimpleLQRAlgorithm(BaseAlgorithm):
        """简化的LQR算法实现"""
        
        def __init__(self, config: AlgorithmConfig):
            super().__init__(config)
            self.name = "SimpleLQR"
            self.description = "简化的LQR控制器（不依赖SciPy）"
            
            # 控制参数
            self.K_gain = np.array([
                [5.0, 0.0, 2.0, 0.0],  # x方向控制增益
                [0.0, 5.0, 0.0, 2.0]   # y方向控制增益
            ])
            
            self.reference_state = np.zeros(4)
            self.max_control = 5.0
            
            # 性能监控
            self.control_history = []
            self.cost_history = []
            
        def initialize(self, **kwargs) -> bool:
            """初始化算法"""
            try:
                if 'reference_state' in kwargs:
                    self.reference_state = np.array(kwargs['reference_state'])
                
                if 'max_control' in kwargs:
                    self.max_control = kwargs['max_control']
                
                self.logger.info(f"SimpleLQR初始化成功，参考状态: {self.reference_state}")
                return True
                
            except Exception as e:
                self.logger.error(f"SimpleLQR初始化失败: {e}")
                return False
        
        def execute(self, inputs: dict) -> dict:
            """执行控制算法"""
            try:
                current_state = inputs.get('current_state')
                if current_state is None:
                    return {'error': '缺少当前状态输入'}
                
                current_state = np.array(current_state)
                
                # 更新参考状态（如果提供）
                if 'reference_state' in inputs:
                    self.reference_state = np.array(inputs['reference_state'])
                
                # 计算状态误差
                error = current_state - self.reference_state
                
                # LQR控制律：u = -K * error
                control = -self.K_gain @ error
                
                # 应用控制限制
                control = np.clip(control, -self.max_control, self.max_control)
                
                # 计算代价（简化）
                Q = np.diag([10.0, 10.0, 1.0, 1.0])
                R = np.diag([0.1, 0.1])
                cost = error.T @ Q @ error + control.T @ R @ control
                
                # 记录历史
                self.control_history.append(control.copy())
                self.cost_history.append(float(cost))
                
                return {
                    'control_input': control,
                    'cost': float(cost),
                    'state_error': error,
                    'algorithm': self.name
                }
                
            except Exception as e:
                self.logger.error(f"SimpleLQR执行失败: {e}")
                return {'error': str(e)}
        
        def cleanup(self):
            """清理算法资源"""
            self.control_history.clear()
            self.cost_history.clear()
            self.logger.info("SimpleLQR清理完成")
        
        def get_parameters(self) -> dict:
            """获取算法参数"""
            return {
                'name': self.name,
                'description': self.description,
                'K_gain': self.K_gain.tolist(),
                'reference_state': self.reference_state.tolist(),
                'max_control': self.max_control,
                'control_history_length': len(self.control_history),
                'average_cost': np.mean(self.cost_history) if self.cost_history else 0.0
            }
        
        def set_parameters(self, parameters: dict):
            """设置算法参数"""
            if 'K_gain' in parameters:
                self.K_gain = np.array(parameters['K_gain'])
            
            if 'reference_state' in parameters:
                self.reference_state = np.array(parameters['reference_state'])
            
            if 'max_control' in parameters:
                self.max_control = parameters['max_control']
    
    # 创建配置并返回算法实例
    config = AlgorithmConfig(
        name="SimpleLQR",
        algorithm_type=AlgorithmType.CONTROL,
        parameters={
            'reference_state': [0.0, 0.0, 0.0, 0.0],
            'max_control': 5.0
        }
    )
    
    return SimpleLQRAlgorithm(config)

def demo_lqr_integration():
    """演示LQR与算法管理器的集成"""
    print("🔗 LQR控制器与算法管理器集成演示")
    print("=" * 60)
    
    try:
        from wheel_legged_control.algorithms.algorithm_manager import AlgorithmManager, AlgorithmConfig, AlgorithmType
        
        # 创建算法管理器
        manager = AlgorithmManager()
        
        # 创建LQR算法配置
        lqr_config = AlgorithmConfig(
            name="SimpleLQR",
            algorithm_type=AlgorithmType.CONTROL,
            parameters={
                'reference_state': [2.0, 1.0, 0.0, 0.0],
                'max_control': 5.0
            }
        )
        
        # 注册LQR算法工厂
        def lqr_factory(config):
            # 创建内部类来使用传入的config
            from wheel_legged_control.algorithms.algorithm_manager import BaseAlgorithm
            
            class SimpleLQRAlgorithm(BaseAlgorithm):
                """简化的LQR算法实现"""
                
                def __init__(self, config):
                    super().__init__(config)
                    
                    # 控制参数
                    self.K_gain = np.array([
                        [5.0, 0.0, 2.0, 0.0],  # x方向控制增益
                        [0.0, 5.0, 0.0, 2.0]   # y方向控制增益
                    ])
                    
                    self.reference_state = np.zeros(4)
                    self.max_control = 5.0
                    
                    # 从配置中获取参数
                    if 'K_gain' in config.parameters:
                        self.K_gain = np.array(config.parameters['K_gain'])
                    if 'reference_state' in config.parameters:
                        self.reference_state = np.array(config.parameters['reference_state'])
                    if 'max_control' in config.parameters:
                        self.max_control = config.parameters['max_control']
                    
                    # 性能监控
                    self.control_history = []
                    self.cost_history = []
                
                def initialize(self) -> bool:
                    """初始化算法"""
                    try:
                        self.logger.info(f"SimpleLQR初始化成功，参考状态: {self.reference_state}")
                        return True
                        
                    except Exception as e:
                        self.logger.error(f"SimpleLQR初始化失败: {e}")
                        return False
                
                def execute(self, inputs: dict) -> dict:
                    """执行控制算法"""
                    try:
                        current_state = inputs.get('current_state')
                        if current_state is None:
                            return {'error': '缺少当前状态输入'}
                        
                        current_state = np.array(current_state)
                        
                        # 更新参考状态（如果提供）
                        if 'reference_state' in inputs:
                            self.reference_state = np.array(inputs['reference_state'])
                        
                        # 计算状态误差
                        error = current_state - self.reference_state
                        
                        # LQR控制律：u = -K * error
                        control = -self.K_gain @ error
                        
                        # 应用控制限制
                        control = np.clip(control, -self.max_control, self.max_control)
                        
                        # 计算代价（简化）
                        Q = np.diag([10.0, 10.0, 1.0, 1.0])
                        R = np.diag([0.1, 0.1])
                        cost = error.T @ Q @ error + control.T @ R @ control
                        
                        # 记录历史
                        self.control_history.append(control.copy())
                        self.cost_history.append(float(cost))
                        
                        return {
                            'control_input': control,
                            'cost': float(cost),
                            'state_error': error,
                            'algorithm': self.config.name
                        }
                        
                    except Exception as e:
                        self.logger.error(f"SimpleLQR执行失败: {e}")
                        return {'error': str(e)}
                
                def cleanup(self) -> bool:
                    """清理算法资源"""
                    try:
                        self.control_history.clear()
                        self.cost_history.clear()
                        self.logger.info("SimpleLQR清理完成")
                        return True
                    except Exception as e:
                        self.logger.error(f"SimpleLQR清理失败: {e}")
                        return False
            
            return SimpleLQRAlgorithm(config)
        
        manager.register_algorithm_factory("simple_lqr", lqr_factory)
        
        # 创建算法实例
        success = manager.create_algorithm("simple_lqr_instance", "simple_lqr", lqr_config)
        print(f"✅ 算法创建: {'成功' if success else '失败'}")
        
        if not success:
            return False
        
        # 设置为活跃算法
        success = manager.set_active_algorithm(AlgorithmType.CONTROL, "simple_lqr_instance")
        print(f"🔄 算法激活: {'成功' if success else '失败'}")
        
        if not success:
            return False
        
        # 仿真控制循环
        print(f"\n🎮 开始控制仿真...")
        
        current_state = np.array([0.0, 0.0, 0.0, 0.0])
        target_state = np.array([2.0, 1.0, 0.0, 0.0])
        
        # 简化的系统动力学
        A = np.array([
            [0, 0, 1, 0],
            [0, 0, 0, 1],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ])
        B = np.array([
            [0, 0],
            [0, 0],
            [1, 0],
            [0, 1]
        ])
        dt = 0.1
        I = np.eye(4)
        A_d = I + A * dt
        B_d = B * dt
        
        states = [current_state.copy()]
        controls = []
        costs = []
        
        for step in range(30):
            # 执行算法
            inputs = {
                'current_state': current_state,
                'reference_state': target_state
            }
            
            result = manager.execute_algorithm(AlgorithmType.CONTROL, inputs)
            
            if result is None or 'error' in result:
                error_msg = result.get('error', '未知错误') if result else '算法返回None'
                print(f"❌ 算法执行错误: {error_msg}")
                break
            
            control = result['control_input']
            cost = result['cost']
            
            # 更新状态
            current_state = A_d @ current_state + B_d @ control
            
            # 记录数据
            states.append(current_state.copy())
            controls.append(control.copy())
            costs.append(cost)
            
            # 每5步输出一次
            if step % 5 == 0:
                pos_error = np.linalg.norm(current_state[:2] - target_state[:2])
                print(f"   步骤 {step:2d}: 位置误差={pos_error:.4f}, 代价={cost:.4f}")
        
        # 获取算法性能指标
        performance = manager.get_performance_report()
        
        print(f"\n📊 算法性能指标:")
        for key, value in performance.items():
            if key == 'algorithms':
                for alg_id, alg_info in value.items():
                    print(f"   算法 {alg_id}:")
                    for sub_key, sub_value in alg_info.items():
                        if isinstance(sub_value, float):
                            print(f"     {sub_key}: {sub_value:.4f}")
                        else:
                            print(f"     {sub_key}: {sub_value}")
            else:
                print(f"   {key}: {value}")
        
        # 获取算法信息
        alg_info = manager.get_algorithm_info("simple_lqr_instance")
        if alg_info:
            print(f"\n⚙️  算法信息:")
            for key, value in alg_info.items():
                if isinstance(value, dict):
                    print(f"   {key}:")
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, float):
                            print(f"     {sub_key}: {sub_value:.4f}")
                        else:
                            print(f"     {sub_key}: {sub_value}")
                elif isinstance(value, float):
                    print(f"   {key}: {value:.4f}")
                else:
                    print(f"   {key}: {value}")
        
        # 分析结果
        if len(states) > 1:
            states = np.array(states)
            controls = np.array(controls)
            costs = np.array(costs)
            
            final_error = np.linalg.norm(states[-1][:2] - target_state[:2])
            avg_cost = np.mean(costs)
            max_control = np.max(np.abs(controls))
            
            print(f"\n📈 仿真结果:")
            print(f"   最终位置误差: {final_error:.4f}")
            print(f"   平均代价: {avg_cost:.4f}")
            print(f"   最大控制力: {max_control:.4f}")
            
            if final_error < 0.2:
                print("✅ 控制成功收敛到目标！")
            else:
                print("⚠️  控制未完全收敛")
        
        # 清理算法
        manager.remove_algorithm("simple_lqr_instance")
        
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False
    
    except Exception as e:
        print(f"❌ 集成演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def demo_algorithm_switching():
    """演示算法切换功能"""
    print("\n🔄 算法切换演示")
    print("-" * 40)
    
    try:
        from wheel_legged_control.algorithms.algorithm_manager import AlgorithmManager, AlgorithmConfig, AlgorithmType
        
        # 创建算法管理器
        manager = AlgorithmManager()
        
        # 注册LQR算法工厂
        def lqr_factory(config):
            # 创建内部类来使用传入的config
            from wheel_legged_control.algorithms.algorithm_manager import BaseAlgorithm
            
            class SimpleLQRAlgorithm(BaseAlgorithm):
                """简化的LQR算法实现"""
                
                def __init__(self, config):
                    super().__init__(config)
                    
                    # 控制参数
                    self.K_gain = np.array([
                        [5.0, 0.0, 2.0, 0.0],  # x方向控制增益
                        [0.0, 5.0, 0.0, 2.0]   # y方向控制增益
                    ])
                    
                    self.reference_state = np.zeros(4)
                    self.max_control = 5.0
                    
                    # 从配置中获取参数
                    if 'K_gain' in config.parameters:
                        self.K_gain = np.array(config.parameters['K_gain'])
                    if 'reference_state' in config.parameters:
                        self.reference_state = np.array(config.parameters['reference_state'])
                    if 'max_control' in config.parameters:
                        self.max_control = config.parameters['max_control']
                    
                    # 性能监控
                    self.control_history = []
                    self.cost_history = []
                
                def initialize(self) -> bool:
                    """初始化算法"""
                    try:
                        self.logger.info(f"SimpleLQR初始化成功，参考状态: {self.reference_state}")
                        return True
                        
                    except Exception as e:
                        self.logger.error(f"SimpleLQR初始化失败: {e}")
                        return False
                
                def execute(self, inputs: dict) -> dict:
                    """执行控制算法"""
                    try:
                        current_state = inputs.get('current_state')
                        if current_state is None:
                            return {'error': '缺少当前状态输入'}
                        
                        current_state = np.array(current_state)
                        
                        # 更新参考状态（如果提供）
                        if 'reference_state' in inputs:
                            self.reference_state = np.array(inputs['reference_state'])
                        
                        # 计算状态误差
                        error = current_state - self.reference_state
                        
                        # LQR控制律：u = -K * error
                        control = -self.K_gain @ error
                        
                        # 应用控制限制
                        control = np.clip(control, -self.max_control, self.max_control)
                        
                        # 计算代价（简化）
                        Q = np.diag([10.0, 10.0, 1.0, 1.0])
                        R = np.diag([0.1, 0.1])
                        cost = error.T @ Q @ error + control.T @ R @ control
                        
                        # 记录历史
                        self.control_history.append(control.copy())
                        self.cost_history.append(float(cost))
                        
                        return {
                            'control_input': control,
                            'cost': float(cost),
                            'state_error': error,
                            'algorithm': self.config.name
                        }
                        
                    except Exception as e:
                        self.logger.error(f"SimpleLQR执行失败: {e}")
                        return {'error': str(e)}
                
                def cleanup(self) -> bool:
                    """清理算法资源"""
                    try:
                        self.control_history.clear()
                        self.cost_history.clear()
                        self.logger.info("SimpleLQR清理完成")
                        return True
                    except Exception as e:
                        self.logger.error(f"SimpleLQR清理失败: {e}")
                        return False
            
            return SimpleLQRAlgorithm(config)
        
        manager.register_algorithm_factory("simple_lqr", lqr_factory)
        
        # 创建多个算法配置
        conservative_config = AlgorithmConfig(
            name="LQR_Conservative",
            algorithm_type=AlgorithmType.CONTROL,
            parameters={
                'K_gain': [[3.0, 0.0, 1.5, 0.0], [0.0, 3.0, 0.0, 1.5]],
                'reference_state': [1.0, 1.0, 0.0, 0.0],
                'max_control': 5.0
            }
        )
        
        aggressive_config = AlgorithmConfig(
            name="LQR_Aggressive", 
            algorithm_type=AlgorithmType.CONTROL,
            parameters={
                'K_gain': [[8.0, 0.0, 3.0, 0.0], [0.0, 8.0, 0.0, 3.0]],
                'reference_state': [1.0, 1.0, 0.0, 0.0],
                'max_control': 5.0
            }
        )
        
        # 创建算法实例
        manager.create_algorithm("conservative", "simple_lqr", conservative_config)
        manager.create_algorithm("aggressive", "simple_lqr", aggressive_config)
        
        algorithms_info = manager.get_all_algorithms_info()
        print(f"📋 注册的算法: {list(algorithms_info.keys())}")
        
        # 测试不同算法的性能
        algorithms_to_test = ["conservative", "aggressive"]
        results = {}
        
        for alg_name in algorithms_to_test:
            print(f"\n🧪 测试算法: {alg_name}")
            
            # 设置为活跃算法
            manager.set_active_algorithm(AlgorithmType.CONTROL, alg_name)
            
            # 简单测试
            test_state = np.array([0.0, 0.0, 0.0, 0.0])
            inputs = {
                'current_state': test_state,
                'reference_state': [1.0, 1.0, 0.0, 0.0]
            }
            
            result = manager.execute_algorithm(AlgorithmType.CONTROL, inputs)
            
            if result is not None and 'error' not in result:
                control_magnitude = np.linalg.norm(result['control_input'])
                cost = result['cost']
                
                results[alg_name] = {
                    'control_magnitude': control_magnitude,
                    'cost': cost
                }
                
                print(f"   控制力大小: {control_magnitude:.4f}")
                print(f"   代价: {cost:.4f}")
            else:
                print(f"   算法执行失败")
        
        # 比较结果
        print(f"\n📊 算法比较:")
        for alg_name, metrics in results.items():
            print(f"   {alg_name}:")
            print(f"     控制力大小: {metrics['control_magnitude']:.4f}")
            print(f"     代价: {metrics['cost']:.4f}")
        
        # 清理
        manager.cleanup()
        
        return True
        
    except Exception as e:
        print(f"❌ 算法切换演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 LQR控制器集成演示")
    print("=" * 60)
    print(f"📅 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 演示LQR与算法管理器集成
        success1 = demo_lqr_integration()
        
        if success1:
            # 演示算法切换
            success2 = demo_algorithm_switching()
            
            if success1 and success2:
                print(f"\n🎉 所有演示完成！")
                print(f"✅ LQR控制器已成功集成到算法管理器")
                print(f"✅ 算法切换功能正常工作")
                return 0
        
        print(f"\n⚠️  部分演示未完成")
        return 1
        
    except KeyboardInterrupt:
        print(f"\n⏹️  演示被用户中断")
        return 0
    
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)