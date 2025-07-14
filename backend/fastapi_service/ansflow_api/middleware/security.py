"""
安全配置中间件
包含认证、授权、CORS、CSRF等安全功能
"""

import time
import hashlib
import secrets
from typing import List, Dict, Optional, Any
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
from datetime import datetime, timedelta
import jwt

from ..config.performance import security_settings

logger = logging.getLogger(__name__)

# JWT 安全配置
security = HTTPBearer()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头中间件"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # 添加安全头
        security_headers = {
            # 防止点击劫持
            "X-Frame-Options": "DENY",
            # 防止 MIME 类型嗅探
            "X-Content-Type-Options": "nosniff",
            # XSS 保护
            "X-XSS-Protection": "1; mode=block",
            # 引用策略
            "Referrer-Policy": "strict-origin-when-cross-origin",
            # 权限策略
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            # 内容安全策略
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            ),
        }
        
        # HSTS (仅在 HTTPS 时启用)
        if security_settings.enable_https_redirect and request.url.scheme == "https":
            security_headers["Strict-Transport-Security"] = f"max-age={security_settings.hsts_max_age}; includeSubDomains"
        
        # 添加所有安全头
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """请求验证中间件"""
    
    def __init__(self, app):
        super().__init__(app)
        self.blocked_ips: set = set()
        self.suspicious_requests: Dict[str, list] = {}
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端真实IP"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _is_suspicious_request(self, request: Request) -> bool:
        """检测可疑请求"""
        suspicious_patterns = [
            # SQL 注入模式
            "union", "select", "insert", "delete", "drop", "exec",
            # XSS 模式
            "<script", "javascript:", "onerror=", "onload=",
            # 路径遍历
            "../", "..\\", "/etc/passwd", "/proc/",
            # 命令注入
            "; rm -rf", "| cat", "&& echo",
        ]
        
        # 检查 URL 路径
        path = request.url.path.lower()
        query = str(request.url.query).lower()
        
        for pattern in suspicious_patterns:
            if pattern in path or pattern in query:
                return True
        
        return False
    
    async def dispatch(self, request: Request, call_next):
        client_ip = self._get_client_ip(request)
        
        # 检查被阻止的IP
        if client_ip in self.blocked_ips:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # 检查可疑请求
        if self._is_suspicious_request(request):
            logger.warning(f"Suspicious request from {client_ip}: {request.url}")
            
            # 记录可疑请求
            if client_ip not in self.suspicious_requests:
                self.suspicious_requests[client_ip] = []
            
            self.suspicious_requests[client_ip].append(time.time())
            
            # 如果可疑请求过多，暂时阻止该IP
            recent_requests = [
                req_time for req_time in self.suspicious_requests[client_ip]
                if time.time() - req_time < 300  # 5分钟内
            ]
            
            if len(recent_requests) > 5:
                self.blocked_ips.add(client_ip)
                logger.error(f"Blocking IP {client_ip} due to multiple suspicious requests")
                raise HTTPException(status_code=403, detail="Too many suspicious requests")
        
        # 验证请求大小
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > security_settings.max_request_size:
            raise HTTPException(status_code=413, detail="Request too large")
        
        return await call_next(request)


class AuditLogMiddleware(BaseHTTPMiddleware):
    """审计日志中间件"""
    
    def __init__(self, app):
        super().__init__(app)
        self.sensitive_endpoints = {
            "/api/v1/auth/",
            "/api/v1/users/",
            "/admin/",
        }
    
    def _is_sensitive_endpoint(self, path: str) -> bool:
        """判断是否为敏感端点"""
        return any(path.startswith(endpoint) for endpoint in self.sensitive_endpoints)
    
    def _get_user_info(self, request: Request) -> Dict[str, Any]:
        """提取用户信息"""
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                payload = jwt.decode(
                    token, 
                    security_settings.jwt_secret_key, 
                    algorithms=[security_settings.jwt_algorithm]
                )
                return {
                    "user_id": payload.get("sub"),
                    "username": payload.get("username"),
                    "roles": payload.get("roles", [])
                }
            except jwt.InvalidTokenError:
                pass
        
        return {"user_id": None, "username": "anonymous", "roles": []}
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        user_info = self._get_user_info(request)
        
        # 记录请求开始
        if security_settings.enable_audit_log and self._is_sensitive_endpoint(request.url.path):
            logger.info(
                f"AUDIT: {user_info['username']} ({client_ip}) accessing {request.method} {request.url.path}",
                extra={
                    "audit": True,
                    "user_id": user_info["user_id"],
                    "username": user_info["username"],
                    "ip_address": client_ip,
                    "method": request.method,
                    "path": request.url.path,
                    "user_agent": request.headers.get("user-agent"),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        try:
            response = await call_next(request)
            
            # 记录响应
            if security_settings.enable_audit_log and self._is_sensitive_endpoint(request.url.path):
                duration = time.time() - start_time
                logger.info(
                    f"AUDIT: Request completed with status {response.status_code} in {duration:.3f}s",
                    extra={
                        "audit": True,
                        "user_id": user_info["user_id"],
                        "username": user_info["username"],
                        "ip_address": client_ip,
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "duration": duration,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            
            return response
            
        except Exception as e:
            # 记录错误
            if security_settings.enable_audit_log:
                duration = time.time() - start_time
                logger.error(
                    f"AUDIT: Request failed with error: {str(e)}",
                    extra={
                        "audit": True,
                        "user_id": user_info["user_id"],
                        "username": user_info["username"],
                        "ip_address": client_ip,
                        "method": request.method,
                        "path": request.url.path,
                        "error": str(e),
                        "duration": duration,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            raise


class JWTAuthMiddleware:
    """JWT 认证中间件"""
    
    def __init__(self):
        self.secret_key = security_settings.jwt_secret_key
        self.algorithm = security_settings.jwt_algorithm
        self.access_token_expire_minutes = security_settings.jwt_access_token_expire_minutes
    
    def create_access_token(self, data: dict) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
        """验证令牌"""
        try:
            payload = jwt.decode(
                credentials.credentials, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            user_id = payload.get("sub")
            if user_id is None:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")


class APIKeyMiddleware(BaseHTTPMiddleware):
    """API Key 认证中间件（可选）"""
    
    def __init__(self, app):
        super().__init__(app)
        self.api_keys = {
            # 示例 API Keys，生产环境应从数据库或配置文件读取
            "ansflow-dev-key": {"name": "Development", "permissions": ["read", "write"]},
            "ansflow-monitor-key": {"name": "Monitoring", "permissions": ["read"]},
        }
    
    async def dispatch(self, request: Request, call_next):
        # 跳过公开端点
        if request.url.path in ["/", "/health/", "/metrics", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        # 如果启用了 API Key 认证
        if security_settings.enable_api_key_auth:
            api_key = request.headers.get(security_settings.api_key_header)
            
            if not api_key or api_key not in self.api_keys:
                raise HTTPException(
                    status_code=401,
                    detail="Valid API key required"
                )
            
            # 添加 API Key 信息到请求状态
            request.state.api_key_info = self.api_keys[api_key]
        
        return await call_next(request)


# CORS 配置
def get_cors_middleware():
    """获取 CORS 中间件配置"""
    return CORSMiddleware, {
        "allow_origins": security_settings.cors_origins,
        "allow_credentials": True,
        "allow_methods": security_settings.cors_methods,
        "allow_headers": security_settings.cors_headers,
    }


# 全局安全中间件实例
jwt_auth = JWTAuthMiddleware()
security_headers_middleware = SecurityHeadersMiddleware
request_validation_middleware = RequestValidationMiddleware
audit_log_middleware = AuditLogMiddleware
api_key_middleware = APIKeyMiddleware


def get_security_middlewares():
    """获取所有安全中间件"""
    return [
        security_headers_middleware,
        request_validation_middleware,
        audit_log_middleware,
        api_key_middleware,
    ]
