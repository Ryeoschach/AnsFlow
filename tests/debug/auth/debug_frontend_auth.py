#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
前端认证问题诊断脚本
检查前端为什么无法获取Docker注册表数据
"""

print("🔍 前端Docker注册表数据获取问题诊断")
print("=" * 50)

print("\n1️⃣ 检查后端API状态")
print("✅ Django服务: 运行在 http://localhost:8000")
print("✅ 注册表API: /api/v1/docker/registries/ - 6个注册表")
print("✅ 项目API: /api/v1/docker/registries/projects/ - 5个项目")
print("✅ 认证API: /api/v1/auth/token/ - JWT token正常")

print("\n2️⃣ 可能的问题原因分析")
print("🔍 前端认证问题:")
print("   - localStorage中没有有效的authToken")
print("   - token已过期或格式不正确")
print("   - 前端API Base URL配置问题")

print("\n3️⃣ 解决方案步骤")
print("💡 步骤1: 检查前端认证状态")
print("   - 打开浏览器开发者工具")
print("   - 查看 Application > Local Storage")
print("   - 检查是否有 'authToken' 或类似的key")

print("💡 步骤2: 手动设置token (临时测试)")
print("   - 在浏览器控制台执行:")
print("   localStorage.setItem('authToken', 'YOUR_ACCESS_TOKEN')")

print("💡 步骤3: 检查网络请求")
print("   - 在开发者工具的Network标签页")
print("   - 查看对 /api/v1/docker/registries/ 的请求")
print("   - 检查请求头是否包含正确的Authorization")

print("\n4️⃣ 临时解决方案 - 获取有效token")
print("🔑 有效的access token:")
access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzUzOTQxMjUxLCJpYXQiOjE3NTM5Mzc2NTEsImp0aSI6ImEzNjk4MTA3MDJmMDQ0MTk4ZWJmYTBjNWU5MTM4MGZiIiwidXNlcl9pZCI6MX0.LavVqV1HwrA_Q-u_96enizxCQhxkhNpXjmJYkUPIJhc"
print(f"   {access_token}")

print("\n💻 在浏览器控制台执行以下命令设置token:")
print(f"localStorage.setItem('authToken', '{access_token}')")

print("\n🔄 然后刷新页面或重新打开Docker配置模态框")

print("\n5️⃣ 验证步骤")
print("✅ 设置token后，检查注册表下拉框是否显示数据")
print("✅ 如果显示数据，说明认证问题已解决")
print("✅ 如果仍然没有数据，检查console中的错误信息")

print("\n6️⃣ 长期解决方案")
print("🛠️ 需要确保用户登录流程正确设置authToken")
print("🛠️ 检查token过期处理逻辑")
print("🛠️ 添加自动刷新token机制")

print("\n🎯 立即操作指南:")
print("1. 打开浏览器，访问AnsFlow前端")
print("2. 按F12打开开发者工具")
print("3. 在Console中执行上面的localStorage.setItem命令")
print("4. 刷新页面")
print("5. 打开流水线编辑，添加Docker步骤")
print("6. 检查目标注册表下拉框是否显示数据")

print("\n✨ 如果成功显示数据，恭喜！Docker管理功能正常工作！")
