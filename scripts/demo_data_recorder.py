#!/usr/bin/env python3
"""
数据记录器演示脚本

演示如何使用数据记录器记录机器人实验数据，包括关节状态、IMU数据和控制指令。
"""

import os
import sys
import time
import numpy as np
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src/wheel_legged_control'))

def demo_basic_recording():
    """基础数据记录演示"""
    print("📹 基础数据记录演示")
    print("-" * 40)
    
    try:
        from wheel_legged_control.data import create_default_recorder
        
        # 创建数据记录器
        output_dir = "./data/demo_recordings"
        recorder = create_default_recorder(output_dir)
        
        print(f"✅ 数据记录器创建成功")
        print(f"📁 输出目录: {output_dir}")
        
        # 开始记录
        experiment_name = "basic_demo"
        metadata = {
            "experiment_type": "basic_recording_demo",
            "robot_model": "wheel_legged_robot",
            "operator": "demo_user",
            "notes": "基础功能演示"
        }
        
        success = recorder.start_recording(experiment_name, metadata)
        if not success:
            print("❌ 记录启动失败")
            return False
        
        print(f"🎬 开始记录实验: {experiment_name}")
        
        # 模拟机器人运动数据
        print("🤖 模拟机器人运动...")
        
        joint_names = ['left_hip', 'left_knee', 'left_wheel', 'right_hip', 'right_knee', 'right_wheel']
        
        for step in range(50):
            # 模拟时间步进
            t = step * 0.02  # 50Hz
            
            # 生成关节状态（正弦波运动）
            positions = [
                0.3 * np.sin(2 * np.pi * 0.5 * t),      # left_hip
                0.5 * np.sin(2 * np.pi * 0.5 * t + np.pi/4),  # left_knee
                2.0 * t,                                 # left_wheel (持续旋转)
                0.3 * np.sin(2 * np.pi * 0.5 * t + np.pi),     # right_hip
                0.5 * np.sin(2 * np.pi * 0.5 * t + np.pi + np.pi/4),  # right_knee
                2.0 * t                                  # right_wheel
            ]
            
            velocities = [
                0.3 * 2 * np.pi * 0.5 * np.cos(2 * np.pi * 0.5 * t),
                0.5 * 2 * np.pi * 0.5 * np.cos(2 * np.pi * 0.5 * t + np.pi/4),
                2.0,
                0.3 * 2 * np.pi * 0.5 * np.cos(2 * np.pi * 0.5 * t + np.pi),
                0.5 * 2 * np.pi * 0.5 * np.cos(2 * np.pi * 0.5 * t + np.pi + np.pi/4),
                2.0
            ]
            
            efforts = [pos * 10.0 for pos in positions]  # 简化的力矩计算
            
            # 记录关节状态
            recorder.record_joint_state(joint_names, positions, velocities, efforts)
            
            # 生成IMU数据
            roll = 0.1 * np.sin(2 * np.pi * 0.2 * t)
            pitch = 0.05 * np.sin(2 * np.pi * 0.3 * t)
            yaw = 0.5 * t
            
            # 简化的四元数（仅绕Z轴旋转）
            orientation = [0.0, 0.0, np.sin(yaw/2), np.cos(yaw/2)]
            angular_velocity = [0.1 * np.cos(2 * np.pi * 0.2 * t), 
                               0.05 * np.cos(2 * np.pi * 0.3 * t), 
                               0.5]
            linear_acceleration = [0.2 * np.sin(2 * np.pi * 0.1 * t), 
                                  0.1 * np.cos(2 * np.pi * 0.1 * t), 
                                  9.81]
            
            recorder.record_imu_data(orientation, angular_velocity, linear_acceleration)
            
            # 生成控制指令
            control_commands = [pos + 0.1 * np.random.randn() for pos in positions]  # 添加噪声
            recorder.record_control_command(joint_names, control_commands, 'position')
            
            # 记录系统状态
            system_state = {
                'step': step,
                'simulation_time': t,
                'battery_voltage': 24.0 - 0.01 * step,
                'cpu_temperature': 45.0 + 5.0 * np.sin(2 * np.pi * 0.05 * t),
                'memory_usage': 30.0 + 10.0 * np.random.rand(),
                'control_frequency': 50.0,
                'active_algorithm': 'LQR_Controller'
            }
            recorder.record_system_state(system_state)
            
            # 每10步显示进度
            if step % 10 == 0:
                status = recorder.get_recording_status()
                print(f"   步骤 {step:2d}: 缓冲区={status['buffer_size']}, "
                      f"总点数={status['stats']['total_points']}")
            
            time.sleep(0.02)  # 50Hz
        
        # 获取最终状态
        final_status = recorder.get_recording_status()
        print(f"\n📊 记录完成:")
        print(f"   记录时长: {final_status['recording_duration']:.2f}秒")
        print(f"   总数据点: {final_status['stats']['total_points']}")
        print(f"   关节状态: {final_status['stats']['joint_states']}")
        print(f"   IMU数据: {final_status['stats']['imu_data']}")
        print(f"   控制指令: {final_status['stats']['control_commands']}")
        print(f"   系统状态: {final_status['stats']['system_states']}")
        
        # 停止记录
        success = recorder.stop_recording()
        if success:
            print(f"✅ 数据记录成功保存")
            print(f"📁 文件前缀: {final_status['current_filename']}")
        else:
            print(f"❌ 数据记录保存失败")
        
        # 清理
        recorder.cleanup()
        
        return success
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False
    
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def demo_advanced_recording():
    """高级数据记录演示"""
    print("\n🎯 高级数据记录演示")
    print("-" * 40)
    
    try:
        from wheel_legged_control.data import DataRecorder, RecordingConfig
        
        # 创建自定义配置
        config = RecordingConfig(
            output_directory="./data/advanced_recordings",
            filename_prefix="advanced_experiment",
            auto_timestamp=True,
            save_json=True,
            save_csv=True,
            save_rosbag=False,
            record_joint_states=True,
            record_imu_data=True,
            record_control_commands=True,
            record_system_states=True,
            max_buffer_size=1000,
            flush_interval=0.5,  # 更频繁的刷新
            compression=True,
            include_metadata=True
        )
        
        recorder = DataRecorder(config)
        print(f"✅ 高级数据记录器创建成功")
        
        # 多阶段实验记录
        experiments = [
            {"name": "walking_forward", "duration": 2.0, "description": "前进行走"},
            {"name": "turning_left", "duration": 1.5, "description": "左转"},
            {"name": "jumping", "duration": 1.0, "description": "跳跃动作"}
        ]
        
        for exp in experiments:
            print(f"\n🎬 开始实验: {exp['description']}")
            
            # 开始记录
            metadata = {
                "experiment_phase": exp['name'],
                "expected_duration": exp['duration'],
                "description": exp['description'],
                "test_conditions": "室内平地",
                "robot_configuration": "标准配置"
            }
            
            success = recorder.start_recording(exp['name'], metadata)
            if not success:
                print(f"❌ 实验 {exp['name']} 记录启动失败")
                continue
            
            # 模拟实验数据
            steps = int(exp['duration'] / 0.02)  # 50Hz
            joint_names = ['joint1', 'joint2', 'joint3', 'joint4']
            
            for step in range(steps):
                t = step * 0.02
                
                # 根据实验类型生成不同的运动模式
                if exp['name'] == 'walking_forward':
                    # 行走模式
                    positions = [0.5 * np.sin(4 * np.pi * t + i * np.pi/2) for i in range(4)]
                elif exp['name'] == 'turning_left':
                    # 转向模式
                    positions = [0.3 * np.sin(6 * np.pi * t + i * np.pi/3) for i in range(4)]
                else:  # jumping
                    # 跳跃模式
                    positions = [0.8 * np.sin(8 * np.pi * t) * np.exp(-2*t) for _ in range(4)]
                
                velocities = [p * 2 for p in positions]
                efforts = [p * 15 for p in positions]
                
                recorder.record_joint_state(joint_names, positions, velocities, efforts)
                
                # IMU数据
                orientation = [0.0, 0.0, 0.0, 1.0]
                angular_velocity = [0.1 * np.random.randn() for _ in range(3)]
                linear_acceleration = [0.0, 0.0, 9.81 + 0.5 * np.random.randn()]
                
                recorder.record_imu_data(orientation, angular_velocity, linear_acceleration)
                
                # 控制指令
                commands = [p + 0.05 * np.random.randn() for p in positions]
                recorder.record_control_command(joint_names, commands, 'position')
                
                # 系统状态
                system_state = {
                    'experiment_phase': exp['name'],
                    'phase_progress': step / steps,
                    'step': step,
                    'time': t,
                    'battery_level': max(0, 100 - step * 0.1),
                    'motor_temperature': 40 + 10 * np.random.rand()
                }
                recorder.record_system_state(system_state)
                
                time.sleep(0.02)
            
            # 停止当前实验记录
            success = recorder.stop_recording()
            status = recorder.get_recording_status()
            
            print(f"   ✅ 实验完成: {status['stats']['total_points']} 数据点")
            
            # 短暂休息
            time.sleep(0.5)
        
        print(f"\n🎉 所有实验完成！")
        
        # 清理
        recorder.cleanup()
        
        return True
        
    except Exception as e:
        print(f"❌ 高级演示失败: {e}")
        return False

def main():
    """主函数"""
    print("🎬 数据记录器演示")
    print("=" * 60)
    print(f"📅 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 基础演示
        success1 = demo_basic_recording()
        
        if success1:
            # 高级演示
            success2 = demo_advanced_recording()
            
            if success1 and success2:
                print(f"\n🎉 所有演示完成！")
                print(f"✅ 基础数据记录功能正常")
                print(f"✅ 高级数据记录功能正常")
                print(f"📁 数据文件已保存到 ./data/ 目录")
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