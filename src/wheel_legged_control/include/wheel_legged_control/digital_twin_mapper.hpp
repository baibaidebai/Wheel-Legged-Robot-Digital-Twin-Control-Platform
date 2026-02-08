/**
 * @file digital_twin_mapper.hpp
 * @brief 基于URDF的轮腿混合运动数字孪生映射器
 * @author 轮腿机器人项目团队
 * @date 2024
 * 
 * 核心创新功能：解决轮腿机器人闭环机构在URDF中的表达与控制映射问题
 */

#ifndef WHEEL_LEGGED_CONTROL_DIGITAL_TWIN_MAPPER_HPP
#define WHEEL_LEGGED_CONTROL_DIGITAL_TWIN_MAPPER_HPP

#include <memory>
#include <vector>
#include <string>
#include <map>
#include <Eigen/Dense>

namespace wheel_legged_control {

/**
 * @brief 约束类型枚举
 */
enum class ConstraintType {
    HOLONOMIC,      ///< 完整约束
    NONHOLONOMIC    ///< 非完整约束
};

/**
 * @brief 轮子约束结构
 */
struct WheelConstraint {
    std::string wheel_name;           ///< 轮子名称
    Eigen::Vector3d contact_point;    ///< 接触点位置
    Eigen::Vector3d normal_vector;    ///< 法向量
    double friction_coefficient;      ///< 摩擦系数
    
    WheelConstraint() : contact_point(Eigen::Vector3d::Zero()), 
                       normal_vector(Eigen::Vector3d::UnitZ()), 
                       friction_coefficient(0.8) {}
};

/**
 * @brief 腿部约束结构
 */
struct LegConstraint {
    std::string leg_name;            ///< 腿部名称
    std::vector<std::string> joints; ///< 关节列表
    Eigen::MatrixXd jacobian;        ///< 雅可比矩阵
    
    LegConstraint() : jacobian(Eigen::MatrixXd::Identity(3, 2)) {}
};

/**
 * @brief 耦合约束结构
 */
struct CouplingConstraint {
    std::vector<std::string> joint_names; ///< 关节名称列表
    Eigen::MatrixXd constraint_matrix;    ///< 约束矩阵
    ConstraintType constraint_type;       ///< 约束类型
    
    CouplingConstraint() : constraint_matrix(Eigen::MatrixXd::Identity(2, 2)),
                          constraint_type(ConstraintType::HOLONOMIC) {}
};

/**
 * @brief 约束模型类
 */
class ConstraintModel {
public:
    std::vector<WheelConstraint> wheel_constraints;      ///< 轮子约束
    std::vector<LegConstraint> leg_constraints;          ///< 腿部约束
    std::vector<CouplingConstraint> coupling_constraints; ///< 耦合约束
};

/**
 * @brief 任务空间状态结构
 */
struct TaskSpaceState {
    Eigen::Vector3d base_position;                        ///< 基座位置
    Eigen::Quaterniond base_orientation;                  ///< 基座姿态
    std::map<std::string, Eigen::Vector3d> wheel_positions; ///< 轮子位置
    std::map<std::string, Eigen::Vector3d> leg_end_positions; ///< 腿端位置
    
    TaskSpaceState() : base_position(Eigen::Vector3d::Zero()),
                      base_orientation(Eigen::Quaterniond::Identity()) {}
};

/**
 * @brief 验证结果结构
 */
struct ValidationResult {
    bool is_valid;              ///< 是否有效
    std::string error_message;  ///< 错误信息
    double consistency_error;   ///< 一致性误差
    
    ValidationResult() : is_valid(false), consistency_error(0.0) {}
};

/**
 * @brief 数字孪生映射器类
 * 
 * 核心创新功能，实现基于URDF的轮腿混合运动映射
 */
class DigitalTwinMapper {
public:
    /**
     * @brief 构造函数
     */
    DigitalTwinMapper();
    
    /**
     * @brief 析构函数
     */
    ~DigitalTwinMapper();
    
    /**
     * @brief 解析URDF约束
     * @param urdf_path URDF文件路径
     * @return 约束模型
     */
    ConstraintModel parse_urdf_constraints(const std::string& urdf_path);
    
    /**
     * @brief 构建运动学模型
     * @param constraint_model 约束模型
     * @return 是否成功
     */
    bool build_kinematic_model(const ConstraintModel& constraint_model);
    
    /**
     * @brief 关节空间到任务空间映射
     * @param joint_angles 关节角度
     * @return 任务空间状态
     */
    TaskSpaceState joint_to_task_mapping(const Eigen::VectorXd& joint_angles);
    
    /**
     * @brief 任务空间到关节空间映射
     * @param task_state 任务空间状态
     * @return 关节角度
     */
    Eigen::VectorXd task_to_joint_mapping(const TaskSpaceState& task_state);
    
    /**
     * @brief 验证运动一致性
     * @param joint_angles 关节角度
     * @return 验证结果
     */
    ValidationResult validate_motion_consistency(const Eigen::VectorXd& joint_angles);
    
    /**
     * @brief 处理奇异位形
     * @param jacobian 雅可比矩阵
     * @return 处理后的雅可比矩阵
     */
    Eigen::MatrixXd handle_singular_configuration(const Eigen::MatrixXd& jacobian);

private:
    class Impl;                    ///< 实现类前向声明
    std::unique_ptr<Impl> pimpl_;  ///< PIMPL指针
};

} // namespace wheel_legged_control

#endif // WHEEL_LEGGED_CONTROL_DIGITAL_TWIN_MAPPER_HPP