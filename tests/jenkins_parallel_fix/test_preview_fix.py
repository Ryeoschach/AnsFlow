#!/usr/bin/env python
"""
测试脚本：验证预览API中的Jenkins并行语法修复
"""
import os
import sys
import django

# 添加Django项目路径
sys.path.insert(0, '/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_service.settings')
django.setup()

from cicd_integrations.views.pipeline_preview import generate_mock_jenkinsfile_with_parallel

def test_jenkins_parallel_syntax():
    """测试Jenkins并行语法是否使用官方格式"""
    
    # 模拟步骤数据
    test_steps = [
        {
            'id': 1,
            'name': '代码检出',
            'step_type': 'fetch_code',
            'parameters': {'repository': 'https://github.com/test/repo.git'},
            'parallel_group': None,
            'order': 1
        },
        {
            'id': 2,
            'name': '并行测试1',
            'step_type': 'test',
            'parameters': {'test_command': 'npm test'},
            'parallel_group': 'test_group',
            'order': 2
        },
        {
            'id': 3,
            'name': '并行测试2',
            'step_type': 'test',
            'parameters': {'test_command': 'pytest'},
            'parallel_group': 'test_group',
            'order': 3
        },
        {
            'id': 4,
            'name': '部署',
            'step_type': 'deploy',
            'parameters': {'deploy_command': 'kubectl apply -f deployment.yaml'},
            'parallel_group': None,
            'order': 4
        }
    ]
    
    # 模拟并行组数据
    parallel_groups = [
        {
            'name': '测试并行组',
            'steps': [
                {
                    'name': '并行测试1',
                    'step_type': 'test',
                    'parameters': {'test_command': 'npm test'},
                    'order': 2
                },
                {
                    'name': '并行测试2', 
                    'step_type': 'test',
                    'parameters': {'test_command': 'pytest'},
                    'order': 3
                }
            ]
        }
    ]
    
    print("测试 generate_mock_jenkinsfile_with_parallel 函数...")
    
    # 生成Jenkins pipeline
    jenkinsfile = generate_mock_jenkinsfile_with_parallel(test_steps, parallel_groups)
    
    print("\n生成的Jenkinsfile:")
    print("=" * 80)
    print(jenkinsfile)
    print("=" * 80)
    
    # 检查是否使用官方语法
    print("\n语法检查:")
    
    # 检查是否包含官方的stage()语法
    if "stage('并行测试1') {" in jenkinsfile and "stage('并行测试2') {" in jenkinsfile:
        print("✅ 并行步骤使用官方 stage('name') { } 语法")
    else:
        print("❌ 并行步骤未使用官方语法")
    
    # 检查是否没有旧的语法
    if "'并行测试1': {" not in jenkinsfile and "'并行测试2': {" not in jenkinsfile:
        print("✅ 没有发现旧的 'name': { } 语法")
    else:
        print("❌ 仍然存在旧的 'name': { } 语法")
    
    # 检查并行块结构
    if "parallel {" in jenkinsfile:
        print("✅ 包含并行块")
    else:
        print("❌ 未找到并行块")
    
    return jenkinsfile

if __name__ == "__main__":
    try:
        test_jenkins_parallel_syntax()
        print("\n测试完成！")
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
