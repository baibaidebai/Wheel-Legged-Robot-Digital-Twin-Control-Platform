/**
 * @file digital_twin_mapper.cpp
 * @brief 基于URDF的轮腿混合运动数字孪生映射器实现
 * @author 轮腿机器人项目团队
 * @date 2024
 */

#include "wheel_legged_control/digital_twin_mapper.hpp"
#include <tinyxml2.h>
#include <iostream>
#include <fstream>
#include <cmath>
#include <algorithm>

namespace wheel_legged_control {

/**
 * @brief DigitalTwinMapper实现类
 */
class DigitalTwinMapper::Impl {
public:
    ConstraintModel constraint_model_;
    std::map<std::string, int> joint_index_map_;
    Eigen::MatrixXd jacobian_matrix_;
    bool model_initialized_;
    
    Impl() : model_initialized_(false) {}
    
    /**
     * @brief 解析URDF文件中的约束信息
     */
    ConstraintModel parse_urdf_constraints(const std::string& urdf_path) {
        ConstraintModel model;
        
        // 使用tinyxml2解析URDF文件
        tinyxml2::XMLDocument doc;
        if (doc.LoadFile(urdf_path.c_str()) != tinyxml2::XML_SUCCESS) {
            throw std::runtime_error("Failed to load URDF file: " + urdf_path);
        }
        
        auto robot_elem = doc.FirstChildElement("robot");
        if (!robot_elem) {
            throw std::runtime_error("Invalid URDF: missing robot element");
        }
        
        // 解析关节信息
        std::vector<std::string> wheel_joints;
        std::vector<std::string> leg_joints;
        
        for (auto joint_elem = robot_elem->FirstChildElement("joint");
             joint_elem; joint_elem = joint_elem->NextSiblingElement("joint")) {
            
            const char* joint_name = joint_elem->Attribute("name");
            const char* joint_type = joint_elem->Attribute("type");
            
            if (!joint_name || !joint_type) continue;
            
            std::string name(joint_name);
            std::string type(joint_type);
            
            // 分类关节
            if (name.find("wheel") != std::string::npos) {
                wheel_joints.push_back(name);
            } else if (name.find("lf") != std::string::npos || 
                      name.find("rf") != std::string::npos ||
                      name.find("lb") != std::string::npos ||
                      name.find("rb") != std::string::npos) {
                leg_joints.push_back(name);
            }
        }
        
        // 创建轮子约束
        for (const auto& wheel_joint : wheel_joints) {
            WheelConstraint constraint;
            constraint.wheel_name = wheel_joint;
            constraint.contact_point = Eigen::Vector3d::Zero();
            constraint.normal_vector = Eigen::Vector3d(0, 0, 1);
            constraint.friction_coefficient = 0.8;
            model.wheel_constraints.push_back(constraint);
        }
        
        // 创建腿部约束
        std::map<std::string, std::vector<std::string>> leg_groups;
        for (const auto& leg_joint : leg_joints) {
            std::string leg_prefix = leg_joint.substr(0, 2); // "lf", "rf", etc.
            leg_groups[leg_prefix].push_back(leg_joint);
        }
        
        for (const auto& group : leg_groups) {
            LegConstraint constraint;
            constraint.leg_name = group.first;
            constraint.joints = group.second;
            constraint.jacobian = Eigen::MatrixXd::Identity(3, group.second.size());
            model.leg_constraints.push_back(constraint);
        }
        
        // 创建耦合约束（轮腿协调）
        if (!wheel_joints.empty() && !leg_joints.empty()) {
            CouplingConstraint coupling;
            coupling.joint_names = wheel_joints;
            coupling.joint_names.insert(coupling.joint_names.end(), 
                                       leg_joints.begin(), leg_joints.end());
            
            int total_joints = coupling.joint_names.size();
            coupling.constraint_matrix = Eigen::MatrixXd::Zero(total_joints, total_joints);
            
            // 设置轮腿耦合关系
            for (size_t i = 0; i < wheel_joints.size(); ++i) {
                for (size_t j = wheel_joints.size(); j < total_joints; ++j) {
                    coupling.constraint_matrix(i, j) = 0.1; // 弱耦合
                }
            }
            
            coupling.constraint_type = ConstraintType::NONHOLONOMIC;
            model.coupling_constraints.push_back(coupling);
        }
        
        return model;
    }
    
    /**
     * @brief 构建运动学模型
     */
    bool build_kinematic_model(const ConstraintModel& model) {
        constraint_model_ = model;
        
        // 建立关节索引映射
        joint_index_map_.clear();
        int index = 0;
        
        for (const auto& wheel_constraint : model.wheel_constraints) {
            joint_index_map_[wheel_constraint.wheel_name] = index++;
        }
        
        for (const auto& leg_constraint : model.leg_constraints) {
            for (const auto& joint : leg_constraint.joints) {
                joint_index_map_[joint] = index++;
            }
        }
        
        // 初始化雅可比矩阵
        int total_joints = joint_index_map_.size();
        jacobian_matrix_ = Eigen::MatrixXd::Identity(6, total_joints); // 6DOF任务空间
        
        model_initialized_ = true;
        return true;
    }
    
    /**
     * @brief 关节空间到任务空间映射
     */
    TaskSpaceState joint_to_task_mapping(const Eigen::VectorXd& joint_angles) {
        if (!model_initialized_) {
            throw std::runtime_error("Kinematic model not initialized");
        }
        
        TaskSpaceState task_state;
        
        // 基座位置和姿态（简化计算）
        task_state.base_position = Eigen::Vector3d::Zero();
        task_state.base_orientation = Eigen::Quaterniond::Identity();
        
        // 安全检查：确保关节角度向量大小正确
        if (joint_angles.size() != static_cast<int>(joint_index_map_.size())) {
            throw std::runtime_error("Joint angles vector size mismatch. Expected: " + 
                                   std::to_string(joint_index_map_.size()) + 
                                   ", Got: " + std::to_string(joint_angles.size()));
        }
        
        // 计算轮子位置
        for (const auto& wheel_constraint : constraint_model_.wheel_constraints) {
            auto it = joint_index_map_.find(wheel_constraint.wheel_name);
            if (it != joint_index_map_.end()) {
                int index = it->second;
                if (index >= 0 && index < joint_angles.size()) {
                    double angle = joint_angles[index];
                    // 简化的轮子位置计算
                    Eigen::Vector3d wheel_pos(0.3 * std::cos(angle), 0.3 * std::sin(angle), 0.1);
                    task_state.wheel_positions[wheel_constraint.wheel_name] = wheel_pos;
                }
            }
        }
        
        // 计算腿端位置
        for (const auto& leg_constraint : constraint_model_.leg_constraints) {
            Eigen::Vector3d leg_end_pos = Eigen::Vector3d::Zero();
            
            // 简化的正运动学计算
            double link1_length = 0.2;
            double link2_length = 0.25;
            
            if (leg_constraint.joints.size() >= 2) {
                auto it1 = joint_index_map_.find(leg_constraint.joints[0]);
                auto it2 = joint_index_map_.find(leg_constraint.joints[1]);
                
                if (it1 != joint_index_map_.end() && it2 != joint_index_map_.end()) {
                    int index1 = it1->second;
                    int index2 = it2->second;
                    
                    if (index1 >= 0 && index1 < joint_angles.size() &&
                        index2 >= 0 && index2 < joint_angles.size()) {
                        
                        double q1 = joint_angles[index1];
                        double q2 = joint_angles[index2];
                        
                        // 二连杆正运动学
                        leg_end_pos.x() = link1_length * std::cos(q1) + link2_length * std::cos(q1 + q2);
                        leg_end_pos.y() = link1_length * std::sin(q1) + link2_length * std::sin(q1 + q2);
                        leg_end_pos.z() = 0.0;
                    }
                }
            }
            
            task_state.leg_end_positions[leg_constraint.leg_name] = leg_end_pos;
        }
        
        return task_state;
    }
    
    /**
     * @brief 任务空间到关节空间映射（逆运动学）
     */
    Eigen::VectorXd task_to_joint_mapping(const TaskSpaceState& task_state) {
        if (!model_initialized_) {
            throw std::runtime_error("Kinematic model not initialized");
        }
        
        int total_joints = joint_index_map_.size();
        Eigen::VectorXd joint_angles = Eigen::VectorXd::Zero(total_joints);
        
        // 轮子关节逆运动学
        for (const auto& wheel_pos : task_state.wheel_positions) {
            auto it = joint_index_map_.find(wheel_pos.first);
            if (it != joint_index_map_.end()) {
                // 简化的轮子角度计算
                double angle = atan2(wheel_pos.second.y(), wheel_pos.second.x());
                joint_angles[it->second] = angle;
            }
        }
        
        // 腿部关节逆运动学
        for (const auto& leg_end : task_state.leg_end_positions) {
            // 查找对应的腿部约束
            for (const auto& leg_constraint : constraint_model_.leg_constraints) {
                if (leg_constraint.leg_name == leg_end.first && 
                    leg_constraint.joints.size() >= 2) {
                    
                    auto it1 = joint_index_map_.find(leg_constraint.joints[0]);
                    auto it2 = joint_index_map_.find(leg_constraint.joints[1]);
                    
                    if (it1 != joint_index_map_.end() && it2 != joint_index_map_.end()) {
                        // 二连杆逆运动学
                        double x = leg_end.second.x();
                        double y = leg_end.second.y();
                        double link1_length = 0.2;
                        double link2_length = 0.25;
                        
                        double r = sqrt(x*x + y*y);
                        
                        // 检查工作空间
                        if (r <= link1_length + link2_length && 
                            r >= abs(link1_length - link2_length)) {
                            
                            double cos_q2 = (r*r - link1_length*link1_length - link2_length*link2_length) /
                                           (2 * link1_length * link2_length);
                            cos_q2 = std::max(-1.0, std::min(1.0, cos_q2));
                            
                            double q2 = acos(cos_q2);
                            double q1 = atan2(y, x) - atan2(link2_length * sin(q2),
                                                           link1_length + link2_length * cos(q2));
                            
                            joint_angles[it1->second] = q1;
                            joint_angles[it2->second] = q2;
                        }
                    }
                    break;
                }
            }
        }
        
        return joint_angles;
    }
    
    /**
     * @brief 验证运动一致性
     */
    ValidationResult validate_motion_consistency(const Eigen::VectorXd& joint_angles) {
        ValidationResult result;
        result.is_valid = true;
        result.consistency_error = 0.0;
        result.error_message = "";
        
        if (!model_initialized_) {
            result.is_valid = false;
            result.error_message = "Kinematic model not initialized";
            return result;
        }
        
        // 检查关节限制
        for (const auto& joint_pair : joint_index_map_) {
            int index = joint_pair.second;
            if (index >= joint_angles.size()) {
                result.is_valid = false;
                result.error_message = "Joint angle vector size mismatch";
                return result;
            }
            
            double angle = joint_angles[index];
            // 简化的关节限制检查（-π到π）
            if (angle < -M_PI || angle > M_PI) {
                result.is_valid = false;
                result.error_message = "Joint " + joint_pair.first + " exceeds limits";
                result.consistency_error += abs(angle) - M_PI;
            }
        }
        
        // 检查轮腿协调一致性
        TaskSpaceState forward_result = joint_to_task_mapping(joint_angles);
        Eigen::VectorXd inverse_result = task_to_joint_mapping(forward_result);
        
        if (inverse_result.size() == joint_angles.size()) {
            double error = (joint_angles - inverse_result).norm();
            result.consistency_error += error;
            
            if (error > 0.1) { // 10cm误差阈值
                result.is_valid = false;
                result.error_message = "Forward-inverse kinematics inconsistency";
            }
        }
        
        return result;
    }
    
    /**
     * @brief 处理奇异位形（简化版本）
     */
    Eigen::MatrixXd handle_singular_configuration(const Eigen::MatrixXd& jacobian) {
        // 输入验证
        if (jacobian.rows() == 0 || jacobian.cols() == 0) {
            throw std::runtime_error("Invalid jacobian matrix dimensions");
        }
        
        // 简化版本：直接返回带有小正则化项的矩阵
        Eigen::MatrixXd regularized = jacobian;
        double reg_factor = 1e-6;
        
        // 对角线正则化
        int min_dim = std::min(jacobian.rows(), jacobian.cols());
        for (int i = 0; i < min_dim; ++i) {
            regularized(i, i) += reg_factor;
        }
        
        return regularized;
    }
};

// DigitalTwinMapper类实现
DigitalTwinMapper::DigitalTwinMapper() : pimpl_(std::make_unique<Impl>()) {}

DigitalTwinMapper::~DigitalTwinMapper() = default;

ConstraintModel DigitalTwinMapper::parse_urdf_constraints(const std::string& urdf_path) {
    return pimpl_->parse_urdf_constraints(urdf_path);
}

bool DigitalTwinMapper::build_kinematic_model(const ConstraintModel& constraint_model) {
    return pimpl_->build_kinematic_model(constraint_model);
}

TaskSpaceState DigitalTwinMapper::joint_to_task_mapping(const Eigen::VectorXd& joint_angles) {
    return pimpl_->joint_to_task_mapping(joint_angles);
}

Eigen::VectorXd DigitalTwinMapper::task_to_joint_mapping(const TaskSpaceState& task_state) {
    return pimpl_->task_to_joint_mapping(task_state);
}

ValidationResult DigitalTwinMapper::validate_motion_consistency(const Eigen::VectorXd& joint_angles) {
    return pimpl_->validate_motion_consistency(joint_angles);
}

Eigen::MatrixXd DigitalTwinMapper::handle_singular_configuration(const Eigen::MatrixXd& jacobian) {
    return pimpl_->handle_singular_configuration(jacobian);
}

} // namespace wheel_legged_control