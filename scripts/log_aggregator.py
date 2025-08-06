#!/usr/bin/env python3
"""
AnsFlow 日志聚合脚本 v2.0
实现方案一：统一日志目录 + 自动聚合 + 智能分析
"""

import os
import json
import time
import shutil
import argparse
import glob
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import argparse
import gzip
import shutil


class LogAggregator:
    """日志聚合器 - 实现方案一的聚合策略"""
    
    def __init__(self, log_dir: str = None):
        self.log_dir = Path(log_dir or os.getenv('LOG_DIR', '/Users/creed/Workspace/OpenSource/ansflow/logs'))
        self.services_dir = self.log_dir / 'services'
        self.aggregated_dir = self.log_dir / 'aggregated'
        self.archived_dir = self.log_dir / 'archived'
        
        # 确保目录存在
        self.aggregated_dir.mkdir(parents=True, exist_ok=True)
        self.archived_dir.mkdir(parents=True, exist_ok=True)
        
        self.services = ['django', 'fastapi', 'system']
        
    def aggregate_all_logs(self):
        """聚合所有服务的日志"""
        print(f"开始聚合日志 - {datetime.now().isoformat()}")
        
        # 聚合各类型日志
        self.aggregate_main_logs()
        self.aggregate_error_logs()
        self.aggregate_access_logs()
        self.aggregate_performance_logs()
        
        # 按时间范围聚合
        self.aggregate_by_time_range()
        
        print(f"日志聚合完成 - {datetime.now().isoformat()}")
        
    def aggregate_main_logs(self):
        """聚合主日志文件"""
        print("聚合主日志文件...")
        
        output_file = self.aggregated_dir / f"all_services_{datetime.now().strftime('%Y%m%d')}.log"
        
        with open(output_file, 'w', encoding='utf-8') as outf:
            for service in self.services:
                service_dir = self.services_dir / service
                if not service_dir.exists():
                    continue
                    
                # 查找主日志文件
                log_files = list(service_dir.glob(f"{service}_main.log*"))
                log_files.sort()  # 按文件名排序
                
                for log_file in log_files:
                    if log_file.suffix == '.gz':
                        # 处理压缩文件
                        with gzip.open(log_file, 'rt', encoding='utf-8') as inf:
                            self._copy_logs_with_service_tag(inf, outf, service)
                    else:
                        # 处理普通文件
                        with open(log_file, 'r', encoding='utf-8') as inf:
                            self._copy_logs_with_service_tag(inf, outf, service)
                            
        print(f"主日志聚合完成: {output_file}")
        
    def aggregate_error_logs(self):
        """聚合错误日志文件"""
        print("聚合错误日志文件...")
        
        output_file = self.aggregated_dir / f"errors_only_{datetime.now().strftime('%Y%m%d')}.log"
        
        with open(output_file, 'w', encoding='utf-8') as outf:
            for service in self.services:
                service_dir = self.services_dir / service
                if not service_dir.exists():
                    continue
                    
                # 查找错误日志文件
                log_files = list(service_dir.glob(f"{service}_error.log*"))
                log_files.sort()
                
                for log_file in log_files:
                    if log_file.suffix == '.gz':
                        with gzip.open(log_file, 'rt', encoding='utf-8') as inf:
                            self._copy_logs_with_service_tag(inf, outf, service)
                    else:
                        with open(log_file, 'r', encoding='utf-8') as inf:
                            self._copy_logs_with_service_tag(inf, outf, service)
                            
        print(f"错误日志聚合完成: {output_file}")
        
    def aggregate_access_logs(self):
        """聚合访问日志文件（仅Web服务）"""
        print("聚合访问日志文件...")
        
        output_file = self.aggregated_dir / f"access_combined_{datetime.now().strftime('%Y%m%d')}.log"
        web_services = ['django', 'fastapi']
        
        with open(output_file, 'w', encoding='utf-8') as outf:
            for service in web_services:
                service_dir = self.services_dir / service
                if not service_dir.exists():
                    continue
                    
                # 查找访问日志文件
                log_files = list(service_dir.glob(f"{service}_access.log*"))
                log_files.sort()
                
                for log_file in log_files:
                    if log_file.suffix == '.gz':
                        with gzip.open(log_file, 'rt', encoding='utf-8') as inf:
                            self._copy_logs_with_service_tag(inf, outf, service)
                    else:
                        with open(log_file, 'r', encoding='utf-8') as inf:
                            self._copy_logs_with_service_tag(inf, outf, service)
                            
        print(f"访问日志聚合完成: {output_file}")
        
    def aggregate_performance_logs(self):
        """聚合性能日志文件"""
        print("聚合性能日志文件...")
        
        output_file = self.aggregated_dir / f"performance_combined_{datetime.now().strftime('%Y%m%d')}.log"
        
        with open(output_file, 'w', encoding='utf-8') as outf:
            for service in self.services:
                service_dir = self.services_dir / service
                if not service_dir.exists():
                    continue
                    
                # 查找性能日志文件
                log_files = list(service_dir.glob(f"{service}_performance.log*"))
                log_files.sort()
                
                for log_file in log_files:
                    if log_file.suffix == '.gz':
                        with gzip.open(log_file, 'rt', encoding='utf-8') as inf:
                            self._copy_logs_with_service_tag(inf, outf, service)
                    else:
                        with open(log_file, 'r', encoding='utf-8') as inf:
                            self._copy_logs_with_service_tag(inf, outf, service)
                            
        print(f"性能日志聚合完成: {output_file}")
        
    def aggregate_by_time_range(self):
        """按时间范围聚合日志"""
        print("按时间范围聚合日志...")
        
        # 聚合今日日志
        self._aggregate_time_range('today', 0)
        
        # 聚合昨日日志
        self._aggregate_time_range('yesterday', 1)
        
        # 聚合本周日志
        self._aggregate_time_range('this_week', 7)
        
    def _aggregate_time_range(self, range_name: str, days_back: int):
        """按指定时间范围聚合日志"""
        target_date = datetime.now() - timedelta(days=days_back)
        date_str = target_date.strftime('%Y-%m-%d')
        
        output_file = self.aggregated_dir / f"logs_{range_name}_{target_date.strftime('%Y%m%d')}.log"
        
        with open(output_file, 'w', encoding='utf-8') as outf:
            for service in self.services:
                service_dir = self.services_dir / service
                if not service_dir.exists():
                    continue
                    
                # 查找指定日期的所有日志文件
                log_files = list(service_dir.glob(f"{service}_*.log*"))
                
                for log_file in log_files:
                    # 检查文件修改时间
                    file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                    
                    if range_name == 'today' and file_mtime.date() == target_date.date():
                        self._process_log_file(log_file, outf, service, date_str)
                    elif range_name == 'yesterday' and file_mtime.date() == target_date.date():
                        self._process_log_file(log_file, outf, service, date_str)
                    elif range_name == 'this_week' and (datetime.now() - file_mtime).days <= 7:
                        self._process_log_file(log_file, outf, service, date_str)
                        
        print(f"时间范围日志聚合完成 ({range_name}): {output_file}")
        
    def _process_log_file(self, log_file: Path, output_file, service: str, date_filter: str):
        """处理单个日志文件"""
        try:
            if log_file.suffix == '.gz':
                with gzip.open(log_file, 'rt', encoding='utf-8') as inf:
                    self._copy_logs_with_service_tag(inf, output_file, service, date_filter)
            else:
                with open(log_file, 'r', encoding='utf-8') as inf:
                    self._copy_logs_with_service_tag(inf, output_file, service, date_filter)
        except Exception as e:
            print(f"处理日志文件失败 {log_file}: {e}")
            
    def _copy_logs_with_service_tag(self, input_file, output_file, service: str, date_filter: str = None):
        """复制日志并添加服务标签"""
        for line in input_file:
            line = line.strip()
            if not line:
                continue
                
            # 如果指定了日期过滤器，检查日志时间戳
            if date_filter and not self._matches_date_filter(line, date_filter):
                continue
                
            # 尝试解析JSON日志
            try:
                log_data = json.loads(line)
                # 确保服务标签正确
                if 'service' not in log_data:
                    log_data['service'] = service
                output_file.write(json.dumps(log_data, ensure_ascii=False) + '\n')
            except json.JSONDecodeError:
                # 非JSON格式的日志，添加服务标签前缀
                timestamp = datetime.utcnow().isoformat() + 'Z'
                tagged_line = f"[{timestamp}] [{service}] {line}\n"
                output_file.write(tagged_line)
                
    def _matches_date_filter(self, line: str, date_filter: str) -> bool:
        """检查日志行是否匹配日期过滤器"""
        try:
            # 尝试解析JSON格式的时间戳
            log_data = json.loads(line)
            if 'timestamp' in log_data:
                log_date = datetime.fromisoformat(log_data['timestamp'].replace('Z', '+00:00'))
                return log_date.strftime('%Y-%m-%d') == date_filter
        except:
            # 对于非JSON格式，使用简单的字符串匹配
            return date_filter in line
            
        return False
        
    def archive_old_logs(self, days_to_keep: int = None):
        """归档旧日志文件"""
        if days_to_keep is None:
            days_to_keep = int(os.getenv('LOG_RETENTION_DAYS', '30'))
            
        print(f"归档 {days_to_keep} 天前的日志文件...")
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        archived_count = 0
        
        # 归档各服务的旧日志
        for service in self.services:
            service_dir = self.services_dir / service
            if not service_dir.exists():
                continue
                
            for log_file in service_dir.glob("*.log.*"):  # 轮转后的日志文件
                file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                
                if file_mtime < cutoff_date:
                    # 移动到归档目录
                    archive_subdir = self.archived_dir / service
                    archive_subdir.mkdir(exist_ok=True)
                    
                    archive_path = archive_subdir / log_file.name
                    
                    # 如果文件未压缩，先压缩
                    if not log_file.name.endswith('.gz'):
                        compressed_path = archive_path.with_suffix(archive_path.suffix + '.gz')
                        with open(log_file, 'rb') as f_in:
                            with gzip.open(compressed_path, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        log_file.unlink()  # 删除原文件
                        archived_count += 1
                        print(f"归档并压缩: {log_file} -> {compressed_path}")
                    else:
                        # 直接移动已压缩的文件
                        shutil.move(str(log_file), str(archive_path))
                        archived_count += 1
                        print(f"归档: {log_file} -> {archive_path}")
                        
        # 归档聚合日志
        for agg_file in self.aggregated_dir.glob("*.log"):
            file_mtime = datetime.fromtimestamp(agg_file.stat().st_mtime)
            
            if file_mtime < cutoff_date:
                archive_path = self.archived_dir / agg_file.name
                
                # 压缩并移动
                compressed_path = archive_path.with_suffix('.gz')
                with open(agg_file, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                agg_file.unlink()
                archived_count += 1
                print(f"归档聚合日志: {agg_file} -> {compressed_path}")
                
        print(f"归档完成，共处理 {archived_count} 个文件")
        
    def generate_report(self) -> Dict[str, Any]:
        """生成日志统计报告"""
        print("生成日志统计报告...")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "log_directory": str(self.log_dir),
            "services": {},
            "aggregated_files": [],
            "archived_files": [],
            "total_size_mb": 0
        }
        
        total_size = 0
        
        # 统计各服务日志
        for service in self.services:
            service_dir = self.services_dir / service
            if not service_dir.exists():
                continue
                
            service_stats = {
                "log_files": [],
                "total_size_mb": 0,
                "file_count": 0
            }
            
            for log_file in service_dir.glob("*"):
                if log_file.is_file():
                    file_size = log_file.stat().st_size
                    service_stats["log_files"].append({
                        "name": log_file.name,
                        "size_mb": round(file_size / 1024 / 1024, 2),
                        "modified": datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
                    })
                    service_stats["total_size_mb"] += file_size / 1024 / 1024
                    service_stats["file_count"] += 1
                    total_size += file_size
                    
            service_stats["total_size_mb"] = round(service_stats["total_size_mb"], 2)
            report["services"][service] = service_stats
            
        # 统计聚合文件
        for agg_file in self.aggregated_dir.glob("*"):
            if agg_file.is_file():
                file_size = agg_file.stat().st_size
                report["aggregated_files"].append({
                    "name": agg_file.name,
                    "size_mb": round(file_size / 1024 / 1024, 2),
                    "modified": datetime.fromtimestamp(agg_file.stat().st_mtime).isoformat()
                })
                total_size += file_size
                
        # 统计归档文件
        for archive_file in self.archived_dir.glob("**/*"):
            if archive_file.is_file():
                file_size = archive_file.stat().st_size
                report["archived_files"].append({
                    "name": str(archive_file.relative_to(self.archived_dir)),
                    "size_mb": round(file_size / 1024 / 1024, 2),
                    "modified": datetime.fromtimestamp(archive_file.stat().st_mtime).isoformat()
                })
                total_size += file_size
                
        report["total_size_mb"] = round(total_size / 1024 / 1024, 2)
        
        # 保存报告
        report_file = self.log_dir / f"log_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        print(f"日志统计报告生成完成: {report_file}")
        return report


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='AnsFlow 日志聚合工具')
    parser.add_argument('--log-dir', help='日志目录路径', default=None)
    parser.add_argument('--aggregate', action='store_true', help='执行日志聚合')
    parser.add_argument('--archive', action='store_true', help='归档旧日志')
    parser.add_argument('--days-to-keep', type=int, default=30, help='保留天数')
    parser.add_argument('--report', action='store_true', help='生成统计报告')
    parser.add_argument('--all', action='store_true', help='执行所有操作')
    
    args = parser.parse_args()
    
    aggregator = LogAggregator(args.log_dir)
    
    if args.all or args.aggregate:
        aggregator.aggregate_all_logs()
        
    if args.all or args.archive:
        aggregator.archive_old_logs(args.days_to_keep)
        
    if args.all or args.report:
        report = aggregator.generate_report()
        print("\n=== 日志统计摘要 ===")
        print(f"总大小: {report['total_size_mb']} MB")
        print(f"服务数量: {len(report['services'])}")
        print(f"聚合文件数: {len(report['aggregated_files'])}")
        print(f"归档文件数: {len(report['archived_files'])}")
        
    if not any([args.aggregate, args.archive, args.report, args.all]):
        parser.print_help()


if __name__ == "__main__":
    main()
