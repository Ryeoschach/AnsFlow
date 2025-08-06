#!/usr/bin/env python3
"""
简单的Redis Stream日志验证脚本
"""
import redis
import json
from datetime import datetime

def check_redis_logs():
    """检查Redis Stream中的日志"""
    try:
        # 连接Redis
        r = redis.Redis(host='localhost', port=6379, db=5, decode_responses=True)
        r.ping()
        print("✅ Redis连接成功")
        
        # 获取Stream信息
        try:
            stream_info = r.xinfo_stream('ansflow:logs:stream')
            total_logs = stream_info['length']
            first_id = stream_info.get('first-entry-id', '无')
            last_id = stream_info.get('last-generated-id', '无')
            
            print(f"\n📊 Redis Stream统计:")
            print(f"   • 总日志数: {total_logs}")
            print(f"   • 第一条ID: {first_id}")
            print(f"   • 最新ID: {last_id}")
            
        except Exception as e:
            print(f"❌ 获取Stream信息失败: {e}")
            return
        
        # 获取最新的20条日志
        try:
            messages = r.xrevrange('ansflow:logs:stream', count=20)
            
            if not messages:
                print("⚠️ 没有找到日志消息")
                return
            
            print(f"\n🔍 最新20条日志:")
            service_stats = {}
            level_stats = {}
            
            for i, (msg_id, fields) in enumerate(messages):
                service = fields.get('service', 'unknown')
                level = fields.get('level', 'unknown')
                message = fields.get('message', '')
                timestamp = fields.get('timestamp', '')
                
                # 统计服务类型
                service_stats[service] = service_stats.get(service, 0) + 1
                
                # 统计日志级别
                level_stats[level] = level_stats.get(level, 0) + 1
                
                print(f"   {i+1:2d}. [{level:5s}] {service:15s} | {message[:50]}")
                if len(message) > 50:
                    print(f"      {'':23s} | {message[50:]}")
            
            print(f"\n📈 服务统计:")
            for service, count in service_stats.items():
                print(f"   • {service}: {count}条")
            
            print(f"\n📊 级别统计:")
            for level, count in level_stats.items():
                print(f"   • {level}: {count}条")
            
            # 检查FastAPI日志
            fastapi_logs = [msg for msg_id, fields in messages if fields.get('service') == 'fastapi_service']
            
            if fastapi_logs:
                print(f"\n✅ 找到 {len(fastapi_logs)} 条 FastAPI 日志")
                print("   最新的FastAPI日志:")
                for i, (msg_id, fields) in enumerate([(msg_id, fields) for msg_id, fields in messages if fields.get('service') == 'fastapi_service'][:5]):
                    message = fields.get('message', '')
                    timestamp = fields.get('timestamp', '')
                    level = fields.get('level', '')
                    print(f"     {i+1}. [{level}] {message}")
            else:
                print("❌ 没有找到FastAPI日志")
            
        except Exception as e:
            print(f"❌ 读取日志失败: {e}")
        
        print(f"\n🎯 实时日志推送状态:")
        print(f"   如果FastAPI服务正在运行且WebSocket已连接，")
        print(f"   新的FastAPI日志应该会实时出现在前端页面中。")
        
    except Exception as e:
        print(f"❌ Redis连接失败: {e}")

if __name__ == "__main__":
    check_redis_logs()
