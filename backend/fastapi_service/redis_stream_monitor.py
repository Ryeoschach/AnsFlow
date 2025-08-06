#!/usr/bin/env python3
"""
实时监控Redis Stream日志数据
每秒自动刷新显示最新的日志信息
"""
import redis
import json
import time
import os
import sys
from datetime import datetime
from typing import Dict, List, Tuple

class RedisStreamMonitor:
    def __init__(self, host='localhost', port=6379, db=5):
        self.host = host
        self.port = port
        self.db = db
        self.redis_client = None
        self.last_displayed_count = 0
        
    def connect(self):
        """连接Redis"""
        try:
            self.redis_client = redis.Redis(
                host=self.host, 
                port=self.port, 
                db=self.db, 
                decode_responses=True
            )
            self.redis_client.ping()
            return True
        except Exception as e:
            print(f"❌ Redis连接失败: {e}")
            return False
    
    def get_stream_info(self) -> Dict:
        """获取Stream基本信息"""
        try:
            info = self.redis_client.xinfo_stream('ansflow:logs:stream')
            return {
                'length': info.get('length', 0),
                'first_id': info.get('first-entry-id', 'N/A'),
                'last_id': info.get('last-generated-id', 'N/A'),
                'groups': info.get('groups', 0)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_latest_messages(self, count=20) -> List[Tuple]:
        """获取最新的消息"""
        try:
            messages = self.redis_client.xrevrange('ansflow:logs:stream', count=count)
            return messages
        except Exception as e:
            print(f"❌ 获取消息失败: {e}")
            return []
    
    def format_message(self, msg_id: str, fields: Dict, index: int) -> str:
        """格式化消息显示"""
        timestamp = fields.get('timestamp', '')[:19].replace('T', ' ')  # 简化时间显示
        level = fields.get('level', 'UNKNOWN')
        service = fields.get('service', 'unknown')
        message = fields.get('message', '')
        
        # 截断过长的消息
        if len(message) > 80:
            message = message[:77] + '...'
        
        # 颜色编码
        level_colors = {
            'ERROR': '\033[91m',    # 红色
            'WARNING': '\033[93m',  # 黄色
            'INFO': '\033[92m',     # 绿色
            'DEBUG': '\033[94m',    # 蓝色
        }
        
        service_colors = {
            'fastapi': '\033[96m',   # 青色
            'django': '\033[95m',    # 紫色
            'system': '\033[97m',    # 白色
        }
        
        reset_color = '\033[0m'
        
        level_color = level_colors.get(level.upper(), '\033[0m')
        service_color = service_colors.get(service, '\033[0m')
        
        return (f"{index:2d}. {timestamp} "
                f"{level_color}[{level:7s}]{reset_color} "
                f"{service_color}{service:8s}{reset_color} | {message}")
    
    def get_statistics(self, messages: List[Tuple]) -> Dict:
        """统计信息"""
        stats = {
            'services': {},
            'levels': {},
            'total': len(messages)
        }
        
        for msg_id, fields in messages:
            service = fields.get('service', 'unknown')
            level = fields.get('level', 'unknown')
            
            stats['services'][service] = stats['services'].get(service, 0) + 1
            stats['levels'][level] = stats['levels'].get(level, 0) + 1
        
        return stats
    
    def clear_screen(self):
        """清屏"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def display_header(self, stream_info: Dict):
        """显示头部信息"""
        print("🔄 AnsFlow Redis Stream 实时监控")
        print("=" * 80)
        print(f"📊 连接信息: Redis {self.host}:{self.port} DB:{self.db}")
        print(f"📈 Stream状态: ansflow:logs:stream")
        
        if 'error' in stream_info:
            print(f"❌ Stream错误: {stream_info['error']}")
        else:
            print(f"   • 总消息数: {stream_info['length']}")
            print(f"   • 最新ID: {stream_info['last_id']}")
        
        print(f"⏰ 刷新时间: {datetime.now().strftime('%H:%M:%S')}")
        print("-" * 80)
    
    def display_messages(self, messages: List[Tuple]):
        """显示消息列表"""
        if not messages:
            print("📭 暂无日志消息")
            return
        
        print(f"📝 最新 {len(messages)} 条日志:")
        for i, (msg_id, fields) in enumerate(messages, 1):
            print(self.format_message(msg_id, fields, i))
    
    def display_statistics(self, stats: Dict):
        """显示统计信息"""
        print("-" * 80)
        print("📊 统计信息:")
        
        # 服务统计
        services = stats['services']
        if services:
            service_list = [f"{k}({v})" for k, v in services.items()]
            print(f"   服务分布: {', '.join(service_list)}")
        
        # 级别统计
        levels = stats['levels']
        if levels:
            level_list = [f"{k}({v})" for k, v in levels.items()]
            print(f"   级别分布: {', '.join(level_list)}")
        
        print(f"   显示总数: {stats['total']}")
    
    def display_help(self):
        """显示帮助信息"""
        print("\n💡 控制说明:")
        print("   • Ctrl+C: 退出监控")
        print("   • 数据每1秒自动刷新")
        print("   • 显示最新20条日志")
        print("\n🎨 颜色说明:")
        print(f"   \033[91mERROR\033[0m | \033[93mWARNING\033[0m | \033[92mINFO\033[0m | \033[94mDEBUG\033[0m")
        print(f"   \033[96mfastapi\033[0m | \033[95mdjango\033[0m | \033[97msystem\033[0m")
    
    def run_monitor(self, refresh_interval=1, message_count=20):
        """运行监控"""
        if not self.connect():
            return
        
        print("🚀 开始实时监控Redis Stream...")
        self.display_help()
        time.sleep(3)  # 显示帮助信息3秒
        
        try:
            while True:
                # 清屏
                self.clear_screen()
                
                # 获取数据
                stream_info = self.get_stream_info()
                messages = self.get_latest_messages(message_count)
                stats = self.get_statistics(messages)
                
                # 显示信息
                self.display_header(stream_info)
                self.display_messages(messages)
                self.display_statistics(stats)
                
                # 检查是否有新数据
                current_count = stream_info.get('length', 0)
                if current_count > self.last_displayed_count:
                    print(f"\n🔔 检测到 {current_count - self.last_displayed_count} 条新日志!")
                    self.last_displayed_count = current_count
                elif current_count == self.last_displayed_count and current_count > 0:
                    print(f"\n💤 无新日志 (总计 {current_count} 条)")
                
                print(f"\n⏳ {refresh_interval}秒后自动刷新... (Ctrl+C 退出)")
                
                # 等待刷新
                time.sleep(refresh_interval)
                
        except KeyboardInterrupt:
            print(f"\n\n👋 监控已停止")
        except Exception as e:
            print(f"\n❌ 监控出错: {e}")

def main():
    """主函数"""
    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description='Redis Stream实时监控工具')
    parser.add_argument('--host', default='localhost', help='Redis主机地址')
    parser.add_argument('--port', type=int, default=6379, help='Redis端口')
    parser.add_argument('--db', type=int, default=5, help='Redis数据库编号')
    parser.add_argument('--interval', type=int, default=1, help='刷新间隔(秒)')
    parser.add_argument('--count', type=int, default=20, help='显示消息数量')
    
    args = parser.parse_args()
    
    # 创建监控器
    monitor = RedisStreamMonitor(args.host, args.port, args.db)
    
    # 运行监控
    monitor.run_monitor(args.interval, args.count)

if __name__ == "__main__":
    main()
