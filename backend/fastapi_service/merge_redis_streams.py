#!/usr/bin/env python3
"""
合并Django和FastAPI的Redis Stream
将ansflow:logs中的消息迁移到ansflow:logs:stream中
"""
import redis
import json

def merge_streams():
    """合并Redis Stream"""
    try:
        r = redis.Redis(host='localhost', port=6379, db=5, decode_responses=True)
        r.ping()
        print("✅ Redis连接成功")
        
        # 获取源Stream (Django)
        source_stream = 'ansflow:logs'
        target_stream = 'ansflow:logs:stream'
        
        # 检查源Stream
        try:
            source_info = r.xinfo_stream(source_stream)
            source_count = source_info['length']
            print(f"📊 源Stream ({source_stream}): {source_count} 条消息")
        except Exception as e:
            print(f"❌ 源Stream不存在或为空: {e}")
            return
        
        # 检查目标Stream
        try:
            target_info = r.xinfo_stream(target_stream) 
            target_count = target_info['length']
            print(f"📊 目标Stream ({target_stream}): {target_count} 条消息")
        except:
            print(f"📊 目标Stream ({target_stream}): 不存在，将创建")
            target_count = 0
        
        # 读取源Stream的所有消息
        print(f"\n🔄 开始迁移消息...")
        messages = r.xrange(source_stream)
        migrated_count = 0
        
        for msg_id, fields in messages:
            try:
                # 将消息写入目标Stream
                # 注意: 不保留原始ID，让Redis自动生成新ID
                new_id = r.xadd(target_stream, fields)
                migrated_count += 1
                
                # 显示迁移的消息
                service = fields.get('service', 'unknown')
                message = fields.get('message', '')[:50] + ('...' if len(fields.get('message', '')) > 50 else '')
                print(f"  ✅ 迁移: [{service}] {message}")
                
            except Exception as e:
                print(f"  ❌ 迁移失败: {msg_id} - {e}")
        
        print(f"\n🎉 迁移完成! 成功迁移 {migrated_count} 条消息")
        
        # 验证结果
        new_target_info = r.xinfo_stream(target_stream)
        new_target_count = new_target_info['length'] 
        print(f"📊 目标Stream新总数: {new_target_count} 条消息")
        
        # 可选：删除源Stream
        confirm = input(f"\n❓ 是否删除源Stream ({source_stream})? (y/N): ")
        if confirm.lower() == 'y':
            deleted = r.delete(source_stream)
            if deleted:
                print(f"🗑️ 已删除源Stream: {source_stream}")
            else:
                print(f"⚠️ 删除源Stream失败")
        else:
            print("ℹ️ 保留源Stream，可以手动删除")
            
    except Exception as e:
        print(f"❌ 操作失败: {e}")

def show_merged_result():
    """显示合并后的结果"""
    try:
        r = redis.Redis(host='localhost', port=6379, db=5, decode_responses=True)
        
        print(f"\n📊 合并后的Stream状态:")
        target_stream = 'ansflow:logs:stream'
        
        info = r.xinfo_stream(target_stream)
        total_count = info['length']
        print(f"  • 总消息数: {total_count}")
        
        # 统计服务类型
        messages = r.xrevrange(target_stream, count=50)  # 检查最新50条
        services = {}
        for msg_id, fields in messages:
            service = fields.get('service', 'unknown')
            services[service] = services.get(service, 0) + 1
        
        print(f"  • 服务分布 (最新50条):")
        for service, count in services.items():
            print(f"    - {service}: {count} 条")
            
        print(f"\n🎯 现在所有日志都统一在 {target_stream} 中了！")
        
    except Exception as e:
        print(f"❌ 查看结果失败: {e}")

if __name__ == "__main__":
    print("🔄 Redis Stream 合并工具")
    print("=" * 50)
    merge_streams()
    show_merged_result()
    print("\n✅ 现在重启Django服务后，所有日志都会写入统一的Stream")
