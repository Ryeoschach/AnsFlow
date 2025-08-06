#!/usr/bin/env python3
"""
清空Redis日志数据库
"""
import redis
import sys

def clear_redis_logs():
    """清空Redis中的日志数据"""
    try:
        # 连接到Redis (DB 5 - 日志专用数据库)
        r = redis.Redis(host='localhost', port=6379, db=5, decode_responses=True)
        r.ping()
        print("✅ Redis连接成功 (DB 5)")
        
        # 获取清空前的统计信息
        print("\n📊 清空前的数据统计:")
        try:
            stream_info = r.xinfo_stream('ansflow:logs:stream')
            total_logs = stream_info['length']
            first_id = stream_info.get('first-entry-id', '无')
            last_id = stream_info.get('last-generated-id', '无')
            
            print(f"   • Stream名称: ansflow:logs:stream")
            print(f"   • 总日志数量: {total_logs}")
            print(f"   • 第一条ID: {first_id}")
            print(f"   • 最新ID: {last_id}")
            
        except Exception as e:
            print(f"   ⚠️ Stream可能不存在或为空: {e}")
            total_logs = 0
        
        # 获取所有keys
        all_keys = r.keys('*')
        print(f"   • Redis DB 5 中的所有键数量: {len(all_keys)}")
        if all_keys:
            print(f"   • 键列表: {all_keys}")
        
        if total_logs == 0 and len(all_keys) == 0:
            print("\n✅ Redis DB 5 已经是空的，无需清空")
            return
        
        # 确认清空操作
        print(f"\n⚠️ 即将清空Redis DB 5中的所有数据:")
        print(f"   • 日志Stream: {total_logs} 条")
        print(f"   • 其他键: {len(all_keys)} 个")
        
        confirm = input("\n确认清空? (输入 'yes' 确认): ")
        
        if confirm.lower() != 'yes':
            print("❌ 操作已取消")
            return
        
        print("\n🧹 开始清空Redis数据...")
        
        # 方法1: 删除特定的Stream
        if total_logs > 0:
            try:
                result = r.delete('ansflow:logs:stream')
                print(f"   ✅ 删除日志Stream: {result} 个键")
            except Exception as e:
                print(f"   ❌ 删除Stream失败: {e}")
        
        # 方法2: 清空整个数据库 (更彻底)
        try:
            r.flushdb()
            print("   ✅ 清空整个Redis DB 5")
        except Exception as e:
            print(f"   ❌ 清空数据库失败: {e}")
        
        # 验证清空结果
        print("\n🔍 验证清空结果:")
        try:
            remaining_keys = r.keys('*')
            print(f"   • 剩余键数量: {len(remaining_keys)}")
            
            if len(remaining_keys) == 0:
                print("   ✅ Redis DB 5 已完全清空")
            else:
                print(f"   ⚠️ 仍有剩余键: {remaining_keys}")
                
            # 尝试检查Stream是否还存在
            try:
                stream_info = r.xinfo_stream('ansflow:logs:stream')
                print(f"   ⚠️ Stream仍存在，长度: {stream_info['length']}")
            except:
                print("   ✅ 日志Stream已不存在")
                
        except Exception as e:
            print(f"   ❌ 验证失败: {e}")
        
        print("\n🎉 Redis日志数据清空完成!")
        print("📋 注意事项:")
        print("   • 实时日志界面将不再显示历史数据")
        print("   • 新的日志将重新开始记录")
        print("   • MySQL中的历史日志不受影响")
        print("   • 重启服务后日志系统将正常工作")
        
    except redis.ConnectionError:
        print("❌ Redis连接失败，请确保Redis服务正在运行")
        print("   检查命令: redis-cli ping")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 清空Redis失败: {e}")
        sys.exit(1)

def show_redis_status():
    """显示Redis当前状态"""
    try:
        r = redis.Redis(host='localhost', port=6379, db=5, decode_responses=True)
        r.ping()
        
        print("📊 Redis当前状态 (DB 5):")
        print("=" * 40)
        
        # 获取所有键
        all_keys = r.keys('*')
        print(f"总键数量: {len(all_keys)}")
        
        if all_keys:
            for key in all_keys:
                key_type = r.type(key)
                if key_type == 'stream':
                    try:
                        stream_info = r.xinfo_stream(key)
                        length = stream_info['length']
                        print(f"  • {key} (Stream): {length} 条消息")
                    except:
                        print(f"  • {key} (Stream): 无法获取信息")
                else:
                    print(f"  • {key} ({key_type})")
        else:
            print("🔄 数据库为空")
            
    except Exception as e:
        print(f"❌ 无法获取Redis状态: {e}")

if __name__ == "__main__":
    print("🧹 Redis日志数据清空工具")
    print("=" * 40)
    
    # 显示当前状态
    show_redis_status()
    
    # 执行清空操作
    clear_redis_logs()
    
    print("\n" + "=" * 40)
    # 再次显示状态确认清空结果
    show_redis_status()
