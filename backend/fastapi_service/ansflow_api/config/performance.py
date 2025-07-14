"""
FastAPI 性能优化配置
针对高并发和低延迟场景的优化设置
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class PerformanceSettings(BaseSettings):
    """性能优化配置"""
    
    # 服务器配置
    workers: int = 4  # Uvicorn worker 数量
    max_connections: int = 1000  # 最大连接数
    keep_alive_timeout: int = 5  # Keep-alive 超时
    timeout_keep_alive: int = 5  # Keep-alive 超时
    
    # 数据库连接池优化
    db_pool_size: int = 20  # 数据库连接池大小
    db_max_overflow: int = 30  # 数据库连接池溢出
    db_pool_timeout: int = 30  # 连接池超时
    db_pool_recycle: int = 3600  # 连接回收时间
    
    # Redis 连接池优化
    redis_pool_size: int = 50  # Redis 连接池大小
    redis_pool_timeout: int = 10  # Redis 连接超时
    
    # HTTP 客户端优化
    http_pool_connections: int = 100  # HTTP 连接池
    http_pool_maxsize: int = 100  # HTTP 连接池最大大小
    http_max_retries: int = 3  # HTTP 重试次数
    
    # 缓存配置
    enable_response_cache: bool = True  # 启用响应缓存
    cache_ttl: int = 300  # 缓存TTL（秒）
    cache_max_size: int = 1000  # 缓存最大条目数
    
    # WebSocket 优化
    websocket_ping_interval: int = 20  # WebSocket ping 间隔
    websocket_ping_timeout: int = 10  # WebSocket ping 超时
    websocket_close_timeout: int = 10  # WebSocket 关闭超时
    
    # 请求限制
    rate_limit_requests: int = 1000  # 每分钟请求限制
    rate_limit_window: int = 60  # 限流窗口（秒）
    
    # 异步任务配置
    task_queue_size: int = 1000  # 任务队列大小
    worker_concurrency: int = 100  # Worker 并发数
    
    # 监控配置
    metrics_collection_interval: int = 5  # 指标收集间隔（秒）
    health_check_interval: int = 30  # 健康检查间隔（秒）
    
    # 内存优化
    gc_collection_threshold: int = 1000  # GC 收集阈值
    enable_gc_optimization: bool = True  # 启用 GC 优化
    
    class Config:
        env_prefix = "ANSFLOW_PERF_"


class SecuritySettings(BaseSettings):
    """安全配置"""
    
    # JWT 配置
    jwt_secret_key: str = "your-super-secret-jwt-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # 密码配置
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_digits: bool = True
    password_require_special: bool = True
    
    # API 安全
    enable_cors: bool = True
    cors_origins: list = ["http://localhost:3000", "http://localhost:3001"]
    cors_methods: list = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_headers: list = ["*"]
    
    # 请求限制
    max_request_size: int = 16 * 1024 * 1024  # 16MB
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    
    # 会话安全
    session_cookie_secure: bool = False  # 开发环境设为 False
    session_cookie_httponly: bool = True
    session_cookie_samesite: str = "lax"
    
    # HTTPS 配置
    enable_https_redirect: bool = False  # 开发环境设为 False
    hsts_max_age: int = 31536000  # HSTS 最大年龄
    
    # API 访问控制
    enable_api_key_auth: bool = False  # 可选的 API Key 认证
    api_key_header: str = "X-API-Key"
    
    # 审计日志
    enable_audit_log: bool = True
    audit_log_level: str = "INFO"
    
    class Config:
        env_prefix = "ANSFLOW_SEC_"


# 全局配置实例
performance_settings = PerformanceSettings()
security_settings = SecuritySettings()
