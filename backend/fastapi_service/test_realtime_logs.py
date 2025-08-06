#!/usr/bin/env python3
"""
测试FastAPI独立日志系统的实时日志功能
"""

import time
import requests
from standalone_logging import get_fastapi_logger

def test_fastapi_realtime_logs():
    """测试FastAPI实时日志"""
    logger = get_fastapi_logger('test_realtime')
    
    print("🚀 开始测试FastAPI实时日志...")
    
    # 生成不同类型的测试日志
    test_cases = [
        ('info', 'FastAPI服务健康检查通过'),
        ('warning', '请求处理时间超过预期阈值'),
        ('error', '数据库连接暂时失败，正在重试'),
        ('info', 'WebSocket连接建立成功'),
        ('debug', '处理流水线请求'),
        ('info', '流水线执行开始: pipeline_test_123'),
        ('warning', '步骤执行耗时较长'),
        ('info', '用户认证成功'),
        ('error', '路由处理异常'),
        ('info', 'API响应发送完成')
    ]
    
    for i, (level, message) in enumerate(test_cases, 1):
        # 添加结构化数据
        extra_data = {
            'request_id': f'req_test_{i:03d}',
            'user_id': 1001 if i % 3 == 0 else None,
            'execution_time_ms': 50 + (i * 10),
            'component': 'test_realtime'
        }
        
        # 根据日志级别调用相应方法
        log_method = getattr(logger, level)
        log_method(f"[测试 {i}/10] {message}", extra=extra_data)
        
        print(f"✅ 发送测试日志 {i}/10: {level.upper()} - {message}")
        time.sleep(1)  # 间隔1秒，方便观察实时效果
    
    print("🏁 FastAPI实时日志测试完成！")
    print("📋 请检查页面实时日志是否显示了上述10条新的fastapi_service日志")

if __name__ == "__main__":
    test_fastapi_realtime_logs()
