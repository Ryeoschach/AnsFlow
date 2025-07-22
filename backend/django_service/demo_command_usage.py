#!/usr/bin/env python
"""
演示实际使用场景：command字段的优先级
"""

import os
import sys
import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
django.setup()

def demo_command_usage():
    """演示如何在实际流水线中使用command字段"""
    print("📋 代码拉取步骤配置示例")
    print("=" * 50)
    
    print("\n✅ 方式1：使用自定义command字段（高优先级）")
    print("配置示例：")
    config1 = {
        "command": "git clone ssh://git@gitlab.cyfee.com:2424/root/test.git",
        "git_credential_id": 1
    }
    print(f"  {config1}")
    print("说明：")
    print("  - command字段包含完整的git clone命令")
    print("  - 支持SSH协议和自定义端口")
    print("  - git_credential_id用于SSH密钥认证")
    
    print("\n✅ 方式2：使用repository_url字段（回退方案）")
    print("配置示例：")
    config2 = {
        "repository_url": "https://github.com/user/repo.git",
        "branch": "main",
        "git_credential_id": 2
    }
    print(f"  {config2}")
    print("说明：")
    print("  - repository_url用于标准的HTTPS Git仓库")
    print("  - 自动生成 git clone 命令")
    print("  - 支持分支指定")
    
    print("\n✅ 方式3：组合使用（command优先）")
    print("配置示例：")
    config3 = {
        "command": "git clone ssh://git@gitlab.cyfee.com:2424/root/test.git",
        "repository_url": "https://github.com/backup/repo.git",  # 这个会被忽略
        "git_credential_id": 1,
        "branch": "develop"
    }
    print(f"  {config3}")
    print("说明：")
    print("  - 同时存在时，command字段优先")
    print("  - repository_url字段会被忽略")
    print("  - 分支切换会在clone后执行")
    
    print("\n❌ 错误配置：两个字段都缺失")
    print("配置示例：")
    config4 = {
        "branch": "main",
        "git_credential_id": 1
    }
    print(f"  {config4}")
    print("错误信息：")
    print("  '代码拉取配置缺失，请在步骤配置中指定 command 或 repository_url'")
    
    print("\n🔧 Git凭据支持")
    print("=" * 30)
    print("支持的认证类型：")
    print("  1. username_password - 用户名密码")
    print("  2. access_token - 访问令牌")
    print("  3. ssh_key - SSH密钥（推荐用于command字段）")
    
    print("\n📝 实际使用建议")
    print("=" * 30)
    print("1. 对于标准的GitHub/GitLab仓库：使用repository_url")
    print("2. 对于自定义端口或特殊协议：使用command字段")
    print("3. 对于SSH协议：推荐使用command + ssh_key凭据")
    print("4. 始终配置git_credential_id以确保认证成功")
    
    print("\n🎯 修复前后对比")
    print("=" * 30)
    print("修复前：只支持repository_url，缺失时报错")
    print("修复后：优先使用command，回退到repository_url，两者都缺失才报错")
    
    print("\n✨ 总结")
    print("现在您可以在流水线步骤配置中使用：")
    print('{"command": "git clone ssh://git@gitlab.cyfee.com:2424/root/test.git", "git_credential_id": 1}')
    print("这样就解决了'请在步骤配置中指定repository_url'的错误！")

if __name__ == "__main__":
    demo_command_usage()
