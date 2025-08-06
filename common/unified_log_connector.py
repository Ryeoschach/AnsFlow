#!/usr/bin/env python3
"""
AnsFlow 统一日志连接器
使用uv管理的统一连接接口，确保实时日志、历史查询和索引系统的数据一致性
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, AsyncGenerator
from dataclasses import dataclass
from contextlib import asynccontextmanager

import redis.asyncio as redis
import aiomysql
from elasticsearch import AsyncElasticsearch


@dataclass
class LogEntry:
    """统一日志条目结构"""
    id: str
    timestamp: datetime
    level: str
    service: str
    component: str
    module: str
    message: str
    execution_id: Optional[int] = None
    trace_id: Optional[str] = None
    extra_data: Optional[Dict] = None


class UnifiedLogConnector:
    """统一日志连接器 - 确保所有日志源的数据一致性"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.redis_client = None
        self.mysql_pool = None
        self.es_client = None
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self):
        """初始化所有连接"""
        try:
            # Redis连接 (实时日志流)
            self.redis_client = redis.Redis(
                host=self.config.get('redis_host', 'localhost'),
                port=self.config.get('redis_port', 6379),
                db=self.config.get('redis_db', 5),
                decode_responses=True
            )
            
            # MySQL连接池 (历史查询)
            self.mysql_pool = await aiomysql.create_pool(
                host=self.config.get('mysql_host', 'localhost'),
                port=self.config.get('mysql_port', 3306),
                user=self.config.get('mysql_user', 'root'),
                password=self.config.get('mysql_password', ''),
                db=self.config.get('mysql_db', 'ansflow'),
                minsize=5,
                maxsize=20
            )
            
            # ElasticSearch连接 (日志索引)
            if self.config.get('elasticsearch_enabled', False):
                self.es_client = AsyncElasticsearch([{
                    'host': self.config.get('es_host', 'localhost'),
                    'port': self.config.get('es_port', 9200)
                }])
            
            self.logger.info("统一日志连接器初始化完成")
            
        except Exception as e:
            self.logger.error(f"统一日志连接器初始化失败: {e}")
            raise

    async def close(self):
        """关闭所有连接"""
        if self.redis_client:
            await self.redis_client.aclose()
        if self.mysql_pool:
            self.mysql_pool.close()
            await self.mysql_pool.wait_closed()
        if self.es_client:
            await self.es_client.close()

    # ==================== 实时日志接口 ====================
    
    async def stream_realtime_logs(
        self, 
        start_id: str = '$',
        count: int = 100,
        block: int = 1000
    ) -> AsyncGenerator[LogEntry, None]:
        """流式获取实时日志"""
        try:
            while True:
                messages = await self.redis_client.xread(
                    {'ansflow:logs:stream': start_id},
                    count=count,
                    block=block
                )
                
                for stream_name, stream_messages in messages:
                    for message_id, fields in stream_messages:
                        try:
                            log_entry = self._parse_redis_log(message_id, fields)
                            yield log_entry
                            start_id = message_id
                        except Exception as e:
                            self.logger.error(f"解析Redis日志失败: {e}")
                            continue
                            
        except Exception as e:
            self.logger.error(f"实时日志流读取失败: {e}")
            raise

    async def write_realtime_log(self, log_entry: LogEntry) -> str:
        """写入实时日志到Redis Stream"""
        try:
            fields = {
                'timestamp': log_entry.timestamp.isoformat(),
                'level': log_entry.level,
                'service': log_entry.service,
                'component': log_entry.component,
                'module': log_entry.module,
                'message': log_entry.message,
            }
            
            if log_entry.execution_id:
                fields['execution_id'] = str(log_entry.execution_id)
            if log_entry.trace_id:
                fields['trace_id'] = log_entry.trace_id
            if log_entry.extra_data:
                fields['extra_data'] = json.dumps(log_entry.extra_data)
            
            message_id = await self.redis_client.xadd(
                'ansflow:logs:stream',
                fields
            )
            
            return message_id
            
        except Exception as e:
            self.logger.error(f"写入实时日志失败: {e}")
            raise

    # ==================== 历史查询接口 ====================
    
    async def query_historical_logs(
        self,
        execution_id: Optional[int] = None,
        service: Optional[str] = None,
        level: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[LogEntry]:
        """查询历史日志 - 使用Django ORM"""
        try:
            # 导入Django模型
            import sys
            import os
            import django
            
            django_path = '/Users/creed/Workspace/OpenSource/ansflow/backend/django_service'
            if django_path not in sys.path:
                sys.path.insert(0, django_path)
                
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
            django.setup()
            
            from logging_system.models import UnifiedLog
            from asgiref.sync import sync_to_async
            from django.db.models import Q
            
            # 构建查询条件
            filters = Q()
            
            if execution_id:
                filters &= Q(execution_id=execution_id)
            if service:
                filters &= Q(service=service)
            if level:
                filters &= Q(level=level)
            if start_time:
                filters &= Q(timestamp__gte=start_time)
            if end_time:
                filters &= Q(timestamp__lte=end_time)
            
            # 使用Django ORM异步查询
            @sync_to_async
            def get_logs():
                queryset = UnifiedLog.objects.filter(filters).order_by('-timestamp')[:limit]
                logs = []
                for log_record in queryset:
                    log_entry = LogEntry(
                        id=log_record.log_id,
                        timestamp=log_record.timestamp,
                        level=log_record.level,
                        service=log_record.service,
                        component=log_record.component,
                        module=log_record.module,
                        message=log_record.message,
                        execution_id=log_record.execution_id,
                        trace_id=log_record.trace_id,
                        extra_data=log_record.extra_data
                    )
                    logs.append(log_entry)
                return logs
            
            return await get_logs()
            
        except Exception as e:
            self.logger.error(f"历史日志查询失败: {e}")
            raise

    async def store_historical_log(self, log_entry: LogEntry):
        """存储日志到历史数据库 - 使用Django ORM"""
        try:
            # 导入Django模型
            import sys
            import os
            import django
            
            django_path = '/Users/creed/Workspace/OpenSource/ansflow/backend/django_service'
            if django_path not in sys.path:
                sys.path.insert(0, django_path)
                
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
            django.setup()
            
            from logging_system.models import UnifiedLog
            from asgiref.sync import sync_to_async
            
            # 使用Django ORM异步创建记录
            await sync_to_async(UnifiedLog.create_from_log_entry)(log_entry)
                    
        except Exception as e:
            self.logger.error(f"存储历史日志失败: {e}")
            raise

    # ==================== 日志索引接口 ====================
    
    async def index_log(self, log_entry: LogEntry):
        """将日志添加到搜索索引"""
        if not self.es_client:
            return
            
        try:
            doc = {
                'timestamp': log_entry.timestamp,
                'level': log_entry.level,
                'service': log_entry.service,
                'component': log_entry.component,
                'module': log_entry.module,
                'message': log_entry.message,
                'execution_id': log_entry.execution_id,
                'trace_id': log_entry.trace_id,
                'extra_data': log_entry.extra_data
            }
            
            await self.es_client.index(
                index=f"ansflow-logs-{datetime.now().strftime('%Y-%m')}",
                id=log_entry.id,
                body=doc
            )
            
        except Exception as e:
            self.logger.error(f"日志索引失败: {e}")

    async def search_logs(
        self,
        query: str,
        service: Optional[str] = None,
        level: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[LogEntry]:
        """搜索日志"""
        if not self.es_client:
            # 回退到MySQL查询
            return await self.query_historical_logs(
                service=service, level=level,
                start_time=start_time, end_time=end_time,
                limit=limit
            )
            
        try:
            # 构建ElasticSearch查询
            must_clauses = [
                {"multi_match": {"query": query, "fields": ["message", "component", "module"]}}
            ]
            
            if service:
                must_clauses.append({"term": {"service": service}})
            if level:
                must_clauses.append({"term": {"level": level}})
            
            if start_time or end_time:
                time_range = {}
                if start_time:
                    time_range["gte"] = start_time
                if end_time:
                    time_range["lte"] = end_time
                must_clauses.append({"range": {"timestamp": time_range}})
            
            search_body = {
                "query": {"bool": {"must": must_clauses}},
                "sort": [{"timestamp": {"order": "desc"}}],
                "size": limit
            }
            
            response = await self.es_client.search(
                index="ansflow-logs-*",
                body=search_body
            )
            
            logs = []
            for hit in response['hits']['hits']:
                source = hit['_source']
                log_entry = LogEntry(
                    id=hit['_id'],
                    timestamp=datetime.fromisoformat(source['timestamp'].replace('Z', '+00:00')),
                    level=source['level'],
                    service=source['service'],
                    component=source['component'],
                    module=source['module'],
                    message=source['message'],
                    execution_id=source.get('execution_id'),
                    trace_id=source.get('trace_id'),
                    extra_data=source.get('extra_data')
                )
                logs.append(log_entry)
            
            return logs
            
        except Exception as e:
            self.logger.error(f"日志搜索失败: {e}")
            # 回退到MySQL查询
            return await self.query_historical_logs(
                service=service, level=level,
                start_time=start_time, end_time=end_time,
                limit=limit
            )

    # ==================== 数据一致性保证 ====================
    
    async def sync_log_entry(self, log_entry: LogEntry):
        """同步日志条目到所有存储系统，确保一致性"""
        tasks = []
        
        # 1. 写入实时流
        tasks.append(self.write_realtime_log(log_entry))
        
        # 2. 存储到历史数据库
        tasks.append(self.store_historical_log(log_entry))
        
        # 3. 添加到搜索索引
        if self.es_client:
            tasks.append(self.index_log(log_entry))
        
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            self.logger.error(f"日志同步失败: {e}")

    async def verify_data_consistency(self, log_id: str) -> Dict[str, bool]:
        """验证数据一致性"""
        results = {
            'redis_stream': False,
            'mysql_historical': False,
            'elasticsearch_index': False
        }
        
        try:
            # 检查Redis Stream
            try:
                messages = await self.redis_client.xrevrange(
                    'ansflow:logs:stream',
                    count=1000
                )
                for msg_id, fields in messages:
                    if fields.get('log_id') == log_id:
                        results['redis_stream'] = True
                        break
            except Exception as e:
                self.logger.error(f"检查Redis Stream失败: {e}")
            
            # 检查MySQL
            try:
                async with self.mysql_pool.acquire() as conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute(
                            "SELECT 1 FROM unified_logs WHERE log_id = %s",
                            (log_id,)
                        )
                        if await cursor.fetchone():
                            results['mysql_historical'] = True
            except Exception as e:
                self.logger.error(f"检查MySQL失败: {e}")
            
            # 检查ElasticSearch
            if self.es_client:
                try:
                    response = await self.es_client.get(
                        index="ansflow-logs-*",
                        id=log_id,
                        ignore=[404]
                    )
                    if response.get('found'):
                        results['elasticsearch_index'] = True
                except Exception as e:
                    self.logger.error(f"检查ElasticSearch失败: {e}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"一致性验证失败: {e}")
            return results

    # ==================== 辅助方法 ====================
    
    def _parse_redis_log(self, message_id: str, fields: Dict) -> LogEntry:
        """解析Redis Stream消息为LogEntry"""
        return LogEntry(
            id=message_id,
            timestamp=datetime.fromisoformat(fields['timestamp']),
            level=fields['level'],
            service=fields['service'],
            component=fields['component'],
            module=fields['module'],
            message=fields['message'],
            execution_id=int(fields['execution_id']) if fields.get('execution_id') else None,
            trace_id=fields.get('trace_id'),
            extra_data=json.loads(fields['extra_data']) if fields.get('extra_data') else None
        )


# ==================== 便捷接口 ====================

@asynccontextmanager
async def get_unified_log_connector(config: Dict):
    """获取统一日志连接器的上下文管理器"""
    connector = UnifiedLogConnector(config)
    try:
        await connector.initialize()
        yield connector
    finally:
        await connector.close()


# 从数据库获取配置
def get_config_from_db():
    """从数据库获取统一日志系统配置"""
    try:
        import os
        import sys
        import django
        
        # 添加Django服务路径
        django_path = '/Users/creed/Workspace/OpenSource/ansflow/backend/django_service'
        if django_path not in sys.path:
            sys.path.insert(0, django_path)
            
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
        django.setup()
        
        from settings_management.models import GlobalConfig
        from django.conf import settings
        
        # 从数据库读取Redis配置
        redis_config = GlobalConfig.get_config_dict()
        
        # 使用Django的数据库配置
        db_config = settings.DATABASES['default']
        
        return {
            'redis_host': redis_config.get('LOGGING_REDIS_HOST', 'localhost'),
            'redis_port': int(redis_config.get('LOGGING_REDIS_PORT', 6379)),
            'redis_db': int(redis_config.get('LOGGING_REDIS_DB', 5)),
            'mysql_host': db_config.get('HOST', 'localhost'),
            'mysql_port': int(db_config.get('PORT', 3306)),
            'mysql_user': db_config.get('USER', 'root'),
            'mysql_password': db_config.get('PASSWORD', ''),
            'mysql_db': db_config.get('NAME', 'ansflow'),
            'elasticsearch_enabled': redis_config.get('LOGGING_ENABLE_ELASTICSEARCH', 'false').lower() == 'true',
            'es_host': redis_config.get('LOGGING_ES_HOST', 'localhost'),
            'es_port': int(redis_config.get('LOGGING_ES_PORT', 9200))
        }
    except Exception as e:
        print(f"从数据库获取配置失败: {e}")
        # fallback 到默认配置
        return {
            'redis_host': 'localhost',
            'redis_port': 6379,
            'redis_db': 5,
            'mysql_host': 'localhost',
            'mysql_port': 3306,
            'mysql_user': 'root',
            'mysql_password': '',
            'mysql_db': 'ansflow',
            'elasticsearch_enabled': False,
            'es_host': 'localhost',
            'es_port': 9200
        }

# 默认配置
DEFAULT_CONFIG = get_config_from_db()


# 使用示例
async def example_usage():
    """使用示例"""
    async with get_unified_log_connector(get_config_from_db()) as connector:
        # 创建日志条目
        log_entry = LogEntry(
            id='test-log-1',
            timestamp=datetime.now(),
            level='INFO',
            service='test-service',
            component='test-component',
            module='test.module',
            message='测试日志消息',
            execution_id=123
        )
        
        # 同步到所有存储系统
        await connector.sync_log_entry(log_entry)
        
        # 验证一致性
        consistency = await connector.verify_data_consistency(log_entry.id)
        print(f"数据一致性检查: {consistency}")
        
        # 实时日志流
        async for log in connector.stream_realtime_logs():
            print(f"实时日志: {log.message}")
            break  # 只获取一条用于演示
        
        # 历史查询
        historical_logs = await connector.query_historical_logs(
            service='test-service',
            limit=10
        )
        print(f"历史日志数量: {len(historical_logs)}")
        
        # 日志搜索
        search_results = await connector.search_logs(
            query='测试',
            service='test-service'
        )
        print(f"搜索结果数量: {len(search_results)}")


if __name__ == "__main__":
    asyncio.run(example_usage())
