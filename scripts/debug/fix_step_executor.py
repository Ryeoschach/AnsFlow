#!/usr/bin/env python3
"""
修复sync_step_executor.py中的方法参数
"""

import re

# 需要修复的方法模式
methods_to_fix = [
    '_execute_build',
    '_execute_test', 
    '_execute_security_scan',
    '_execute_deploy',
    '_execute_notify',
    '_execute_custom',
    '_execute_mock',
    '_execute_docker_step',
    '_execute_docker_fallback'
]

def fix_method_params():
    file_path = '/Users/creed/Workspace/OpenSource/ansflow/backend/django_service/cicd_integrations/executors/sync_step_executor.py'
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 修复方法定义中的参数名
    for method_name in methods_to_fix:
        # 修复方法定义
        pattern = f'def {method_name}\(\s*self,\s*atomic_step[^,]*,\s*execution_env'
        replacement = f'def {method_name}(\n        self,\n        step_obj,\n        execution_env'
        content = re.sub(pattern, replacement, content)
        
        # 修复方法内部使用atomic_step.config的地方
        content = re.sub(f'atomic_step\.config', 'self._get_step_config(step_obj)', content)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ 修复完成")

if __name__ == '__main__':
    fix_method_params()
