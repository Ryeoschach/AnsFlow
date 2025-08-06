#!/usr/bin/env python3
"""
AnsFlow 日志同步服务
负责将Redis Stream中的日志同步到MySQL历史数据库
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

# 添加Django服务路径
django_path = Path(__file__).parent.parent / 'backend' / 'django_service'
sys.path.insert(0, str(django_path))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
import django
django.setup()

from unified_log_connector import UnifiedLogConnector, LogEntry, get_config_from_db


class LogSyncService:
    """日志同步服务"""
    
    def __init__(self):
        self.config = get_config_from_db()
        self.connector = UnifiedLogConnector(self.config)
        self.logger = logging.getLogger(__name__)
        self.last_sync_id = '$'  # 从最新开始
        self.sync_interval = 30  # 30秒同步一次
        self.batch_size = 100    # 每批处理100条
        
    async def initialize(self):
        """初始化服务"""
        await self.connector.initialize()
        
        # 获取上次同步的位置
        await self._load_sync_position()
        
        self.logger.info("日志同步服务初始化完成")
        
    async def _load_sync_position(self):
        """加载上次同步位置"""
        try:
            # 从数据库获取上次同步的位置
            async with self.connector.mysql_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        SELECT redis_stream_id FROM log_sync_position 
                        WHERE service_name = 'log_sync_service'
                        ORDER BY updated_at DESC LIMIT 1
                    """)
                    result = await cursor.fetchone()
                    
                    if result:
                        self.last_sync_id = result[0]
                        self.logger.info(f"恢复同步位置: {self.last_sync_id}")
                    else:
                        # 如果没有记录，从24小时前开始同步
                        start_time = datetime.now() - timedelta(hours=24)
                        start_timestamp = int(start_time.timestamp() * 1000)
                        self.last_sync_id = f"{start_timestamp}-0"
                        self.logger.info(f"首次同步，从24小时前开始: {self.last_sync_id}")
                        
        except Exception as e:
            self.logger.error(f"加载同步位置失败: {e}")
            
    async def _save_sync_position(self, stream_id: str):
        """保存同步位置"""
        try:
            async with self.connector.mysql_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        INSERT INTO log_sync_position (service_name, redis_stream_id, updated_at)
                        VALUES ('log_sync_service', %s, NOW())
                        ON DUPLICATE KEY UPDATE 
                        redis_stream_id = VALUES(redis_stream_id),
                        updated_at = VALUES(updated_at)
                    """, (stream_id,))
                    await conn.commit()
                    
        except Exception as e:
            self.logger.error(f"保存同步位置失败: {e}")
            
    async def sync_logs_to_mysql(self):
        """将Redis Stream中的日志同步到MySQL"""
        try:
            # 从Redis Stream读取新日志
            messages = await self.connector.redis_client.xread(
                {'ansflow:logs:stream': self.last_sync_id},
                count=self.batch_size,
                block=1000  # 等待1秒
            )
            
            if not messages:
                return 0
                
            synced_count = 0
            last_message_id = None
            
            for stream_name, stream_messages in messages:
                for message_id, fields in stream_messages:
                    try:
                        # 解析日志条目
                        log_entry = LogEntry(
                            id=fields.get('log_id', message_id),
                            timestamp=datetime.fromisoformat(fields['timestamp']),
                            level=fields['level'],
                            service=fields['service'],
                            component=fields.get('component', ''),
                            module=fields.get('module', ''),
                            message=fields['message'],
                            execution_id=int(fields['execution_id']) if fields.get('execution_id') else None,
                            trace_id=fields.get('trace_id'),
                            extra_data=json.loads(fields['extra_data']) if fields.get('extra_data') else None
                        )
                        
                        # 存储到MySQL（检查是否已存在）
                        await self._store_log_if_not_exists(log_entry)
                        
                        synced_count += 1
                        last_message_id = message_id
                        
                    except Exception as e:
                        self.logger.error(f"同步单条日志失败 {message_id}: {e}")
                        continue
            
            # 更新同步位置
            if last_message_id:
                self.last_sync_id = last_message_id
                await self._save_sync_position(last_message_id)
                
            if synced_count > 0:
                self.logger.info(f"同步 {synced_count} 条日志到MySQL")
                
            return synced_count
            
        except Exception as e:
            self.logger.error(f"同步日志到MySQL失败: {e}")
            return 0
            
    async def _store_log_if_not_exists(self, log_entry: LogEntry):
        """存储日志到MySQL（如果不存在）"""
        try:
            async with self.connector.mysql_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # 检查是否已存在
                    await cursor.execute(
                        "SELECT 1 FROM unified_logs WHERE log_id = %s",
                        (log_entry.id,)
                    )
                    
                    if not await cursor.fetchone():
                        # 插入新记录
                        await cursor.execute("""
                            INSERT INTO unified_logs (
                                log_id, timestamp, level, service, component, module,
                                message, execution_id, trace_id, extra_data
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            log_entry.id,
                            log_entry.timestamp,
                            log_entry.level,
                            log_entry.service,
                            log_entry.component,
                            log_entry.module,
                            log_entry.message,
                            log_entry.execution_id,
                            log_entry.trace_id,
                            json.dumps(log_entry.extra_data) if log_entry.extra_data else None
                        ))
                        await conn.commit()
                        
        except Exception as e:
            self.logger.error(f"存储日志到MySQL失败: {e}")
            raise
            
    async def cleanup_old_logs(self, days: int = 30):
        """清理超过指定天数的旧日志"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # 清理MySQL中的旧日志
            async with self.connector.mysql_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "DELETE FROM unified_logs WHERE timestamp < %s",
                        (cutoff_date,)
                    )
                    deleted_count = cursor.rowcount
                    await conn.commit()
                    
            # 清理Redis Stream中的旧日志（保留最近的10000条）
            try:
                await self.connector.redis_client.xtrim(
                    'ansflow:logs:stream',
                    maxlen=10000,
                    approximate=True
                )
            except Exception as e:
                self.logger.warning(f"清理Redis Stream失败: {e}")
                
            self.logger.info(f"清理了 {deleted_count} 条 {days} 天前的旧日志")
            
        except Exception as e:
            self.logger.error(f"清理旧日志失败: {e}")
            
    async def run_sync_loop(self):
        """运行同步循环"""
        self.logger.info("日志同步服务启动")
        
        while True:
            try:
                # 同步日志
                synced = await self.sync_logs_to_mysql()
                
                # 每小时清理一次旧日志
                if datetime.now().minute == 0:
                    await self.cleanup_old_logs()
                    
                # 等待下次同步
                await asyncio.sleep(self.sync_interval)
                
            except KeyboardInterrupt:
                self.logger.info("收到停止信号，正在关闭...")
                break
            except Exception as e:
                self.logger.error(f"同步循环异常: {e}")
                await asyncio.sleep(self.sync_interval)
                
    async def close(self):
        """关闭服务"""
        await self.connector.close()
        self.logger.info("日志同步服务已关闭")


async def main():
    """主函数"""
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('/Users/creed/Workspace/OpenSource/ansflow/logs/log_sync_service.log')
        ]
    )
    
    service = LogSyncService()
    try:
        await service.initialize()
        await service.run_sync_loop()
    finally:
        await service.close()


if __name__ == "__main__":
    asyncio.run(main())
