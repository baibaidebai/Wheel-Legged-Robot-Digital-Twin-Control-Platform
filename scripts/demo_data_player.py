#!/usr/bin/env python3
"""
数据回放器演示脚本

演示DataPlayer的各种功能，包括数据加载、回放控制、回调机制等。
"""

import os
import sys
import time
import json
import tempfile
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'wheel_legged_control'))

from wheel_legged_control.data.data_player import (
    DataPlayer, PlaybackConfig, PlaybackState, create_default_player
)
from wheel_legged_control.data.data_recorder import create_default_recorder


def create_sample_data():
    """创建示例数据"""
    print("📊 创建示例数据...")
    
    # 使用数据记录器创建真实的数据文件
    recorder = create_default_recorder("./demo_data")
    
    # 开始记录
    success = recorder.start_recording("data_player_demo", {"demo": True})
    if not success:
        print("❌ 无法开始数据记录")
        return None
    
    print("   正在记录数据...")
    
    # 模拟机器人运动数据
    for i in range(20):
        # 记录关节状态
        joint_names = ['left_hip', 'left_knee', 'right_hip', 'right_knee']
        positions = [0.1 * i, 0.2 * i, -0.1 * i, -0.2 * i]
        velocities = [0.01 * i, 0.02 * i, -0.01 * i, -0.02 * i]
        efforts = [1.0 * i, 2.0 * i, -1.0 * i, -2.0 * i]
        recorder.record_joint_state(joint_names, positions, velocities, efforts)
        
        # 记录IMU数据
        orientation = [0.0, 0.0, 0.1 * i, 1.0]  # 轻微旋转
        angular_velocity = [0.05 * i, 0.0, 0.0]
        linear_acceleration = [0.0, 0.0, 9.81 + 0.1 * i]  # 轻微振动
        recorder.record_imu_data(orientation, angular_velocity, linear_acceleration)
        
        # 记录控制指令
        commands = [0.5 * i, 0.6 * i, -0.5 * i, -0.6 * i]
        recorder.record_control_command(joint_names, commands, 'position')
        
        # 记录系统状态
        system_state = {
            'step': i,
            'battery_level': 100 - i,
            'temperature': 25.0 + i * 0.2,
            'cpu_usage': 10 + i * 2
        }
        recorder.record_system_state(system_state)
        
        time.sleep(0.05)  # 50ms间隔
    
    # 停止记录
    recorder.stop_recording()
    
    # 获取生成的文件
    status = recorder.get_recording_status()
    data_file = None
    
    # 查找JSON文件
    demo_dir = Path("./demo_data")
    if demo_dir.exists():
        json_files = list(demo_dir.glob("*.json"))
        if json_files:
            data_file = str(json_files[0])
    
    recorder.cleanup()
    
    if data_file and os.path.exists(data_file):
        print(f"✅ 示例数据已创建: {data_file}")
        return data_file
    else:
        print("❌ 示例数据创建失败")
        return None


def demo_basic_playback(data_file):
    """演示基础回放功能"""
    print("\n🎬 演示基础回放功能")
    print("-" * 40)
    
    # 创建回放器
    config = PlaybackConfig(
        playback_speed=2.0,  # 2倍速回放
        loop_playback=False,
        auto_start=False
    )
    player = DataPlayer(config)
    
    try:
        # 加载数据
        success = player.load_data_from_json(data_file)
        if not success:
            print("❌ 数据加载失败")
            return
        
        # 获取数据摘要
        summary = player.get_data_summary()
        print(f"📊 数据摘要:")
        print(f"   总数据点: {summary['total_points']}")
        print(f"   数据类型: {summary['data_types']}")
        print(f"   时间范围: {summary['time_range']['duration']:.2f}秒")
        
        # 注册回调函数
        joint_data_count = 0
        imu_data_count = 0
        
        def joint_callback(data_point):
            nonlocal joint_data_count
            joint_data_count += 1
            if joint_data_count <= 3:  # 只显示前3个
                positions = data_point.data['positions']
                print(f"   关节位置: {[f'{p:.2f}' for p in positions]}")
        
        def imu_callback(data_point):
            nonlocal imu_data_count
            imu_data_count += 1
            if imu_data_count <= 3:  # 只显示前3个
                acc = data_point.data['linear_acceleration']
                print(f"   IMU加速度: {[f'{a:.2f}' for a in acc]}")
        
        def status_callback(status):
            if status.current_index % 20 == 0:  # 每20个数据点显示一次
                progress = (status.current_index / status.total_points) * 100
                print(f"   回放进度: {progress:.1f}% ({status.current_time:.2f}s)")
        
        player.register_data_callback('joint_state', joint_callback)
        player.register_data_callback('imu_data', imu_callback)
        player.register_status_callback(status_callback)
        
        # 开始回放
        print("\n▶️  开始回放...")
        success = player.start_playback()
        if not success:
            print("❌ 回放启动失败")
            return
        
        # 等待回放完成
        while player.get_status().state in [PlaybackState.PLAYING, PlaybackState.PAUSED]:
            time.sleep(0.1)
        
        # 显示最终统计
        final_status = player.get_status()
        stats = player.get_stats()
        print(f"\n📈 回放完成:")
        print(f"   最终状态: {final_status.state.value}")
        print(f"   播放数据点: {stats['total_played_points']}")
        print(f"   接收关节数据: {joint_data_count}")
        print(f"   接收IMU数据: {imu_data_count}")
        
    finally:
        player.cleanup()


def demo_playback_control(data_file):
    """演示回放控制功能"""
    print("\n🎮 演示回放控制功能")
    print("-" * 40)
    
    # 创建回放器
    config = PlaybackConfig(
        playback_speed=5.0,  # 5倍速以加快演示
        loop_playback=False,
        auto_start=False
    )
    player = DataPlayer(config)
    
    try:
        # 加载数据
        player.load_data_from_json(data_file)
        
        # 注册状态回调
        def status_callback(status):
            if status.current_index % 10 == 0:
                print(f"   状态: {status.state.value}, 进度: {status.current_index}/{status.total_points}")
        
        player.register_status_callback(status_callback)
        
        # 开始回放
        print("▶️  开始回放...")
        player.start_playback()
        time.sleep(0.3)
        
        # 暂停回放
        print("⏸️  暂停回放...")
        player.pause_playback()
        time.sleep(0.5)
        
        # 恢复回放
        print("▶️  恢复回放...")
        player.resume_playback()
        time.sleep(0.3)
        
        # 跳转到中间位置
        print("⏭️  跳转到50%位置...")
        total_points = player.get_status().total_points
        player.seek_to_index(total_points // 2)
        time.sleep(0.2)
        
        # 改变回放速度
        print("⚡ 设置为10倍速...")
        player.set_playback_speed(10.0)
        time.sleep(0.3)
        
        # 停止回放
        print("⏹️  停止回放...")
        player.stop_playback()
        
        print("✅ 回放控制演示完成")
        
    finally:
        player.cleanup()


def demo_data_filtering(data_file):
    """演示数据过滤功能"""
    print("\n🔍 演示数据过滤功能")
    print("-" * 40)
    
    # 创建带过滤器的回放器
    config = PlaybackConfig(
        playback_speed=10.0,
        loop_playback=False,
        data_types_filter=['joint_state'],  # 只回放关节状态数据
        auto_start=False
    )
    player = DataPlayer(config)
    
    try:
        # 加载数据
        player.load_data_from_json(data_file)
        
        # 获取过滤后的数据摘要
        summary = player.get_data_summary()
        print(f"📊 过滤后数据摘要:")
        print(f"   总数据点: {summary['total_points']}")
        print(f"   数据类型: {summary['data_types']}")
        
        # 注册回调函数
        received_types = set()
        
        def data_callback(data_point):
            received_types.add(data_point.data_type)
        
        player.register_data_callback('joint_state', data_callback)
        player.register_data_callback('imu_data', data_callback)
        player.register_data_callback('control_command', data_callback)
        player.register_data_callback('system_state', data_callback)
        
        # 开始回放
        print("▶️  开始过滤回放...")
        player.start_playback()
        
        # 等待回放完成
        while player.get_status().state == PlaybackState.PLAYING:
            time.sleep(0.1)
        
        print(f"✅ 过滤回放完成，接收到的数据类型: {received_types}")
        
    finally:
        player.cleanup()


def demo_loop_playback(data_file):
    """演示循环回放功能"""
    print("\n🔄 演示循环回放功能")
    print("-" * 40)
    
    # 创建循环回放器
    config = PlaybackConfig(
        playback_speed=20.0,  # 非常快的回放速度
        loop_playback=True,
        auto_start=False
    )
    player = DataPlayer(config)
    
    try:
        # 加载数据
        player.load_data_from_json(data_file)
        
        # 注册状态回调
        def status_callback(status):
            if status.loop_count > 0 and status.current_index == 0:
                print(f"   开始第{status.loop_count + 1}次循环")
        
        player.register_status_callback(status_callback)
        
        # 开始循环回放
        print("🔄 开始循环回放...")
        player.start_playback()
        
        # 让它循环几次
        time.sleep(1.0)
        
        # 停止回放
        player.stop_playback()
        
        final_status = player.get_status()
        print(f"✅ 循环回放完成，总循环次数: {final_status.loop_count}")
        
    finally:
        player.cleanup()


def cleanup_demo_data():
    """清理演示数据"""
    print("\n🧹 清理演示数据...")
    
    demo_dir = Path("./demo_data")
    if demo_dir.exists():
        import shutil
        shutil.rmtree(demo_dir)
        print("✅ 演示数据已清理")


def main():
    """主函数"""
    print("🎬 数据回放器功能演示")
    print("=" * 50)
    
    try:
        # 创建示例数据
        data_file = create_sample_data()
        if not data_file:
            print("❌ 无法创建示例数据，演示终止")
            return
        
        # 演示各种功能
        demo_basic_playback(data_file)
        demo_playback_control(data_file)
        demo_data_filtering(data_file)
        demo_loop_playback(data_file)
        
        print("\n🎉 数据回放器演示完成！")
        
        # 询问是否保留数据文件
        try:
            keep_data = input("\n是否保留演示数据文件？(y/N): ").lower().strip()
            if keep_data != 'y':
                cleanup_demo_data()
            else:
                print(f"📁 演示数据保存在: {os.path.dirname(data_file)}")
        except KeyboardInterrupt:
            print("\n")
            cleanup_demo_data()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  演示被用户中断")
        cleanup_demo_data()
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
        cleanup_demo_data()


if __name__ == "__main__":
    main()