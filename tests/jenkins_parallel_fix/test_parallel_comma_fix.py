#!/usr/bin/env python
"""
测试脚本：验证Jenkins并行语法修复（移除stage之间的逗号）
"""
import os
import sys
import django

# 添加Django项目路径
sys.path.insert(0, '/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_service.settings')
django.setup()

from cicd_integrations.views.pipeline_preview import generate_mock_jenkinsfile_with_parallel

def test_parallel_stage_syntax():
    """测试并行stage语法是否移除了逗号"""
    
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
            'name': '222_1',
            'step_type': 'test',
            'parameters': {'test_command': 'echo "Hello World222222222-1"'},
            'parallel_group': 'test_group',
            'order': 2
        },
        {
            'id': 3,
            'name': '222_2',
            'step_type': 'test',
            'parameters': {'test_command': 'echo "Hello World22222-2"'},
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
                    'name': '222_1',
                    'step_type': 'test',
                    'parameters': {'test_command': 'echo "Hello World222222222-1"'},
                    'order': 2
                },
                {
                    'name': '222_2', 
                    'step_type': 'test',
                    'parameters': {'test_command': 'echo "Hello World22222-2"'},
                    'order': 3
                }
            ]
        }
    ]
    
    print("测试并行stage语法（移除逗号）...")
    
    # 生成Jenkins pipeline
    jenkinsfile = generate_mock_jenkinsfile_with_parallel(test_steps, parallel_groups)
    
    print("\n生成的Jenkinsfile:")
    print("=" * 80)
    print(jenkinsfile)
    print("=" * 80)
    
    # 检查语法
    print("\n语法检查:")
    
    # 检查是否使用了正确的stage语法
    if "stage('222_1') {" in jenkinsfile and "stage('222_2') {" in jenkinsfile:
        print("✅ 使用官方 stage('name') { } 语法")
    else:
        print("❌ 未使用官方stage语法")
    
    # 检查是否移除了逗号
    parallel_section = jenkinsfile[jenkinsfile.find("parallel {"):jenkinsfile.find("            }", jenkinsfile.find("parallel {"))]
    
    if "}," not in parallel_section:
        print("✅ 并行stage之间没有逗号分隔符")
    else:
        print("❌ 仍然存在逗号分隔符")
        print(f"问题部分: {parallel_section}")
    
    # 检查期望的格式
    expected_format = """parallel {
                stage('222_1') {
                    steps {
                        sh 'echo "Hello World222222222-1"'
                    }
                }
                stage('222_2') {
                    steps {
                        sh 'echo "Hello World22222-2"'
                    }
                }
            }"""
    
    if "stage('222_1') {" in jenkinsfile and "stage('222_2') {" in jenkinsfile and "}," not in parallel_section:
        print("✅ 生成的格式符合要求")
    else:
        print("❌ 生成的格式不符合要求")
    
    return jenkinsfile

if __name__ == "__main__":
    try:
        test_parallel_stage_syntax()
        print("\n测试完成！")
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
