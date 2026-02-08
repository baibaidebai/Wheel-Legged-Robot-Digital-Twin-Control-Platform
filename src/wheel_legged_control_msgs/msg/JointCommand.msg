# 关节指令消息
std_msgs/Header header

# 关节名称列表
string[] joint_names

# 关节位置指令 (rad)
float64[] positions

# 关节速度指令 (rad/s) - 可选
float64[] velocities

# 关节力矩指令 (N·m) - 可选
float64[] efforts

# 指令类型
uint8 POSITION_CONTROL = 0
uint8 VELOCITY_CONTROL = 1
uint8 EFFORT_CONTROL = 2
uint8 command_type

# 执行时间 (s) - 0表示立即执行
float64 execution_time