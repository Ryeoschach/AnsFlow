#!/usr/bin/env python3
"""
测试Git clone + Docker build完整集成
验证Git clone自动目录检测 + Docker build在正确目录执行
"""

import os
import sys
import tempfile
import shutil
import subprocess
from unittest.mock import patch, MagicMock

# 添加后端路径
sys.path.insert(0, '/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
import django
django.setup()

from cicd_integrations.executors.execution_context import ExecutionContext
from cicd_integrations.executors.sync_step_executor import SyncStepExecutor

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

def test_git_clone_docker_integration():
    """测试Git clone + Docker build完整流程"""
    
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
                pipeline_name="test-pipeline",
                trigger_type="manual",
                workspace_path=workspace_dir
            )
            
            # 4. 创建执行器
            executor = SyncStepExecutor(context=context)
            
            # 5. 模拟Git clone步骤对象
            git_clone_step = MagicMock()
            git_clone_step.repository_url = test_repo_path  # 使用本地路径模拟
            git_clone_step.branch = 'main'
            git_clone_step.get_credential_info.return_value = (None, None)
            
            # 模拟配置获取方法
            def mock_get_step_config(step_obj):
                return {
                    'repository_url': test_repo_path,
                    'branch': 'main',
                    'command': f'git clone {test_repo_path}'
                }
            
            # 模拟步骤类型获取方法
            def mock_get_step_type(step_obj):
                if hasattr(step_obj, 'docker_image'):
                    return 'docker_build'
                return 'git_clone'
            
            # 替换执行器的方法
            executor._get_step_config = mock_get_step_config
            executor._get_step_type = mock_get_step_type
            
            # 6. 执行Git clone（模拟）
            print("\n=== 步骤1: 执行Git clone ===")
            git_result = executor._execute_fetch_code(
                step_obj=git_clone_step,
                execution_env=os.environ.copy()
            )
            
            print(f"Git clone结果: {git_result['success']}")
            if git_result['output']:
                print(f"Git clone输出:\n{git_result['output']}")
            
            # 7. 检查当前工作目录
            current_dir = context.get_current_directory()
            print(f"Git clone后当前目录: {current_dir}")
            
            # 8. 检查是否存在Dockerfile
            dockerfile_path = os.path.join(current_dir, 'Dockerfile')
            print(f"Dockerfile路径: {dockerfile_path}")
            print(f"Dockerfile存在: {os.path.exists(dockerfile_path)}")
            
            if os.path.exists(dockerfile_path):
                print("✅ Dockerfile找到!")
                with open(dockerfile_path, 'r') as f:
                    print(f"Dockerfile内容预览:\n{f.read()[:200]}...")
            
            # 9. 模拟Docker build步骤对象
            docker_step = MagicMock()
            docker_step.docker_image = 'test-app'
            docker_step.docker_tag = 'latest'
            
            # 10. 执行Docker build（使用fallback方法）
            print("\n=== 步骤2: 执行Docker build ===")
            docker_result = executor._execute_docker_fallback(
                step_obj=docker_step,
                execution_env=os.environ.copy()
            )
            
            print(f"Docker build结果: {docker_result['success']}")
            if docker_result['output']:
                print(f"Docker build输出:\n{docker_result['output']}")
            
            if not docker_result['success'] and 'error_message' in docker_result:
                print(f"Docker build错误: {docker_result['error_message']}")
            
            # 11. 验证结果
            print("\n=== 验证结果 ===")
            success = git_result['success'] and docker_result['success']
            print(f"整体测试成功: {success}")
            
            if success:
                print("✅ Git clone + Docker build集成测试通过!")
                print("✅ Git clone自动目录检测工作正常")
                print("✅ Docker build在正确目录执行")
            else:
                print("❌ 集成测试失败")
                if not git_result['success']:
                    print("  - Git clone步骤失败")
                if not docker_result['success']:
                    print("  - Docker build步骤失败")
            
            return success

if __name__ == '__main__':
    print("🧪 开始Git clone + Docker build集成测试")
    print("=" * 50)
    
    try:
        success = test_git_clone_docker_integration()
        exit_code = 0 if success else 1
        
        print("\n" + "=" * 50)
        if success:
            print("🎉 所有集成测试通过!")
        else:
            print("💥 集成测试失败!")
        
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"\n💥 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
