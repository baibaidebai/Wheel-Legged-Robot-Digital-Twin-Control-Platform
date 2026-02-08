cmake_minimum_required(VERSION 3.8)
project(wheel_legged_control_msgs)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(rosidl_default_generators REQUIRED)

# 生成消息和服务
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/JointCommand.msg"
  "msg/RobotState.msg"
  "msg/DigitalTwinState.msg"
  "srv/SetJointPositions.srv"
  "srv/GetJointStates.srv"
  "srv/ValidateMotion.srv"
  DEPENDENCIES builtin_interfaces std_msgs geometry_msgs sensor_msgs
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_export_dependencies(rosidl_default_runtime)
ament_package()