#!/usr/bin/env python3
"""
RM轮腿机器人综合控制器
集成PID控制器和LQR控制器，支持MuJoCo仿真环境下的移动和跳跃控制
"""

import numpy as np
import time
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
import logging
from abc import ABC, abstractmethod

# ROS2相关导入（如果可用）
try:
    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import JointState
    from std_msgs.msg import Float64MultiArray
    ROS_AVAILABLE = True
except ImportError:
    ROS_AVAILABLE = False
    Node = object

# 控制算法导入
try:
    from ..algorithms.lqr_controller import LQRController, LQRConfig, LinearSystemModel
    from ..algorithms.lqr_controller import create_wheel_legged_robot_model
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    try:
        from wheel_legged_control.algorithms.lqr_controller import LQRController, LQRConfig, LinearSystemModel
        from wheel_legged_control.algorithms.lqr_controller import create_wheel_legged_robot_model
    except ImportError:
        # 创建简化版本用于测试
        class LQRConfig:
            def __init__(self, **kwargs):
                self.state_dim = kwargs.get('state_dim', 12)
                self.control_dim = kwargs.get('control_dim', 6)
                self.Q_weights = kwargs.get('Q_weights', [10.0] * 6 + [1.0] * 6)
                self.R_weights = kwargs.get('R_weights', [0.1] * 6)
                self.dt = kwargs.get('dt', 0.01)
        
        class LinearSystemModel:
            def predict(self, state, control):
                # 简化的预测模型
                return state + control * 0.01
        
        class LQRController:
            def __init__(self, config, system_model=None):
                self.lqr_config = config
                self.system_model = system_model or LinearSystemModel()
                self.K_gain = np.random.rand(config.control_dim, config.state_dim) * 0.1
                self.reference_state = np.zeros(config.state_dim)
            
            def set_reference(self, reference_state):
                self.reference_state = reference_state
            
            def compute_control(self, current_state):
                error = self.reference_state - current_state
                return np.dot(self.K_gain, error)
        
        def create_wheel_legged_robot_model(config):
            return LinearSystemModel()

logger = logging.getLogger(__name__)


@dataclass
class PIDGains:
    """PID控制器增益参数"""
    kp: float = 10.0    # 比例增益
    ki: float = 0.1     # 积分增益
    kd: float = 0.5     # 微分增益
    max_integral: float = 1.0    # 积分限幅
    max_output: float = 30.0     # 输出限幅 (N·m)


@dataclass
class JointStateData:
    """关节状态数据"""
    position: float = 0.0
    velocity: float = 0.0
    effort: float = 0.0
    timestamp: float = 0.0


class BaseRMController(ABC):
    """RM机器人控制器基类"""
    
    def __init__(self, joint_names: List[str]):
        self.joint_names = joint_names
        self.num_joints = len(joint_names)
        self.joint_indices = {name: i for i, name in enumerate(joint_names)}
        
        # 关节状态存储
        self.joint_states: Dict[str, JointStateData] = {}
        for name in joint_names:
            self.joint_states[name] = JointStateData()
        
        # 控制器启用状态
        self.enabled = True
        self.last_update_time = time.time()
        
    @abstractmethod
    def compute_control(self, target_positions: Dict[str, float], 
                       dt: float = None) -> Dict[str, float]:
        """计算控制输出"""
        pass
    
    def update_joint_state(self, joint_name: str, position: float, 
                          velocity: float = 0.0, effort: float = 0.0):
        """更新关节状态"""
        if joint_name in self.joint_states:
            self.joint_states[joint_name].position = position
            self.joint_states[joint_name].velocity = velocity
            self.joint_states[joint_name].effort = effort
            self.joint_states[joint_name].timestamp = time.time()
    
    def get_joint_positions(self) -> Dict[str, float]:
        """获取当前关节位置"""
        return {name: state.position for name, state in self.joint_states.items()}
    
    def get_joint_velocities(self) -> Dict[str, float]:
        """获取当前关节速度"""
        return {name: state.velocity for name, state in self.joint_states.items()}
    
    def reset(self):
        """重置控制器状态"""
        for state in self.joint_states.values():
            state.position = 0.0
            state.velocity = 0.0
            state.effort = 0.0
        self.last_update_time = time.time()


class PIDRMController(BaseRMController):
    """RM机器人PID控制器"""
    
    def __init__(self, joint_names: List[str], gains_dict: Dict[str, PIDGains] = None):
        super().__init__(joint_names)
        
        # 初始化PID控制器
        self.pid_controllers: Dict[str, 'PIDController'] = {}
        self.gains_dict = gains_dict or {}
        
        # 为每个关节创建PID控制器
        default_gains = PIDGains()
        for joint_name in joint_names:
            gains = self.gains_dict.get(joint_name, default_gains)
            self.pid_controllers[joint_name] = PIDController(gains)
    
    def set_pid_gains(self, joint_name: str, gains: PIDGains):
        """设置特定关节的PID增益"""
        if joint_name in self.pid_controllers:
            self.pid_controllers[joint_name].gains = gains
            self.gains_dict[joint_name] = gains
    
    def compute_control(self, target_positions: Dict[str, float], 
                       dt: float = None) -> Dict[str, float]:
        """计算PID控制输出"""
        if not self.enabled:
            return {name: 0.0 for name in self.joint_names}
        
        if dt is None:
            current_time = time.time()
            dt = current_time - self.last_update_time
            self.last_update_time = current_time
        
        control_outputs = {}
        
        for joint_name in self.joint_names:
            if joint_name in target_positions:
                current_pos = self.joint_states[joint_name].position
                target_pos = target_positions[joint_name]
                
                control_output = self.pid_controllers[joint_name].update(
                    target_pos, current_pos, dt
                )
                control_outputs[joint_name] = control_output
            else:
                control_outputs[joint_name] = 0.0
        
        return control_outputs


class LQRRMController(BaseRMController):
    """RM机器人LQR控制器"""
    
    def __init__(self, joint_names: List[str], lqr_config: LQRConfig = None):
        super().__init__(joint_names)
        
        # 创建LQR控制器
        if lqr_config is None:
            # 默认配置适用于6自由度关节控制
            lqr_config = LQRConfig(
                state_dim=12,  # 位置(6) + 速度(6)
                control_dim=6,  # 6个关节力矩
                Q_weights=[10.0] * 6 + [1.0] * 6,  # 位置权重高，速度权重低
                R_weights=[0.1] * 6,  # 控制输入权重
                dt=0.01
            )
        
        # 创建系统模型
        system_model = create_wheel_legged_robot_model(lqr_config)
        self.lqr_controller = LQRController(lqr_config, system_model)
        
        # 关节到状态的映射
        self.joint_to_state_map = {
            'lf0_Joint': 0, 'lf1_Joint': 1, 'l_wheel_Joint': 2,
            'rf0_Joint': 3, 'rf1_Joint': 4, 'r_wheel_Joint': 5
        }
    
    def set_reference_trajectory(self, target_positions: Dict[str, float]):
        """设置参考轨迹"""
        # 将关节位置目标转换为状态空间参考
        reference_state = np.zeros(self.lqr_controller.lqr_config.state_dim)
        
        # 设置位置参考
        for joint_name, target_pos in target_positions.items():
            if joint_name in self.joint_to_state_map:
                state_idx = self.joint_to_state_map[joint_name]
                reference_state[state_idx] = target_pos
        
        self.lqr_controller.set_reference(reference_state)
    
    def compute_control(self, target_positions: Dict[str, float], 
                       dt: float = None) -> Dict[str, float]:
        """计算LQR控制输出"""
        if not self.enabled:
            return {name: 0.0 for name in self.joint_names}
        
        # 设置参考轨迹
        self.set_reference_trajectory(target_positions)
        
        # 构建当前状态向量
        current_state = self._build_state_vector()
        
        # 计算LQR控制输入
        control_vector = self.lqr_controller.compute_control(current_state)
        
        # 将控制向量转换为关节力矩字典
        control_outputs = {}
        for joint_name, state_idx in self.joint_to_state_map.items():
            if state_idx < len(control_vector):
                control_outputs[joint_name] = control_vector[state_idx]
            else:
                control_outputs[joint_name] = 0.0
        
        # 补充其他关节
        for joint_name in self.joint_names:
            if joint_name not in control_outputs:
                control_outputs[joint_name] = 0.0
        
        return control_outputs
    
    def _build_state_vector(self) -> np.ndarray:
        """构建状态向量"""
        state = np.zeros(self.lqr_controller.lqr_config.state_dim)
        
        # 填充位置信息（前6维）
        for joint_name, state_idx in self.joint_to_state_map.items():
            if state_idx < 6:  # 位置维度
                state[state_idx] = self.joint_states[joint_name].position
        
        # 填充速度信息（后6维）
        for joint_name, state_idx in self.joint_to_state_map.items():
            if state_idx < 6:  # 对应的速度维度是 state_idx + 6
                state[state_idx + 6] = self.joint_states[joint_name].velocity
        
        return state


class HybridRMController(BaseRMController):
    """混合控制器：结合PID和LQR的优势"""
    
    def __init__(self, joint_names: List[str], 
                 pid_gains_dict: Dict[str, PIDGains] = None,
                 lqr_config: LQRConfig = None):
        super().__init__(joint_names)
        
        # 创建两个子控制器
        self.pid_controller = PIDRMController(joint_names, pid_gains_dict)
        self.lqr_controller = LQRRMController(joint_names, lqr_config)
        
        # 控制模式：'pid', 'lqr', 'hybrid'
        self.control_mode = 'hybrid'
        
        # 混合权重 (0=纯PID, 1=纯LQR)
        self.hybrid_weights = {name: 0.5 for name in joint_names}
    
    def set_control_mode(self, mode: str):
        """设置控制模式"""
        if mode in ['pid', 'lqr', 'hybrid']:
            self.control_mode = mode
        else:
            raise ValueError("控制模式必须是 'pid', 'lqr', 或 'hybrid'")
    
    def set_hybrid_weights(self, weights: Dict[str, float]):
        """设置混合控制权重"""
        for joint_name, weight in weights.items():
            if 0 <= weight <= 1:
                self.hybrid_weights[joint_name] = weight
            else:
                raise ValueError(f"权重必须在0-1之间，收到: {weight}")
    
    def compute_control(self, target_positions: Dict[str, float], 
                       dt: float = None) -> Dict[str, float]:
        """计算混合控制输出"""
        if not self.enabled:
            return {name: 0.0 for name in self.joint_names}
        
        # 更新子控制器的状态
        self._sync_subcontrollers()
        
        if self.control_mode == 'pid':
            return self.pid_controller.compute_control(target_positions, dt)
        elif self.control_mode == 'lqr':
            return self.lqr_controller.compute_control(target_positions, dt)
        else:  # hybrid
            return self._compute_hybrid_control(target_positions, dt)
    
    def _compute_hybrid_control(self, target_positions: Dict[str, float], 
                               dt: float) -> Dict[str, float]:
        """计算混合控制输出"""
        # 获取PID和LQR控制输出
        pid_outputs = self.pid_controller.compute_control(target_positions, dt)
        lqr_outputs = self.lqr_controller.compute_control(target_positions, dt)
        
        # 按权重混合
        hybrid_outputs = {}
        for joint_name in self.joint_names:
            pid_weight = 1.0 - self.hybrid_weights[joint_name]
            lqr_weight = self.hybrid_weights[joint_name]
            
            hybrid_outputs[joint_name] = (
                pid_weight * pid_outputs[joint_name] + 
                lqr_weight * lqr_outputs[joint_name]
            )
        
        return hybrid_outputs
    
    def _sync_subcontrollers(self):
        """同步子控制器的状态"""
        for joint_name in self.joint_names:
            state = self.joint_states[joint_name]
            self.pid_controller.update_joint_state(
                joint_name, state.position, state.velocity, state.effort
            )
            self.lqr_controller.update_joint_state(
                joint_name, state.position, state.velocity, state.effort
            )


class PIDController:
    """独立的PID控制器实现"""
    
    def __init__(self, gains: PIDGains):
        self.gains = gains
        self.reset()
    
    def reset(self):
        """重置PID状态"""
        self.prev_error = 0.0
        self.integral = 0.0
        self.prev_time = None
    
    def update(self, setpoint: float, current: float, dt: float) -> float:
        """
        更新PID控制器
        
        Args:
            setpoint: 目标值
            current: 当前值
            dt: 时间间隔
            
        Returns:
            控制输出
        """
        error = setpoint - current
        
        # 比例项
        proportional = self.gains.kp * error
        
        # 积分项
        self.integral += error * dt
        # 积分限幅
        self.integral = np.clip(self.integral, -self.gains.max_integral, self.gains.max_integral)
        integral = self.gains.ki * self.integral
        
        # 微分项
        if dt > 0:
            derivative = self.gains.kd * (error - self.prev_error) / dt
        else:
            derivative = 0.0
        
        # 总输出
        output = proportional + integral + derivative
        
        # 输出限幅
        output = np.clip(output, -self.gains.max_output, self.gains.max_output)
        
        # 更新状态
        self.prev_error = error
        
        return output


class RMRobotControllerNode(Node if ROS_AVAILABLE else object):
    """RM机器人控制器ROS2节点"""
    
    def __init__(self):
        if ROS_AVAILABLE:
            super().__init__('rm_robot_controller')
        else:
            # 非ROS环境下的模拟实现
            self.logger = logger
        
        # RM机器人关节配置
        self.joint_names = [
            'lf0_Joint', 'lf1_Joint', 'l_wheel_Joint',
            'rf0_Joint', 'rf1_Joint', 'r_wheel_Joint'
        ]
        
        # 初始化控制器
        self._setup_controllers()
        
        if ROS_AVAILABLE:
            # 设置ROS通信
            self._setup_ros_interface()
        
        # 控制循环
        self.control_frequency = 100.0  # 100Hz
        self.last_control_time = time.time()
        
        self.logger.info('RM机器人控制器节点已启动')
        self.logger.info(f'控制关节: {self.joint_names}')
        self.logger.info(f'控制模式: {self.controller.control_mode}')
    
    def _setup_controllers(self):
        """设置控制器"""
        # PID增益配置
        pid_gains_dict = {
            'lf0_Joint': PIDGains(kp=15.0, ki=0.2, kd=0.8),
            'lf1_Joint': PIDGains(kp=12.0, ki=0.15, kd=0.6),
            'l_wheel_Joint': PIDGains(kp=8.0, ki=0.05, kd=0.3),
            'rf0_Joint': PIDGains(kp=15.0, ki=0.2, kd=0.8),
            'rf1_Joint': PIDGains(kp=12.0, ki=0.15, kd=0.6),
            'r_wheel_Joint': PIDGains(kp=8.0, ki=0.05, kd=0.3)
        }
        
        # 创建混合控制器
        self.controller = HybridRMController(self.joint_names, pid_gains_dict)
        
        # 设置初始状态
        initial_positions = {name: 0.0 for name in self.joint_names}
        for joint_name, position in initial_positions.items():
            self.controller.update_joint_state(joint_name, position)
    
    def _setup_ros_interface(self):
        """设置ROS接口"""
        if not ROS_AVAILABLE:
            return
        
        # 订阅者
        self.joint_state_sub = self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_state_callback,
            10
        )
        
        # 发布者
        self.joint_command_pub = self.create_publisher(
            Float64MultiArray,
            '/joint_commands',
            10
        )
        
        # 控制定时器
        self.control_timer = self.create_timer(
            1.0 / self.control_frequency,
            self.control_loop
        )
    
    def joint_state_callback(self, msg: JointState):
        """关节状态回调"""
        for i, name in enumerate(msg.name):
            if name in self.joint_names and i < len(msg.position):
                position = msg.position[i] if i < len(msg.position) else 0.0
                velocity = msg.velocity[i] if i < len(msg.velocity) else 0.0
                effort = msg.effort[i] if i < len(msg.effort) else 0.0
                
                self.controller.update_joint_state(name, position, velocity, effort)
    
    def control_loop(self):
        """控制循环"""
        if not hasattr(self, 'target_positions'):
            return
        
        current_time = time.time()
        dt = current_time - self.last_control_time
        self.last_control_time = current_time
        
        # 计算控制输出
        control_outputs = self.controller.compute_control(self.target_positions, dt)
        
        # 发布控制命令
        self.publish_control_commands(control_outputs)
    
    def publish_control_commands(self, control_outputs: Dict[str, float]):
        """发布控制命令"""
        if ROS_AVAILABLE:
            msg = Float64MultiArray()
            # 按关节顺序排列
            msg.data = [control_outputs[name] for name in self.joint_names]
            self.joint_command_pub.publish(msg)
        else:
            # 非ROS环境下打印控制输出
            self.logger.debug(f"控制输出: {control_outputs}")
    
    def set_target_positions(self, positions: Dict[str, float]):
        """设置目标位置"""
        self.target_positions = positions
        self.logger.info(f"设置目标位置: {positions}")
    
    def set_control_mode(self, mode: str):
        """设置控制模式"""
        self.controller.set_control_mode(mode)
        self.logger.info(f"控制模式设置为: {mode}")


# Mujoco仿真控制器接口
class MujocoRMController:
    """MuJoCo仿真环境下的RM机器人控制器"""
    
    def __init__(self, model, data):
        """
        初始化MuJoCo控制器
        
        Args:
            model: MuJoCo模型对象
            data: MuJoCo数据对象
        """
        self.model = model
        self.data = data
        
        # RM机器人关节配置
        self.joint_names = [
            'lf0_Joint', 'lf1_Joint', 'l_wheel_Joint',
            'rf0_Joint', 'rf1_Joint', 'r_wheel_Joint'
        ]
        
        # 获取关节ID
        self.joint_ids = {}
        for joint_name in self.joint_names:
            try:
                joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
                self.joint_ids[joint_name] = joint_id
            except:
                self.logger.warning(f"未找到关节: {joint_name}")
        
        # 初始化控制器
        self.controller = HybridRMController(self.joint_names)
        
        # 控制历史
        self.control_history = []
        self.state_history = []
        
        self.logger = logging.getLogger(__name__)
    
    def update_joint_states(self):
        """从MuJoCo更新关节状态"""
        for joint_name, joint_id in self.joint_ids.items():
            if joint_id >= 0:
                position = self.data.qpos[joint_id]
                velocity = self.data.qvel[joint_id]
                self.controller.update_joint_state(joint_name, position, velocity)
    
    def apply_control(self, target_positions: Dict[str, float], dt: float = 0.01):
        """
        应用控制力矩到MuJoCo模型
        
        Args:
            target_positions: 目标关节位置
            dt: 控制时间步长
        """
        # 更新关节状态
        self.update_joint_states()
        
        # 计算控制输出
        control_outputs = self.controller.compute_control(target_positions, dt)
        
        # 应用力矩到关节
        for joint_name, torque in control_outputs.items():
            if joint_name in self.joint_ids:
                joint_id = self.joint_ids[joint_name]
                if joint_id >= 0:
                    self.data.ctrl[joint_id] = torque
        
        # 记录历史
        self.control_history.append(control_outputs.copy())
        current_states = self.controller.get_joint_positions()
        self.state_history.append(current_states.copy())
        
        return control_outputs
    
    def set_control_mode(self, mode: str):
        """设置控制模式"""
        self.controller.set_control_mode(mode)
    
    def get_joint_positions(self) -> Dict[str, float]:
        """获取当前关节位置"""
        return self.controller.get_joint_positions()


# 尝试导入MuJoCo
try:
    import mujoco
    MUJOCO_AVAILABLE = True
except ImportError:
    MUJOCO_AVAILABLE = False
    logger.warning("MuJoCo未安装，部分功能将不可用")


def main():
    """主函数 - 用于测试"""
    print("🤖 RM轮腿机器人控制器测试")
    print("=" * 50)
    
    # 测试关节名称
    joint_names = [
        'lf0_Joint', 'lf1_Joint', 'l_wheel_Joint',
        'rf0_Joint', 'rf1_Joint', 'r_wheel_Joint'
    ]
    
    print(f"🔧 控制关节数量: {len(joint_names)}")
    print(f"📋 关节列表: {joint_names}")
    
    # 测试PID控制器
    print("\n🧪 测试PID控制器...")
    pid_gains = {
        'lf0_Joint': PIDGains(kp=10.0, ki=0.1, kd=0.5),
        'lf1_Joint': PIDGains(kp=8.0, ki=0.05, kd=0.3)
    }
    
    pid_controller = PIDRMController(joint_names[:2], pid_gains)
    
    # 设置目标位置
    target_positions = {'lf0_Joint': 0.5, 'lf1_Joint': -0.3}
    
    # 模拟关节状态更新
    pid_controller.update_joint_state('lf0_Joint', 0.1, 0.0)
    pid_controller.update_joint_state('lf1_Joint', -0.1, 0.0)
    
    # 计算控制输出
    control_output = pid_controller.compute_control(target_positions, 0.01)
    print(f"✅ PID控制输出: {control_output}")
    
    # 测试LQR控制器
    print("\n🧪 测试LQR控制器...")
    lqr_config = LQRConfig(
        state_dim=12,
        control_dim=6,
        Q_weights=[10.0] * 6 + [1.0] * 6,
        R_weights=[0.1] * 6,
        dt=0.01
    )
    
    lqr_controller = LQRRMController(joint_names, lqr_config)
    
    # 更新状态
    for joint_name in joint_names:
        lqr_controller.update_joint_state(joint_name, 0.0, 0.0)
    
    # 计算LQR控制输出
    lqr_output = lqr_controller.compute_control(target_positions, 0.01)
    print(f"✅ LQR控制输出: {lqr_output}")
    
    # 测试混合控制器
    print("\n🧪 测试混合控制器...")
    hybrid_controller = HybridRMController(joint_names, pid_gains, lqr_config)
    
    # 设置混合权重
    hybrid_weights = {'lf0_Joint': 0.7, 'lf1_Joint': 0.3}
    hybrid_controller.set_hybrid_weights(hybrid_weights)
    
    # 计算混合控制输出
    hybrid_output = hybrid_controller.compute_control(target_positions, 0.01)
    print(f"✅ 混合控制输出: {hybrid_output}")
    
    print("\n🎉 控制器测试完成!")


if __name__ == "__main__":
    main()