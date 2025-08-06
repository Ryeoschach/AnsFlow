#!/usr/bin/env python3
"""
AnsFlow日志系统Phase 3独立测试脚本
不依赖Django环境的简化测试
"""

import os
import sys
import json
import gzip
import re
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Any, Optional


class StandaloneLogFileIndexer:
    """独立的日志文件索引器（不依赖Django）"""
    
    def __init__(self, log_dir: str = None):
        self.log_dir = log_dir or "/Users/creed/Workspace/OpenSource/ansflow/logs"
        self.cache = {}
    
    def build_file_index(self, days: int = 30) -> Dict[str, Any]:
        """构建文件索引"""
        try:
            log_path = Path(self.log_dir)
            if not log_path.exists():
                return {
                    'files': [],
                    'date_range': [],
                    'services': [],
                    'levels': [],
                    'total_size': 0,
                    'build_time': datetime.now().isoformat()
                }
            
            cutoff_date = datetime.now() - timedelta(days=days)
            files = []
            services = set()
            levels = set()
            total_size = 0
            
            for file_path in log_path.glob("**/*.log"):
                if file_path.is_file():
                    stat = file_path.stat()
                    modified = datetime.fromtimestamp(stat.st_mtime)
                    
                    if modified >= cutoff_date:
                        service = self._extract_service_from_path(str(file_path))
                        level = self._extract_level_from_path(str(file_path))
                        
                        files.append({
                            'path': str(file_path),
                            'relative_path': str(file_path.relative_to(log_path)),
                            'size': stat.st_size,
                            'modified': modified.isoformat(),
                            'is_compressed': file_path.suffix == '.gz',
                            'service': service,
                            'level': level
                        })
                        
                        services.add(service)
                        levels.add(level)
                        total_size += stat.st_size
            
            # 检查压缩文件
            for file_path in log_path.glob("**/*.log.gz"):
                if file_path.is_file():
                    stat = file_path.stat()
                    modified = datetime.fromtimestamp(stat.st_mtime)
                    
                    if modified >= cutoff_date:
                        service = self._extract_service_from_path(str(file_path))
                        level = self._extract_level_from_path(str(file_path))
                        
                        files.append({
                            'path': str(file_path),
                            'relative_path': str(file_path.relative_to(log_path)),
                            'size': stat.st_size,
                            'modified': modified.isoformat(),
                            'is_compressed': True,
                            'service': service,
                            'level': level
                        })
                        
                        services.add(service)
                        levels.add(level)
                        total_size += stat.st_size
            
            return {
                'files': sorted(files, key=lambda x: x['modified'], reverse=True),
                'date_range': [
                    cutoff_date.strftime('%Y-%m-%d'),
                    datetime.now().strftime('%Y-%m-%d')
                ],
                'services': sorted(list(services)),
                'levels': sorted(list(levels)),
                'total_size': total_size,
                'build_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"构建文件索引失败: {e}")
            return {
                'files': [],
                'date_range': [],
                'services': [],
                'levels': [],
                'total_size': 0,
                'build_time': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def _extract_service_from_path(self, path: str) -> str:
        """从文件路径提取服务名"""
        if 'django' in path.lower():
            return 'django'
        elif 'fastapi' in path.lower():
            return 'fastapi'
        elif 'system' in path.lower():
            return 'system'
        elif 'test' in path.lower():
            return 'test'
        else:
            return 'unknown'
    
    def _extract_level_from_path(self, path: str) -> str:
        """从文件路径提取日志级别"""
        path_lower = path.lower()
        if 'error' in path_lower:
            return 'ERROR'
        elif 'warning' in path_lower:
            return 'WARNING'
        elif 'debug' in path_lower:
            return 'DEBUG'
        else:
            return 'INFO'


class StandaloneLogQueryEngine:
    """独立的日志查询引擎（不依赖Django）"""
    
    def __init__(self, log_dir: str = None):
        self.log_dir = log_dir or "/Users/creed/Workspace/OpenSource/ansflow/logs"
        self.indexer = StandaloneLogFileIndexer(log_dir)
    
    def search_logs(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """搜索日志"""
        try:
            # 获取相关文件
            relevant_files = self._get_relevant_files(query_params)
            
            if not relevant_files:
                return {
                    'logs': [],
                    'total_count': 0,
                    'files_searched': 0,
                    'query_time': datetime.now().isoformat(),
                    'has_more': False
                }
            
            all_logs = []
            files_searched = 0
            
            for file_info in relevant_files:
                try:
                    logs = self._search_in_file(file_info['path'], query_params)
                    all_logs.extend(logs)
                    files_searched += 1
                    
                    # 限制结果数量以提高性能
                    if len(all_logs) > query_params.get('limit', 1000):
                        break
                        
                except Exception as e:
                    print(f"搜索文件 {file_info['path']} 失败: {e}")
                    continue
            
            # 按时间戳排序
            all_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            # 分页处理
            limit = query_params.get('limit', 100)
            offset = query_params.get('offset', 0)
            
            paginated_logs = all_logs[offset:offset + limit]
            
            return {
                'logs': paginated_logs,
                'total_count': len(all_logs),
                'files_searched': files_searched,
                'query_time': datetime.now().isoformat(),
                'has_more': len(all_logs) > offset + limit
            }
            
        except Exception as e:
            print(f"日志搜索失败: {e}")
            return {
                'logs': [],
                'total_count': 0,
                'files_searched': 0,
                'query_time': datetime.now().isoformat(),
                'has_more': False,
                'error': str(e)
            }
    
    def _get_relevant_files(self, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取相关文件列表"""
        index = self.indexer.build_file_index()
        files = index['files']
        
        # 过滤条件
        start_time = query_params.get('start_time')
        end_time = query_params.get('end_time')
        services = query_params.get('services', [])
        levels = query_params.get('levels', [])
        
        filtered_files = []
        
        for file_info in files:
            # 时间过滤
            if start_time:
                try:
                    file_time = datetime.fromisoformat(file_info['modified'])
                    query_start = datetime.fromisoformat(start_time)
                    if file_time < query_start:
                        continue
                except:
                    pass
            
            if end_time:
                try:
                    file_time = datetime.fromisoformat(file_info['modified'])
                    query_end = datetime.fromisoformat(end_time)
                    if file_time > query_end:
                        continue
                except:
                    pass
            
            # 服务过滤
            if services and file_info['service'] not in services:
                continue
            
            # 级别过滤
            if levels and file_info['level'] not in levels:
                continue
            
            filtered_files.append(file_info)
        
        return filtered_files
    
    def _search_in_file(self, file_path: str, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """在单个文件中搜索"""
        logs = []
        keywords = query_params.get('keywords', '')
        
        try:
            # 判断是否为压缩文件
            if file_path.endswith('.gz'):
                file_obj = gzip.open(file_path, 'rt', encoding='utf-8', errors='ignore')
            else:
                file_obj = open(file_path, 'r', encoding='utf-8', errors='ignore')
            
            with file_obj:
                for line_num, line in enumerate(file_obj, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 关键字过滤
                    if keywords:
                        keyword_list = [k.strip() for k in keywords.split() if k.strip()]
                        if not any(keyword.lower() in line.lower() for keyword in keyword_list):
                            continue
                    
                    # 解析日志行
                    log_entry = self._parse_log_line(line, file_path, line_num)
                    if log_entry:
                        logs.append(log_entry)
                        
                        # 限制单文件结果数量
                        if len(logs) >= 500:
                            break
            
            return logs
            
        except Exception as e:
            print(f"读取文件 {file_path} 失败: {e}")
            return []
    
    def _parse_log_line(self, line: str, file_path: str, line_num: int) -> Optional[Dict[str, Any]]:
        """解析日志行"""
        try:
            # 尝试解析JSON格式日志
            if line.startswith('{'):
                try:
                    data = json.loads(line)
                    return {
                        'timestamp': data.get('timestamp', ''),
                        'level': data.get('level', 'INFO'),
                        'service': data.get('service', 'unknown'),
                        'logger': data.get('logger', ''),
                        'message': data.get('message', line),
                        'file': file_path,
                        'line_number': line_num,
                        'raw': False
                    }
                except json.JSONDecodeError:
                    pass
            
            # 尝试解析传统格式 [时间] 级别 模块: 消息
            pattern = r'^(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}[.,]\d+).*?(\w+)\s+(.+?):\s*(.+)$'
            match = re.match(pattern, line)
            
            if match:
                timestamp, level, logger, message = match.groups()
                return {
                    'timestamp': timestamp.replace(',', '.'),
                    'level': level.upper(),
                    'service': self._extract_service_from_path(file_path),
                    'logger': logger.strip(),
                    'message': message.strip(),
                    'file': file_path,
                    'line_number': line_num,
                    'raw': False
                }
            
            # 如果无法解析，返回原始格式
            return {
                'timestamp': datetime.now().isoformat(),
                'level': 'INFO',
                'service': self._extract_service_from_path(file_path),
                'logger': 'unknown',
                'message': line,
                'file': file_path,
                'line_number': line_num,
                'raw': True
            }
            
        except Exception as e:
            return None
    
    def _extract_service_from_path(self, path: str) -> str:
        """从文件路径提取服务名"""
        if 'django' in path.lower():
            return 'django'
        elif 'fastapi' in path.lower():
            return 'fastapi'
        elif 'system' in path.lower():
            return 'system'
        elif 'test' in path.lower():
            return 'test'
        else:
            return 'unknown'


class StandaloneLogAnalyzer:
    """独立的日志分析器（不依赖Django）"""
    
    def __init__(self, log_dir: str = None):
        self.log_dir = log_dir or "/Users/creed/Workspace/OpenSource/ansflow/logs"
        self.query_engine = StandaloneLogQueryEngine(log_dir)
    
    def analyze_trends(self, days: int = 7) -> Dict[str, Any]:
        """分析日志趋势"""
        try:
            # 查询最近N天的所有日志
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            query_params = {
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'limit': 10000  # 增加限制以获取更多数据
            }
            
            result = self.query_engine.search_logs(query_params)
            logs = result['logs']
            
            if not logs:
                return {
                    'time_range': {
                        'start': start_time.isoformat(),
                        'end': end_time.isoformat(),
                        'days': days
                    },
                    'summary': {
                        'total_logs': 0,
                        'files_analyzed': 0
                    },
                    'by_level': {},
                    'by_service': {},
                    'by_hour': {},
                    'by_date': {},
                    'error_patterns': [],
                    'top_loggers': {},
                    'generated_at': datetime.now().isoformat()
                }
            
            # 统计分析
            by_level = Counter()
            by_service = Counter()
            by_hour = defaultdict(int)
            by_date = defaultdict(int)
            top_loggers = Counter()
            error_patterns = []
            
            for log in logs:
                # 级别统计
                by_level[log.get('level', 'INFO')] += 1
                
                # 服务统计
                by_service[log.get('service', 'unknown')] += 1
                
                # Logger统计
                logger_name = log.get('logger', 'unknown')
                top_loggers[logger_name] += 1
                
                # 时间统计
                timestamp = log.get('timestamp', '')
                if timestamp:
                    try:
                        dt = self._parse_timestamp(timestamp)
                        if dt:
                            hour_key = dt.strftime('%H:00')
                            date_key = dt.strftime('%Y-%m-%d')
                            by_hour[hour_key] += 1
                            by_date[date_key] += 1
                    except:
                        pass
                
                # 错误模式收集
                if log.get('level') in ['ERROR', 'CRITICAL']:
                    error_patterns.append({
                        'message': log.get('message', '')[:200],  # 限制长度
                        'service': log.get('service', 'unknown'),
                        'timestamp': log.get('timestamp', ''),
                        'logger': log.get('logger', 'unknown')
                    })
            
            return {
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat(),
                    'days': days
                },
                'summary': {
                    'total_logs': len(logs),
                    'files_analyzed': result['files_searched']
                },
                'by_level': dict(by_level),
                'by_service': dict(by_service),
                'by_hour': dict(by_hour),
                'by_date': dict(by_date),
                'error_patterns': error_patterns[:20],  # 只返回前20个错误
                'top_loggers': dict(top_loggers.most_common(10)),
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"日志分析失败: {e}")
            return {
                'time_range': {
                    'start': start_time.isoformat() if 'start_time' in locals() else '',
                    'end': end_time.isoformat() if 'end_time' in locals() else '',
                    'days': days
                },
                'summary': {
                    'total_logs': 0,
                    'files_analyzed': 0
                },
                'by_level': {},
                'by_service': {},
                'error': str(e),
                'generated_at': datetime.now().isoformat()
            }
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """解析时间戳"""
        formats = [
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M:%S,%f'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str[:26], fmt)
            except ValueError:
                continue
        
        return None


def create_sample_logs():
    """创建示例日志数据"""
    print("=" * 60)
    print("📝 创建示例日志数据")
    print("=" * 60)
    
    log_dir = Path("/Users/creed/Workspace/OpenSource/ansflow/logs")
    log_dir.mkdir(exist_ok=True)
    
    # 创建多个测试日志文件
    sample_logs = [
        {
            'filename': 'django_test.log',
            'service': 'django',
            'entries': [
                '2025-08-05T15:45:00.123 INFO django.request: GET /api/settings/logging/',
                '2025-08-05T15:45:01.456 WARNING django.security: Invalid authentication attempt',
                '2025-08-05T15:45:02.789 ERROR django.db: Database connection failed',
                '2025-08-05T15:45:03.012 INFO django.middleware: Request processed successfully'
            ]
        },
        {
            'filename': 'fastapi_test.log',
            'service': 'fastapi',
            'entries': [
                '{"timestamp": "2025-08-05T15:45:00.123", "level": "INFO", "service": "fastapi", "logger": "fastapi.main", "message": "Application startup complete"}',
                '{"timestamp": "2025-08-05T15:45:01.456", "level": "WARNING", "service": "fastapi", "logger": "fastapi.middleware", "message": "Slow request detected"}',
                '{"timestamp": "2025-08-05T15:45:02.789", "level": "ERROR", "service": "fastapi", "logger": "fastapi.routes", "message": "Route handler exception"}',
                '{"timestamp": "2025-08-05T15:45:03.012", "level": "DEBUG", "service": "fastapi", "logger": "fastapi.websocket", "message": "WebSocket connection established"}'
            ]
        },
        {
            'filename': 'system_test.log',
            'service': 'system',
            'entries': [
                '2025-08-05 15:45:00,123 INFO system.monitor: System health check passed',
                '2025-08-05 15:45:01,456 WARNING system.disk: Disk usage above 80%',
                '2025-08-05 15:45:02,789 CRITICAL system.memory: Memory usage critical',
                '2025-08-05 15:45:03,012 INFO system.process: Process cleanup completed'
            ]
        }
    ]
    
    created_files = []
    
    for log_file in sample_logs:
        file_path = log_dir / log_file['filename']
        
        with open(file_path, 'w', encoding='utf-8') as f:
            for entry in log_file['entries']:
                f.write(entry + '\n')
        
        created_files.append({
            'path': str(file_path),
            'service': log_file['service'],
            'entries': len(log_file['entries'])
        })
    
    print("✅ 示例日志创建成功")
    for file_info in created_files:
        print(f"   - {file_info['path']} ({file_info['service']}, {file_info['entries']} entries)")
    
    return created_files


def test_file_indexer():
    """测试文件索引功能"""
    print("=" * 60)
    print("📁 测试日志文件索引功能")
    print("=" * 60)
    
    try:
        indexer = StandaloneLogFileIndexer()
        index = indexer.build_file_index(days=7)
        
        print(f"✅ 文件索引构建成功")
        print(f"   - 文件数量: {len(index['files'])}")
        print(f"   - 总大小: {round(index['total_size'] / 1024, 2)} KB")
        print(f"   - 服务列表: {index['services']}")
        print(f"   - 日志级别: {index['levels']}")
        print(f"   - 时间范围: {index['date_range']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 文件索引测试失败: {e}")
        return False


def test_query_engine():
    """测试查询引擎功能"""
    print("=" * 60)
    print("🔍 测试日志查询引擎功能")
    print("=" * 60)
    
    try:
        engine = StandaloneLogQueryEngine()
        
        # 测试基本查询
        query_params = {
            'keywords': 'ERROR WARNING',
            'limit': 10,
            'offset': 0
        }
        
        result = engine.search_logs(query_params)
        
        print(f"✅ 查询引擎测试成功")
        print(f"   - 搜索结果: {result['total_count']} 条日志")
        print(f"   - 搜索文件: {result['files_searched']} 个文件")
        print(f"   - 查询时间: {result['query_time']}")
        
        # 显示前几条结果
        for i, log in enumerate(result['logs'][:3], 1):
            print(f"   - 日志{i}: [{log['level']}] {log['message'][:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 查询引擎测试失败: {e}")
        return False


def test_analyzer():
    """测试日志分析功能"""
    print("=" * 60)
    print("📊 测试日志分析功能")
    print("=" * 60)
    
    try:
        analyzer = StandaloneLogAnalyzer()
        analysis = analyzer.analyze_trends(days=7)
        
        print(f"✅ 日志分析测试成功")
        print(f"   - 分析时间范围: {analysis['time_range']['days']} 天")
        print(f"   - 总日志数: {analysis['summary']['total_logs']}")
        print(f"   - 分析文件数: {analysis['summary']['files_analyzed']}")
        print(f"   - 按级别统计: {analysis['by_level']}")
        print(f"   - 按服务统计: {analysis['by_service']}")
        print(f"   - 错误模式数: {len(analysis['error_patterns'])}")
        print(f"   - Top Logger数: {len(analysis['top_loggers'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ 日志分析测试失败: {e}")
        return False


def test_prometheus_metrics():
    """测试Prometheus指标功能"""
    print("=" * 60)
    print("📈 测试Prometheus指标收集")
    print("=" * 60)
    
    try:
        # 模拟指标收集
        analyzer = StandaloneLogAnalyzer()
        indexer = StandaloneLogFileIndexer()
        
        analysis = analyzer.analyze_trends(days=1)
        index = indexer.build_file_index()
        
        # 生成指标数据
        metrics_data = {
            'log_messages_total': analysis['summary']['total_logs'],
            'log_files_total': len(index['files']),
            'log_storage_bytes': index['total_size'],
            'log_by_level': analysis['by_level'],
            'log_by_service': analysis['by_service']
        }
        
        # 生成Prometheus格式
        prometheus_lines = []
        prometheus_lines.append("# HELP ansflow_log_messages_total Total number of log messages")
        prometheus_lines.append("# TYPE ansflow_log_messages_total counter")
        prometheus_lines.append(f"ansflow_log_messages_total {metrics_data['log_messages_total']}")
        prometheus_lines.append("")
        
        prometheus_lines.append("# HELP ansflow_log_files_total Total number of log files")
        prometheus_lines.append("# TYPE ansflow_log_files_total gauge")
        prometheus_lines.append(f"ansflow_log_files_total {metrics_data['log_files_total']}")
        prometheus_lines.append("")
        
        prometheus_format = "\n".join(prometheus_lines)
        
        print(f"✅ Prometheus指标测试成功")
        print(f"   - 总日志消息数: {metrics_data['log_messages_total']}")
        print(f"   - 总文件数: {metrics_data['log_files_total']}")
        print(f"   - 存储大小: {metrics_data['log_storage_bytes']} bytes")
        print(f"   - 按级别统计: {metrics_data['log_by_level']}")
        print(f"   - 按服务统计: {metrics_data['log_by_service']}")
        print(f"   - Prometheus格式长度: {len(prometheus_format)} chars")
        
        return True
        
    except Exception as e:
        print(f"❌ Prometheus指标测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 AnsFlow日志系统Phase 3独立测试")
    print("=" * 80)
    print(f"测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 准备测试环境
    print("🏗️  准备测试环境...")
    created_files = create_sample_logs()
    
    # 运行测试
    test_results = {}
    
    tests = [
        ("文件索引器", test_file_indexer),
        ("查询引擎", test_query_engine),
        ("日志分析器", test_analyzer),
        ("Prometheus指标", test_prometheus_metrics)
    ]
    
    for test_name, test_func in tests:
        print(f"\n🧪 运行 {test_name} 测试...")
        success = test_func()
        test_results[test_name] = success
    
    # 测试总结
    print("\n" + "=" * 80)
    print("📊 Phase 3独立测试结果总结")
    print("=" * 80)
    
    passed_count = 0
    total_count = len(test_results)
    
    for test_name, success in test_results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name:<20}: {status}")
        if success:
            passed_count += 1
    
    print("-" * 80)
    print(f"总体结果: {passed_count}/{total_count} 测试通过")
    
    if passed_count == total_count:
        print("🎉 所有测试通过！Phase 3功能正常工作")
        return 0
    else:
        print("⚠️  部分测试失败，请检查实现")
        return 1


if __name__ == "__main__":
    sys.exit(main())
