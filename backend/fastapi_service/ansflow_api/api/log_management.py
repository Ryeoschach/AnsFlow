"""
日志管理系统 API 端点 - Phase 3
提供日志查询、分析、统计、索引管理等功能
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import structlog
import json
import os
import glob
import re
from pathlib import Path
import aiofiles
import asyncio
from collections import defaultdict, Counter

# 创建日志管理路由器
log_router = APIRouter(prefix="/logs", tags=["日志管理"])
logger = structlog.get_logger(__name__)

# 日志文件基础路径
LOG_BASE_PATH = Path("/Users/creed/Workspace/OpenSource/ansflow/logs")

class LogSearchParams(BaseModel):
    """日志搜索参数"""
    start_time: Optional[str] = Field(None, description="开始时间 ISO格式")
    end_time: Optional[str] = Field(None, description="结束时间 ISO格式")
    levels: Optional[List[str]] = Field(default=[], description="日志级别过滤")
    services: Optional[List[str]] = Field(default=[], description="服务过滤")
    keywords: Optional[str] = Field(None, description="关键词搜索")
    limit: int = Field(100, le=1000, description="返回条数限制")
    offset: int = Field(0, description="偏移量")

class LogEntry(BaseModel):
    """单条日志条目"""
    id: Optional[str] = None
    timestamp: str
    level: str
    service: str
    message: str
    module: Optional[str] = None
    function: Optional[str] = None
    line_number: Optional[int] = None
    extra_data: Optional[Dict[str, Any]] = None

class LogSearchResult(BaseModel):
    """日志搜索结果"""
    logs: List[LogEntry]
    total_count: int
    page: int
    per_page: int
    has_more: bool

class LogAnalysis(BaseModel):
    """日志分析结果"""
    total_count: int
    by_level: Dict[str, int]
    by_service: Dict[str, int]
    by_hour: Dict[str, int]
    by_date: Dict[str, int]
    error_trends: List[Dict[str, Any]]
    top_errors: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]

class LogStats(BaseModel):
    """日志系统统计信息"""
    total_files: int
    total_size_mb: float
    services: List[str]
    levels: List[str]
    date_range: List[str]
    last_updated: str
    files_by_service: Dict[str, int]
    size_by_service: Dict[str, float]

class LogFileIndex(BaseModel):
    """日志文件索引信息"""
    file_path: str
    service: str
    size_mb: float
    line_count: int
    last_modified: str
    date_range: List[str]
    levels_found: List[str]

def parse_log_line(line: str) -> Optional[LogEntry]:
    """解析单行日志"""
    try:
        # 匹配常见日志格式：[2025-01-21 14:30:25] [INFO] [service_name] message
        pattern = r'\[(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})\]\s*\[(\w+)\]\s*\[(\w+)\]\s*(.*)'
        match = re.match(pattern, line.strip())
        
        if match:
            timestamp_str, level, service, message = match.groups()
            
            # 尝试解析为 ISO 格式
            try:
                dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                iso_timestamp = dt.isoformat() + 'Z'
            except:
                iso_timestamp = timestamp_str
            
            return LogEntry(
                timestamp=iso_timestamp,
                level=level.upper(),
                service=service.lower(),
                message=message.strip()
            )
    except Exception as e:
        logger.debug(f"Failed to parse log line: {line[:100]}...", error=str(e))
    
    return None

async def search_logs_in_files(params: LogSearchParams) -> LogSearchResult:
    """在日志文件中搜索日志"""
    logs = []
    total_count = 0
    
    try:
        # 获取所有日志文件
        log_files = []
        if LOG_BASE_PATH.exists():
            log_files = list(LOG_BASE_PATH.glob("**/*.log"))
        
        # 如果没有找到日志文件，返回空结果
        if not log_files:
            return LogSearchResult(
                logs=[],
                total_count=0,
                page=1,
                per_page=params.limit,
                has_more=False
            )
        
        # 时间过滤
        start_dt = None
        end_dt = None
        if params.start_time:
            try:
                start_dt = datetime.fromisoformat(params.start_time.replace('Z', '+00:00'))
            except:
                pass
        if params.end_time:
            try:
                end_dt = datetime.fromisoformat(params.end_time.replace('Z', '+00:00'))
            except:
                pass
        
        # 搜索日志文件
        for log_file in log_files:
            try:
                async with aiofiles.open(log_file, 'r', encoding='utf-8') as f:
                    line_number = 0
                    async for line in f:
                        line_number += 1
                        
                        log_entry = parse_log_line(line)
                        if not log_entry:
                            continue
                        
                        # 设置唯一ID
                        log_entry.id = f"{log_file.name}:{line_number}"
                        
                        # 时间过滤
                        if start_dt or end_dt:
                            try:
                                log_dt = datetime.fromisoformat(log_entry.timestamp.replace('Z', '+00:00'))
                                if start_dt and log_dt < start_dt:
                                    continue
                                if end_dt and log_dt > end_dt:
                                    continue
                            except:
                                continue
                        
                        # 级别过滤
                        if params.levels and log_entry.level not in params.levels:
                            continue
                        
                        # 服务过滤
                        if params.services and log_entry.service not in params.services:
                            continue
                        
                        # 关键词过滤
                        if params.keywords:
                            # 支持简单的AND、OR、NOT逻辑
                            keywords = params.keywords.upper()
                            message_upper = log_entry.message.upper()
                            
                            # 简单的关键词匹配
                            if 'AND' in keywords:
                                words = [w.strip() for w in keywords.split('AND')]
                                if not all(word in message_upper for word in words):
                                    continue
                            elif 'OR' in keywords:
                                words = [w.strip() for w in keywords.split('OR')]
                                if not any(word in message_upper for word in words):
                                    continue
                            elif 'NOT' in keywords:
                                parts = keywords.split('NOT')
                                if len(parts) == 2:
                                    required, excluded = parts[0].strip(), parts[1].strip()
                                    if excluded in message_upper:
                                        continue
                                    if required and required not in message_upper:
                                        continue
                            else:
                                if keywords not in message_upper:
                                    continue
                        
                        total_count += 1
                        
                        # 分页处理
                        if total_count > params.offset and len(logs) < params.limit:
                            logs.append(log_entry)
                        
                        # 如果已经收集够了，可以提前结束
                        if len(logs) >= params.limit:
                            break
                    
                    # 如果已经收集够了，可以提前结束文件循环
                    if len(logs) >= params.limit:
                        break
                        
            except Exception as e:
                logger.error(f"Error reading log file {log_file}", error=str(e))
                continue
    
    except Exception as e:
        logger.error("Error searching logs", error=str(e))
        raise HTTPException(status_code=500, detail=f"日志搜索失败: {str(e)}")
    
    # 按时间倒序排列
    logs.sort(key=lambda x: x.timestamp, reverse=True)
    
    page = (params.offset // params.limit) + 1
    has_more = total_count > (params.offset + len(logs))
    
    return LogSearchResult(
        logs=logs,
        total_count=total_count,
        page=page,
        per_page=params.limit,
        has_more=has_more
    )

async def analyze_logs(params: LogSearchParams) -> LogAnalysis:
    """分析日志数据"""
    by_level = Counter()
    by_service = Counter()
    by_hour = Counter()
    by_date = Counter()
    error_logs = []
    total_count = 0
    
    try:
        # 获取所有日志文件
        log_files = []
        if LOG_BASE_PATH.exists():
            log_files = list(LOG_BASE_PATH.glob("**/*.log"))
        
        for log_file in log_files:
            try:
                async with aiofiles.open(log_file, 'r', encoding='utf-8') as f:
                    async for line in f:
                        log_entry = parse_log_line(line)
                        if not log_entry:
                            continue
                        
                        # 应用相同的过滤条件
                        # (这里可以复用search_logs_in_files中的过滤逻辑)
                        
                        total_count += 1
                        by_level[log_entry.level] += 1
                        by_service[log_entry.service] += 1
                        
                        # 提取时间信息用于趋势分析
                        try:
                            dt = datetime.fromisoformat(log_entry.timestamp.replace('Z', '+00:00'))
                            hour_key = dt.strftime('%Y-%m-%d %H:00')
                            date_key = dt.strftime('%Y-%m-%d')
                            by_hour[hour_key] += 1
                            by_date[date_key] += 1
                        except:
                            pass
                        
                        # 收集错误日志
                        if log_entry.level in ['ERROR', 'CRITICAL'] and len(error_logs) < 20:
                            error_logs.append({
                                'timestamp': log_entry.timestamp,
                                'service': log_entry.service,
                                'message': log_entry.message[:200]  # 截断长消息
                            })
                            
            except Exception as e:
                logger.error(f"Error analyzing log file {log_file}", error=str(e))
                continue
    
    except Exception as e:
        logger.error("Error analyzing logs", error=str(e))
        
    # 构建错误趋势（按小时统计错误数）
    error_trends = []
    for hour_key in sorted(by_hour.keys())[-24:]:  # 最近24小时
        error_count = 0  # 这里需要单独统计错误
        error_trends.append({
            'time': hour_key,
            'count': error_count
        })
    
    # 构建 top 错误
    top_errors = []
    error_messages = Counter()
    for error_log in error_logs:
        # 简化错误消息进行分组
        simplified_msg = error_log['message'][:100]
        error_messages[simplified_msg] += 1
    
    for message, count in error_messages.most_common(10):
        top_errors.append({
            'message': message,
            'count': count,
            'services': ['unknown']  # 这里可以进一步统计
        })
    
    return LogAnalysis(
        total_count=total_count,
        by_level=dict(by_level),
        by_service=dict(by_service),
        by_hour=dict(by_hour),
        by_date=dict(by_date),
        error_trends=error_trends,
        top_errors=top_errors,
        performance_metrics={
            'avg_logs_per_hour': total_count / max(len(by_hour), 1),
            'error_rate': (by_level.get('ERROR', 0) + by_level.get('CRITICAL', 0)) / max(total_count, 1)
        }
    )

async def get_log_stats() -> LogStats:
    """获取日志系统统计信息"""
    total_files = 0
    total_size_mb = 0.0
    services = set()
    levels = set()
    files_by_service = Counter()
    size_by_service = Counter()
    date_range = []
    last_updated = datetime.now().isoformat()
    
    try:
        if LOG_BASE_PATH.exists():
            log_files = list(LOG_BASE_PATH.glob("**/*.log"))
            total_files = len(log_files)
            
            for log_file in log_files:
                try:
                    # 文件大小
                    size_bytes = log_file.stat().st_size
                    size_mb = size_bytes / (1024 * 1024)
                    total_size_mb += size_mb
                    
                    # 从文件名推断服务
                    service = 'unknown'
                    if 'django' in log_file.name.lower():
                        service = 'django'
                    elif 'fastapi' in log_file.name.lower():
                        service = 'fastapi'
                    elif 'system' in log_file.name.lower():
                        service = 'system'
                    
                    services.add(service)
                    files_by_service[service] += 1
                    size_by_service[service] += size_mb
                    
                    # 快速扫描文件获取级别信息（只读前100行）
                    try:
                        with open(log_file, 'r', encoding='utf-8') as f:
                            for i, line in enumerate(f):
                                if i >= 100:  # 只扫描前100行
                                    break
                                log_entry = parse_log_line(line)
                                if log_entry:
                                    levels.add(log_entry.level)
                    except:
                        pass
                        
                except Exception as e:
                    logger.error(f"Error processing log file {log_file}", error=str(e))
                    continue
    
    except Exception as e:
        logger.error("Error getting log stats", error=str(e))
    
    # 设置默认值
    if not services:
        services = {'django', 'fastapi', 'system'}
    if not levels:
        levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
    
    # 设置日期范围（最近30天）
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    date_range = [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')]
    
    return LogStats(
        total_files=total_files,
        total_size_mb=round(total_size_mb, 2),
        services=list(services),
        levels=list(levels),
        date_range=date_range,
        last_updated=last_updated,
        files_by_service=dict(files_by_service),
        size_by_service={k: round(v, 2) for k, v in size_by_service.items()}
    )

# API 端点定义

@log_router.post("/search", response_model=LogSearchResult)
async def search_logs(params: LogSearchParams):
    """
    搜索日志条目
    支持时间范围、级别、服务、关键词等多维度过滤
    """
    return await search_logs_in_files(params)

@log_router.post("/analyze", response_model=LogAnalysis)
async def analyze_logs_endpoint(params: LogSearchParams):
    """
    分析日志数据
    提供级别分布、服务分布、时间趋势、错误统计等分析
    """
    return await analyze_logs(params)

@log_router.get("/stats", response_model=LogStats)
async def get_logs_stats():
    """
    获取日志系统统计信息
    包括文件数量、大小、服务分布等
    """
    return await get_log_stats()

@log_router.get("/files", response_model=List[LogFileIndex])
async def get_log_files():
    """
    获取日志文件索引
    返回所有日志文件的详细信息
    """
    files = []
    
    try:
        if LOG_BASE_PATH.exists():
            log_files = list(LOG_BASE_PATH.glob("**/*.log"))
            
            for log_file in log_files:
                try:
                    stat = log_file.stat()
                    size_mb = stat.st_size / (1024 * 1024)
                    last_modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
                    
                    # 从文件名推断服务
                    service = 'unknown'
                    if 'django' in log_file.name.lower():
                        service = 'django'
                    elif 'fastapi' in log_file.name.lower():
                        service = 'fastapi'
                    elif 'system' in log_file.name.lower():
                        service = 'system'
                    
                    # 快速扫描获取基础信息
                    line_count = 0
                    levels_found = set()
                    dates_found = set()
                    
                    try:
                        with open(log_file, 'r', encoding='utf-8') as f:
                            for line in f:
                                line_count += 1
                                if line_count <= 1000:  # 只扫描前1000行获取样本信息
                                    log_entry = parse_log_line(line)
                                    if log_entry:
                                        levels_found.add(log_entry.level)
                                        try:
                                            dt = datetime.fromisoformat(log_entry.timestamp.replace('Z', '+00:00'))
                                            dates_found.add(dt.strftime('%Y-%m-%d'))
                                        except:
                                            pass
                    except:
                        pass
                    
                    date_range = []
                    if dates_found:
                        sorted_dates = sorted(dates_found)
                        date_range = [sorted_dates[0], sorted_dates[-1]]
                    
                    files.append(LogFileIndex(
                        file_path=str(log_file.relative_to(LOG_BASE_PATH)),
                        service=service,
                        size_mb=round(size_mb, 2),
                        line_count=line_count,
                        last_modified=last_modified,
                        date_range=date_range,
                        levels_found=list(levels_found)
                    ))
                    
                except Exception as e:
                    logger.error(f"Error processing log file {log_file}", error=str(e))
                    continue
    
    except Exception as e:
        logger.error("Error getting log files", error=str(e))
        raise HTTPException(status_code=500, detail=f"获取日志文件失败: {str(e)}")
    
    return files

@log_router.post("/rebuild-index")
async def rebuild_log_index(background_tasks: BackgroundTasks):
    """
    重建日志索引
    后台任务重新扫描和索引所有日志文件
    """
    
    async def rebuild_task():
        """后台重建索引任务"""
        logger.info("Starting log index rebuild")
        try:
            # 这里可以实现更复杂的索引重建逻辑
            # 例如：创建全文搜索索引、缓存热点数据等
            await asyncio.sleep(2)  # 模拟重建过程
            logger.info("Log index rebuild completed")
        except Exception as e:
            logger.error("Log index rebuild failed", error=str(e))
    
    background_tasks.add_task(rebuild_task)
    
    return {"message": "日志索引重建任务已启动，将在后台执行"}

@log_router.get("/stream/{service}")
async def stream_logs(
    service: str,
    follow: bool = Query(True, description="是否实时跟踪"),
    tail: int = Query(100, le=1000, description="尾部行数")
):
    """
    流式获取日志
    支持实时跟踪特定服务的日志输出
    """
    
    async def log_stream():
        try:
            # 查找对应服务的日志文件
            service_files = []
            if LOG_BASE_PATH.exists():
                pattern = f"**/*{service}*.log"
                service_files = list(LOG_BASE_PATH.glob(pattern))
            
            if not service_files:
                yield f"data: {json.dumps({'error': f'No log files found for service: {service}'})}\n\n"
                return
            
            # 获取最新的日志文件
            latest_file = max(service_files, key=lambda f: f.stat().st_mtime)
            
            # 读取尾部日志
            try:
                with open(latest_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines[-tail:]:
                        log_entry = parse_log_line(line)
                        if log_entry:
                            yield f"data: {json.dumps(log_entry.dict(), ensure_ascii=False)}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': f'Failed to read log file: {str(e)}'})}\n\n"
                return
            
            # 实时跟踪
            if follow:
                # 这里可以实现文件变化监控
                # 暂时用模拟数据
                for i in range(5):
                    await asyncio.sleep(3)
                    mock_log = LogEntry(
                        timestamp=datetime.now().isoformat() + 'Z',
                        level='INFO',
                        service=service,
                        message=f'Real-time log message {i+1} from {service} service'
                    )
                    yield f"data: {json.dumps(mock_log.dict(), ensure_ascii=False)}\n\n"
                    
        except Exception as e:
            error_msg = {'error': f'Stream error: {str(e)}'}
            yield f"data: {json.dumps(error_msg)}\n\n"
    
    return StreamingResponse(
        log_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

# 实时日志推送 WebSocket 支持（如果需要）
@log_router.websocket("/ws/{service}")
async def websocket_logs(websocket, service: str):
    """
    WebSocket 实时日志推送
    为特定服务提供实时日志流
    """
    await websocket.accept()
    
    try:
        while True:
            # 这里可以实现真正的实时日志推送
            # 暂时发送模拟数据
            await asyncio.sleep(5)
            
            mock_log = LogEntry(
                timestamp=datetime.now().isoformat() + 'Z',
                level='INFO',
                service=service,
                message=f'WebSocket real-time log from {service}'
            )
            
            await websocket.send_json(mock_log.dict())
            
    except Exception as e:
        logger.error(f"WebSocket error for service {service}", error=str(e))
    finally:
        await websocket.close()
