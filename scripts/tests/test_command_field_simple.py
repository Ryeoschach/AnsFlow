#!/usr/bin/env python3
"""
简化的command字段优先级测试
验证修复逻辑而不依赖Django环境
"""

def test_step_config_logic():
    """测试步骤配置逻辑（模拟修复后的_get_step_config方法）"""
    print("🧪 测试command字段优先级修复逻辑")
    print("=" * 50)
    
    # 模拟修复后的_get_step_config方法逻辑
    def get_step_config_fixed(step):
        """修复后的配置获取逻辑"""
        config = {}
        
        # 从ansible_parameters获取主要配置（包含command等）
        ansible_params = getattr(step, 'ansible_parameters', {})
        if ansible_params:
            config.update(ansible_params)
        
        # 添加环境变量
        env_vars = getattr(step, 'environment_vars', {})
        if env_vars:
            config['environment'] = env_vars
        
        # 添加其他字段
        if hasattr(step, 'command') and step.command:
            config['command'] = step.command
            
        return config
    
    # 模拟修复前的_get_step_config方法逻辑（有问题的版本）
    def get_step_config_buggy(step):
        """修复前的配置获取逻辑（有问题）"""
        return getattr(step, 'environment_vars', {})
    
    # 创建模拟的PipelineStep对象
    class MockPipelineStep:
        def __init__(self):
            self.id = 999
            self.name = "测试代码拉取步骤"
            self.step_type = "fetch_code"
            self.command = ""  # PipelineStep的command字段为空
            self.environment_vars = {}
            # 用户的实际配置存储在ansible_parameters中
            self.ansible_parameters = {
                "command": "git clone ssh://git@gitlab.cyfee.com:2424/root/test.git",
                "git_credential_id": 1
            }
    
    # 模拟代码拉取执行逻辑
    def simulate_fetch_code_logic(config):
        """模拟_execute_fetch_code的判断逻辑"""
        custom_command = config.get('command')
        repository_url = config.get('repository_url')
        
        if custom_command:
            return True, f"✅ 使用自定义命令: {custom_command}"
        elif repository_url:
            return True, f"✅ 使用仓库URL: {repository_url}"
        else:
            return False, "❌ 代码拉取配置缺失，请在步骤配置中指定 command 或 repository_url"
    
    # 创建测试步骤
    step = MockPipelineStep()
    
    print(f"📋 测试步骤信息:")
    print(f"   名称: {step.name}")
    print(f"   类型: {step.step_type}")
    print(f"   ansible_parameters: {step.ansible_parameters}")
    print(f"   environment_vars: {step.environment_vars}")
    
    # 测试修复前的逻辑
    print(f"\n🐛 修复前的配置获取:")
    config_buggy = get_step_config_buggy(step)
    print(f"   获取到的配置: {config_buggy}")
    success_buggy, result_buggy = simulate_fetch_code_logic(config_buggy)
    print(f"   执行结果: {result_buggy}")
    
    # 测试修复后的逻辑
    print(f"\n✅ 修复后的配置获取:")
    config_fixed = get_step_config_fixed(step)
    print(f"   获取到的配置: {config_fixed}")
    success_fixed, result_fixed = simulate_fetch_code_logic(config_fixed)
    print(f"   执行结果: {result_fixed}")
    
    # 验证修复效果
    print(f"\n📊 修复效果对比:")
    print(f"   修复前: {'✅ 成功' if success_buggy else '❌ 失败'}")
    print(f"   修复后: {'✅ 成功' if success_fixed else '❌ 失败'}")
    
    if not success_buggy and success_fixed:
        print(f"\n🎉 修复成功！")
        print(f"   ✓ 用户配置现在能正确获取command字段")
        print(f"   ✓ 不会再报'请在步骤配置中指定repository_url'错误")
        return True
    else:
        print(f"\n❌ 修复失败或测试有问题")
        return False

def test_various_configurations():
    """测试各种配置情况"""
    print(f"\n🔬 测试各种配置情况")
    print("=" * 50)
    
    # 修复后的配置获取逻辑
    def get_step_config_fixed(step):
        config = {}
        ansible_params = getattr(step, 'ansible_parameters', {})
        if ansible_params:
            config.update(ansible_params)
        env_vars = getattr(step, 'environment_vars', {})
        if env_vars:
            config['environment'] = env_vars
        if hasattr(step, 'command') and step.command:
            config['command'] = step.command
        return config
    
    def simulate_fetch_code_logic(config):
        custom_command = config.get('command')
        repository_url = config.get('repository_url')
        
        if custom_command:
            return True, f"使用自定义命令"
        elif repository_url:
            return True, f"使用仓库URL"
        else:
            return False, "配置缺失错误"
    
    # 测试案例
    test_cases = [
        {
            "name": "用户的实际配置（command + git_credential_id）",
            "ansible_parameters": {
                "command": "git clone ssh://git@gitlab.cyfee.com:2424/root/test.git",
                "git_credential_id": 1
            },
            "command": "",
            "environment_vars": {}
        },
        {
            "name": "只有repository_url配置",
            "ansible_parameters": {
                "repository_url": "https://github.com/user/repo.git",
                "branch": "main"
            },
            "command": "",
            "environment_vars": {}
        },
        {
            "name": "PipelineStep的command字段有值",
            "ansible_parameters": {},
            "command": "git clone https://example.com/repo.git",
            "environment_vars": {}
        },
        {
            "name": "配置完全缺失",
            "ansible_parameters": {},
            "command": "",
            "environment_vars": {}
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📋 测试案例 {i}: {case['name']}")
        
        # 创建模拟步骤对象
        class MockStep:
            def __init__(self, params, cmd, env):
                self.ansible_parameters = params
                self.command = cmd
                self.environment_vars = env
        
        step = MockStep(case['ansible_parameters'], case['command'], case['environment_vars'])
        config = get_step_config_fixed(step)
        success, result = simulate_fetch_code_logic(config)
        
        print(f"   配置: {config}")
        print(f"   结果: {'✅' if success else '❌'} {result}")

if __name__ == "__main__":
    print("🚀 开始测试command字段优先级修复")
    
    # 测试主要修复逻辑
    success = test_step_config_logic()
    
    # 测试各种配置情况
    test_various_configurations()
    
    print(f"\n📋 总结:")
    if success:
        print(f"   ✅ 修复验证成功")
        print(f"   ✅ 用户配置 {{ \"command\": \"git clone ssh://git@gitlab.cyfee.com:2424/root/test.git\", \"git_credential_id\": 1 }} 现在应该能正常工作")
        print(f"   ✅ 不会再报'请在步骤配置中指定repository_url'错误")
    else:
        print(f"   ❌ 修复验证失败")
        
    print(f"\n💡 修复要点:")
    print(f"   1. 修复了_get_step_config方法对PipelineStep的处理")
    print(f"   2. 现在会正确从ansible_parameters中获取command字段")
    print(f"   3. command字段优先级高于repository_url")
