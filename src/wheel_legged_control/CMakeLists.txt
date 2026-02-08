cmake_minimum_required(VERSION 3.8)
project(wheel_legged_control)

# 编译选项
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# C++标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 查找依赖包
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclpy REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(trajectory_msgs REQUIRED)
find_package(urdf REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)
find_package(eigen3_cmake_module REQUIRED)
find_package(Eigen3 REQUIRED)
find_package(pybind11_vendor REQUIRED)
find_package(pybind11 REQUIRED)
find_package(PkgConfig REQUIRED)
pkg_check_modules(TINYXML2 REQUIRED tinyxml2)

# 包含目录
include_directories(
  include
  ${EIGEN3_INCLUDE_DIRS}
)

# C++库 - 数字孪生映射器
add_library(digital_twin_mapper SHARED
  src/digital_twin_mapper/digital_twin_mapper.cpp
)

target_include_directories(digital_twin_mapper PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
  ${TINYXML2_INCLUDE_DIRS}
)

ament_target_dependencies(digital_twin_mapper
  rclcpp
  std_msgs
  sensor_msgs
  geometry_msgs
  tf2
  tf2_ros
  urdf
  Eigen3
)

target_link_libraries(digital_twin_mapper ${TINYXML2_LIBRARIES})

# Python绑定
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)

add_library(digital_twin_mapper_py MODULE
  src/python_bindings/digital_twin_mapper_bindings.cpp
)

target_include_directories(digital_twin_mapper_py PRIVATE
  ${Python3_INCLUDE_DIRS}
)

target_link_libraries(digital_twin_mapper_py PRIVATE 
  digital_twin_mapper 
  pybind11::module
  ${Python3_LIBRARIES}
)

pybind11_extension(digital_twin_mapper_py)
pybind11_strip(digital_twin_mapper_py)

set_target_properties(digital_twin_mapper_py PROPERTIES 
  CXX_VISIBILITY_PRESET "hidden"
  PREFIX "${PYTHON_MODULE_PREFIX}"
  SUFFIX "${PYTHON_MODULE_EXTENSION}"
)

# Python模块安装
ament_python_install_package(${PROJECT_NAME})

# 安装C++库
install(TARGETS digital_twin_mapper
  EXPORT export_${PROJECT_NAME}
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

# 安装Python绑定
install(TARGETS digital_twin_mapper_py
  DESTINATION "${PYTHON_INSTALL_DIR}/${PROJECT_NAME}"
)

# 安装头文件
install(DIRECTORY include/
  DESTINATION include
)

# 安装Python脚本
install(PROGRAMS
  scripts/gazebo_simulator.py
  DESTINATION lib/${PROJECT_NAME}
)

# 安装launch文件
install(DIRECTORY launch/
  DESTINATION share/${PROJECT_NAME}/launch
)

# 安装配置文件
install(DIRECTORY config/
  DESTINATION share/${PROJECT_NAME}/config
)

# 安装URDF文件
install(DIRECTORY urdf/
  DESTINATION share/${PROJECT_NAME}/urdf
)

# 安装世界文件
install(DIRECTORY worlds/
  DESTINATION share/${PROJECT_NAME}/worlds
)

# 测试
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  find_package(ament_cmake_pytest REQUIRED)
  find_package(ament_cmake_gtest REQUIRED)
  find_package(launch_testing_ament_cmake REQUIRED)
  
  # Lint测试
  ament_lint_auto_find_test_dependencies()
  
  # C++单元测试
  ament_add_gtest(test_digital_twin_mapper
    ../../test/cpp/test_digital_twin_mapper.cpp
  )
  
  if(TARGET test_digital_twin_mapper)
    target_link_libraries(test_digital_twin_mapper digital_twin_mapper)
    ament_target_dependencies(test_digital_twin_mapper
      rclcpp
      std_msgs
      sensor_msgs
      geometry_msgs
    )
  endif()
  
  # Python测试
  ament_add_pytest_test(test_python_modules ../../test/python/
    PYTHON_EXECUTABLE "${PYTHON_EXECUTABLE}"
  )
  
  # 集成测试
  # add_launch_test(../../test/integration/test_system_integration.py)
endif()

# 导出依赖
ament_export_targets(export_${PROJECT_NAME} HAS_LIBRARY_TARGET)
ament_export_dependencies(
  rclcpp
  rclpy
  std_msgs
  sensor_msgs
  geometry_msgs
  trajectory_msgs
  urdf
  tf2
  tf2_ros
  tf2_geometry_msgs
  Eigen3
)

ament_package()