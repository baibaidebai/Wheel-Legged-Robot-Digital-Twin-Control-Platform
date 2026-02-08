/**
 * @file digital_twin_mapper_bindings.cpp
 * @brief 数字孪生映射器Python绑定
 * @author 轮腿机器人项目团队
 * @date 2024
 */

#include <pybind11/pybind11.h>
#include <pybind11/eigen.h>
#include <pybind11/stl.h>
#include <pybind11/stl_bind.h>
#include "wheel_legged_control/digital_twin_mapper.hpp"

namespace py = pybind11;
using namespace wheel_legged_control;

PYBIND11_MODULE(digital_twin_mapper_py, m) {
    m.doc() = "轮腿机器人数字孪生映射器Python绑定";
    
    // 约束类型枚举
    py::enum_<ConstraintType>(m, "ConstraintType")
        .value("HOLONOMIC", ConstraintType::HOLONOMIC)
        .value("NONHOLONOMIC", ConstraintType::NONHOLONOMIC);
    
    // 轮子约束结构
    py::class_<WheelConstraint>(m, "WheelConstraint")
        .def(py::init<>())
        .def_readwrite("wheel_name", &WheelConstraint::wheel_name)
        .def_readwrite("contact_point", &WheelConstraint::contact_point)
        .def_readwrite("normal_vector", &WheelConstraint::normal_vector)
        .def_readwrite("friction_coefficient", &WheelConstraint::friction_coefficient);
    
    // 腿部约束结构
    py::class_<LegConstraint>(m, "LegConstraint")
        .def(py::init<>())
        .def_readwrite("leg_name", &LegConstraint::leg_name)
        .def_readwrite("joints", &LegConstraint::joints)
        .def_readwrite("jacobian", &LegConstraint::jacobian);
    
    // 耦合约束结构
    py::class_<CouplingConstraint>(m, "CouplingConstraint")
        .def(py::init<>())
        .def_readwrite("joint_names", &CouplingConstraint::joint_names)
        .def_readwrite("constraint_matrix", &CouplingConstraint::constraint_matrix)
        .def_readwrite("constraint_type", &CouplingConstraint::constraint_type);
    
    // 约束模型类
    py::class_<ConstraintModel>(m, "ConstraintModel")
        .def(py::init<>())
        .def_readwrite("wheel_constraints", &ConstraintModel::wheel_constraints)
        .def_readwrite("leg_constraints", &ConstraintModel::leg_constraints)
        .def_readwrite("coupling_constraints", &ConstraintModel::coupling_constraints);
    
    // 任务空间状态结构
    py::class_<TaskSpaceState>(m, "TaskSpaceState")
        .def(py::init<>())
        .def_readwrite("base_position", &TaskSpaceState::base_position)
        .def_readwrite("base_orientation", &TaskSpaceState::base_orientation)
        .def_readwrite("wheel_positions", &TaskSpaceState::wheel_positions)
        .def_readwrite("leg_end_positions", &TaskSpaceState::leg_end_positions);
    
    // 验证结果结构
    py::class_<ValidationResult>(m, "ValidationResult")
        .def(py::init<>())
        .def_readwrite("is_valid", &ValidationResult::is_valid)
        .def_readwrite("error_message", &ValidationResult::error_message)
        .def_readwrite("consistency_error", &ValidationResult::consistency_error);
    
    // 数字孪生映射器主类
    py::class_<DigitalTwinMapper>(m, "DigitalTwinMapper")
        .def(py::init<>())
        .def("parse_urdf_constraints", &DigitalTwinMapper::parse_urdf_constraints,
             "解析URDF约束",
             py::arg("urdf_path"))
        .def("build_kinematic_model", &DigitalTwinMapper::build_kinematic_model,
             "构建运动学模型",
             py::arg("constraint_model"))
        .def("joint_to_task_mapping", &DigitalTwinMapper::joint_to_task_mapping,
             "关节空间到任务空间映射",
             py::arg("joint_angles"))
        .def("task_to_joint_mapping", &DigitalTwinMapper::task_to_joint_mapping,
             "任务空间到关节空间映射",
             py::arg("task_state"))
        .def("validate_motion_consistency", &DigitalTwinMapper::validate_motion_consistency,
             "验证运动一致性",
             py::arg("joint_angles"))
        .def("handle_singular_configuration", &DigitalTwinMapper::handle_singular_configuration,
             "处理奇异位形",
             py::arg("jacobian"));
    
    // 辅助函数
    m.def("create_test_constraint_model", []() {
        ConstraintModel model;
        
        // 创建测试轮子约束
        WheelConstraint wheel1;
        wheel1.wheel_name = "left_wheel";
        wheel1.contact_point = Eigen::Vector3d(0.0, 0.2, 0.0);
        wheel1.normal_vector = Eigen::Vector3d(0.0, 0.0, 1.0);
        wheel1.friction_coefficient = 0.8;
        model.wheel_constraints.push_back(wheel1);
        
        WheelConstraint wheel2;
        wheel2.wheel_name = "right_wheel";
        wheel2.contact_point = Eigen::Vector3d(0.0, -0.2, 0.0);
        wheel2.normal_vector = Eigen::Vector3d(0.0, 0.0, 1.0);
        wheel2.friction_coefficient = 0.8;
        model.wheel_constraints.push_back(wheel2);
        
        // 创建测试腿部约束
        LegConstraint leg1;
        leg1.leg_name = "left_leg";
        leg1.joints = {"lf0_joint", "lf1_joint"};
        leg1.jacobian = Eigen::MatrixXd::Identity(3, 2);
        model.leg_constraints.push_back(leg1);
        
        LegConstraint leg2;
        leg2.leg_name = "right_leg";
        leg2.joints = {"rf0_joint", "rf1_joint"};
        leg2.jacobian = Eigen::MatrixXd::Identity(3, 2);
        model.leg_constraints.push_back(leg2);
        
        return model;
    }, "创建测试约束模型");
    
    m.def("create_test_task_state", []() {
        TaskSpaceState state;
        state.base_position = Eigen::Vector3d(0.0, 0.0, 0.2);
        state.base_orientation = Eigen::Quaterniond::Identity();
        
        state.wheel_positions["left_wheel"] = Eigen::Vector3d(0.0, 0.2, 0.0);
        state.wheel_positions["right_wheel"] = Eigen::Vector3d(0.0, -0.2, 0.0);
        
        state.leg_end_positions["left_leg"] = Eigen::Vector3d(0.3, 0.2, -0.1);
        state.leg_end_positions["right_leg"] = Eigen::Vector3d(0.3, -0.2, -0.1);
        
        return state;
    }, "创建测试任务空间状态");
}