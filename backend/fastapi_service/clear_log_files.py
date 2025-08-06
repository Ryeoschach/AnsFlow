#!/usr/bin/env python3
"""
清空所有本地日志文件
"""
import os
import sys
from pathlib import Path

def clear_log_files():
    """清空所有本地日志文件"""
    
    # 日志目录列表
    log_dirs = [
        "/Users/creed/Workspace/OpenSource/ansflow/logs",
        "/Users/creed/Workspace/OpenSource/ansflow/backend/django_service/logs", 
        "/Users/creed/Workspace/OpenSource/ansflow/backend/fastapi_service/logs"
    ]
    
    print("🧹 本地日志文件清理工具")
    print("=" * 50)
    
    # 统计所有日志文件
    all_log_files = []
    total_size = 0
    
    for log_dir in log_dirs:
        if os.path.exists(log_dir):
            log_files = list(Path(log_dir).rglob("*.log*"))
            for log_file in log_files:
                if log_file.is_file():
                    size = log_file.stat().st_size
                    all_log_files.append((str(log_file), size))
                    total_size += size
    
    print(f"📊 发现的日志文件统计:")
    print(f"   • 总文件数: {len(all_log_files)}")
    print(f"   • 总大小: {total_size / 1024:.2f} KB ({total_size / 1024 / 1024:.2f} MB)")
    
    if len(all_log_files) == 0:
        print("✅ 没有发现日志文件，无需清理")
        return
    
    # 显示文件列表 (前10个)
    print(f"\n📋 日志文件列表 (显示前10个):")
    for i, (file_path, size) in enumerate(all_log_files[:10]):
        filename = Path(file_path).name
        dir_name = Path(file_path).parent.name
        print(f"   {i+1:2d}. {dir_name}/{filename} ({size/1024:.1f} KB)")
    
    if len(all_log_files) > 10:
        print(f"   ... 还有 {len(all_log_files) - 10} 个文件")
    
    # 确认清空操作
    print(f"\n⚠️ 即将清空所有日志文件内容:")
    print(f"   • 文件不会被删除，只是内容清空")
    print(f"   • 这样可以保持文件结构不变")
    print(f"   • 新日志可以继续写入这些文件")
    
    confirm = input(f"\n确认清空 {len(all_log_files)} 个日志文件? (输入 'yes' 确认): ")
    
    if confirm.lower() != 'yes':
        print("❌ 操作已取消")
        return
    
    print(f"\n🧹 开始清空日志文件...")
    
    # 清空文件内容
    success_count = 0
    error_count = 0
    
    for file_path, original_size in all_log_files:
        try:
            # 清空文件内容但保留文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('')  # 写入空内容
            
            print(f"   ✅ 已清空: {Path(file_path).name} ({original_size/1024:.1f} KB -> 0 KB)")
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ 清空失败: {Path(file_path).name} - {e}")
            error_count += 1
    
    print(f"\n🎉 日志文件清空完成!")
    print(f"   • 成功清空: {success_count} 个文件")
    print(f"   • 清空失败: {error_count} 个文件")
    print(f"   • 释放空间: {total_size / 1024 / 1024:.2f} MB")
    
    print(f"\n📋 影响说明:")
    print(f"   ✅ 实时日志页面将不再显示文件历史数据")
    print(f"   ✅ 文件结构保持不变，新日志可以继续写入")
    print(f"   ✅ Redis Stream 实时日志不受影响")
    print(f"   ⚠️ 文件中的历史日志数据已丢失")

def verify_cleanup():
    """验证清理效果"""
    print(f"\n🔍 验证清理效果:")
    print("=" * 30)
    
    log_dirs = [
        "/Users/creed/Workspace/OpenSource/ansflow/logs",
        "/Users/creed/Workspace/OpenSource/ansflow/backend/django_service/logs",
        "/Users/creed/Workspace/OpenSource/ansflow/backend/fastapi_service/logs"
    ]
    
    total_files = 0
    total_size = 0
    
    for log_dir in log_dirs:
        if os.path.exists(log_dir):
            log_files = list(Path(log_dir).rglob("*.log*"))
            for log_file in log_files:
                if log_file.is_file():
                    size = log_file.stat().st_size
                    total_files += 1
                    total_size += size
                    
                    if size > 0:
                        print(f"   ⚠️ {log_file.name}: {size} bytes (非空)")
                    else:
                        print(f"   ✅ {log_file.name}: 空文件")
    
    print(f"\n📊 清理后统计:")
    print(f"   • 总文件数: {total_files}")
    print(f"   • 总大小: {total_size} bytes ({total_size/1024:.2f} KB)")
    
    if total_size == 0:
        print("✅ 所有日志文件已成功清空")
    else:
        print(f"⚠️ 还有 {total_size} bytes 数据未清空")

if __name__ == "__main__":
    clear_log_files()
    verify_cleanup()
