"""
测试DockerRegistry auth_config字段的密码提取
"""

def test_auth_config_password_extraction():
    """测试从auth_config中提取密码"""
    
    # 模拟DockerRegistry的auth_config
    class MockDockerRegistry:
        def __init__(self, url, username, auth_config):
            self.url = url
            self.username = username
            self.auth_config = auth_config
    
    # 测试正常的auth_config
    registry = MockDockerRegistry(
        url='https://gitlab.cyfee.com:8443',
        username='gitlab-ci-token',
        auth_config={'password': 'glpat-abcd1234'}
    )
    
    # 模拟修复后的密码提取逻辑
    password = None
    if registry.auth_config and isinstance(registry.auth_config, dict):
        password = registry.auth_config.get('password')
    
    print(f"注册表URL: {registry.url}")
    print(f"用户名: {registry.username}")
    print(f"密码提取结果: {password}")
    print(f"是否有密码: {bool(password)}")
    
    # 测试空的auth_config
    empty_registry = MockDockerRegistry(
        url='https://example.com',
        username='test',
        auth_config=None
    )
    
    password_empty = None
    if empty_registry.auth_config and isinstance(empty_registry.auth_config, dict):
        password_empty = empty_registry.auth_config.get('password')
    
    print(f"\n空auth_config测试:")
    print(f"密码提取结果: {password_empty}")
    print(f"是否有密码: {bool(password_empty)}")
    
    # 测试不是字典的auth_config
    invalid_registry = MockDockerRegistry(
        url='https://example.com',
        username='test',
        auth_config='invalid_format'
    )
    
    password_invalid = None
    if invalid_registry.auth_config and isinstance(invalid_registry.auth_config, dict):
        password_invalid = invalid_registry.auth_config.get('password')
    
    print(f"\n无效auth_config测试:")
    print(f"密码提取结果: {password_invalid}")
    print(f"是否有密码: {bool(password_invalid)}")

def test_image_name_construction():
    """测试镜像名称构建逻辑"""
    
    # 测试私有仓库镜像名称构建
    registry_url = 'https://gitlab.cyfee.com:8443'
    image = 'test'
    tag = '072201'
    
    # 移除协议前缀
    registry_host = registry_url.replace('https://', '').replace('http://', '')
    
    # 构建完整镜像名称
    full_image_name = f"{registry_host}/{image}:{tag}"
    
    print(f"\n镜像名称构建测试:")
    print(f"注册表URL: {registry_url}")
    print(f"镜像名: {image}")
    print(f"标签: {tag}")
    print(f"构建后的完整镜像名: {full_image_name}")

if __name__ == "__main__":
    print("🔍 测试DockerRegistry认证修复...")
    test_auth_config_password_extraction()
    test_image_name_construction()
    print("\n✅ 认证配置测试完成！")
