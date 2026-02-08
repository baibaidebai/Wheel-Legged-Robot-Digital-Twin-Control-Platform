#!/usr/bin/env python3
"""
数字孪生映射器Python包装器

提供数字孪生映射器的Python接口，包含C++绑定的安全包装和纯Python实现的备用功能。
当C++绑定不可用或出现问题时，自动回退到Python实现。
"""

import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import os
import sys

# 尝试导入C++绑定
try:
    # 添加构建路径
    build_path = os.path.join(os.path.dirname(__file__), '../../../../build/wheel_legged_control')
    if os.path.exists(build_path):
        sys.path.insert(0, build_path)
    
    import digital_twin_mapper_py as dtm_cpp
    CPP_BINDINGS_AVAILABLE = True
    logging.info("C++数字孪生映射器绑定可用")
except ImportError as e:
    CPP_BINDINGS_AVAILABLE = False
    logging.warning(f"C++绑定不可用，使用Python实现: {e}")


class ConstraintType(Enum):
    """约束类型枚举"""
    HOLONOMIC = "holonomic"
    NONHOLONOMIC = "nonholonomic"


@dataclass
class WheelConstraint:
    """轮子约束"""
    wheel_name: str = ""
    contact_point: np.ndarray = None
    normal_vector: np.ndarray = None
    friction_coefficient: float = 0.8
    
    def __post_init__(self):
        if self.contact_point is None:
            self.contact_point = np.zeros(3)
        if self.normal_vector is None:
            self.normal_vector = np.array([0.0, 0.0, 1.0])


@dataclass
class LegConstraint:
    """腿部约束"""
    leg_name: str = ""
    joints: List[str] = None
    jacobian: np.ndarray = None
    
    def __post_init__(self):
        if self.joints is None:
            self.joints = []
        if self.jacobian is None:
            self.jacobian = np.eye(3, 2)


@dataclass
class CouplingConstraint:
    """耦合约束"""
    joint_names: List[str] = None
    constraint_matrix: np.ndarray = None
    constraint_type: ConstraintType = ConstraintType.HOLONOMIC
    
    def __post_init__(self):
        if self.joint_names is None:
            self.joint_names = []
        if self.constraint_matrix is None:
            self.constraint_matrix = np.eye(2, 2)


@dataclass
class ConstraintModel:
    """约束模型"""
    wheel_constraints: List[WheelConstraint] = None
    leg_constraints: List[LegConstraint] = None
    coupling_constraints: List[CouplingConstraint] = None
    
    def __post_init__(self):
        if self.wheel_constraints is None:
            self.wheel_constraints = []
        if self.leg_constraints is None:
            self.leg_constraints = []
        if self.coupling_constraints is None:
            self.coupling_constraints = []


@dataclass
class TaskSpaceState:
    """任务空间状态"""
    base_position: np.ndarray = None
    base_orientation: np.ndarray = None  # 四元数 [x, y, z, w]
    wheel_positions: Dict[str, np.ndarray] = None
    leg_end_positions: Dict[str, np.ndarray] = None
    
    def __post_init__(self):
        if self.base_position is None:
            self.base_position = np.zeros(3)
        if self.base_orientation is None:
            self.base_orientation = np.array([0.0, 0.0, 0.0, 1.0])
        if self.wheel_positions is None:
            self.wheel_positions = {}
        if self.leg_end_positions is None:
            self.leg_end_positions = {}


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool = False
    error_message: str = ""
    consistency_error: float = 0.0


class DigitalTwinMapperPython:
    """数字孪生映射器纯Python实现"""
    
    def __init__(self):
        self.constraint_model: Optional[ConstraintModel] = None
        self.joint_index_map: Dict[str, int] = {}
        self.model_initialized = False
        self.logger = logging.getLogger(__name__)
    
    def build_kinematic_model(self, constraint_model: ConstraintModel) -> bool:
        """构建运动学模型"""
        try:
            self.constraint_model = constraint_model
            
            # 建立关节索引映射
            self.joint_index_map.clear()
            index = 0
            
            # 轮子关节
            for wheel_constraint in constraint_model.wheel_constraints:
                self.joint_index_map[wheel_constraint.wheel_name] = index
                index += 1
            
            # 腿部关节
            for leg_constraint in constraint_model.leg_constraints:
                for joint in leg_constraint.joints:
                    self.joint_index_map[joint] = index
                    index += 1
            
            self.model_initialized = True
            self.logger.info(f"运动学模型构建成功，总关节数: {len(self.joint_index_map)}")
            return True
            
        except Exception as e:
            self.logger.error(f"运动学模型构建失败: {e}")
            return False
    
    def joint_to_task_mapping(self, joint_angles: np.ndarray) -> TaskSpaceState:
        """关节空间到任务空间映射"""
        if not self.model_initialized:
            raise RuntimeError("运动学模型未初始化")
        
        if len(joint_angles) != len(self.joint_index_map):
            raise ValueError(f"关节角度向量大小不匹配。期望: {len(self.joint_index_map)}, 实际: {len(joint_angles)}")
        
        task_state = TaskSpaceState()
        
        # 基座位置和姿态（简化）
        task_state.base_position = np.zeros(3)
        task_state.base_orientation = np.array([0.0, 0.0, 0.0, 1.0])
        
        # 计算轮子位置
        for wheel_constraint in self.constraint_model.wheel_constraints:
            if wheel_constraint.wheel_name in self.joint_index_map:
                index = self.joint_index_map[wheel_constraint.wheel_name]
                angle = joint_angles[index]
                
                # 简化的轮子位置计算
                wheel_pos = np.array([
                    0.3 * np.cos(angle),
                    0.3 * np.sin(angle),
                    0.1
                ])
                task_state.wheel_positions[wheel_constraint.wheel_name] = wheel_pos
        
        # 计算腿端位置
        for leg_constraint in self.constraint_model.leg_constraints:
            leg_end_pos = np.zeros(3)
            
            if len(leg_constraint.joints) >= 2:
                joint1_name = leg_constraint.joints[0]
                joint2_name = leg_constraint.joints[1]
                
                if joint1_name in self.joint_index_map and joint2_name in self.joint_index_map:
                    index1 = self.joint_index_map[joint1_name]
                    index2 = self.joint_index_map[joint2_name]
                    
                    q1 = joint_angles[index1]
                    q2 = joint_angles[index2]
                    
                    # 二连杆正运动学
                    link1_length = 0.2
                    link2_length = 0.25
                    
                    leg_end_pos[0] = link1_length * np.cos(q1) + link2_length * np.cos(q1 + q2)
                    leg_end_pos[1] = link1_length * np.sin(q1) + link2_length * np.sin(q1 + q2)
                    leg_end_pos[2] = 0.0
            
            task_state.leg_end_positions[leg_constraint.leg_name] = leg_end_pos
        
        return task_state
    
    def task_to_joint_mapping(self, task_state: TaskSpaceState) -> np.ndarray:
        """任务空间到关节空间映射"""
        if not self.model_initialized:
            raise RuntimeError("运动学模型未初始化")
        
        joint_angles = np.zeros(len(self.joint_index_map))
        
        # 轮子关节逆运动学
        for wheel_name, wheel_pos in task_state.wheel_positions.items():
            if wheel_name in self.joint_index_map:
                index = self.joint_index_map[wheel_name]
                angle = np.arctan2(wheel_pos[1], wheel_pos[0])
                joint_angles[index] = angle
        
        # 腿部关节逆运动学
        for leg_name, leg_end_pos in task_state.leg_end_positions.items():
            # 查找对应的腿部约束
            for leg_constraint in self.constraint_model.leg_constraints:
                if leg_constraint.leg_name == leg_name and len(leg_constraint.joints) >= 2:
                    joint1_name = leg_constraint.joints[0]
                    joint2_name = leg_constraint.joints[1]
                    
                    if joint1_name in self.joint_index_map and joint2_name in self.joint_index_map:
                        index1 = self.joint_index_map[joint1_name]
                        index2 = self.joint_index_map[joint2_name]
                        
                        # 二连杆逆运动学
                        x = leg_end_pos[0]
                        y = leg_end_pos[1]
                        link1_length = 0.2
                        link2_length = 0.25
                        
                        r = np.sqrt(x*x + y*y)
                        
                        # 检查工作空间
                        if r <= link1_length + link2_length and r >= abs(link1_length - link2_length):
                            cos_q2 = (r*r - link1_length*link1_length - link2_length*link2_length) / (2 * link1_length * link2_length)
                            cos_q2 = np.clip(cos_q2, -1.0, 1.0)
                            
                            q2 = np.arccos(cos_q2)
                            q1 = np.arctan2(y, x) - np.arctan2(link2_length * np.sin(q2), link1_length + link2_length * np.cos(q2))
                            
                            joint_angles[index1] = q1
                            joint_angles[index2] = q2
                    break
        
        return joint_angles
    
    def validate_motion_consistency(self, joint_angles: np.ndarray) -> ValidationResult:
        """验证运动一致性"""
        result = ValidationResult()
        
        if not self.model_initialized:
            result.is_valid = False
            result.error_message = "运动学模型未初始化"
            return result
        
        try:
            # 检查关节限制
            for angle in joint_angles:
                if abs(angle) > np.pi:
                    result.is_valid = False
                    result.error_message = "关节角度超出限制"
                    result.consistency_error += abs(angle) - np.pi
                    return result
            
            # 检查正逆运动学一致性
            task_state = self.joint_to_task_mapping(joint_angles)
            recovered_angles = self.task_to_joint_mapping(task_state)
            
            if len(recovered_angles) == len(joint_angles):
                error = np.linalg.norm(joint_angles - recovered_angles)
                result.consistency_error = error
                
                if error > 0.1:
                    result.is_valid = False
                    result.error_message = "正逆运动学不一致"
                else:
                    result.is_valid = True
            else:
                result.is_valid = False
                result.error_message = "关节角度向量大小不匹配"
            
        except Exception as e:
            result.is_valid = False
            result.error_message = f"验证过程出错: {str(e)}"
        
        return result
    
    def handle_singular_configuration(self, jacobian: np.ndarray) -> np.ndarray:
        """处理奇异位形"""
        if jacobian.size == 0:
            raise ValueError("雅可比矩阵为空")
        
        # 简单的正则化方法
        regularized = jacobian.copy()
        reg_factor = 1e-6
        
        # 对角线正则化
        min_dim = min(jacobian.shape)
        for i in range(min_dim):
            regularized[i, i] += reg_factor
        
        return regularized


class DigitalTwinMapper:
    """数字孪生映射器统一接口"""
    
    def __init__(self):
        self.use_cpp = CPP_BINDINGS_AVAILABLE
        self.logger = logging.getLogger(__name__)
        
        if self.use_cpp:
            try:
                self.cpp_mapper = dtm_cpp.DigitalTwinMapper()
                self.logger.info("使用C++数字孪生映射器")
            except Exception as e:
                self.logger.warning(f"C++映射器初始化失败，回退到Python实现: {e}")
                self.use_cpp = False
                self.python_mapper = DigitalTwinMapperPython()
        else:
            self.python_mapper = DigitalTwinMapperPython()
            self.logger.info("使用Python数字孪生映射器")
    
    def build_kinematic_model(self, constraint_model: ConstraintModel) -> bool:
        """构建运动学模型"""
        if self.use_cpp:
            try:
                # 转换为C++格式（如果需要）
                cpp_model = self._convert_to_cpp_model(constraint_model)
                return self.cpp_mapper.build_kinematic_model(cpp_model)
            except Exception as e:
                self.logger.warning(f"C++模型构建失败，回退到Python: {e}")
                self.use_cpp = False
                self.python_mapper = DigitalTwinMapperPython()
                return self.python_mapper.build_kinematic_model(constraint_model)
        else:
            return self.python_mapper.build_kinematic_model(constraint_model)
    
    def joint_to_task_mapping(self, joint_angles: np.ndarray) -> TaskSpaceState:
        """关节空间到任务空间映射"""
        if self.use_cpp:
            try:
                cpp_result = self.cpp_mapper.joint_to_task_mapping(joint_angles)
                return self._convert_from_cpp_task_state(cpp_result)
            except Exception as e:
                self.logger.warning(f"C++正运动学失败，回退到Python: {e}")
                self.use_cpp = False
                return self.python_mapper.joint_to_task_mapping(joint_angles)
        else:
            return self.python_mapper.joint_to_task_mapping(joint_angles)
    
    def task_to_joint_mapping(self, task_state: TaskSpaceState) -> np.ndarray:
        """任务空间到关节空间映射"""
        if self.use_cpp:
            try:
                cpp_task_state = self._convert_to_cpp_task_state(task_state)
                return self.cpp_mapper.task_to_joint_mapping(cpp_task_state)
            except Exception as e:
                self.logger.warning(f"C++逆运动学失败，回退到Python: {e}")
                self.use_cpp = False
                return self.python_mapper.task_to_joint_mapping(task_state)
        else:
            return self.python_mapper.task_to_joint_mapping(task_state)
    
    def validate_motion_consistency(self, joint_angles: np.ndarray) -> ValidationResult:
        """验证运动一致性"""
        if self.use_cpp:
            try:
                cpp_result = self.cpp_mapper.validate_motion_consistency(joint_angles)
                return ValidationResult(
                    is_valid=cpp_result.is_valid,
                    error_message=cpp_result.error_message,
                    consistency_error=cpp_result.consistency_error
                )
            except Exception as e:
                self.logger.warning(f"C++验证失败，回退到Python: {e}")
                self.use_cpp = False
                return self.python_mapper.validate_motion_consistency(joint_angles)
        else:
            return self.python_mapper.validate_motion_consistency(joint_angles)
    
    def handle_singular_configuration(self, jacobian: np.ndarray) -> np.ndarray:
        """处理奇异位形"""
        # 由于C++版本有问题，直接使用Python实现
        return self.python_mapper.handle_singular_configuration(jacobian)
    
    def _convert_to_cpp_model(self, model: ConstraintModel):
        """转换为C++约束模型（如果需要）"""
        # 这里可以添加转换逻辑
        return model
    
    def _convert_to_cpp_task_state(self, task_state: TaskSpaceState):
        """转换为C++任务空间状态（如果需要）"""
        # 这里可以添加转换逻辑
        return task_state
    
    def _convert_from_cpp_task_state(self, cpp_task_state) -> TaskSpaceState:
        """从C++任务空间状态转换（如果需要）"""
        # 这里可以添加转换逻辑
        return cpp_task_state


def create_test_constraint_model() -> ConstraintModel:
    """创建测试约束模型"""
    model = ConstraintModel()
    
    # 创建轮子约束
    left_wheel = WheelConstraint(
        wheel_name="left_wheel",
        contact_point=np.array([0.0, 0.2, 0.0]),
        normal_vector=np.array([0.0, 0.0, 1.0]),
        friction_coefficient=0.8
    )
    
    right_wheel = WheelConstraint(
        wheel_name="right_wheel",
        contact_point=np.array([0.0, -0.2, 0.0]),
        normal_vector=np.array([0.0, 0.0, 1.0]),
        friction_coefficient=0.8
    )
    
    model.wheel_constraints = [left_wheel, right_wheel]
    
    # 创建腿部约束
    left_leg = LegConstraint(
        leg_name="left_leg",
        joints=["lf0_joint", "lf1_joint"],
        jacobian=np.eye(3, 2)
    )
    
    right_leg = LegConstraint(
        leg_name="right_leg",
        joints=["rf0_joint", "rf1_joint"],
        jacobian=np.eye(3, 2)
    )
    
    model.leg_constraints = [left_leg, right_leg]
    
    return model


def create_test_task_state() -> TaskSpaceState:
    """创建测试任务空间状态"""
    task_state = TaskSpaceState()
    
    task_state.base_position = np.array([0.0, 0.0, 0.2])
    task_state.base_orientation = np.array([0.0, 0.0, 0.0, 1.0])
    
    task_state.wheel_positions = {
        "left_wheel": np.array([0.0, 0.2, 0.0]),
        "right_wheel": np.array([0.0, -0.2, 0.0])
    }
    
    task_state.leg_end_positions = {
        "left_leg": np.array([0.3, 0.2, -0.1]),
        "right_leg": np.array([0.3, -0.2, -0.1])
    }
    
    return task_state


if __name__ == "__main__":
    # 测试数字孪生映射器
    print("🚀 测试数字孪生映射器Python包装器")
    
    # 创建映射器
    mapper = DigitalTwinMapper()
    
    # 创建测试模型
    test_model = create_test_constraint_model()
    
    # 构建运动学模型
    success = mapper.build_kinematic_model(test_model)
    print(f"✅ 运动学模型构建: {'成功' if success else '失败'}")
    
    if success:
        # 测试正运动学
        joint_angles = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
        task_state = mapper.joint_to_task_mapping(joint_angles)
        print(f"✅ 正运动学映射成功")
        print(f"   基座位置: {task_state.base_position}")
        print(f"   轮子位置数量: {len(task_state.wheel_positions)}")
        print(f"   腿端位置数量: {len(task_state.leg_end_positions)}")
        
        # 测试逆运动学
        test_state = create_test_task_state()
        recovered_angles = mapper.task_to_joint_mapping(test_state)
        print(f"✅ 逆运动学映射成功")
        print(f"   恢复的关节角度: {recovered_angles}")
        
        # 测试验证
        result = mapper.validate_motion_consistency(joint_angles)
        print(f"✅ 运动一致性验证: {'有效' if result.is_valid else '无效'}")
        print(f"   一致性误差: {result.consistency_error:.6f}")
        
        # 测试奇异位形处理
        jacobian = np.eye(3, 3)
        regularized = mapper.handle_singular_configuration(jacobian)
        print(f"✅ 奇异位形处理成功，输出形状: {regularized.shape}")
    
    print("\n🎉 数字孪生映射器测试完成！")