/**
 * @file test_digital_twin_mapper.cpp
 * @brief 数字孪生映射器C++单元测试
 * @author 轮腿机器人项目团队
 * @date 2024
 */

#include <gtest/gtest.h>
#include "wheel_legged_control/digital_twin_mapper.hpp"
#include <filesystem>
#include <fstream>
#include <chrono>

using namespace wheel_legged_control;

class DigitalTwinMapperTest : public ::testing::Test {
protected:
    void SetUp() override {
        mapper_ = std::make_unique<DigitalTwinMapper>();
        
        // 创建测试URDF内容
        test_urdf_content_ = R"(<?xml version="1.0"?>
<robot name="test_wheel_legged_robot">
    <link name="base_link">
        <inertial>
            <mass value="5.0"/>
            <inertia ixx="0.1" ixy="0.0" ixz="0.0" iyy="0.1" iyz="0.0" izz="0.1"/>
        </inertial>
    </link>
    
    <link name="lf0_link">
        <inertial>
            <mass value="0.5"/>
            <inertia ixx="0.01" ixy="0.0" ixz="0.0" iyy="0.01" iyz="0.0" izz="0.01"/>
        </inertial>
    </link>
    
    <link name="lf1_link">
        <inertial>
            <mass value="0.3"/>
            <inertia ixx="0.005" ixy="0.0" ixz="0.0" iyy="0.005" iyz="0.0" izz="0.005"/>
        </inertial>
    </link>
    
    <link name="left_wheel_link">
        <inertial>
            <mass value="1.0"/>
            <inertia ixx="0.02" ixy="0.0" ixz="0.0" iyy="0.02" iyz="0.0" izz="0.02"/>
        </inertial>
    </link>
    
    <joint name="lf0_joint" type="revolute">
        <parent link="base_link"/>
        <child link="lf0_link"/>
        <axis xyz="0 1 0"/>
        <limit lower="-1.57" upper="1.57" effort="30" velocity="10"/>
    </joint>
    
    <joint name="lf1_joint" type="revolute">
        <parent link="lf0_link"/>
        <child link="lf1_link"/>
        <axis xyz="0 1 0"/>
        <limit lower="-1.57" upper="1.57" effort="30" velocity="10"/>
    </joint>
    
    <joint name="left_wheel_joint" type="continuous">
        <parent link="lf1_link"/>
        <child link="left_wheel_link"/>
        <axis xyz="0 1 0"/>
    </joint>
</robot>)";
        
        // 创建临时URDF文件
        test_urdf_path_ = "/tmp/test_robot.urdf";
        std::ofstream urdf_file(test_urdf_path_);
        urdf_file << test_urdf_content_;
        urdf_file.close();
    }
    
    void TearDown() override {
        // 清理临时文件
        if (std::filesystem::exists(test_urdf_path_)) {
            std::filesystem::remove(test_urdf_path_);
        }
    }
    
    std::unique_ptr<DigitalTwinMapper> mapper_;
    std::string test_urdf_content_;
    std::string test_urdf_path_;
};

TEST_F(DigitalTwinMapperTest, ParseURDFConstraints) {
    // 测试URDF约束解析
    ConstraintModel model = mapper_->parse_urdf_constraints(test_urdf_path_);
    
    // 验证轮子约束
    EXPECT_EQ(model.wheel_constraints.size(), 1);
    EXPECT_EQ(model.wheel_constraints[0].wheel_name, "left_wheel_joint");
    
    // 验证腿部约束
    EXPECT_EQ(model.leg_constraints.size(), 1);
    EXPECT_EQ(model.leg_constraints[0].leg_name, "lf");
    EXPECT_EQ(model.leg_constraints[0].joints.size(), 2);
    
    // 验证耦合约束
    EXPECT_EQ(model.coupling_constraints.size(), 1);
    EXPECT_EQ(model.coupling_constraints[0].constraint_type, ConstraintType::NONHOLONOMIC);
}

TEST_F(DigitalTwinMapperTest, BuildKinematicModel) {
    // 解析URDF并构建模型
    ConstraintModel model = mapper_->parse_urdf_constraints(test_urdf_path_);
    bool success = mapper_->build_kinematic_model(model);
    
    EXPECT_TRUE(success);
}

TEST_F(DigitalTwinMapperTest, ForwardKinematics) {
    // 构建模型
    ConstraintModel model = mapper_->parse_urdf_constraints(test_urdf_path_);
    mapper_->build_kinematic_model(model);
    
    // 测试正运动学
    Eigen::VectorXd joint_angles(3);
    joint_angles << 0.5, -0.3, 1.0; // lf0, lf1, wheel
    
    TaskSpaceState task_state = mapper_->joint_to_task_mapping(joint_angles);
    
    // 验证结果
    EXPECT_EQ(task_state.wheel_positions.size(), 1);
    EXPECT_EQ(task_state.leg_end_positions.size(), 1);
    
    // 验证基座位置
    EXPECT_NEAR(task_state.base_position.norm(), 0.0, 1e-6);
}

TEST_F(DigitalTwinMapperTest, InverseKinematics) {
    // 构建模型
    ConstraintModel model = mapper_->parse_urdf_constraints(test_urdf_path_);
    mapper_->build_kinematic_model(model);
    
    // 创建目标任务空间状态
    TaskSpaceState target_state;
    target_state.base_position = Eigen::Vector3d::Zero();
    target_state.base_orientation = Eigen::Quaterniond::Identity();
    target_state.wheel_positions["left_wheel_joint"] = Eigen::Vector3d(0.2, 0.2, 0.1);
    target_state.leg_end_positions["lf"] = Eigen::Vector3d(0.3, 0.0, -0.1);
    
    // 测试逆运动学
    Eigen::VectorXd joint_angles = mapper_->task_to_joint_mapping(target_state);
    
    // 验证结果维度
    EXPECT_EQ(joint_angles.size(), 3);
    
    // 验证关节角度在合理范围内
    for (int i = 0; i < joint_angles.size(); ++i) {
        EXPECT_GE(joint_angles[i], -M_PI);
        EXPECT_LE(joint_angles[i], M_PI);
    }
}

TEST_F(DigitalTwinMapperTest, MotionConsistencyValidation) {
    // 构建模型
    ConstraintModel model = mapper_->parse_urdf_constraints(test_urdf_path_);
    mapper_->build_kinematic_model(model);
    
    // 测试有效关节角度
    Eigen::VectorXd valid_angles(3);
    valid_angles << 0.5, -0.3, 1.0;
    
    ValidationResult result = mapper_->validate_motion_consistency(valid_angles);
    EXPECT_TRUE(result.is_valid);
    EXPECT_LT(result.consistency_error, 0.2); // 允许小误差
    
    // 测试无效关节角度（超出限制）
    Eigen::VectorXd invalid_angles(3);
    invalid_angles << 5.0, -5.0, 10.0; // 超出±π限制
    
    ValidationResult invalid_result = mapper_->validate_motion_consistency(invalid_angles);
    EXPECT_FALSE(invalid_result.is_valid);
    EXPECT_GT(invalid_result.consistency_error, 0.0);
}

TEST_F(DigitalTwinMapperTest, SingularConfigurationHandling) {
    // 创建奇异雅可比矩阵
    Eigen::MatrixXd singular_jacobian(3, 3);
    singular_jacobian << 1.0, 0.0, 0.0,
                         0.0, 1.0, 0.0,
                         0.0, 0.0, 0.0; // 第三行为零，导致奇异
    
    // 测试奇异处理
    Eigen::MatrixXd regularized = mapper_->handle_singular_configuration(singular_jacobian);
    
    // 验证正则化后的矩阵不再奇异
    Eigen::JacobiSVD<Eigen::MatrixXd> svd(regularized);
    Eigen::VectorXd singular_values = svd.singularValues();
    
    for (int i = 0; i < singular_values.size(); ++i) {
        EXPECT_GT(singular_values[i], 1e-7); // 所有奇异值应大于阈值
    }
}

TEST_F(DigitalTwinMapperTest, RoundTripConsistency) {
    // 构建模型
    ConstraintModel model = mapper_->parse_urdf_constraints(test_urdf_path_);
    mapper_->build_kinematic_model(model);
    
    // 原始关节角度
    Eigen::VectorXd original_angles(3);
    original_angles << 0.2, -0.1, 0.5;
    
    // 正运动学 -> 逆运动学往返测试
    TaskSpaceState task_state = mapper_->joint_to_task_mapping(original_angles);
    Eigen::VectorXd recovered_angles = mapper_->task_to_joint_mapping(task_state);
    
    // 验证往返一致性
    double error = (original_angles - recovered_angles).norm();
    EXPECT_LT(error, 0.1); // 允许10cm误差
}

// 主函数
int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}