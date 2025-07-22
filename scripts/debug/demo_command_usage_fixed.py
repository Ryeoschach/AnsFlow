#!/usr/bin/env python3
"""
Command字段优先级修复 - 用法演示

演示修复后支持的各种配置方式
"""

def demonstrate_usage():
    """演示修复后的用法"""
    print("🎯 Command字段优先级修复 - 用法演示")
    print("=" * 60)
    
    configurations = [
        {
            "name": "用户的实际配置（SSH Git克隆）",
            "description": "使用SSH方式克隆GitLab私有仓库",
            "config": {
                "command": "git clone ssh://git@gitlab.cyfee.com:2424/root/test.git",
                "git_credential_id": 1
            },
            "notes": [
                "✅ command字段优先级最高",
                "✅ 支持SSH认证",
                "✅ 自动使用指定的Git凭据"
            ]
        },
        {
            "name": "标准HTTPS仓库配置",
            "description": "使用HTTPS方式访问公开或私有仓库",
            "config": {
                "repository_url": "https://github.com/company/project.git",
                "branch": "develop",
                "git_credential_id": 2
            },
            "notes": [
                "✅ 标准的repository_url方式",
                "✅ 指定分支",
                "✅ 支持HTTPS认证"
            ]
        },
        {
            "name": "复杂的自定义Git命令",
            "description": "使用复杂的Git命令进行浅克隆",
            "config": {
                "command": "git clone --depth 1 --branch main --single-branch https://github.com/example/repo.git .",
                "git_credential_id": 3
            },
            "notes": [
                "✅ 支持Git命令参数",
                "✅ 浅克隆优化",
                "✅ 单分支克隆"
            ]
        },
        {
            "name": "多步骤Git操作",
            "description": "克隆后执行额外的Git操作",
            "config": {
                "command": "git clone ssh://git@internal.com:2424/team/service.git && cd service && git submodule update --init --recursive",
                "git_credential_id": 4
            },
            "notes": [
                "✅ 支持复合命令",
                "✅ 自动处理子模块",
                "✅ 内部服务器支持"
            ]
        },
        {
            "name": "带环境变量的配置",
            "description": "结合环境变量进行代码拉取",
            "config": {
                "command": "git clone ${GIT_REPO_URL}",
                "git_credential_id": 5,
                "environment": {
                    "GIT_REPO_URL": "ssh://git@gitlab.example.com:2424/project/app.git"
                }
            },
            "notes": [
                "✅ 支持环境变量替换",
                "✅ 灵活的配置方式",
                "✅ 便于多环境管理"
            ]
        }
    ]
    
    for i, config_example in enumerate(configurations, 1):
        print(f"\n📋 示例 {i}: {config_example['name']}")
        print(f"📝 描述: {config_example['description']}")
        print(f"⚙️  配置:")
        
        import json
        print(json.dumps(config_example['config'], indent=2, ensure_ascii=False))
        
        print(f"💡 特点:")
        for note in config_example['notes']:
            print(f"   {note}")

def show_migration_guide():
    """显示迁移指南"""
    print(f"\n🚀 迁移指南")
    print("=" * 60)
    
    print(f"\n📖 如果你之前遇到了错误，现在可以这样修复：")
    
    migration_examples = [
        {
            "before": "❌ 之前会报错的配置",
            "before_config": {
                "command": "git clone ssh://git@gitlab.cyfee.com:2424/root/test.git",
                "git_credential_id": 1
            },
            "before_error": "代码拉取配置缺失，请在步骤配置中指定 command 或 repository_url",
            "after": "✅ 现在正常工作",
            "after_result": "使用自定义命令执行代码拉取，支持SSH认证"
        }
    ]
    
    for example in migration_examples:
        print(f"\n{example['before']}:")
        import json
        print(json.dumps(example['before_config'], indent=2, ensure_ascii=False))
        print(f"错误信息: {example['before_error']}")
        
        print(f"\n{example['after']}:")
        print(json.dumps(example['before_config'], indent=2, ensure_ascii=False))
        print(f"执行结果: {example['after_result']}")

def show_best_practices():
    """显示最佳实践"""
    print(f"\n💎 最佳实践")
    print("=" * 60)
    
    practices = [
        {
            "title": "选择合适的配置方式",
            "tips": [
                "🎯 对于简单的公开仓库，使用 repository_url",
                "🎯 对于需要特殊参数的Git操作，使用 command",
                "🎯 对于私有仓库，务必配置 git_credential_id"
            ]
        },
        {
            "title": "Git凭据管理",
            "tips": [
                "🔐 SSH密钥方式最安全，推荐用于私有仓库",
                "🔐 Personal Access Token适用于HTTPS方式",
                "🔐 避免在command中直接包含密码"
            ]
        },
        {
            "title": "性能优化",
            "tips": [
                "⚡ 使用 --depth 1 进行浅克隆",
                "⚡ 使用 --single-branch 只拉取需要的分支",
                "⚡ 大型仓库考虑使用 --filter 参数"
            ]
        },
        {
            "title": "错误处理",
            "tips": [
                "🔧 确保Git凭据配置正确",
                "🔧 检查网络连接和服务器可访问性",
                "🔧 验证仓库URL和分支名称"
            ]
        }
    ]
    
    for practice in practices:
        print(f"\n📚 {practice['title']}:")
        for tip in practice['tips']:
            print(f"   {tip}")

if __name__ == "__main__":
    print("🎉 Command字段优先级已修复！")
    
    # 演示用法
    demonstrate_usage()
    
    # 迁移指南
    show_migration_guide()
    
    # 最佳实践
    show_best_practices()
    
    print(f"\n🎊 总结:")
    print(f"   ✅ 用户配置现在可以正常工作")
    print(f"   ✅ command字段优先级高于repository_url")
    print(f"   ✅ 支持复杂的Git操作和认证")
    print(f"   ✅ 保持向下兼容")
    
    print(f"\n📞 如果还有问题，请检查:")
    print(f"   1. Git凭据配置是否正确")
    print(f"   2. 网络连接和服务器访问权限")
    print(f"   3. Git命令语法是否正确")
