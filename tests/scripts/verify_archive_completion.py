#!/usr/bin/env python3
"""
项目归档整理完成验证脚本
验证所有文档和测试脚本是否已正确归档
"""

import os
import sys
from pathlib import Path

def main():
    """主验证函数"""
    base_path = Path(__file__).parent.parent.parent
    
    print("🔍 项目归档整理验证报告")
    print("=" * 50)
    
    # 验证目录结构
    expected_dirs = {
        "docs/reports": "项目报告归档",
        "docs/guides": "使用指南归档", 
        "docs/showcase": "展示页面归档",
        "tests/integration": "集成测试脚本",
        "tests/frontend": "前端测试页面",
        "tests/scripts": "调试和修复脚本"
    }
    
    print("📂 目录结构验证:")
    all_dirs_exist = True
    for dir_path, description in expected_dirs.items():
        full_path = base_path / dir_path
        if full_path.exists():
            file_count = len(list(full_path.iterdir()))
            print(f"  ✅ {dir_path} - {description} ({file_count} 个文件)")
        else:
            print(f"  ❌ {dir_path} - 目录不存在")
            all_dirs_exist = False
    
    # 验证根目录清理
    print(f"\n📁 根目录清理验证:")
    root_files = list(base_path.iterdir())
    expected_root_files = {
        "README.md", "LICENSE", "Makefile", "docker-compose.yml",
        "requirements.txt", "uv-setup.sh", ".gitignore", ".env.example",
        "backend", "frontend", "deployment", "monitoring", "scripts", 
        "docs", "tests", ".git", "项目说明", "README_NEW.md"
    }
    
    unexpected_files = []
    for item in root_files:
        if item.name not in expected_root_files:
            # 检查是否为测试脚本或说明文档
            if (item.name.endswith('.py') and 'test_' in item.name) or \
               (item.name.endswith('.md') and item.name not in ['README.md']):
                unexpected_files.append(item.name)
    
    if not unexpected_files:
        print("  ✅ 根目录已清理，无多余的测试脚本或说明文档")
    else:
        print(f"  ⚠️  根目录仍有未归档文件: {', '.join(unexpected_files)}")
    
    # 验证关键文档存在
    print(f"\n📖 关键文档验证:")
    key_docs = {
        "README.md": "项目主说明文档",
        "docs/README.md": "文档目录说明",
        "docs/PROJECT_STRUCTURE.md": "项目结构文档",
        "docs/QUICK_START_GUIDE.md": "快速开始指南"
    }
    
    docs_complete = True
    for doc_path, description in key_docs.items():
        full_path = base_path / doc_path
        if full_path.exists():
            print(f"  ✅ {doc_path} - {description}")
        else:
            print(f"  ❌ {doc_path} - 文档缺失")
            docs_complete = False
    
    # 统计归档文件数量
    print(f"\n📊 归档文件统计:")
    total_archived = 0
    for dir_path in expected_dirs.keys():
        full_path = base_path / dir_path
        if full_path.exists():
            count = len([f for f in full_path.iterdir() if f.is_file()])
            total_archived += count
            print(f"  📁 {dir_path}: {count} 个文件")
    
    print(f"\n📈 总计归档文件: {total_archived} 个")
    
    # 总体验证结果
    print(f"\n🎯 验证结果:")
    if all_dirs_exist and not unexpected_files and docs_complete:
        print("  ✅ 项目归档整理完全成功！")
        print("  ✅ 所有目录结构正确")
        print("  ✅ 根目录已清理")
        print("  ✅ 关键文档齐全")
        return True
    else:
        print("  ⚠️  项目归档整理存在问题，请检查上述报告")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
