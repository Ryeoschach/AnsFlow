#!/usr/bin/env python3
"""
执行日志重构检查脚本
用于识别项目中需要使用ExecutionLogger重构的代码模式
"""

import os
import re
from pathlib import Path

# 需要检查的重复代码模式
PATTERNS_TO_REFACTOR = [
    # 状态设置模式
    r'\.status\s*=\s*[\'"]running[\'"]',
    r'\.status\s*=\s*[\'"]success[\'"]',
    r'\.status\s*=\s*[\'"]failed[\'"]',
    r'\.status\s*=\s*[\'"]completed[\'"]',
    
    # 时间设置模式
    r'\.started_at\s*=\s*timezone\.now\(\)',
    r'\.completed_at\s*=\s*timezone\.now\(\)',
    
    # 日志设置模式
    r'\.stdout\s*=\s*result\.stdout',
    r'\.stderr\s*=\s*result\.stderr',
    r'\.return_code\s*=\s*result\.returncode',
    r'\.logs\s*=\s*',
    
    # 异常处理模式
    r'except subprocess\.TimeoutExpired:',
    r'execution\.status\s*=\s*[\'"]failed[\'"].*timeout',
]

# 需要检查的文件扩展名
FILE_EXTENSIONS = ['.py']

# 需要排除的目录
EXCLUDE_DIRS = [
    '__pycache__',
    '.git',
    'migrations',
    'common',  # 排除我们刚创建的common目录
    'venv',
    'env',
    'node_modules'
]

def find_files_to_check(root_dir):
    """查找需要检查的Python文件"""
    files_to_check = []
    
    for root, dirs, files in os.walk(root_dir):
        # 排除指定目录
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            if any(file.endswith(ext) for ext in FILE_EXTENSIONS):
                files_to_check.append(os.path.join(root, file))
    
    return files_to_check

def check_file_for_patterns(file_path):
    """检查文件中是否包含需要重构的模式"""
    matches = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                for pattern in PATTERNS_TO_REFACTOR:
                    if re.search(pattern, line, re.IGNORECASE):
                        matches.append({
                            'line_number': i,
                            'line_content': line.strip(),
                            'pattern': pattern
                        })
    
    except (UnicodeDecodeError, PermissionError):
        # 跳过无法读取的文件
        pass
    
    return matches

def generate_refactor_report(root_dir):
    """生成重构报告"""
    print("🔍 执行日志重构检查报告")
    print("=" * 60)
    print()
    
    files_to_check = find_files_to_check(root_dir)
    files_with_patterns = {}
    total_matches = 0
    
    for file_path in files_to_check:
        matches = check_file_for_patterns(file_path)
        if matches:
            rel_path = os.path.relpath(file_path, root_dir)
            files_with_patterns[rel_path] = matches
            total_matches += len(matches)
    
    if not files_with_patterns:
        print("✅ 未发现需要重构的代码模式")
        return
    
    print(f"📊 总共发现 {len(files_with_patterns)} 个文件包含 {total_matches} 个需要重构的代码模式")
    print()
    
    # 按优先级排序文件
    priority_files = []
    for file_path, matches in files_with_patterns.items():
        priority = calculate_priority(file_path, matches)
        priority_files.append((priority, file_path, matches))
    
    priority_files.sort(reverse=True)
    
    for priority, file_path, matches in priority_files:
        print(f"🔥 {file_path} (优先级: {priority})")
        print(f"   发现 {len(matches)} 个需要重构的模式:")
        
        for match in matches[:5]:  # 只显示前5个匹配
            print(f"   📍 第{match['line_number']}行: {match['line_content']}")
        
        if len(matches) > 5:
            print(f"   ... 还有 {len(matches) - 5} 个匹配")
        
        print()
    
    print("💡 重构建议:")
    print("1. 优先重构高优先级文件")
    print("2. 使用 ExecutionLogger 替换重复的日志记录代码")
    print("3. 参考 common/execution_logger_usage.md 了解使用方法")
    print("4. 测试每个重构的文件以确保功能正常")

def calculate_priority(file_path, matches):
    """计算文件重构优先级"""
    priority = len(matches)  # 基础优先级 = 匹配数量
    
    # 核心执行器文件优先级更高
    if 'executor' in file_path.lower():
        priority += 20
    
    # 任务文件优先级较高
    if 'tasks.py' in file_path:
        priority += 15
    
    # 服务文件优先级较高
    if 'services' in file_path:
        priority += 10
    
    # 集成文件优先级中等
    if 'integration' in file_path:
        priority += 5
    
    return priority

def suggest_refactoring(file_path, matches):
    """为特定文件提供重构建议"""
    suggestions = []
    
    status_patterns = [m for m in matches if '.status' in m['line_content']]
    time_patterns = [m for m in matches if 'started_at' in m['line_content'] or 'completed_at' in m['line_content']]
    result_patterns = [m for m in matches if any(field in m['line_content'] for field in ['stdout', 'stderr', 'return_code'])]
    
    if status_patterns and time_patterns:
        suggestions.append("可以使用 ExecutionLogger.start_execution() 和 ExecutionLogger.complete_execution()")
    
    if result_patterns:
        suggestions.append("可以将 subprocess 结果直接传递给 ExecutionLogger.complete_execution()")
    
    timeout_patterns = [m for m in matches if 'timeout' in m['line_content'].lower()]
    if timeout_patterns:
        suggestions.append("可以使用 ExecutionLogger.timeout_execution() 处理超时")
    
    return suggestions

if __name__ == "__main__":
    # 获取项目根目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # 上一级目录
    
    print(f"检查目录: {project_root}")
    print()
    
    generate_refactor_report(project_root)
