#!/usr/bin/env python3
"""
AnsFlow 统一日志系统 uv 连接管理器
管理所有日志相关的连接和依赖，确保数据一致性
"""

import subprocess
import sys
import os
from pathlib import Path


class UVLogConnector:
    """基于UV的统一日志连接管理器"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.services = {
            'django': self.project_root / 'backend/django_service',
            'fastapi': self.project_root / 'backend/fastapi_service'
        }
        
    def install_dependencies(self, service: str = 'all'):
        """使用uv安装日志相关依赖"""
        dependencies = {
            'common': [
                'redis[hiredis]',
                'aiomysql',
                'elasticsearch[async]',
                'structlog',
                'python-json-logger'
            ],
            'django': [
                'django-redis',
                'celery[redis]',
                'django-structlog'
            ],
            'fastapi': [
                'fastapi',
                'uvicorn',
                'websockets',
                'aiofiles'
            ]
        }
        
        if service == 'all':
            for svc in self.services.keys():
                self._install_for_service(svc, dependencies)
        else:
            self._install_for_service(service, dependencies)
    
    def _install_for_service(self, service: str, dependencies: dict):
        """为特定服务安装依赖"""
        if service not in self.services:
            print(f"❌ 未知服务: {service}")
            return
        
        service_path = self.services[service]
        
        print(f"📦 为 {service} 服务安装日志依赖...")
        
        # 安装通用依赖
        for dep in dependencies['common']:
            self._run_uv_add(service_path, dep)
        
        # 安装服务特定依赖
        if service in dependencies:
            for dep in dependencies[service]:
                self._run_uv_add(service_path, dep)
    
    def _run_uv_add(self, service_path: Path, dependency: str):
        """运行uv add命令"""
        try:
            result = subprocess.run([
                'uv', 'add', dependency
            ], cwd=service_path, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {dependency} 安装成功")
            else:
                print(f"❌ {dependency} 安装失败: {result.stderr}")
        except FileNotFoundError:
            print("❌ uv命令未找到，请先安装uv")
            sys.exit(1)
    
    def setup_unified_logging(self):
        """设置统一日志配置"""
        print("🔧 设置统一日志配置...")
        
        # 创建统一日志配置
        config_content = '''
# AnsFlow 统一日志配置
import os
from pathlib import Path

# 日志根目录
LOG_ROOT = Path(os.getenv('ANSFLOW_LOG_ROOT', '/Users/creed/Workspace/OpenSource/ansflow/logs'))

# Redis配置
REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDIS_PORT', '6379')),
    'db': int(os.getenv('REDIS_LOG_DB', '5')),
    'stream_name': 'ansflow:logs:stream'
}

# MySQL配置
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', '3306')),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DB', 'ansflow')
}

# ElasticSearch配置
ELASTICSEARCH_CONFIG = {
    'enabled': os.getenv('ES_ENABLED', 'false').lower() == 'true',
    'hosts': [os.getenv('ES_HOST', 'localhost:9200')],
    'index_pattern': 'ansflow-logs-{date}'
}

# 日志级别配置
LOG_LEVELS = {
    'DEBUG': 10,
    'INFO': 20,
    'WARNING': 30,
    'ERROR': 40,
    'CRITICAL': 50
}

# 服务配置
SERVICES = {
    'django': {
        'port': 8000,
        'log_dir': LOG_ROOT / 'services/django',
        'component': 'web'
    },
    'fastapi': {
        'port': 8001,
        'log_dir': LOG_ROOT / 'services/fastapi',
        'component': 'api'
    },
    'celery': {
        'log_dir': LOG_ROOT / 'services/celery',
        'component': 'worker'
    }
}
'''
        
        config_file = self.project_root / 'common/log_config.py'
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print(f"✅ 统一日志配置已创建: {config_file}")
    
    def create_connection_script(self):
        """创建连接测试脚本"""
        script_content = '''#!/usr/bin/env python3
"""
AnsFlow 统一日志连接测试脚本
测试所有日志存储系统的连接状态
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

try:
    import redis.asyncio as redis
    import aiomysql
    from elasticsearch import AsyncElasticsearch
except ImportError as e:
    print(f"❌ 缺少依赖: {e}")
    print("请运行: uv sync 安装所有依赖")
    sys.exit(1)

from common.log_config import REDIS_CONFIG, MYSQL_CONFIG, ELASTICSEARCH_CONFIG


async def test_redis_connection():
    """测试Redis连接"""
    print("🔍 测试Redis连接...")
    try:
        client = redis.Redis(**REDIS_CONFIG, decode_responses=True)
        
        # 测试ping
        pong = await client.ping()
        if pong:
            print("✅ Redis连接正常")
            
            # 测试Stream操作
            test_data = {
                'timestamp': datetime.now().isoformat(),
                'level': 'INFO',
                'service': 'test',
                'message': 'Redis连接测试'
            }
            
            msg_id = await client.xadd(REDIS_CONFIG['stream_name'], test_data)
            print(f"✅ Redis Stream写入成功: {msg_id}")
            
            # 读取测试
            messages = await client.xread({REDIS_CONFIG['stream_name']: '$'}, count=1, block=100)
            if messages:
                print("✅ Redis Stream读取正常")
            
            await client.aclose()
            return True
        else:
            print("❌ Redis ping失败")
            return False
            
    except Exception as e:
        print(f"❌ Redis连接失败: {e}")
        return False


async def test_mysql_connection():
    """测试MySQL连接"""
    print("🔍 测试MySQL连接...")
    try:
        pool = await aiomysql.create_pool(
            host=MYSQL_CONFIG['host'],
            port=MYSQL_CONFIG['port'],
            user=MYSQL_CONFIG['user'],
            password=MYSQL_CONFIG['password'],
            db=MYSQL_CONFIG['database'],
            minsize=1,
            maxsize=1
        )
        
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT 1")
                result = await cursor.fetchone()
                if result and result[0] == 1:
                    print("✅ MySQL连接正常")
                    
                    # 测试统一日志表是否存在
                    await cursor.execute("""
                        SELECT COUNT(*) FROM information_schema.tables 
                        WHERE table_schema = %s AND table_name = 'unified_logs'
                    """, (MYSQL_CONFIG['database'],))
                    
                    table_exists = await cursor.fetchone()
                    if table_exists and table_exists[0] > 0:
                        print("✅ 统一日志表已存在")
                    else:
                        print("⚠️  统一日志表不存在，需要创建")
                        return False
        
        pool.close()
        await pool.wait_closed()
        return True
        
    except Exception as e:
        print(f"❌ MySQL连接失败: {e}")
        return False


async def test_elasticsearch_connection():
    """测试ElasticSearch连接"""
    if not ELASTICSEARCH_CONFIG['enabled']:
        print("⏭️  ElasticSearch未启用，跳过测试")
        return True
        
    print("🔍 测试ElasticSearch连接...")
    try:
        es = AsyncElasticsearch(ELASTICSEARCH_CONFIG['hosts'])
        
        # 测试集群健康状态
        health = await es.cluster.health()
        if health['status'] in ['green', 'yellow']:
            print(f"✅ ElasticSearch连接正常 (状态: {health['status']})")
            
            # 测试索引操作
            test_doc = {
                'timestamp': datetime.now(),
                'level': 'INFO',
                'service': 'test',
                'message': 'ElasticSearch连接测试'
            }
            
            await es.index(
                index='ansflow-logs-test',
                body=test_doc
            )
            print("✅ ElasticSearch索引写入成功")
            
            await es.close()
            return True
        else:
            print(f"❌ ElasticSearch状态异常: {health['status']}")
            return False
            
    except Exception as e:
        print(f"❌ ElasticSearch连接失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("🚀 开始AnsFlow统一日志连接测试...")
    print("=" * 50)
    
    results = {
        'redis': await test_redis_connection(),
        'mysql': await test_mysql_connection(),
        'elasticsearch': await test_elasticsearch_connection()
    }
    
    print("=" * 50)
    print("📊 连接测试结果:")
    
    all_ok = True
    for service, status in results.items():
        icon = "✅" if status else "❌"
        print(f"  {icon} {service.upper()}: {'正常' if status else '异常'}")
        if not status:
            all_ok = False
    
    if all_ok:
        print("\\n🎉 所有连接测试通过！统一日志系统可以正常工作。")
        return 0
    else:
        print("\\n⚠️  部分连接测试失败，请检查相关服务状态。")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
'''
        
        script_file = self.project_root / 'scripts/test_log_connections.py'
        script_file.parent.mkdir(exist_ok=True)
        
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        # 设置执行权限
        os.chmod(script_file, 0o755)
        
        print(f"✅ 连接测试脚本已创建: {script_file}")
    
    def create_database_schema(self):
        """创建统一日志数据库架构"""
        schema_sql = '''-- AnsFlow 统一日志系统数据库架构

-- 创建统一日志表
CREATE TABLE IF NOT EXISTS unified_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    log_id VARCHAR(255) UNIQUE NOT NULL COMMENT '日志唯一标识',
    timestamp DATETIME(6) NOT NULL COMMENT '日志时间戳',
    level VARCHAR(20) NOT NULL COMMENT '日志级别',
    service VARCHAR(50) NOT NULL COMMENT '服务名称',
    component VARCHAR(100) COMMENT '组件名称',
    module VARCHAR(200) COMMENT '模块名称',
    message TEXT NOT NULL COMMENT '日志消息',
    execution_id INT COMMENT '执行ID',
    trace_id VARCHAR(100) COMMENT '链路追踪ID',
    extra_data JSON COMMENT '额外数据',
    created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    INDEX idx_timestamp (timestamp),
    INDEX idx_service_level (service, level),
    INDEX idx_execution_id (execution_id),
    INDEX idx_trace_id (trace_id),
    FULLTEXT KEY ft_message (message)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='统一日志存储表';

-- 创建日志统计表
CREATE TABLE IF NOT EXISTS log_statistics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    service VARCHAR(50) NOT NULL,
    level VARCHAR(20) NOT NULL,
    date_hour DATETIME NOT NULL COMMENT '按小时统计',
    count INT DEFAULT 0 COMMENT '日志数量',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_service_level_hour (service, level, date_hour),
    INDEX idx_date_hour (date_hour)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='日志统计表';

-- 创建日志配置表
CREATE TABLE IF NOT EXISTS log_configurations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    service VARCHAR(50) NOT NULL,
    log_level VARCHAR(20) NOT NULL DEFAULT 'INFO',
    enable_realtime BOOLEAN DEFAULT TRUE,
    enable_indexing BOOLEAN DEFAULT TRUE,
    retention_days INT DEFAULT 30,
    config_json JSON COMMENT '扩展配置',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_service (service)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='日志配置表';

-- 插入默认配置
INSERT IGNORE INTO log_configurations (service, log_level, enable_realtime, enable_indexing) VALUES
('django', 'INFO', TRUE, TRUE),
('fastapi', 'INFO', TRUE, TRUE),
('celery', 'INFO', TRUE, TRUE);
'''
        
        schema_file = self.project_root / 'scripts/unified_logs_schema.sql'
        with open(schema_file, 'w', encoding='utf-8') as f:
            f.write(schema_sql)
        
        print(f"✅ 数据库架构文件已创建: {schema_file}")
        print("   请执行以下命令创建数据库表:")
        print(f"   mysql -u root -p ansflow < {schema_file}")
    
    def generate_consistency_report(self):
        """生成数据一致性分析报告"""
        report_content = '''# AnsFlow 统一日志系统数据一致性分析报告

## 📊 当前架构概述

### 数据抓取对象分析

#### 1. 实时日志抓取对象 ✅
- **主要数据源**: Redis Stream (`ansflow:logs:stream` DB 5)  
- **辅助数据源**: 文件系统监控 (`/logs/services/*/`)
- **传输方式**: WebSocket实时推送
- **数据格式**: 标准化JSON格式
- **延迟**: < 100ms

#### 2. 历史查询抓取对象 ⚠️
- **主要数据源**: MySQL数据库 (PipelineExecution, StepExecution)
- **辅助数据源**: 本地日志文件
- **查询方式**: REST API + SQL查询  
- **数据格式**: 关系型数据 + 文本日志
- **一致性**: 存在数据同步延迟

#### 3. 日志索引抓取对象 🔄
- **当前状态**: 基础文件索引 + Redis时间戳索引
- **计划中**: ElasticSearch全文索引
- **索引方式**: 时间戳 + 执行ID + 服务名
- **搜索能力**: 基础关键词匹配

## ⚠️ 数据一致性问题

### 发现的问题

1. **数据源分散**
   - 实时日志 → Redis Stream
   - 历史查询 → MySQL + 文件系统  
   - 索引系统 → 多存储后端
   - 🔴 风险: 数据不同步，查询结果不一致

2. **格式不统一**
   - Redis: 标准化JSON结构
   - MySQL: 关系型数据结构
   - 文件: 混合格式 (JSON + 纯文本)
   - 🔴 风险: 解析逻辑复杂，容易出错

3. **时效性差异**
   - 实时日志: 毫秒级延迟
   - 历史存储: 可能有秒级或分钟级延迟
   - 索引更新: 异步处理，延迟不确定
   - 🔴 风险: 用户看到的数据不一致

### 具体表现

```bash
# 实时日志显示
WebSocket日志: 4条记录 (1 Django + 3 FastAPI)

# 历史查询可能显示
MySQL查询: 可能是0-4条记录 (取决于同步状态)

# 索引搜索可能显示  
ElasticSearch: 当前未启用
文件索引: 基于文件修改时间
```

## ✅ 解决方案

### 1. 统一连接器 (已实现)
- 📝 `common/unified_log_connector.py`
- 🔧 统一所有存储后端的访问接口
- 🎯 确保写入操作的原子性
- 📊 提供数据一致性验证

### 2. 数据同步策略
```python
async def sync_log_entry(self, log_entry: LogEntry):
    # 同步写入所有存储系统
    tasks = [
        self.write_realtime_log(log_entry),      # Redis Stream
        self.store_historical_log(log_entry),    # MySQL
        self.index_log(log_entry)                # ElasticSearch
    ]
    await asyncio.gather(*tasks, return_exceptions=True)
```

### 3. 一致性验证
```python
async def verify_data_consistency(self, log_id: str) -> Dict[str, bool]:
    # 检查所有存储系统中的数据
    return {
        'redis_stream': bool,      # 实时流
        'mysql_historical': bool,  # 历史数据  
        'elasticsearch_index': bool # 搜索索引
    }
```

## 🎯 推荐的统一架构

### 架构原则
1. **单一写入点**: 所有日志通过统一连接器写入
2. **多存储后端**: Redis(实时) + MySQL(历史) + ES(索引)
3. **一致性保证**: 同步写入 + 定期校验
4. **优雅降级**: 单个存储失败不影响其他存储

### 数据流向
```
日志产生 → 统一连接器 → {Redis Stream, MySQL, ElasticSearch}
                        ↓
                    前端查询接口 ← {实时日志, 历史查询, 全文搜索}
```

### 查询优先级
1. **实时监控**: Redis Stream (最高优先级)
2. **历史查询**: MySQL数据库 (结构化查询)
3. **全文搜索**: ElasticSearch (复杂搜索)
4. **文件系统**: 降级方案 (系统故障时)

## 📋 实施建议

### 立即实施 (优先级: 高)
- [ ] 部署统一连接器到生产环境
- [ ] 创建unified_logs表结构
- [ ] 修改现有日志写入代码使用统一接口

### 中期实施 (优先级: 中)
- [ ] 集成ElasticSearch索引系统
- [ ] 实现数据一致性监控面板
- [ ] 添加自动数据修复机制

### 长期优化 (优先级: 低)  
- [ ] 实现日志数据压缩和归档
- [ ] 添加日志数据分析和告警
- [ ] 支持多租户日志隔离

## 🔍 验证方法

### 连接测试
```bash
# 运行连接测试脚本
uv run scripts/test_log_connections.py
```

### 一致性验证
```bash  
# 写入测试日志
# 验证三个存储系统都包含相同数据
# 检查查询结果一致性
```

### 性能测试
```bash
# 测试并发写入性能
# 测试查询响应时间
# 测试故障恢复能力
```

---

**总结**: 当前系统存在数据一致性问题，但已有完整的解决方案。通过实施统一连接器和标准化数据格式，可以确保实时日志、历史查询和日志索引的数据完全一致。
'''
        
        report_file = self.project_root / 'docs/日志系统数据一致性分析报告.md'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"✅ 数据一致性分析报告已生成: {report_file}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AnsFlow统一日志系统UV连接管理器')
    parser.add_argument('action', choices=[
        'install', 'setup', 'test', 'schema', 'report', 'all'
    ], help='要执行的操作')
    parser.add_argument('--service', default='all', 
                       choices=['all', 'django', 'fastapi'],
                       help='目标服务')
    parser.add_argument('--root', default='/Users/creed/Workspace/OpenSource/ansflow',
                       help='项目根目录')
    
    args = parser.parse_args()
    
    connector = UVLogConnector(args.root)
    
    if args.action == 'install' or args.action == 'all':
        print("📦 安装日志系统依赖...")
        connector.install_dependencies(args.service)
    
    if args.action == 'setup' or args.action == 'all':
        print("🔧 设置统一日志配置...")
        connector.setup_unified_logging()
    
    if args.action == 'test' or args.action == 'all':
        print("🧪 创建连接测试脚本...")
        connector.create_connection_script()
    
    if args.action == 'schema' or args.action == 'all':
        print("🗄️  创建数据库架构...")
        connector.create_database_schema()
    
    if args.action == 'report' or args.action == 'all':
        print("📊 生成一致性分析报告...")
        connector.generate_consistency_report()
    
    if args.action == 'all':
        print("\n🎉 AnsFlow统一日志系统UV连接管理完成！")
        print("\n📋 下一步操作：")
        print("1. 运行数据库架构：mysql -u root -p ansflow < scripts/unified_logs_schema.sql")
        print("2. 测试连接状态：uv run scripts/test_log_connections.py")
        print("3. 查看分析报告：docs/日志系统数据一致性分析报告.md")


if __name__ == "__main__":
    main()
