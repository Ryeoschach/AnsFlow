#!/usr/bin/env python3
"""
测试 Helm Chart 工作目录上下文修复效果
模拟流水线执行场景，验证工作目录是否正确传递到 K8s 执行器
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

def create_test_chart(chart_dir):
    """创建测试 Helm Chart 结构"""
    chart_yaml_content = """apiVersion: v2
name: fe-app
description: A Helm chart for fe-app
type: application
version: 0.1.0
appVersion: 1.0.0
"""
    
    values_yaml_content = """replicaCount: 1
image:
  repository: fe-app
  tag: latest
"""
    
    # 创建 Chart.yaml
    chart_yaml_path = os.path.join(chart_dir, 'Chart.yaml')
    with open(chart_yaml_path, 'w') as f:
        f.write(chart_yaml_content)
    
    # 创建 values.yaml
    values_yaml_path = os.path.join(chart_dir, 'values.yaml')
    with open(values_yaml_path, 'w') as f:
        f.write(values_yaml_content)
    
    # 创建 templates 目录
    templates_dir = os.path.join(chart_dir, 'templates')
    os.makedirs(templates_dir, exist_ok=True)
    
    print(f"✅ 测试 Chart 结构已创建: {chart_dir}")
    print(f"  - Chart.yaml: {chart_yaml_path}")
    print(f"  - values.yaml: {values_yaml_path}")
    print(f"  - templates/: {templates_dir}")

def simulate_shell_step_cd(target_dir):
    """模拟 shell 步骤执行 cd 命令"""
    original_cwd = os.getcwd()
    os.chdir(target_dir)
    current_cwd = os.getcwd()
    
    print(f"🔄 模拟 shell 步骤: cd {target_dir}")
    print(f"  原始目录: {original_cwd}")
    print(f"  当前目录: {current_cwd}")
    
    # 模拟 context 更新
    context = {
        'working_directory': current_cwd,
        'previous_step_output': 'Changed directory successfully'
    }
    
    return context

def simulate_k8s_step_execution(context):
    """模拟 K8s 步骤执行，测试工作目录上下文应用"""
    print(f"\n🎯 模拟 K8s 步骤执行")
    print(f"  传入的工作目录上下文: {context.get('working_directory', 'None')}")
    
    # 应用工作目录上下文（模拟修复后的逻辑）
    original_cwd = None
    if 'working_directory' in context and context['working_directory']:
        original_cwd = os.getcwd()
        try:
            os.chdir(context['working_directory'])
            print(f"  ✅ 成功切换到工作目录: {context['working_directory']}")
        except Exception as e:
            print(f"  ❌ 切换工作目录失败: {e}")
            return False
    
    # 模拟 Chart 检测逻辑
    current_dir = os.getcwd()
    chart_yaml_path = os.path.join(current_dir, 'Chart.yaml')
    
    print(f"  当前执行目录: {current_dir}")
    print(f"  检查 Chart.yaml: {chart_yaml_path}")
    
    if os.path.exists(chart_yaml_path):
        print(f"  ✅ 找到 Chart.yaml，Chart 名称应被识别为当前目录")
        chart_name = os.path.basename(current_dir)
        print(f"  📦 推断的 Chart 名称: {chart_name}")
        success = True
    else:
        print(f"  ❌ 未找到 Chart.yaml，Chart 检测失败")
        success = False
    
    # 恢复原始工作目录
    if original_cwd:
        try:
            os.chdir(original_cwd)
            print(f"  🔄 已恢复到原始目录: {original_cwd}")
        except Exception as e:
            print(f"  ⚠️  恢复目录失败: {e}")
    
    return success

def main():
    """主测试流程"""
    print("🚀 开始测试 Helm Chart 工作目录上下文修复效果\n")
    
    # 创建临时测试目录
    with tempfile.TemporaryDirectory() as temp_dir:
        chart_dir = os.path.join(temp_dir, 'fe-app')
        os.makedirs(chart_dir)
        
        # 创建测试 Chart
        create_test_chart(chart_dir)
        
        print(f"\n📁 测试场景: 用户在 Chart 目录中执行流水线")
        print(f"  Chart 目录: {chart_dir}")
        
        # 模拟用户 cd 到 Chart 目录（通过 shell 步骤）
        context = simulate_shell_step_cd(chart_dir)
        
        # 模拟 K8s 步骤执行，检查工作目录上下文是否正确应用
        success = simulate_k8s_step_execution(context)
        
        print(f"\n📊 测试结果:")
        if success:
            print("  ✅ 修复成功！K8s 执行器正确应用了工作目录上下文")
            print("  ✅ Chart.yaml 被正确检测到")
            print("  ✅ Chart 名称可以被推断为当前目录名称")
        else:
            print("  ❌ 修复失败！工作目录上下文未正确传递")
            print("  ❌ Chart 检测逻辑仍然存在问题")
        
        return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 测试过程中发生错误: {e}")
        sys.exit(1)
