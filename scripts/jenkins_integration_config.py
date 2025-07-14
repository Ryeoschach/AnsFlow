#!/usr/bin/env python3
"""
Jenkins集成测试配置文件
配置Jenkins连接信息和测试参数
"""

import os
from typing import Dict, Any

class JenkinsTestConfig:
    """Jenkins测试配置类"""
    
    def __init__(self):
        # Jenkins连接配置
        self.jenkins_url = os.getenv('JENKINS_URL', 'http://localhost:8080')
        self.jenkins_username = os.getenv('JENKINS_USERNAME', 'admin')
        self.jenkins_token = os.getenv('JENKINS_TOKEN', '')
        
        # 测试配置
        self.test_timeout = int(os.getenv('TEST_TIMEOUT', '600'))  # 10分钟
        self.cleanup_jobs = os.getenv('CLEANUP_JOBS', 'true').lower() == 'true'
        self.verify_ssl = os.getenv('VERIFY_SSL', 'false').lower() == 'true'
        
        # AnsFlow后端配置
        self.ansflow_api_url = os.getenv('ANSFLOW_API_URL', 'http://localhost:8000/api')
        self.use_ansflow_api = os.getenv('USE_ANSFLOW_API', 'true').lower() == 'true'
        
        # 测试用例配置
        self.test_cases = [
            {
                'name': 'simple_parallel',
                'description': '简单并行组测试',
                'parallel_groups': 1,
                'max_steps_per_group': 3,
                'timeout': 300
            },
            {
                'name': 'complex_parallel',
                'description': '复杂并行组测试',
                'parallel_groups': 2,
                'max_steps_per_group': 5,
                'timeout': 600
            },
            {
                'name': 'nested_parallel',
                'description': '嵌套并行组测试',
                'parallel_groups': 3,
                'max_steps_per_group': 4,
                'timeout': 900
            }
        ]
    
    def validate_config(self) -> Dict[str, Any]:
        """验证配置有效性"""
        errors = []
        warnings = []
        
        # 检查必需的配置
        if not self.jenkins_url:
            errors.append("Jenkins URL is required")
        
        if not self.jenkins_username:
            warnings.append("Jenkins username not set, using default 'admin'")
        
        if not self.jenkins_token:
            warnings.append("Jenkins token not set, authentication may fail")
        
        # 检查URL格式
        if self.jenkins_url and not (self.jenkins_url.startswith('http://') or self.jenkins_url.startswith('https://')):
            errors.append("Jenkins URL must start with http:// or https://")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def get_jenkins_auth(self) -> tuple:
        """获取Jenkins认证信息"""
        return (self.jenkins_username, self.jenkins_token)
    
    def get_test_case_by_name(self, name: str) -> Dict[str, Any]:
        """根据名称获取测试用例配置"""
        for test_case in self.test_cases:
            if test_case['name'] == name:
                return test_case
        return {}
    
    def print_config_summary(self):
        """打印配置摘要"""
        print("=== Jenkins集成测试配置 ===")
        print(f"Jenkins URL: {self.jenkins_url}")
        print(f"Jenkins用户: {self.jenkins_username}")
        print(f"Jenkins Token: {'***设置***' if self.jenkins_token else '未设置'}")
        print(f"AnsFlow API: {self.ansflow_api_url}")
        print(f"使用AnsFlow API: {self.use_ansflow_api}")
        print(f"测试超时: {self.test_timeout}秒")
        print(f"清理测试Job: {self.cleanup_jobs}")
        print(f"验证SSL: {self.verify_ssl}")
        print(f"测试用例数量: {len(self.test_cases)}")
        print("========================")


# 配置使用示例
if __name__ == "__main__":
    config = JenkinsTestConfig()
    config.print_config_summary()
    
    validation = config.validate_config()
    if validation['valid']:
        print("✅ 配置验证通过")
    else:
        print("❌ 配置验证失败:")
        for error in validation['errors']:
            print(f"  - {error}")
    
    if validation['warnings']:
        print("⚠️ 配置警告:")
        for warning in validation['warnings']:
            print(f"  - {warning}")
