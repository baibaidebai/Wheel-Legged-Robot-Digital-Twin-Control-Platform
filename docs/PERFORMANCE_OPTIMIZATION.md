# 性能优化指南

## 概述

本文档提供系统性能优化的最佳实践、工具和技巧。

## 性能监控

### 使用性能监控器

```python
from wheel_legged_control.utils.performance_monitor import measure_performance, PerformanceContext

# 方式1: 使用装饰器
@measure_performance
def my_function():
    # 函数代码
    pass

# 方式2: 使用上下文管理器
with PerformanceContext('operation_name'):
    # 代码块
    pass
```

### 生成性能报告

```python
from wheel_legged_control.utils.performance_monitor import get_performance_monitor

monitor = get_performance_monitor()
report = monitor.generate_report()
print(report)
```

## 优化策略

### 1. Python代码优化

#### 使用NumPy向量化操作

**❌ 不推荐 - 使用循环**:
```python
result = []
for i in range(len(data)):
    result.append(data[i] * 2)
```

**✅ 推荐 - 使用NumPy**:
```python
import numpy as np
result = np.array(data) * 2
```

#### 避免重复计算

**❌ 不推荐**:
```python
for i in range(len(data)):
    if expensive_function(x) > threshold:
        process(expensive_function(x))
```

**✅ 推荐**:
```python
for i in range(len(data)):
    value = expensive_function(x)
    if value > threshold:
        process(value)
```

#### 使用生成器

**❌ 不推荐 - 创建完整列表**:
```python
def get_data():
    return [process(i) for i in range(1000000)]
```

**✅ 推荐 - 使用生成器**:
```python
def get_data():
    for i in range(1000000):
        yield process(i)
```

### 2. ROS2通信优化

#### QoS配置

```python
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

# 高频率数据 - 使用Best Effort
qos_profile = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST,
    depth=1
)

# 关键数据 - 使用Reliable
qos_profile = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,
    history=HistoryPolicy.KEEP_LAST,
    depth=10
)
```

#### 减少消息大小

**❌ 不推荐 - 发送大量数据**:
```python
msg.data = [float(x) for x in range(10000)]
```

**✅ 推荐 - 压缩或采样**:
```python
msg.data = [float(x) for x in range(10000)[::10]]  # 采样
```

#### 批量处理

```python
# 累积消息批量处理
buffer = []
BATCH_SIZE = 10

def callback(msg):
    buffer.append(msg)
    if len(buffer) >= BATCH_SIZE:
        process_batch(buffer)
        buffer.clear()
```

### 3. 仿真性能优化

#### MuJoCo优化

```python
from wheel_legged_control.simulation import SimulationConfig

config = SimulationConfig(
    backend=SimulationBackend.MUJOCO,
    dt=0.002,  # 增大时间步长
    enable_rendering=False,  # 禁用渲染
    mujoco_solver="Newton",  # 使用快速求解器
    mujoco_iterations=50  # 减少迭代次数
)
```

#### 并行仿真

```python
from wheel_legged_control.simulation import ParallelMuJoCoBackend

# 使用并行仿真加速训练
parallel_backend = ParallelMuJoCoBackend(
    config,
    num_envs=8,  # 8个并行环境
    use_multiprocessing=True
)
```

### 4. 内存优化

#### 对象池

```python
class ObjectPool:
    def __init__(self, factory, size=10):
        self.pool = [factory() for _ in range(size)]
        self.available = list(self.pool)
    
    def acquire(self):
        if self.available:
            return self.available.pop()
        return None
    
    def release(self, obj):
        self.available.append(obj)
```

#### 及时释放资源

```python
# 使用上下文管理器
with open('file.txt') as f:
    data = f.read()
# 文件自动关闭

# 显式删除大对象
del large_array
import gc
gc.collect()
```

### 5. 多线程/多进程

#### 使用线程池

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(process, data) for data in dataset]
    results = [f.result() for f in futures]
```

#### CPU密集型任务使用多进程

```python
from concurrent.futures import ProcessPoolExecutor

with ProcessPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(cpu_intensive_task, data_list))
```

## 性能分析工具

### 1. Python Profiler

```bash
# cProfile
python -m cProfile -o output.prof script.py

# 查看结果
python -m pstats output.prof
```

```python
# 代码中使用
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# 要分析的代码
my_function()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

### 2. line_profiler

```bash
# 安装
pip install line_profiler

# 使用
kernprof -l -v script.py
```

```python
@profile
def my_function():
    # 代码
    pass
```

### 3. memory_profiler

```bash
# 安装
pip install memory_profiler

# 使用
python -m memory_profiler script.py
```

```python
from memory_profiler import profile

@profile
def my_function():
    # 代码
    pass
```

### 4. ROS2性能工具

```bash
# 话题频率
ros2 topic hz /topic_name

# 话题带宽
ros2 topic bw /topic_name

# 节点信息
ros2 node info /node_name

# 性能测试
ros2 run performance_test perf_test
```

## 性能基准

### 目标性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 控制循环频率 | ≥100 Hz | 关节控制器 |
| IMU发布频率 | ≥100 Hz | IMU数据 |
| 状态同步延迟 | <10 ms | 状态同步器 |
| 仿真步进时间 | <5 ms | MuJoCo仿真 |
| GUI响应时间 | <100 ms | 用户界面 |
| 内存使用 | <2 GB | 完整系统 |
| CPU使用 | <50% | 单核 |

### 性能测试

```python
from wheel_legged_control.simulation import SimulationBenchmark

benchmark = SimulationBenchmark()

# 测试单个后端
result = benchmark.benchmark_backend(
    SimulationBackend.MUJOCO,
    model_path='robot.xml',
    num_steps=1000
)

# 对比多个后端
results = benchmark.compare_backends(
    [SimulationBackend.GAZEBO, SimulationBackend.MUJOCO],
    model_path='robot.xml',
    num_steps=1000
)

# 测试并行性能
parallel_results = benchmark.benchmark_parallel_performance(
    SimulationBackend.MUJOCO,
    model_path='robot.xml',
    env_counts=[1, 2, 4, 8]
)
```

## 常见性能问题

### 问题1: 控制循环频率低

**症状**: 控制器更新频率低于目标值

**原因**:
- 计算量过大
- 阻塞操作
- GIL限制

**解决方案**:
1. 优化计算密集型代码
2. 使用异步操作
3. 将计算密集型任务移到C++
4. 使用多进程

### 问题2: 内存泄漏

**症状**: 内存使用持续增长

**原因**:
- 未释放的对象引用
- 循环引用
- 缓存无限增长

**解决方案**:
1. 使用弱引用
2. 限制缓存大小
3. 定期清理
4. 使用内存分析工具

```python
import weakref

# 使用弱引用
cache = weakref.WeakValueDictionary()

# 限制缓存大小
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_function(x):
    pass
```

### 问题3: ROS2消息延迟

**症状**: 消息传输延迟高

**原因**:
- QoS配置不当
- 消息过大
- 网络拥塞

**解决方案**:
1. 调整QoS设置
2. 减小消息大小
3. 使用共享内存
4. 批量处理

### 问题4: 仿真速度慢

**症状**: 仿真无法实时运行

**原因**:
- 物理引擎参数不当
- 模型过于复杂
- 渲染开销

**解决方案**:
1. 调整时间步长
2. 简化模型
3. 禁用渲染
4. 使用并行仿真

## 调试技巧

### 1. 日志级别

```python
import logging

# 开发时使用DEBUG
logging.basicConfig(level=logging.DEBUG)

# 生产时使用INFO或WARNING
logging.basicConfig(level=logging.INFO)
```

### 2. 条件断点

```python
# 仅在特定条件下触发
if error_count > 10:
    import pdb; pdb.set_trace()
```

### 3. 远程调试

```python
# 使用debugpy
import debugpy
debugpy.listen(5678)
debugpy.wait_for_client()
```

### 4. 性能热点定位

```python
import cProfile
import pstats
from pstats import SortKey

profiler = cProfile.Profile()
profiler.enable()

# 运行代码
main()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats(SortKey.CUMULATIVE)
stats.print_stats(20)  # 显示前20个最耗时的函数
```

## 最佳实践

1. **提前优化是万恶之源** - 先确保正确性，再优化性能
2. **测量，不要猜测** - 使用性能分析工具找到真正的瓶颈
3. **优化关键路径** - 专注于最频繁执行的代码
4. **权衡取舍** - 考虑代码可读性和维护性
5. **持续监控** - 建立性能基准，定期检查
6. **文档化优化** - 记录优化原因和效果

## 参考资源

- [Python性能优化指南](https://wiki.python.org/moin/PythonSpeed/PerformanceTips)
- [NumPy性能技巧](https://numpy.org/doc/stable/user/performance.html)
- [ROS2性能优化](https://docs.ros.org/en/humble/Tutorials/Performance.html)
- [MuJoCo性能调优](https://mujoco.readthedocs.io/en/latest/programming.html#performance)
