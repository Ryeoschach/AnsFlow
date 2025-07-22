#!/usr/bin/env python3
"""
脚本来修复 docker_executor.py 中的注册表配置获取问题
"""

def fix_docker_executor():
    file_path = "/Users/creed/Workspace/OpenSource/ansflow/backend/django_service/pipelines/services/docker_executor.py"
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 要插入的代码
    insert_code = """            
            # 如果直接属性中没有注册表信息，尝试从 ansible_parameters 获取
            if not registry:
                step_params = getattr(step, 'ansible_parameters', {})
                registry_id = step_params.get('registry_id')
                if registry_id:
                    from docker_integration.models import DockerRegistry
                    try:
                        registry = DockerRegistry.objects.get(id=registry_id)
                        logger.info(f"[DEBUG] PipelineStep从ansible_parameters获取注册表: {registry.name} ({registry.url})")
                    except DockerRegistry.DoesNotExist:
                        logger.warning(f"[WARNING] PipelineStep中ansible_parameters注册表ID {registry_id} 不存在")
                        registry = None
"""
    
    # 修复第一个位置（docker_push方法，大约第483行）
    for i, line in enumerate(lines):
        if i == 482 and "registry = getattr(step, 'docker_registry', None)" in line:
            # 在这一行后插入新代码
            lines.insert(i + 1, insert_code)
            print(f"✅ 在第 {i+1} 行后插入了修复代码（docker_push方法）")
            break
    
    # 重新读取修改后的内容
    file_content = ''.join(lines)
    
    # 修复第二个位置（docker_pull方法）
    lines = file_content.split('\n')
    for i, line in enumerate(lines):
        if i > 500 and "registry = getattr(step, 'docker_registry', None)" in line and "_execute_docker_pull" in ''.join(lines[max(0, i-50):i]):
            # 在这一行后插入新代码
            lines.insert(i + 1, insert_code.strip())
            print(f"✅ 在第 {i+1} 行后插入了修复代码（docker_pull方法）")
            break
    
    # 写入修改后的文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print("🎉 修复完成！")

if __name__ == "__main__":
    fix_docker_executor()
