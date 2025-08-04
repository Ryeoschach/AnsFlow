import os
from cicd_integrations.executors.workspace_manager import workspace_manager
from cicd_integrations.executors.execution_context import ExecutionContext

print('=== 测试工作目录隔离功能 ===')

# 测试工作目录管理器
print('\n1. 测试工作目录创建:')
workspace_path = workspace_manager.create_workspace('测试流水线', 9999)
print(f'工作目录: {workspace_path}')
print(f'目录存在: {os.path.exists(workspace_path)}')

# 测试ExecutionContext
print('\n2. 测试ExecutionContext:')
context = ExecutionContext(
    execution_id=9999,
    pipeline_name='测试流水线',
    trigger_type='manual'
)
context_workspace = context.get_workspace_path()
print(f'ExecutionContext工作目录: {context_workspace}')
print(f'两个路径相同: {workspace_path == context_workspace}')

# 检查目录内容
print('\n3. 检查工作目录:')
if os.path.exists(workspace_path):
    files = os.listdir(workspace_path)
    print(f'目录内容: {files}')
    print(f'目录为空: {len(files) == 0}')

# 模拟git clone测试
print('\n4. 模拟git clone测试:')
test_dir = os.path.join(workspace_path, 'test')
print(f'测试目录: {test_dir}')
print(f'test目录存在: {os.path.exists(test_dir)}')

# 在工作目录中创建test目录模拟git clone
os.makedirs(test_dir, exist_ok=True)
with open(os.path.join(test_dir, 'README.md'), 'w') as f:
    f.write('# Test Repository\n')
print(f'创建test目录后存在: {os.path.exists(test_dir)}')

# 清理
workspace_manager.cleanup_workspace(9999, force_cleanup=True)
print(f'\n5. 清理后目录存在: {os.path.exists(workspace_path)}')

print('\n=== 测试完成 ===')
