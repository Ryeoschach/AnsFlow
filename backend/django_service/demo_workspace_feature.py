#!/usr/bin/env python
"""
工作目录功能演示脚本
展示流水线执行时的工作目录隔离效果
"""

import os
import sys
import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
django.setup()

from cicd_integrations.executors.execution_context import ExecutionContext

def demo_pipeline_execution():
    """演示流水线执行中的工作目录使用"""
    print("🚀 流水线工作目录演示")
    print("=" * 50)
    
    # 模拟三个不同的流水线同时执行
    pipelines = [
        {"name": "前端构建", "execution_id": 1001},
        {"name": "后端API", "execution_id": 1002}, 
        {"name": "Docker镜像构建", "execution_id": 1003}
    ]
    
    contexts = []
    
    print("\n📋 第一阶段：创建流水线执行上下文")
    for pipeline in pipelines:
        context = ExecutionContext(
            execution_id=pipeline["execution_id"],
            pipeline_name=pipeline["name"],
            trigger_type="manual"
        )
        contexts.append(context)
        
        workspace = context.get_workspace_path()
        print(f"✅ {pipeline['name']} -> {workspace}")
    
    print("\n📂 第二阶段：在各自工作目录中执行任务")
    
    # 前端构建流水线
    print(f"\n🔨 {pipelines[0]['name']} 流水线执行:")
    context1 = contexts[0]
    
    # 切换到工作目录
    current_dir = context1.change_directory()
    print(f"   📁 工作目录: {current_dir}")
    
    # 模拟代码检出
    code_dir = context1.change_directory("code")
    print(f"   📁 代码目录: {code_dir}")
    
    # 创建模拟文件
    package_json = context1.resolve_path("code/package.json")
    with open(package_json, 'w') as f:
        f.write('{"name": "frontend-app", "version": "1.0.0"}')
    print(f"   📄 创建文件: package.json")
    
    # 构建目录
    build_dir = context1.change_directory("build")
    print(f"   📁 构建目录: {build_dir}")
    
    # 后端API流水线
    print(f"\n🔧 {pipelines[1]['name']} 流水线执行:")
    context2 = contexts[1]
    
    current_dir = context2.change_directory()
    print(f"   📁 工作目录: {current_dir}")
    
    # 模拟代码检出
    code_dir = context2.change_directory("code")
    print(f"   📁 代码目录: {code_dir}")
    
    # 创建模拟文件
    requirements_txt = context2.resolve_path("code/requirements.txt")
    with open(requirements_txt, 'w') as f:
        f.write('django>=4.0\nfastapi>=0.68.0')
    print(f"   📄 创建文件: requirements.txt")
    
    # 测试目录
    test_dir = context2.change_directory("tests")
    print(f"   📁 测试目录: {test_dir}")
    
    # Docker镜像构建流水线
    print(f"\n🐳 {pipelines[2]['name']} 流水线执行:")
    context3 = contexts[2]
    
    current_dir = context3.change_directory()
    print(f"   📁 工作目录: {current_dir}")
    
    # 模拟代码检出
    code_dir = context3.change_directory("code")
    print(f"   📁 代码目录: {code_dir}")
    
    # 创建模拟文件
    dockerfile = context3.resolve_path("code/Dockerfile")
    with open(dockerfile, 'w') as f:
        f.write('FROM python:3.9\nCOPY . /app\nWORKDIR /app')
    print(f"   📄 创建文件: Dockerfile")
    
    # 输出目录
    output_dir = context3.change_directory("output")
    print(f"   📁 输出目录: {output_dir}")
    
    print("\n📊 第三阶段：查看工作目录隔离效果")
    
    for i, context in enumerate(contexts):
        workspace = context.get_workspace_path()
        pipeline_name = pipelines[i]['name']
        
        print(f"\n📁 {pipeline_name} 工作目录内容:")
        
        # 列出工作目录内容
        for root, dirs, files in os.walk(workspace):
            level = root.replace(workspace, '').count(os.sep)
            indent = '  ' * (level + 1)
            relative_path = os.path.relpath(root, workspace)
            if relative_path == '.':
                print(f"{indent}📂 {os.path.basename(workspace)}/")
            else:
                print(f"{indent}📂 {relative_path}/")
            
            subindent = '  ' * (level + 2)
            for file in files:
                print(f"{subindent}📄 {file}")
    
    print("\n🧹 第四阶段：清理工作目录")
    
    # 恢复到原始目录
    original_cwd = os.getcwd()
    os.chdir(original_cwd)
    
    for i, context in enumerate(contexts):
        pipeline_name = pipelines[i]['name']
        context.cleanup_workspace()
        print(f"✅ {pipeline_name} 工作目录已清理")
    
    print("\n🎉 演示完成！")
    print("✨ 关键特性:")
    print("   🔒 每个流水线都有独立的工作目录")
    print("   📁 目录格式: /tmp/流水线名称_执行编号")
    print("   🧹 执行完成后自动清理")
    print("   🛡️ 避免流水线之间的文件冲突")
    print("   📊 便于调试和问题排查")

if __name__ == "__main__":
    demo_pipeline_execution()
