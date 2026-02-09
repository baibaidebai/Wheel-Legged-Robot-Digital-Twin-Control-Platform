#!/usr/bin/env python3
"""
算法管理器演示脚本

展示算法管理器的核心功能，包括算法创建、切换、性能监控和数据导出。
"""

import sys
import os
import time
import json
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src/wheel_legged_control'))

from wheel_legged_control.algorithms.algorithm_manager import (
    AlgorithmManager, AlgorithmType, AlgorithmConfig, BaseAlgorithm,
    create_default_algorithms
)


class LQRControlAlgorithm(BaseAlgorithm):
    """LQR控制算法演示实现"""
    
    def __init__(self, config: AlgorithmConfig):
        super().__init__(config)
        self.Q = np.array(config.parameters.get('Q', [[1.0, 0.0], [0.0, 1.0]]))
        self.R = np.array(config.parameters.get('R', [[0.1]]))
        self.A = np.array(config.parameters.get('A', [[1.0, 0.1], [0.0, 1.0]]))
        self.B = np.array(config.parameters.get('B', [[0.0], [1.0]]))
        self.K = None  # 控制增益矩阵
        
    def initialize(self) -> bool:
        """初始化LQR控制器"""
        try:
            # 简化的LQR增益计算（实际应使用Riccati方程求解）
            self.K = np.array([[1.0, 0.5]])  # 简化的增益矩阵
            self.status = self.status.IDLE
            self.logger.info("LQR控制器初始化成功")
            return True
        except Exception as e:
            self.logger.error(f"LQR控制器初始化失败: {e}")
            return False
    
    def execute(self, inputs: Dict[str, any]) -> Dict[str, any]:
        """执行LQR控制"""
        try:
            state = np.array(inputs.get('state', [0.0, 0.0]))
            reference = np.array(inputs.get('reference', [0.0, 0.0]))
            
            # LQR控制律: u = -K(x - x_ref)
            error = state - reference
            control_output = -self.K @ error
            
            return {
                'output': control_output[0],
                'state_error': error.tolist(),
                'control_gain': self.K.tolist()
            }
            
        except Exception as e:
            self.logger.error(f"LQR控制执行失败: {e}")
            raise
    
    def cleanup(self) -> bool:
        """清理LQR控制器"""
        try:
            self.K = None
            self.status = self.status.STOPPED
            return True
        except Exception as e:
            self.logger.error(f"LQR控制器清理失败: {e}")
            return False


class ModelPredictiveControlAlgorithm(BaseAlgorithm):
    """模型预测控制算法演示实现"""
    
    def __init__(self, config: AlgorithmConfig):
        super().__init__(config)
        self.prediction_horizon = config.parameters.get('prediction_horizon', 10)
        self.control_horizon = config.parameters.get('control_horizon', 5)
        self.weight_output = config.parameters.get('weight_output', 1.0)
        self.weight_control = config.parameters.get('weight_control', 0.1)
        
    def initialize(self) -> bool:
        """初始化MPC控制器"""
        try:
            self.status = self.status.IDLE
            self.logger.info(f"MPC控制器初始化成功: 预测步长={self.prediction_horizon}")
            return True
        except Exception as e:
            self.logger.error(f"MPC控制器初始化失败: {e}")
            return False
    
    def execute(self, inputs: Dict[str, any]) -> Dict[str, any]:
        """执行MPC控制"""
        try:
            current_state = inputs.get('current_state', 0.0)
            reference = inputs.get('reference', 0.0)
            
            # 简化的MPC控制（实际应进行优化求解）
            error = reference - current_state
            
            # 简单的预测控制输出
            control_output = 0.8 * error  # 简化的控制律
            
            # 模拟预测轨迹
            predicted_states = []
            state = current_state
            for i in range(self.prediction_horizon):
                state = state + 0.1 * control_output  # 简化的状态预测
                predicted_states.append(state)
            
            return {
                'output': control_output,
                'predicted_states': predicted_states,
                'prediction_horizon': self.prediction_horizon,
                'error': error
            }
            
        except Exception as e:
            self.logger.error(f"MPC控制执行失败: {e}")
            raise
    
    def cleanup(self) -> bool:
        """清理MPC控制器"""
        try:
            self.status = self.status.STOPPED
            return True
        except Exception as e:
            self.logger.error(f"MPC控制器清理失败: {e}")
            return False


def create_advanced_algorithms(manager: AlgorithmManager) -> bool:
    """创建高级控制算法"""
    try:
        # 注册算法工厂
        manager.register_algorithm_factory('lqr_control', LQRControlAlgorithm)
        manager.register_algorithm_factory('mpc_control', ModelPredictiveControlAlgorithm)
        
        # 创建LQR控制算法
        lqr_config = AlgorithmConfig(
            name="LQR控制器",
            algorithm_type=AlgorithmType.CONTROL,
            parameters={
                'Q': [[1.0, 0.0], [0.0, 1.0]],
                'R': [[0.1]],
                'A': [[1.0, 0.1], [0.0, 1.0]],
                'B': [[0.0], [1.0]]
            },
            priority=3
        )
        
        # 创建MPC控制算法
        mpc_config = AlgorithmConfig(
            name="模型预测控制器",
            algorithm_type=AlgorithmType.CONTROL,
            parameters={
                'prediction_horizon': 10,
                'control_horizon': 5,
                'weight_output': 1.0,
                'weight_control': 0.1
            },
            priority=4
        )
        
        # 创建算法实例
        success = True
        success &= manager.create_algorithm('lqr_controller', 'lqr_control', lqr_config)
        success &= manager.create_algorithm('mpc_controller', 'mpc_control', mpc_config)
        
        return success
        
    except Exception as e:
        print(f"创建高级算法失败: {e}")
        return False


def demonstrate_algorithm_switching(manager: AlgorithmManager):
    """演示算法切换功能"""
    print("\n" + "="*60)
    print("🔄 算法切换演示")
    print("="*60)
    
    algorithms = ['default_pid', 'lqr_controller', 'mpc_controller']
    test_inputs = [
        {'setpoint': 1.0, 'current_value': 0.0, 'dt': 0.01},  # PID输入
        {'state': [0.5, 0.1], 'reference': [1.0, 0.0]},       # LQR输入
        {'current_state': 0.5, 'reference': 1.0}              # MPC输入
    ]
    
    for i, algorithm_name in enumerate(algorithms):
        print(f"\n🎯 切换到算法: {algorithm_name}")
        
        if manager.set_active_algorithm(AlgorithmType.CONTROL, algorithm_name):
            print(f"✅ 算法切换成功")
            
            # 执行算法
            inputs = test_inputs[i]
            result = manager.execute_algorithm(AlgorithmType.CONTROL, inputs)
            
            if result:
                print(f"📊 算法输出: {result.get('output', 'N/A')}")
                if 'predicted_states' in result:
                    print(f"🔮 预测状态数量: {len(result['predicted_states'])}")
                if 'control_gain' in result:
                    print(f"⚙️  控制增益: {result['control_gain']}")
            else:
                print("❌ 算法执行失败")
        else:
            print(f"❌ 算法切换失败")
        
        time.sleep(0.5)


def demonstrate_performance_monitoring(manager: AlgorithmManager):
    """演示性能监控功能"""
    print("\n" + "="*60)
    print("📊 性能监控演示")
    print("="*60)
    
    # 启动性能监控
    manager.start_monitoring()
    print("🚀 性能监控已启动")
    
    # 执行多种算法进行性能测试
    algorithms = ['default_pid', 'lqr_controller', 'mpc_controller']
    execution_counts = [50, 30, 20]  # 不同算法的执行次数
    
    for algorithm_name, count in zip(algorithms, execution_counts):
        print(f"\n🧪 测试算法: {algorithm_name} ({count}次执行)")
        
        if manager.set_active_algorithm(AlgorithmType.CONTROL, algorithm_name):
            for i in range(count):
                if algorithm_name == 'default_pid':
                    inputs = {'setpoint': 1.0, 'current_value': 0.1 * i, 'dt': 0.01}
                elif algorithm_name == 'lqr_controller':
                    inputs = {'state': [0.1 * i, 0.05 * i], 'reference': [1.0, 0.0]}
                else:  # mpc_controller
                    inputs = {'current_state': 0.1 * i, 'reference': 1.0}
                
                result = manager.execute_algorithm(AlgorithmType.CONTROL, inputs)
                
                # 偶尔模拟执行失败
                if i % 15 == 14:  # 每15次执行模拟一次失败
                    try:
                        manager.execute_algorithm(AlgorithmType.CONTROL, {'invalid': 'input'})
                    except:
                        pass  # 忽略预期的失败
        
        time.sleep(0.1)
    
    # 获取性能报告
    print("\n📈 性能报告:")
    report = manager.get_performance_report()
    
    for alg_id, info in report['algorithms'].items():
        print(f"\n算法: {info['name']}")
        print(f"  - 总调用次数: {info['total_calls']}")
        print(f"  - 成功率: {info['success_rate']:.2%}")
        print(f"  - 平均执行时间: {info['avg_execution_time']:.3f}ms")
        print(f"  - 最小执行时间: {info['min_execution_time']:.3f}ms")
        print(f"  - 最大执行时间: {info['max_execution_time']:.3f}ms")
        print(f"  - 错误次数: {info['error_count']}")
    
    # 停止监控
    manager.stop_monitoring()
    print("\n🛑 性能监控已停止")


def demonstrate_data_export(manager: AlgorithmManager):
    """演示数据导出功能"""
    print("\n" + "="*60)
    print("💾 数据导出演示")
    print("="*60)
    
    # 导出性能数据
    export_file = '/tmp/algorithm_performance_demo.json'
    
    if manager.export_performance_data(export_file):
        print(f"✅ 性能数据已导出到: {export_file}")
        
        # 读取并显示部分数据
        try:
            with open(export_file, 'r') as f:
                data = json.load(f)
            
            print(f"📄 导出数据概览:")
            print(f"  - 导出时间: {time.ctime(data['export_timestamp'])}")
            print(f"  - 总算法数: {data['performance_report']['total_algorithms']}")
            print(f"  - 总执行次数: {data['performance_report']['total_executions']}")
            print(f"  - 执行历史记录数: {len(data['execution_history'])}")
            
            # 显示最近几次执行记录
            if data['execution_history']:
                print(f"\n🕒 最近执行记录:")
                for record in data['execution_history'][-3:]:
                    print(f"  - {record['algorithm_id']}: {record['execution_time']:.3f}ms "
                          f"({'成功' if record['success'] else '失败'})")
        
        except Exception as e:
            print(f"❌ 读取导出数据失败: {e}")
    else:
        print("❌ 数据导出失败")


def create_performance_visualization(manager: AlgorithmManager):
    """创建性能可视化图表"""
    print("\n" + "="*60)
    print("📊 性能可视化")
    print("="*60)
    
    try:
        # 获取性能报告
        report = manager.get_performance_report()
        
        if not report['algorithms']:
            print("❌ 没有算法性能数据可视化")
            return
        
        # 准备数据
        algorithm_names = []
        avg_times = []
        success_rates = []
        total_calls = []
        
        for alg_id, info in report['algorithms'].items():
            algorithm_names.append(info['name'])
            avg_times.append(info['avg_execution_time'])
            success_rates.append(info['success_rate'] * 100)  # 转换为百分比
            total_calls.append(info['total_calls'])
        
        # 创建子图
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('算法管理器性能分析', fontsize=16, fontweight='bold')
        
        # 1. 平均执行时间
        bars1 = ax1.bar(algorithm_names, avg_times, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
        ax1.set_title('平均执行时间')
        ax1.set_ylabel('时间 (ms)')
        ax1.tick_params(axis='x', rotation=45)
        
        # 添加数值标签
        for bar, time_val in zip(bars1, avg_times):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.001,
                    f'{time_val:.3f}', ha='center', va='bottom')
        
        # 2. 成功率
        bars2 = ax2.bar(algorithm_names, success_rates, color=['#96CEB4', '#FFEAA7', '#DDA0DD'])
        ax2.set_title('算法成功率')
        ax2.set_ylabel('成功率 (%)')
        ax2.set_ylim(0, 105)
        ax2.tick_params(axis='x', rotation=45)
        
        # 添加数值标签
        for bar, rate in zip(bars2, success_rates):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                    f'{rate:.1f}%', ha='center', va='bottom')
        
        # 3. 总调用次数
        bars3 = ax3.bar(algorithm_names, total_calls, color=['#FF7675', '#74B9FF', '#A29BFE'])
        ax3.set_title('总调用次数')
        ax3.set_ylabel('调用次数')
        ax3.tick_params(axis='x', rotation=45)
        
        # 添加数值标签
        for bar, calls in zip(bars3, total_calls):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    f'{calls}', ha='center', va='bottom')
        
        # 4. 综合性能评分（自定义指标）
        performance_scores = []
        for i in range(len(algorithm_names)):
            # 综合评分 = 成功率权重 * 成功率 - 执行时间权重 * 归一化执行时间
            normalized_time = avg_times[i] / max(avg_times) if max(avg_times) > 0 else 0
            score = 0.7 * (success_rates[i] / 100) + 0.3 * (1 - normalized_time)
            performance_scores.append(score * 100)  # 转换为百分制
        
        bars4 = ax4.bar(algorithm_names, performance_scores, 
                       color=['#00B894', '#FDCB6E', '#E17055'])
        ax4.set_title('综合性能评分')
        ax4.set_ylabel('评分')
        ax4.set_ylim(0, 105)
        ax4.tick_params(axis='x', rotation=45)
        
        # 添加数值标签
        for bar, score in zip(bars4, performance_scores):
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                    f'{score:.1f}', ha='center', va='bottom')
        
        plt.tight_layout()
        
        # 保存图表
        chart_file = '/tmp/algorithm_performance_chart.png'
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        print(f"📊 性能图表已保存到: {chart_file}")
        
        # 显示图表（如果在支持的环境中）
        try:
            plt.show()
        except:
            print("💡 提示: 在图形界面环境中可以显示图表")
        
    except Exception as e:
        print(f"❌ 创建性能可视化失败: {e}")


def main():
    """主演示函数"""
    print("🎉 算法管理器功能演示")
    print("="*60)
    
    # 创建算法管理器
    manager = AlgorithmManager()
    
    try:
        # 1. 创建默认算法
        print("🔧 创建默认算法...")
        if create_default_algorithms(manager):
            print("✅ 默认算法创建成功")
        else:
            print("❌ 默认算法创建失败")
            return
        
        # 2. 创建高级算法
        print("\n🚀 创建高级控制算法...")
        if create_advanced_algorithms(manager):
            print("✅ 高级算法创建成功")
        else:
            print("❌ 高级算法创建失败")
        
        # 3. 显示可用算法
        print("\n📋 可用算法列表:")
        all_algorithms = manager.get_all_algorithms_info()
        for alg_id, info in all_algorithms.items():
            print(f"  - {alg_id}: {info['name']} ({info['type']})")
        
        # 4. 演示算法切换
        demonstrate_algorithm_switching(manager)
        
        # 5. 演示性能监控
        demonstrate_performance_monitoring(manager)
        
        # 6. 演示数据导出
        demonstrate_data_export(manager)
        
        # 7. 创建性能可视化
        create_performance_visualization(manager)
        
        print("\n" + "="*60)
        print("🎊 算法管理器演示完成！")
        print("="*60)
        
        # 显示最终统计
        final_report = manager.get_performance_report()
        print(f"\n📊 最终统计:")
        print(f"  - 总算法数: {final_report['total_algorithms']}")
        print(f"  - 活跃算法数: {final_report['active_algorithms']}")
        print(f"  - 总执行次数: {final_report['total_executions']}")
        
        print(f"\n💡 演示文件位置:")
        print(f"  - 性能数据: /tmp/algorithm_performance_demo.json")
        print(f"  - 性能图表: /tmp/algorithm_performance_chart.png")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
    finally:
        # 清理资源
        manager.cleanup()
        print("\n🧹 资源清理完成")


if __name__ == '__main__':
    main()