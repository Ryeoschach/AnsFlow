"""
AnsFlow日志管理API视图 - Phase 3历史分析功能
提供日志查询、历史分析、性能统计等功能
"""
import os
import json
import gzip
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
import redis
import re
from collections import defaultdict, Counter
import statistics

# Prometheus 指标相关导入（如果可用）
try:
    from prometheus_client import Counter as PrometheusCounter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    PrometheusCounter = Histogram = Gauge = None


logger = logging.getLogger(__name__)


class LogFileIndexer:
    """日志文件索引器 - Phase 3核心功能"""
    
    def __init__(self, log_dir: str = None):
        self.log_dir = Path(log_dir or getattr(settings, 'LOG_DIR', '/Users/creed/Workspace/OpenSource/ansflow/logs'))
        self.cache_timeout = 300  # 5分钟缓存
        self.logger = logging.getLogger(__name__)
        
    def build_file_index(self, days: int = 30) -> Dict[str, Any]:
        """构建日志文件索引"""
        cache_key = f"log_file_index_{days}"
        cached_index = cache.get(cache_key)
        if cached_index:
            return cached_index
            
        index = {
            'files': [],
            'date_range': [],
            'services': set(),
            'levels': set(),
            'total_size': 0,
            'build_time': datetime.now().isoformat()
        }
        
        try:
            # 扫描日志目录
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for log_file in self.log_dir.rglob('*.log*'):
                if not log_file.is_file():
                    continue
                    
                try:
                    file_stat = log_file.stat()
                    file_time = datetime.fromtimestamp(file_stat.st_mtime)
                    
                    if file_time < cutoff_date:
                        continue
                        
                    file_info = {
                        'path': str(log_file),
                        'relative_path': str(log_file.relative_to(self.log_dir)),
                        'size': file_stat.st_size,
                        'modified': file_time.isoformat(),
                        'is_compressed': log_file.suffix == '.gz',
                        'service': self._extract_service_from_path(log_file),
                        'level': self._extract_level_from_path(log_file)
                    }
                    
                    index['files'].append(file_info)
                    index['services'].add(file_info['service'])
                    index['levels'].add(file_info['level'])
                    index['total_size'] += file_stat.st_size
                    
                except Exception as e:
                    self.logger.warning(f"处理文件 {log_file} 时出错: {e}")
                    
            # 转换集合为列表以便序列化
            index['services'] = list(index['services'])
            index['levels'] = list(index['levels'])
            
            # 按时间排序文件
            index['files'].sort(key=lambda x: x['modified'], reverse=True)
            
            # 计算日期范围
            if index['files']:
                dates = [f['modified'] for f in index['files']]
                index['date_range'] = [min(dates), max(dates)]
                
            # 缓存索引
            cache.set(cache_key, index, self.cache_timeout)
            
            self.logger.info(f"构建日志文件索引完成: {len(index['files'])} 个文件, "
                           f"总大小 {index['total_size'] / 1024 / 1024:.2f}MB")
            
        except Exception as e:
            self.logger.error(f"构建日志文件索引失败: {e}")
            
        return index
    
    def _extract_service_from_path(self, file_path: Path) -> str:
        """从文件路径提取服务名"""
        path_parts = file_path.parts
        if 'django' in str(file_path):
            return 'django'
        elif 'fastapi' in str(file_path):
            return 'fastapi'
        elif len(path_parts) > 1:
            return path_parts[-2]  # 上级目录名
        return 'system'
    
    def _extract_level_from_path(self, file_path: Path) -> str:
        """从文件路径提取日志级别"""
        filename = file_path.stem
        levels = ['ERROR', 'WARNING', 'INFO', 'DEBUG']
        for level in levels:
            if level.lower() in filename.lower():
                return level
        return 'INFO'


class LogQueryEngine:
    """日志查询引擎 - Phase 3核心功能"""
    
    def __init__(self):
        self.indexer = LogFileIndexer()
        self.logger = logging.getLogger(__name__)
    
    def search_logs(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """搜索日志 - 主要查询接口"""
        start_time = query_params.get('start_time')
        end_time = query_params.get('end_time')
        levels = query_params.get('levels', [])
        services = query_params.get('services', [])
        keywords = query_params.get('keywords', '')
        limit = min(int(query_params.get('limit', 100)), 1000)
        offset = int(query_params.get('offset', 0))
        
        # 构建缓存键
        cache_key = f"log_search_{hash(json.dumps(query_params, sort_keys=True))}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            # 获取相关文件
            relevant_files = self._get_relevant_files(start_time, end_time, services)
            
            # 搜索日志条目
            results = []
            total_count = 0
            
            for file_info in relevant_files[:10]:  # 限制搜索文件数量
                file_results = self._search_in_file(
                    file_info, keywords, levels, start_time, end_time
                )
                results.extend(file_results)
                
            # 排序和分页
            results.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            total_count = len(results)
            paginated_results = results[offset:offset + limit]
            
            result = {
                'logs': paginated_results,
                'total_count': total_count,
                'files_searched': len(relevant_files),
                'query_time': datetime.now().isoformat(),
                'has_more': offset + len(paginated_results) < total_count
            }
            
            # 缓存结果
            cache.set(cache_key, result, 60)  # 1分钟缓存
            
            return result
            
        except Exception as e:
            self.logger.error(f"日志搜索失败: {e}")
            return {
                'logs': [],
                'total_count': 0,
                'error': str(e),
                'query_time': datetime.now().isoformat()
            }
    
    def _get_relevant_files(self, start_time: str, end_time: str, services: List[str]) -> List[Dict]:
        """获取相关的日志文件"""
        index = self.indexer.build_file_index()
        relevant_files = []
        
        for file_info in index['files']:
            # 服务过滤
            if services and file_info['service'] not in services:
                continue
                
            # 时间过滤（简单实现）
            if start_time and file_info['modified'] < start_time:
                continue
            if end_time and file_info['modified'] > end_time:
                continue
                
            relevant_files.append(file_info)
            
        return relevant_files
    
    def _search_in_file(self, file_info: Dict, keywords: str, levels: List[str], 
                       start_time: str, end_time: str) -> List[Dict]:
        """在单个文件中搜索"""
        results = []
        file_path = Path(file_info['path'])
        
        try:
            # 打开文件（支持压缩文件）
            if file_info.get('is_compressed'):
                file_handle = gzip.open(file_path, 'rt', encoding='utf-8', errors='ignore')
            else:
                file_handle = open(file_path, 'r', encoding='utf-8', errors='ignore')
            
            with file_handle:
                for line_num, line in enumerate(file_handle, 1):
                    if len(results) >= 200:  # 限制单文件结果数量
                        break
                        
                    try:
                        # 尝试解析JSON格式的日志
                        log_entry = self._parse_log_line(line, line_num, file_info)
                        if not log_entry:
                            continue
                            
                        # 级别过滤
                        if levels and log_entry.get('level') not in levels:
                            continue
                            
                        # 关键字过滤
                        if keywords and not self._match_keywords(log_entry, keywords):
                            continue
                            
                        # 时间过滤
                        if not self._match_time_range(log_entry, start_time, end_time):
                            continue
                            
                        results.append(log_entry)
                        
                    except Exception as e:
                        # 跳过解析失败的行
                        continue
                        
        except Exception as e:
            self.logger.warning(f"读取文件 {file_path} 失败: {e}")
            
        return results
    
    def _parse_log_line(self, line: str, line_num: int, file_info: Dict) -> Optional[Dict]:
        """解析日志行"""
        line = line.strip()
        if not line:
            return None
            
        try:
            # 尝试解析JSON格式
            if line.startswith('{') and line.endswith('}'):
                log_data = json.loads(line)
                log_data['file'] = file_info['relative_path']
                log_data['line_number'] = line_num
                return log_data
        except json.JSONDecodeError:
            pass
            
        # 解析传统格式
        # 示例: "2025-08-05 14:30:25,123 - logger_name - INFO - message"
        pattern = r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-\s*(.+?)\s*-\s*(ERROR|WARNING|INFO|DEBUG)\s*-\s*(.+)'
        match = re.match(pattern, line)
        
        if match:
            timestamp, logger_name, level, message = match.groups()
            return {
                'timestamp': timestamp,
                'logger': logger_name,
                'level': level,
                'message': message,
                'file': file_info['relative_path'],
                'line_number': line_num,
                'service': file_info['service']
            }
            
        # 如果都无法解析，返回原始行
        return {
            'timestamp': file_info.get('modified', ''),
            'level': 'INFO',
            'message': line,
            'file': file_info['relative_path'],
            'line_number': line_num,
            'service': file_info['service'],
            'raw': True
        }
    
    def _match_keywords(self, log_entry: Dict, keywords: str) -> bool:
        """关键字匹配"""
        if not keywords:
            return True
            
        # 支持多个关键字，用空格分隔
        keyword_list = keywords.lower().split()
        text_to_search = ' '.join([
            str(log_entry.get('message', '')),
            str(log_entry.get('logger', '')),
            str(log_entry.get('service', ''))
        ]).lower()
        
        # 所有关键字都要匹配（AND逻辑）
        return all(keyword in text_to_search for keyword in keyword_list)
    
    def _match_time_range(self, log_entry: Dict, start_time: str, end_time: str) -> bool:
        """时间范围匹配"""
        if not start_time and not end_time:
            return True
            
        entry_time = log_entry.get('timestamp', '')
        if not entry_time:
            return True
            
        try:
            # 简单的字符串比较（假设时间格式一致）
            if start_time and entry_time < start_time:
                return False
            if end_time and entry_time > end_time:
                return False
            return True
        except:
            return True


class LogAnalyzer:
    """日志分析器 - Phase 3分析功能"""
    
    def __init__(self):
        self.query_engine = LogQueryEngine()
        self.logger = logging.getLogger(__name__)
    
    def analyze_trends(self, days: int = 7) -> Dict[str, Any]:
        """分析日志趋势"""
        cache_key = f"log_trends_{days}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            # 获取最近N天的日志统计
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            query_params = {
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'limit': 10000
            }
            
            logs_result = self.query_engine.search_logs(query_params)
            logs = logs_result.get('logs', [])
            
            # 分析数据
            analysis = {
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat(),
                    'days': days
                },
                'summary': {
                    'total_logs': len(logs),
                    'files_analyzed': logs_result.get('files_searched', 0)
                },
                'by_level': Counter(),
                'by_service': Counter(),
                'by_hour': defaultdict(int),
                'by_date': defaultdict(int),
                'error_patterns': [],
                'top_loggers': Counter(),
                'generated_at': datetime.now().isoformat()
            }
            
            # 统计分析
            for log in logs:
                level = log.get('level', 'INFO')
                service = log.get('service', 'unknown')
                logger_name = log.get('logger', 'unknown')
                timestamp = log.get('timestamp', '')
                
                analysis['by_level'][level] += 1
                analysis['by_service'][service] += 1
                analysis['top_loggers'][logger_name] += 1
                
                # 时间分析
                if timestamp:
                    try:
                        dt = self._parse_timestamp(timestamp)
                        if dt:
                            date_key = dt.strftime('%Y-%m-%d') 
                            hour_key = dt.strftime('%H')
                            analysis['by_date'][date_key] += 1
                            analysis['by_hour'][hour_key] += 1
                    except:
                        pass
                        
                # 错误模式分析
                if level in ['ERROR', 'CRITICAL']:
                    message = log.get('message', '')
                    if message:
                        analysis['error_patterns'].append({
                            'message': message[:200],  # 截断长消息
                            'service': service,
                            'timestamp': timestamp,
                            'logger': logger_name
                        })
            
            # 转换Counter为字典
            analysis['by_level'] = dict(analysis['by_level'])
            analysis['by_service'] = dict(analysis['by_service'])
            analysis['top_loggers'] = dict(analysis['top_loggers'].most_common(10))
            analysis['by_hour'] = dict(analysis['by_hour'])
            analysis['by_date'] = dict(analysis['by_date'])
            
            # 限制错误模式数量
            analysis['error_patterns'] = analysis['error_patterns'][:50]
            
            # 缓存结果
            cache.set(cache_key, analysis, 300)  # 5分钟缓存
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"日志趋势分析失败: {e}")
            return {
                'error': str(e),
                'generated_at': datetime.now().isoformat()
            }
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """解析时间戳"""
        formats = [
            '%Y-%m-%d %H:%M:%S,%f',
            '%Y-%m-%d %H:%M:%S.%f', 
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str[:26], fmt)
            except ValueError:
                continue
        return None


# API视图类
class LogManagementAPIView(APIView):
    """日志管理API - Phase 3主要接口"""
    permission_classes = [IsAuthenticated]
    
    def __init__(self):
        super().__init__()
        self.indexer = LogFileIndexer()
        self.query_engine = LogQueryEngine()
        self.analyzer = LogAnalyzer()


class LogFileIndexView(LogManagementAPIView):
    """日志文件索引API"""
    
    @method_decorator(cache_page(300))
    def get(self, request):
        """获取日志文件索引"""
        days = int(request.GET.get('days', 30))
        index = self.indexer.build_file_index(days)
        
        return Response({
            'success': True,
            'data': index
        })


class LogSearchView(LogManagementAPIView):
    """日志搜索API"""
    
    def post(self, request):
        """搜索日志"""
        query_params = request.data
        
        # 参数验证
        if not isinstance(query_params, dict):
            return Response({
                'success': False,
                'error': '无效的查询参数'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        results = self.query_engine.search_logs(query_params)
        
        return Response({
            'success': True,
            'data': results
        })


class LogAnalysisView(LogManagementAPIView):
    """日志分析API"""
    
    @method_decorator(cache_page(300))
    def get(self, request):
        """获取日志分析报告"""
        days = int(request.GET.get('days', 7))
        analysis = self.analyzer.analyze_trends(days)
        
        return Response({
            'success': True,
            'data': analysis
        })


class LogExportView(LogManagementAPIView):
    """日志导出API"""
    
    def post(self, request):
        """导出日志"""
        query_params = request.data
        export_format = query_params.get('format', 'json')
        
        # 获取日志数据
        results = self.query_engine.search_logs(query_params)
        logs = results.get('logs', [])
        
        if export_format == 'csv':
            return self._export_csv(logs)
        elif export_format == 'txt':
            return self._export_txt(logs)
        else:
            return self._export_json(logs)
    
    def _export_json(self, logs: List[Dict]) -> HttpResponse:
        """导出JSON格式"""
        response = HttpResponse(
            json.dumps(logs, indent=2, ensure_ascii=False),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
        return response
    
    def _export_csv(self, logs: List[Dict]) -> HttpResponse:
        """导出CSV格式"""
        import csv
        from io import StringIO
        
        output = StringIO()
        if logs:
            fieldnames = ['timestamp', 'level', 'service', 'logger', 'message']
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for log in logs:
                writer.writerow({
                    'timestamp': log.get('timestamp', ''),
                    'level': log.get('level', ''),
                    'service': log.get('service', ''),
                    'logger': log.get('logger', ''),
                    'message': log.get('message', '')
                })
        
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        return response
    
    def _export_txt(self, logs: List[Dict]) -> HttpResponse:
        """导出TXT格式"""
        lines = []
        for log in logs:
            line = f"[{log.get('timestamp', '')}] [{log.get('level', '')}] [{log.get('service', '')}] {log.get('message', '')}"
            lines.append(line)
        
        response = HttpResponse('\n'.join(lines), content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt"'
        return response


# 简化的API函数视图
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def log_config_view(request):
    """获取或保存日志配置信息"""
    if request.method == 'GET':
        try:
            # 从数据库加载已保存的配置
            from settings_management.models import GlobalConfig
            
            # 默认配置
            config = {
                'level': 'INFO',
                'enableRedis': False,
                'redisConfig': {
                    'host': 'localhost',
                    'port': 6379,
                    'db': 0
                },
                'fileRotation': {
                    'when': 'midnight',
                    'interval': 1,
                    'backupCount': 30
                },
                'services': {
                    'django': True,
                    'fastapi': True
                }
            }
            
            # 从数据库读取配置
            try:
                # 读取日志级别
                level_config = GlobalConfig.objects.get(key='LOGGING_LEVEL')
                config['level'] = level_config.value
            except GlobalConfig.DoesNotExist:
                pass
            
            try:
                # 读取Redis启用状态
                redis_enable_config = GlobalConfig.objects.get(key='LOGGING_ENABLE_REDIS')
                config['enableRedis'] = redis_enable_config.value.lower() == 'true'
            except GlobalConfig.DoesNotExist:
                pass
            
            try:
                # 读取Redis主机
                redis_host_config = GlobalConfig.objects.get(key='REDIS_HOST')
                config['redisConfig']['host'] = redis_host_config.value
            except GlobalConfig.DoesNotExist:
                pass
            
            try:
                # 读取Redis端口
                redis_port_config = GlobalConfig.objects.get(key='REDIS_PORT')
                config['redisConfig']['port'] = int(redis_port_config.value)
            except (GlobalConfig.DoesNotExist, ValueError):
                pass
            
            try:
                # 读取Redis数据库
                redis_db_config = GlobalConfig.objects.get(key='REDIS_DB')
                config['redisConfig']['db'] = int(redis_db_config.value)
            except (GlobalConfig.DoesNotExist, ValueError):
                pass
            
            try:
                # 读取日志轮转配置
                rotation_when_config = GlobalConfig.objects.get(key='LOG_ROTATION_WHEN')
                config['fileRotation']['when'] = rotation_when_config.value
            except GlobalConfig.DoesNotExist:
                pass
            
            try:
                rotation_interval_config = GlobalConfig.objects.get(key='LOG_ROTATION_INTERVAL')
                config['fileRotation']['interval'] = int(rotation_interval_config.value)
            except (GlobalConfig.DoesNotExist, ValueError):
                pass
            
            try:
                rotation_backup_config = GlobalConfig.objects.get(key='LOG_ROTATION_BACKUP_COUNT')
                config['fileRotation']['backupCount'] = int(rotation_backup_config.value)
            except (GlobalConfig.DoesNotExist, ValueError):
                pass
            
            logger.info(f"读取到的日志配置: 级别={config['level']}, Redis启用={config['enableRedis']}, Redis数据库={config['redisConfig']['db']}")
            
            return Response({
                'success': True,
                'data': config
            })
            
        except Exception as e:
            logger.error(f"获取日志配置失败: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        try:
            config_data = request.data
            logger.info(f"接收到日志配置保存请求: {config_data}")
            
            # 验证必要字段
            if 'level' not in config_data:
                return Response({
                    'success': False,
                    'error': '缺少必要的日志级别配置'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 验证日志级别
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            if config_data['level'] not in valid_levels:
                return Response({
                    'success': False,
                    'error': f'无效的日志级别: {config_data["level"]}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 验证Redis配置
            if 'redisConfig' in config_data:
                redis_config = config_data['redisConfig']
                if 'db' in redis_config:
                    try:
                        db_num = int(redis_config['db'])
                        if not (0 <= db_num <= 15):
                            return Response({
                                'success': False,
                                'error': 'Redis数据库编号必须在0-15之间'
                            }, status=status.HTTP_400_BAD_REQUEST)
                    except (ValueError, TypeError):
                        return Response({
                            'success': False,
                            'error': 'Redis数据库编号必须是数字'
                        }, status=status.HTTP_400_BAD_REQUEST)
            
            # 实际保存配置到数据库
            from settings_management.models import GlobalConfig
            
            # 保存或更新日志级别配置
            GlobalConfig.objects.update_or_create(
                key='LOGGING_LEVEL',
                defaults={
                    'value': config_data['level'],
                    'type': 'system',
                    'description': '系统日志级别',
                    'created_by': request.user
                }
            )
            
            # 保存Redis启用状态
            if 'enableRedis' in config_data:
                GlobalConfig.objects.update_or_create(
                    key='LOGGING_ENABLE_REDIS',
                    defaults={
                        'value': str(config_data['enableRedis']).lower(),
                        'type': 'system',
                        'description': '是否启用Redis日志',
                        'created_by': request.user
                    }
                )
            
            # 保存Redis配置
            if 'redisConfig' in config_data:
                redis_config = config_data['redisConfig']
                
                # 保存Redis主机
                if 'host' in redis_config:
                    GlobalConfig.objects.update_or_create(
                        key='REDIS_HOST',
                        defaults={
                            'value': redis_config['host'],
                            'type': 'system',
                            'description': 'Redis服务器地址',
                            'created_by': request.user
                        }
                    )
                
                # 保存Redis端口
                if 'port' in redis_config:
                    GlobalConfig.objects.update_or_create(
                        key='REDIS_PORT',
                        defaults={
                            'value': str(redis_config['port']),
                            'type': 'system',
                            'description': 'Redis服务器端口',
                            'created_by': request.user
                        }
                    )
                
                # 保存Redis数据库编号
                if 'db' in redis_config:
                    GlobalConfig.objects.update_or_create(
                        key='REDIS_DB',
                        defaults={
                            'value': str(redis_config['db']),
                            'type': 'system',
                            'description': 'Redis数据库编号',
                            'created_by': request.user
                        }
                    )
            
            # 保存文件轮转配置
            if 'fileRotation' in config_data:
                rotation_config = config_data['fileRotation']
                
                if 'when' in rotation_config:
                    GlobalConfig.objects.update_or_create(
                        key='LOG_ROTATION_WHEN',
                        defaults={
                            'value': rotation_config['when'],
                            'type': 'system',
                            'description': '日志轮转时间',
                            'created_by': request.user
                        }
                    )
                
                if 'interval' in rotation_config:
                    GlobalConfig.objects.update_or_create(
                        key='LOG_ROTATION_INTERVAL',
                        defaults={
                            'value': str(rotation_config['interval']),
                            'type': 'system',
                            'description': '日志轮转间隔',
                            'created_by': request.user
                        }
                    )
                
                if 'backupCount' in rotation_config:
                    GlobalConfig.objects.update_or_create(
                        key='LOG_ROTATION_BACKUP_COUNT',
                        defaults={
                            'value': str(rotation_config['backupCount']),
                            'type': 'system',
                            'description': '日志备份文件数量',
                            'created_by': request.user
                        }
                    )
            
            logger.info(f"日志配置保存成功: 级别={config_data['level']}, Redis启用={config_data.get('enableRedis', False)}, Redis数据库={config_data.get('redisConfig', {}).get('db', 'N/A')}")
            
            return Response({
                'success': True,
                'message': '日志配置保存成功',
                'data': config_data
            })
            
        except Exception as e:
            logger.error(f"保存日志配置失败: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def log_stats_view(request):
    """获取日志统计信息"""
    try:
        indexer = LogFileIndexer()
        index = indexer.build_file_index()
        
        stats = {
            'total_files': len(index['files']),
            'total_size_mb': round(index['total_size'] / 1024 / 1024, 2),
            'services': index['services'],
            'levels': index['levels'],
            'date_range': index['date_range'],
            'last_updated': index['build_time']
        }
        
        return Response({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        logger.error(f"获取日志统计失败: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===========================================
# Phase 3: Prometheus指标集成
# ===========================================

class PrometheusMetricsView(APIView):
    """
    Prometheus指标暴露视图
    提供标准Prometheus格式的指标数据
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """返回Prometheus格式的指标"""
        if not PROMETHEUS_AVAILABLE:
            return HttpResponse(
                "# Prometheus client not available\n",
                content_type='text/plain'
            )
        
        try:
            # 收集日志指标
            metrics_data = self._collect_log_metrics()
            
            # 生成Prometheus格式
            prometheus_metrics = self._generate_prometheus_format(metrics_data)
            
            return HttpResponse(
                prometheus_metrics,
                content_type=CONTENT_TYPE_LATEST
            )
            
        except Exception as e:
            logger.error(f"生成Prometheus指标失败: {e}")
            return HttpResponse(
                f"# Error generating metrics: {e}\n",
                content_type='text/plain'
            )
    
    def _collect_log_metrics(self) -> Dict[str, Any]:
        """收集日志相关指标"""
        try:
            analyzer = LogAnalyzer()
            analysis = analyzer.analyze_trends(days=1)  # 最近1天的数据
            
            indexer = LogFileIndexer()
            index = indexer.build_file_index()
            
            return {
                'log_messages_total': analysis['summary']['total_logs'],
                'log_files_total': len(index['files']),
                'log_storage_bytes': index['total_size'],
                'log_by_level': analysis['by_level'],
                'log_by_service': analysis['by_service']
            }
        except Exception as e:
            logger.error(f"收集日志指标失败: {e}")
            return {}
    
    def _generate_prometheus_format(self, metrics: Dict[str, Any]) -> str:
        """生成Prometheus格式的指标字符串"""
        lines = []
        
        # 添加帮助信息和类型定义
        lines.append("# HELP ansflow_log_messages_total Total number of log messages")
        lines.append("# TYPE ansflow_log_messages_total counter")
        lines.append(f"ansflow_log_messages_total {metrics.get('log_messages_total', 0)}")
        lines.append("")
        
        lines.append("# HELP ansflow_log_files_total Total number of log files")
        lines.append("# TYPE ansflow_log_files_total gauge")
        lines.append(f"ansflow_log_files_total {metrics.get('log_files_total', 0)}")
        lines.append("")
        
        lines.append("# HELP ansflow_log_storage_bytes Total log storage size in bytes")
        lines.append("# TYPE ansflow_log_storage_bytes gauge")
        lines.append(f"ansflow_log_storage_bytes {metrics.get('log_storage_bytes', 0)}")
        lines.append("")
        
        # 按级别分组的指标
        lines.append("# HELP ansflow_log_messages_by_level Number of log messages by level")
        lines.append("# TYPE ansflow_log_messages_by_level counter")
        for level, count in metrics.get('log_by_level', {}).items():
            lines.append(f'ansflow_log_messages_by_level{{level="{level}"}} {count}')
        lines.append("")
        
        # 按服务分组的指标
        lines.append("# HELP ansflow_log_messages_by_service Number of log messages by service")
        lines.append("# TYPE ansflow_log_messages_by_service counter")
        for service, count in metrics.get('log_by_service', {}).items():
            lines.append(f'ansflow_log_messages_by_service{{service="{service}"}} {count}')
        lines.append("")
        
        return "\n".join(lines)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def log_metrics_json_view(request):
    """返回JSON格式的日志指标（用于前端展示）"""
    try:
        analyzer = LogAnalyzer()
        analysis = analyzer.analyze_trends(days=7)  # 最近7天数据
        
        indexer = LogFileIndexer()
        index = indexer.build_file_index()
        
        metrics = {
            'overview': {
                'total_logs': analysis['summary']['total_logs'],
                'total_files': len(index['files']),
                'total_size_mb': round(index['total_size'] / 1024 / 1024, 2),
                'date_range': analysis['time_range']
            },
            'by_level': analysis['by_level'],
            'by_service': analysis['by_service'],
            'by_hour': analysis.get('by_hour', {}),
            'by_date': analysis.get('by_date', {}),
            'top_loggers': analysis.get('top_loggers', {}),
            'error_patterns': analysis.get('error_patterns', [])[:10],  # 只返回前10个错误模式
            'generated_at': datetime.now().isoformat()
        }
        
        return JsonResponse({
            'success': True,
            'data': metrics
        })
        
    except Exception as e:
        logger.error(f"获取JSON指标失败: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
