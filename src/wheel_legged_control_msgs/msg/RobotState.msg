# 机器人完整状态消息
std_msgs/Header header

# 关节状态
sensor_msgs/JointState joint_state

# 基座位姿
geometry_msgs/Pose base_pose

# 基座速度
geometry_msgs/Twist base_velocity

# IMU数据
sensor_msgs/Imu imu_data

# 轮子接触状态
string[] wheel_names
bool[] wheel_contacts

# 系统状态
uint8 IDLE = 0
uint8 ACTIVE = 1
uint8 ERROR = 2
uint8 EMERGENCY_STOP = 3
uint8 system_status

# 错误信息
string error_message