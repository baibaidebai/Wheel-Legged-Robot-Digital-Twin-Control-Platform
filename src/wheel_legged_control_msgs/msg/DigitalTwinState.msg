# 数字孪生状态消息
std_msgs/Header header

# 虚拟机器人状态
RobotState virtual_state

# 实际机器人状态（仿真中为模拟状态）
RobotState real_state

# 同步状态
bool is_synchronized
float64 sync_error
float64 max_allowed_error

# 映射状态
bool mapping_valid
string mapping_error_message

# 约束验证结果
bool constraints_satisfied
float64 constraint_violation_magnitude