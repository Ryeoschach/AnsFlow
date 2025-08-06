#!/usr/bin/env python3
"""
AnsFlow日志系统核心功能演示
展示统一日志格式、敏感数据过滤等核心特性
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path


class SensitiveDataFilter:
    """敏感数据过滤器 - 简化版"""
    
    def __init__(self):
        self.sensitive_fields = {
            'password', 'passwd', 'pwd', 'token', 'key', 'secret',
            'authorization', 'cookie', 'session', 'csrf'
        }
    
    def filter_sensitive_data(self, data):
        """过滤敏感信息"""
        if isinstance(data, dict):
            filtered_data = {}
            for key, value in data.items():
                if isinstance(key, str) and any(sensitive in key.lower() for sensitive in self.sensitive_fields):
                    if isinstance(value, str) and len(value) > 8:
                        filtered_data[key] = value[:3] + '*' * (len(value) - 3)
                    else:
                        filtered_data[key] = '******'
                elif isinstance(value, dict):
                    filtered_data[key] = self.filter_sensitive_data(value)
                else:
                    filtered_data[key] = value
            return filtered_data
        return data


class AnsFlowJSONFormatter(logging.Formatter):
    """AnsFlow JSON格式化器 - 简化版"""
    
    def __init__(self):
        super().__init__()
        self.filter = SensitiveDataFilter()
    
    def format(self, record):
        # 基础日志信息
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat() + 'Z',
            'level': record.levelname,
            'service': getattr(record, 'service', 'unknown'),
            'module': record.name,
            'message': record.getMessage(),
        }
        
        # 添加额外数据
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 
                          'pathname', 'filename', 'module', 'lineno', 
                          'funcName', 'created', 'msecs', 'relativeCreated', 
                          'thread', 'threadName', 'processName', 'process']:
                log_data[key] = value
        
        # 过滤敏感数据
        filtered_data = self.filter.filter_sensitive_data(log_data)
        
        return json.dumps(filtered_data, ensure_ascii=False)


def setup_demo_logger():
    """设置演示日志器"""
    # 创建日志目录
    log_dir = Path('./logs')
    log_dir.mkdir(exist_ok=True)
    
    # 创建日志器
    logger = logging.getLogger('ansflow_demo')
    logger.setLevel(logging.DEBUG)
    
    # 清除现有处理器
    logger.handlers.clear()
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器（JSON格式）
    file_handler = logging.FileHandler(log_dir / 'demo.log', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    json_formatter = AnsFlowJSONFormatter()
    file_handler.setFormatter(json_formatter)
    logger.addHandler(file_handler)
    
    return logger


def demo_basic_logging():
    """演示基础日志功能"""
    print("=" * 60)
    print("演示1: 基础日志记录")
    print("=" * 60)
    
    logger = setup_demo_logger()
    
    # 设置服务信息
    logger = logging.LoggerAdapter(logger, {'service': 'demo_service'})
    
    # 基础日志记录
    logger.debug("这是调试信息")
    logger.info("应用启动成功")
    logger.warning("检测到配置警告")
    logger.error("处理请求时发生错误")
    
    print("✅ 基础日志记录完成")


def demo_structured_logging():
    """演示结构化日志"""
    print("\n" + "=" * 60)
    print("演示2: 结构化日志记录")
    print("=" * 60)
    
    logger = setup_demo_logger()
    
    # 创建带额外数据的日志记录
    record = logger.makeRecord(
        name='ansflow_demo',
        level=logging.INFO,
        fn='',
        lno=0,
        msg="用户登录成功",
        args=(),
        exc_info=None
    )
    
    # 添加额外属性
    record.service = 'django_service'
    record.trace_id = 'req_12345678'
    record.user_id = 12345
    record.user_name = 'demo_user'
    record.ip = '192.168.1.100'
    record.action = 'login'
    record.labels = ['auth', 'user', 'success']
    record.response_time_ms = 245
    
    logger.handle(record)
    
    print("✅ 结构化日志记录完成")


def demo_sensitive_data_filtering():
    """演示敏感数据过滤"""
    print("\n" + "=" * 60)
    print("演示3: 敏感数据过滤")
    print("=" * 60)
    
    logger = setup_demo_logger()
    
    # 包含敏感数据的日志
    record = logger.makeRecord(
        name='ansflow_demo',
        level=logging.WARNING,
        fn='',
        lno=0,  
        msg="处理用户认证信息",
        args=(),
        exc_info=None
    )
    
    # 添加敏感数据
    record.service = 'auth_service'
    record.user_id = 12345
    record.password = 'user_secret_password_123'
    record.api_token = 'sk-1234567890abcdef'
    record.session_key = 'sess_abcdefghijklmnop'
    record.safe_data = '这是安全数据'
    
    logger.handle(record)
    
    print("✅ 敏感数据过滤演示完成")


def demo_http_request_logging():
    """演示HTTP请求日志"""
    print("\n" + "=" * 60)
    print("演示4: HTTP请求日志记录")
    print("=" * 60)
    
    logger = setup_demo_logger()
    
    # 模拟HTTP请求开始
    start_time = time.time()
    request_id = 'req_' + str(int(time.time()))
    
    # 请求开始日志
    record = logger.makeRecord(
        name='ansflow_demo',
        level=logging.INFO,
        fn='',
        lno=0,
        msg="Request started: GET /api/users",
        args=(),
        exc_info=None
    )
    
    record.service = 'django_service'
    record.trace_id = request_id
    record.method = 'GET'
    record.path = '/api/users'
    record.ip = '192.168.1.100'
    record.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    record.labels = ['http', 'request', 'start']
    
    logger.handle(record)
    
    # 模拟处理时间
    time.sleep(0.1)
    
    # 请求完成日志
    record = logger.makeRecord(
        name='ansflow_demo',
        level=logging.INFO,
        fn='',
        lno=0,
        msg="Request completed: GET /api/users - 200",
        args=(),
        exc_info=None
    )
    
    record.service = 'django_service'
    record.trace_id = request_id
    record.method = 'GET'
    record.path = '/api/users'
    record.status_code = 200
    record.response_time_ms = int((time.time() - start_time) * 1000)
    record.labels = ['http', 'response', 'success']
    
    logger.handle(record)
    
    print("✅ HTTP请求日志记录完成")


def demo_log_analysis():
    """演示日志分析"""
    print("\n" + "=" * 60)
    print("演示5: 日志文件分析")
    print("=" * 60)
    
    log_file = Path('./logs/demo.log')
    
    if not log_file.exists():
        print("❌ 日志文件不存在")
        return
    
    print(f"日志文件: {log_file}")
    print(f"文件大小: {log_file.stat().st_size} bytes")
    
    # 分析日志内容
    log_levels = {}
    services = {}
    total_logs = 0
    
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            try:
                log_entry = json.loads(line)
                total_logs += 1
                
                # 统计日志级别
                level = log_entry.get('level', 'UNKNOWN')
                log_levels[level] = log_levels.get(level, 0) + 1
                
                # 统计服务
                service = log_entry.get('service', 'unknown')
                services[service] = services.get(service, 0) + 1
                
            except json.JSONDecodeError:
                continue
    
    print(f"\n📊 日志分析结果:")
    print(f"总日志条数: {total_logs}")
    print(f"日志级别分布: {log_levels}")
    print(f"服务分布: {services}")
    
    # 显示最新的几条日志
    print(f"\n📋 最新日志示例:")
    with open(log_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines[-3:]:
            line = line.strip()
            if line:
                try:
                    log_entry = json.loads(line)
                    print(f"  [{log_entry.get('level')}] {log_entry.get('message')}")
                except:
                    print(f"  {line}")
    
    print("✅ 日志分析完成")


def main():
    """主函数"""
    print("🚀 AnsFlow日志系统核心功能演示开始")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 运行各个演示
    demo_basic_logging()
    demo_structured_logging()
    demo_sensitive_data_filtering()
    demo_http_request_logging()
    demo_log_analysis()
    
    print("\n" + "=" * 60)
    print("🎉 所有演示完成！")
    print("💡 查看 ./logs/demo.log 文件可以看到JSON格式的日志输出")
    print("=" * 60)


if __name__ == "__main__":
    main()
