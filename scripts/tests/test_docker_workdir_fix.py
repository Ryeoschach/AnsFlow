#!/usr/bin/env python3
"""
测试Git clone + Docker build完整流程修复
验证Docker执行器能正确使用Git clone后的工作目录
"""

import os
import sys
import tempfile
import subprocess

# 添加后端路径
sys.path.insert(0, '/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
import django
django.setup()

from cicd_integrations.executors.execution_context import ExecutionContext
from cicd_integrations.executors.sync_step_executor import SyncStepExecutor
from unittest.mock import MagicMock

def create_test_git_repo(repo_path):
    """创建测试Git仓库，包含Dockerfile"""
    # 初始化Git仓库
    subprocess.run(['git', 'init'], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=repo_path, check=True)
    subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=repo_path, check=True)
    
    # 创建Dockerfile
    dockerfile_content = """FROM nginx:alpine
COPY . /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
"""
    with open(os.path.join(repo_path, 'Dockerfile'), 'w') as f:
        f.write(dockerfile_content)
    
    # 创建一个简单的index.html
    with open(os.path.join(repo_path, 'index.html'), 'w') as f:
        f.write('<html><body><h1>Test App</h1></body></html>')
    
    # 提交文件
    subprocess.run(['git', 'add', '.'], cwd=repo_path, check=True)
    subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=repo_path, check=True)

def test_docker_working_directory_fix():
    """测试Docker执行器工作目录修复"""
    
    # 1. 创建临时目录作为测试Git仓库
    with tempfile.TemporaryDirectory() as temp_repo_dir:
        test_repo_path = os.path.join(temp_repo_dir, 'test')
        os.makedirs(test_repo_path)
        
        print(f"创建测试Git仓库: {test_repo_path}")
        create_test_git_repo(test_repo_path)
        
        # 2. 创建测试工作目录
        with tempfile.TemporaryDirectory() as workspace_dir:
            print(f"工作目录: {workspace_dir}")
            
            # 3. 创建执行上下文
            context = ExecutionContext(
                execution_id=1,
                pipeline_name="test-docker-workdir",
                trigger_type="manual",
                workspace_path=workspace_dir
            )
            
            # 4. 创建执行器
            executor = SyncStepExecutor(context=context)
            
            # 模拟步骤类型获取方法
            def mock_get_step_type(step_obj):
                if hasattr(step_obj, 'docker_image'):
                    return 'docker_build'
                return 'git_clone'
            
            # 替换执行器的方法
            executor._get_step_type = mock_get_step_type
            
            # 5. 模拟Git clone步骤对象
            from cicd_integrations.models import AtomicStep
            
            git_clone_step = MagicMock(spec=AtomicStep)
            git_clone_step.repository_url = test_repo_path
            git_clone_step.branch = 'main'
            git_clone_step.get_credential_info.return_value = (None, None)
            # 添加config属性以匹配AtomicStep
            git_clone_step.config = {
                'command': f'git clone {test_repo_path}',
                'repository_url': test_repo_path,
                'branch': 'main'
            }
            
            # 6. 执行Git clone
            print("\n=== 步骤1: 执行Git clone ===")
            git_result = executor._execute_fetch_code(
                step_obj=git_clone_step,
                execution_env=os.environ.copy()
            )
            
            print(f"Git clone结果: {git_result['success']}")
            if 'output' in git_result:
                print(f"Git clone输出: {git_result['output']}")
            if 'error_message' in git_result:
                print(f"Git clone错误: {git_result['error_message']}")
            
            if git_result['success']:
                current_dir = context.get_current_directory()
                print(f"Git clone后当前目录: {current_dir}")
                
                # 验证Dockerfile存在
                dockerfile_path = os.path.join(current_dir, 'Dockerfile')
                print(f"Dockerfile路径: {dockerfile_path}")
                print(f"Dockerfile存在: {os.path.exists(dockerfile_path)}")
                
                if os.path.exists(dockerfile_path):
                    # 7. 模拟Docker build步骤对象
                    docker_step = MagicMock()
                    docker_step.docker_image = 'test-workdir'
                    docker_step.docker_tag = 'fix'
                    docker_step.step_type = 'docker_build'
                    docker_step.name = 'Docker Build Test'
                    docker_step.id = 999
                    docker_step.ansible_parameters = {
                        'dockerfile': 'Dockerfile',
                        'context': '.',
                        'docker_image': 'test-workdir',
                        'docker_tag': 'fix'
                    }
                    # 添加config属性
                    docker_step.config = {
                        'dockerfile': 'Dockerfile',
                        'context': '.',
                        'docker_image': 'test-workdir',
                        'docker_tag': 'fix'
                    }
                    
                    # 8. 执行Docker build
                    print("\n=== 步骤2: 执行Docker build ===")
                    docker_result = executor._execute_docker_step(
                        step_obj=docker_step,
                        execution_env=os.environ.copy()
                    )
                    
                    print(f"Docker build结果: {docker_result['success']}")
                    if docker_result['output']:
                        print(f"Docker build输出:\n{docker_result['output']}")
                    
                    if not docker_result['success'] and 'error_message' in docker_result:
                        print(f"Docker build错误: {docker_result['error_message']}")
                    
                    # 9. 验证结果
                    print("\n=== 验证结果 ===")
                    success = git_result['success'] and docker_result['success']
                    print(f"整体测试成功: {success}")
                    
                    if success:
                        print("✅ Git clone + Docker build工作目录修复成功!")
                        print("✅ Docker执行器正确使用了Git clone后的目录")
                    else:
                        print("❌ 工作目录修复测试失败")
                    
                    return success
                else:
                    print("❌ Dockerfile不存在，无法进行Docker测试")
                    return False
            else:
                print("❌ Git clone失败，无法进行后续测试")
                return False

if __name__ == '__main__':
    print("🧪 开始Git clone + Docker build工作目录修复测试")
    print("=" * 60)
    
    try:
        success = test_docker_working_directory_fix()
        exit_code = 0 if success else 1
        
        print("\n" + "=" * 60)
        if success:
            print("🎉 工作目录修复测试通过!")
        else:
            print("💥 工作目录修复测试失败!")
        
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"\n💥 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
