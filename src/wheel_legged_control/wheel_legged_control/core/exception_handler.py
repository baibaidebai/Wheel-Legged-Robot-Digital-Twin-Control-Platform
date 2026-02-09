#!/usr/bin/env python3
"""
系统异常处理和恢复机制

提供统一的异常捕获、处理和自动恢复功能。
"""

import logging
import traceback
import time
from typing import Callable, Optional, Any, Dict, List
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import threading


class SystemState(Enum):
    """系统状态"""
    NORMAL = "normal"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    SAFE_MODE = "safe_mode"
    RECOVERING = "recovering"
    SHUTDOWN = "shutdown"


class RecoveryStrategy(Enum):
    """恢复策略"""
    RETRY = "retry"
    RESTART = "restart"
    SAFE_MODE = "safe_mode"
    SHUTDOWN = "shutdown"
    IGNORE = "ignore"


@dataclass
class ExceptionRecord:
    """异常记录"""
    timestamp: datetime
    exception_type: str
    exception_message: str
    traceback_info: str
    component: str
    severity: str
    recovery_attempted: bool = False
    recovery_successful: bool = False
    recovery_strategy: Optional[RecoveryStrategy] = None


class ExceptionHandler:
    """系统异常处理器"""
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        self.logger = logging.getLogger(__name__)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # 系统状态
        self.current_state = SystemState.NORMAL
        self.previous_state = SystemState.NORMAL
        
        # 异常记录
        self.exception_history: List[ExceptionRecord] = []
        self.max_history_size = 100
        
        # 组件状态
        self.component_states: Dict[str, SystemState] = {}
        self.component_retry_counts: Dict[str, int] = {}
        
        # 恢复策略映射
        self.recovery_strategies: Dict[type, RecoveryStrategy] = {
            ConnectionError: RecoveryStrategy.RETRY,
            TimeoutError: RecoveryStrategy.RETRY,
            RuntimeError: RecoveryStrategy.RESTART,
            MemoryError: RecoveryStrategy.SAFE_MODE,
            KeyboardInterrupt: RecoveryStrategy.SHUTDOWN,
        }
        
        # 回调函数
        self.state_change_callbacks: List[Callable] = []
        self.recovery_callbacks: Dict[str, Callable] = {}
        
        # 线程锁
        self.lock = threading.Lock()
        
        self.logger.info("异常处理器初始化完成")
    
    def handle_exception(self, 
                        exception: Exception,
                        component: str,
                        context: Optional[Dict[str, Any]] = None) -> bool:
        """
        处理异常
        
        Args:
            exception: 异常对象
            component: 组件名称
            context: 上下文信息
            
        Returns:
            是否成功处理
        """
        with self.lock:
            # 记录异常
            record = self._create_exception_record(exception, component)
            self.exception_history.append(record)
            
            # 限制历史记录大小
            if len(self.exception_history) > self.max_history_size:
                self.exception_history.pop(0)
            
            # 确定严重程度
            severity = self._determine_severity(exception, component)
            record.severity = severity
            
            # 记录日志
            self.logger.error(
                f"组件 {component} 发生异常: {type(exception).__name__}: {str(exception)}"
            )
            
            # 更新组件状态
            self._update_component_state(component, severity)
            
            # 选择恢复策略
            strategy = self._select_recovery_strategy(exception, component)
            record.recovery_strategy = strategy
            
            # 执行恢复
            success = self._execute_recovery(exception, component, strategy, context)
            record.recovery_attempted = True
            record.recovery_successful = success
            
            return success
    
    def _create_exception_record(self, exception: Exception, component: str) -> ExceptionRecord:
        """创建异常记录"""
        return ExceptionRecord(
            timestamp=datetime.now(),
            exception_type=type(exception).__name__,
            exception_message=str(exception),
            traceback_info=traceback.format_exc(),
            component=component
        )
    
    def _determine_severity(self, exception: Exception, component: str) -> str:
        """确定异常严重程度"""
        # 关键组件的异常更严重
        critical_components = ['joint_controller', 'state_synchronizer', 'safety_monitor']
        
        if isinstance(exception, (MemoryError, SystemError)):
            return 'critical'
        elif isinstance(exception, (RuntimeError, ValueError)) and component in critical_components:
            return 'error'
        elif isinstance(exception, (ConnectionError, TimeoutError)):
            return 'warning'
        else:
            return 'error'
    
    def _update_component_state(self, component: str, severity: str):
        """更新组件状态"""
        if severity == 'critical':
            self.component_states[component] = SystemState.CRITICAL
            self._update_system_state(SystemState.CRITICAL)
        elif severity == 'error':
            self.component_states[component] = SystemState.ERROR
            if self.current_state == SystemState.NORMAL:
                self._update_system_state(SystemState.ERROR)
        elif severity == 'warning':
            self.component_states[component] = SystemState.WARNING
            if self.current_state == SystemState.NORMAL:
                self._update_system_state(SystemState.WARNING)
    
    def _update_system_state(self, new_state: SystemState):
        """更新系统状态"""
        if new_state != self.current_state:
            self.previous_state = self.current_state
            self.current_state = new_state
            
            self.logger.info(f"系统状态变更: {self.previous_state.value} -> {new_state.value}")
            
            # 触发回调
            for callback in self.state_change_callbacks:
                try:
                    callback(self.previous_state, new_state)
                except Exception as e:
                    self.logger.error(f"状态变更回调失败: {e}")
    
    def _select_recovery_strategy(self, exception: Exception, component: str) -> RecoveryStrategy:
        """选择恢复策略"""
        # 检查预定义策略
        for exc_type, strategy in self.recovery_strategies.items():
            if isinstance(exception, exc_type):
                return strategy
        
        # 检查重试次数
        retry_count = self.component_retry_counts.get(component, 0)
        if retry_count >= self.max_retries:
            self.logger.warning(f"组件 {component} 重试次数已达上限，切换到安全模式")
            return RecoveryStrategy.SAFE_MODE
        
        # 默认策略
        return RecoveryStrategy.RETRY
    
    def _execute_recovery(self,
                         exception: Exception,
                         component: str,
                         strategy: RecoveryStrategy,
                         context: Optional[Dict[str, Any]]) -> bool:
        """执行恢复策略"""
        self.logger.info(f"执行恢复策略: {strategy.value} for {component}")
        
        try:
            if strategy == RecoveryStrategy.RETRY:
                return self._retry_operation(component, context)
            
            elif strategy == RecoveryStrategy.RESTART:
                return self._restart_component(component, context)
            
            elif strategy == RecoveryStrategy.SAFE_MODE:
                return self._enter_safe_mode(component)
            
            elif strategy == RecoveryStrategy.SHUTDOWN:
                return self._shutdown_system()
            
            elif strategy == RecoveryStrategy.IGNORE:
                self.logger.warning(f"忽略组件 {component} 的异常")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"恢复策略执行失败: {e}")
            return False
    
    def _retry_operation(self, component: str, context: Optional[Dict[str, Any]]) -> bool:
        """重试操作"""
        retry_count = self.component_retry_counts.get(component, 0)
        
        if retry_count >= self.max_retries:
            self.logger.error(f"组件 {component} 重试次数已达上限")
            return False
        
        self.component_retry_counts[component] = retry_count + 1
        
        self.logger.info(f"重试组件 {component} (第 {retry_count + 1}/{self.max_retries} 次)")
        
        # 延迟重试
        time.sleep(self.retry_delay * (retry_count + 1))
        
        # 调用恢复回调
        if component in self.recovery_callbacks:
            try:
                self.recovery_callbacks[component](context)
                self.component_retry_counts[component] = 0  # 重置计数
                self.component_states[component] = SystemState.NORMAL
                return True
            except Exception as e:
                self.logger.error(f"重试失败: {e}")
                return False
        
        return True
    
    def _restart_component(self, component: str, context: Optional[Dict[str, Any]]) -> bool:
        """重启组件"""
        self.logger.info(f"重启组件: {component}")
        
        # 重置状态
        self.component_retry_counts[component] = 0
        self.component_states[component] = SystemState.RECOVERING
        
        # 调用恢复回调
        if component in self.recovery_callbacks:
            try:
                self.recovery_callbacks[component](context)
                self.component_states[component] = SystemState.NORMAL
                return True
            except Exception as e:
                self.logger.error(f"组件重启失败: {e}")
                return False
        
        return True
    
    def _enter_safe_mode(self, component: str) -> bool:
        """进入安全模式"""
        self.logger.warning(f"组件 {component} 进入安全模式")
        
        self._update_system_state(SystemState.SAFE_MODE)
        
        # 停止非关键组件
        self._stop_non_critical_components()
        
        return True
    
    def _shutdown_system(self) -> bool:
        """关闭系统"""
        self.logger.critical("执行系统关闭")
        
        self._update_system_state(SystemState.SHUTDOWN)
        
        # 触发关闭回调
        for callback in self.state_change_callbacks:
            try:
                callback(self.current_state, SystemState.SHUTDOWN)
            except Exception as e:
                self.logger.error(f"关闭回调失败: {e}")
        
        return True
    
    def _stop_non_critical_components(self):
        """停止非关键组件"""
        critical_components = ['joint_controller', 'state_synchronizer', 'safety_monitor']
        
        for component in list(self.component_states.keys()):
            if component not in critical_components:
                self.logger.info(f"停止非关键组件: {component}")
                self.component_states[component] = SystemState.SHUTDOWN
    
    def register_recovery_callback(self, component: str, callback: Callable):
        """注册恢复回调"""
        self.recovery_callbacks[component] = callback
        self.logger.info(f"已注册组件 {component} 的恢复回调")
    
    def register_state_change_callback(self, callback: Callable):
        """注册状态变更回调"""
        self.state_change_callbacks.append(callback)
    
    def get_system_state(self) -> SystemState:
        """获取系统状态"""
        return self.current_state
    
    def get_component_state(self, component: str) -> Optional[SystemState]:
        """获取组件状态"""
        return self.component_states.get(component)
    
    def get_exception_history(self, component: Optional[str] = None, limit: int = 10) -> List[ExceptionRecord]:
        """获取异常历史"""
        if component:
            history = [r for r in self.exception_history if r.component == component]
        else:
            history = self.exception_history
        
        return history[-limit:]
    
    def reset_component(self, component: str):
        """重置组件状态"""
        self.component_retry_counts[component] = 0
        self.component_states[component] = SystemState.NORMAL
        self.logger.info(f"组件 {component} 状态已重置")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_exceptions = len(self.exception_history)
        successful_recoveries = sum(1 for r in self.exception_history if r.recovery_successful)
        
        exception_by_type = {}
        for record in self.exception_history:
            exception_by_type[record.exception_type] = exception_by_type.get(record.exception_type, 0) + 1
        
        return {
            'total_exceptions': total_exceptions,
            'successful_recoveries': successful_recoveries,
            'recovery_rate': successful_recoveries / total_exceptions if total_exceptions > 0 else 0,
            'current_state': self.current_state.value,
            'component_states': {k: v.value for k, v in self.component_states.items()},
            'exception_by_type': exception_by_type
        }


def safe_execute(func: Callable, 
                exception_handler: ExceptionHandler,
                component: str,
                *args, **kwargs) -> Optional[Any]:
    """
    安全执行函数，自动处理异常
    
    Args:
        func: 要执行的函数
        exception_handler: 异常处理器
        component: 组件名称
        *args, **kwargs: 函数参数
        
    Returns:
        函数返回值，如果失败返回None
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        exception_handler.handle_exception(e, component, {'args': args, 'kwargs': kwargs})
        return None


if __name__ == "__main__":
    # 测试异常处理器
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 测试异常处理器")
    print("=" * 50)
    
    handler = ExceptionHandler(max_retries=3, retry_delay=0.5)
    
    # 注册恢复回调
    def recovery_callback(context):
        print(f"执行恢复操作: {context}")
    
    handler.register_recovery_callback('test_component', recovery_callback)
    
    # 测试不同类型的异常
    print("\n测试1: ConnectionError")
    try:
        raise ConnectionError("连接失败")
    except Exception as e:
        handler.handle_exception(e, 'test_component')
    
    print(f"系统状态: {handler.get_system_state().value}")
    
    print("\n测试2: RuntimeError")
    try:
        raise RuntimeError("运行时错误")
    except Exception as e:
        handler.handle_exception(e, 'test_component')
    
    print(f"系统状态: {handler.get_system_state().value}")
    
    # 显示统计
    print("\n📊 统计信息:")
    stats = handler.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 显示异常历史
    print("\n📜 异常历史:")
    for record in handler.get_exception_history():
        print(f"  [{record.timestamp}] {record.component}: {record.exception_type}")
        print(f"    策略: {record.recovery_strategy.value if record.recovery_strategy else 'N/A'}")
        print(f"    成功: {record.recovery_successful}")
    
    print("\n🎉 测试完成")
