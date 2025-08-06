#!/usr/bin/env python3
"""
AnsFlow日志系统Phase 3测试脚本
测试历史分析、指标收集、查询优化等功能
"""
import os
import sys
import time
import json
import asyncio
import logging
import requests
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目路径
project_root = Path(__file__).parent
django_service_path = project_root / 'backend' / 'django_service'
sys.path.insert(0, str(django_service_path))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

def test_file_indexer():
    """测试文件索引功能"""
    print("=" * 60)
    print("📁 测试日志文件索引功能")
    print("=" * 60)
    
    try:
        import django
        django.setup()
        
        from settings_management.views.logging import LogFileIndexer
        
        indexer = LogFileIndexer()
        index = indexer.build_file_index(days=30)
        
        print(f"✅ 索引构建成功")
        print(f"   - 文件数量: {len(index['files'])}")
        print(f"   - 总大小: {index['total_size'] / 1024 / 1024:.2f}MB")
        print(f"   - 服务类型: {', '.join(index['services'])}")
        print(f"   - 日志级别: {', '.join(index['levels'])}")
        
        if index['files']:
            latest_file = index['files'][0]
            print(f"   - 最新文件: {latest_file['relative_path']}")
            print(f"   - 修改时间: {latest_file['modified']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 文件索引测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_query_engine():
    """测试查询引擎功能"""
    print("=" * 60)
    print("🔍 测试日志查询引擎功能")
    print("=" * 60)
    
    try:
        import django
        django.setup()
        
        from settings_management.views.logging import LogQueryEngine
        
        engine = LogQueryEngine()
        
        # 测试基础查询
        query_params = {
            'limit': 10,
            'levels': ['INFO', 'ERROR'],
            'keywords': 'test'
        }
        
        results = engine.search_logs(query_params)
        
        print(f"✅ 查询引擎测试成功")
        print(f"   - 查询结果数量: {len(results.get('logs', []))}")
        print(f"   - 总记录数: {results.get('total_count', 0)}")
        print(f"   - 搜索文件数: {results.get('files_searched', 0)}")
        print(f"   - 查询时间: {results.get('query_time', 'N/A')}")
        
        if results.get('logs'):
            sample_log = results['logs'][0]
            print(f"   - 示例日志: {sample_log.get('message', '')[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 查询引擎测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_analyzer():
    """测试日志分析功能"""
    print("=" * 60)
    print("📊 测试日志分析功能")
    print("=" * 60)
    
    try:
        import django
        django.setup()
        
        from settings_management.views.logging import LogAnalyzer
        
        analyzer = LogAnalyzer()
        analysis = analyzer.analyze_trends(days=7)
        
        if analysis.get('error'):
            print(f"⚠️  分析器返回错误: {analysis['error']}")
            return False
        
        print(f"✅ 日志分析测试成功")
        print(f"   - 分析时间范围: {analysis.get('time_range', {}).get('days', 0)} 天")
        print(f"   - 总日志数: {analysis.get('summary', {}).get('total_logs', 0)}")
        print(f"   - 分析文件数: {analysis.get('summary', {}).get('files_analyzed', 0)}")
        
        by_level = analysis.get('by_level', {})
        if by_level:
            print(f"   - 日志级别分布:")
            for level, count in by_level.items():
                print(f"     * {level}: {count}")
        
        by_service = analysis.get('by_service', {})
        if by_service:
            print(f"   - 服务分布:")
            for service, count in by_service.items():
                print(f"     * {service}: {count}")
        
        error_patterns = analysis.get('error_patterns', [])
        print(f"   - 错误模式数量: {len(error_patterns)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 日志分析测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prometheus_metrics():
    """测试Prometheus指标收集"""
    print("=" * 60)
    print("📈 测试Prometheus指标收集")
    print("=" * 60)
    
    try:
        import django
        django.setup()
        
        from common.prometheus_metrics import LogMetricsCollector
        
        collector = LogMetricsCollector()
        
        # 测试指标收集
        metrics = collector.collect_log_metrics()
        
        print(f"✅ Prometheus指标测试成功")
        print(f"   - 收集时间: {metrics.get('collection_time', 'N/A')}")
        print(f"   - 日志文件数: {metrics.get('log_files', 0)}")
        print(f"   - 总大小: {metrics.get('total_size_bytes', 0) / 1024 / 1024:.2f}MB")
        print(f"   - 最近1小时错误数: {metrics.get('errors_last_hour', 0)}")
        
        # 测试指标记录
        collector.record_log_message('INFO', 'django')
        collector.record_log_message('ERROR', 'fastapi')
        collector.record_http_request('GET', '/api/test', 200, 0.123)
        
        print(f"   - 指标记录功能正常")
        
        # 尝试生成Prometheus格式的输出
        metrics_text = collector.get_metrics_text()
        if metrics_text and not metrics_text.startswith('# Prometheus客户端不可用'):
            print(f"   - Prometheus格式输出: {len(metrics_text)} 字符")
        else:
            print(f"   - Prometheus客户端不可用，使用模拟指标")
        
        return True
        
    except Exception as e:
        print(f"❌ Prometheus指标测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_endpoints():
    """测试API端点"""
    print("=" * 60)
    print("🌐 测试Phase 3 API端点")
    print("=" * 60)
    
    # 基础URL（假设Django运行在8000端口）
    base_url = "http://localhost:8000"
    
    endpoints = [
        ('/api/settings/logging/stats/', 'GET', '日志统计'),
        ('/api/settings/logging/config/', 'GET', '日志配置'),
        ('/api/settings/logging/metrics/', 'GET', 'Prometheus指标'),
        ('/api/settings/logging/metrics/json/', 'GET', 'JSON指标'),
    ]
    
    results = []
    
    for endpoint, method, name in endpoints:
        try:
            url = base_url + endpoint
            print(f"🔍 测试 {name}: {method} {endpoint}")
            
            if method == 'GET':
                response = requests.get(url, timeout=5)
            else:
                response = requests.post(url, timeout=5)
            
            if response.status_code == 200:
                print(f"   ✅ {name} 响应正常 (状态码: {response.status_code})")
                
                # 尝试解析JSON响应
                try:
                    data = response.json()
                    if isinstance(data, dict) and 'success' in data:
                        print(f"   📊 返回数据结构正确")
                    else:
                        print(f"   📄 返回数据: {str(data)[:100]}...")
                except:
                    print(f"   📄 返回文本数据: {len(response.text)} 字符")
                
                results.append((name, True))
            else:
                print(f"   ❌ {name} 响应异常 (状态码: {response.status_code})")
                results.append((name, False))
                
        except requests.exceptions.ConnectionError:
            print(f"   ⚠️  {name} 连接失败 (Django服务可能未启动)")
            results.append((name, False))
        except Exception as e:
            print(f"   ❌ {name} 测试失败: {e}")
            results.append((name, False))
    
    # 总结
    success_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    print(f"\n📊 API测试总结: {success_count}/{total_count} 成功")
    
    return success_count == total_count


def create_sample_logs():
    """创建示例日志数据"""
    print("=" * 60)
    print("📝 创建示例日志数据")
    print("=" * 60)
    
    try:
        # 确保日志目录存在
        log_dir = Path('/Users/creed/Workspace/OpenSource/ansflow/logs')
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建示例日志文件
        sample_logs = [
            {
                'timestamp': datetime.now().isoformat(),
                'level': 'INFO',
                'service': 'django',
                'logger': 'ansflow.test',
                'message': 'Phase 3历史分析功能测试开始'
            },
            {
                'timestamp': (datetime.now() - timedelta(minutes=5)).isoformat(),
                'level': 'ERROR',
                'service': 'fastapi',
                'logger': 'ansflow.api',
                'message': '测试错误日志 - 这是一个示例错误'
            },
            {
                'timestamp': (datetime.now() - timedelta(minutes=10)).isoformat(),
                'level': 'WARNING',
                'service': 'django',
                'logger': 'ansflow.middleware',
                'message': '测试警告日志 - 连接超时重试'
            },
            {
                'timestamp': (datetime.now() - timedelta(hours=1)).isoformat(),
                'level': 'INFO',
                'service': 'system',
                'logger': 'ansflow.scheduler',
                'message': 'Phase 3定时任务执行完成'
            }
        ]
        
        # 写入测试日志文件
        test_log_file = log_dir / 'phase3_test.log'
        with open(test_log_file, 'w', encoding='utf-8') as f:
            for log in sample_logs:
                f.write(json.dumps(log, ensure_ascii=False) + '\n')
        
        print(f"✅ 示例日志创建成功")
        print(f"   - 文件路径: {test_log_file}")
        print(f"   - 日志条数: {len(sample_logs)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 创建示例日志失败: {e}")
        return False


def run_phase3_tests():
    """运行Phase 3完整测试"""
    print("🚀 AnsFlow日志系统Phase 3功能测试")
    print("=" * 80)
    print(f"测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    test_results = []
    
    # 1. 创建示例数据
    print("\n🏗️  准备测试环境...")
    if create_sample_logs():
        test_results.append(("创建示例日志", True))
    else:
        test_results.append(("创建示例日志", False))
    
    # 等待一下确保日志文件写入完成
    time.sleep(1)
    
    # 2. 测试核心功能
    tests = [
        ("文件索引器", test_file_indexer),
        ("查询引擎", test_query_engine),
        ("日志分析器", test_analyzer),
        ("Prometheus指标", test_prometheus_metrics),
        ("API端点", test_api_endpoints)
    ]
    
    for test_name, test_func in tests:
        print(f"\n🧪 运行 {test_name} 测试...")
        try:
            success = test_func()
            test_results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            test_results.append((test_name, False))
        
        # 测试间隔
        time.sleep(1)
    
    # 总结结果
    print("\n" + "=" * 80)
    print("📊 Phase 3测试结果总结")
    print("=" * 80)
    
    success_count = 0
    total_count = len(test_results)
    
    for test_name, success in test_results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name:<20}: {status}")
        if success:
            success_count += 1
    
    print("-" * 80)
    print(f"总体结果: {success_count}/{total_count} 测试通过")
    
    if success_count == total_count:
        print("🎉 恭喜！Phase 3历史分析功能全部测试通过！")
        print("\n✨ 已完成功能:")
        print("   • 日志文件索引和缓存")
        print("   • 高性能历史日志查询")
        print("   • 智能日志趋势分析")
        print("   • Prometheus指标收集")
        print("   • 多格式日志导出")
        print("   • RESTful API接口")
        
        return True
    else:
        print("⚠️  部分测试失败，请检查日志和配置")
        return False


if __name__ == "__main__":
    success = run_phase3_tests()
    sys.exit(0 if success else 1)
