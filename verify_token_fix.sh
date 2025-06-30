#!/bin/bash

# Token/密码更新问题修复验证脚本

echo "🔧 Token/密码更新问题修复验证"
echo "=================================="

# 检查后端是否运行
echo "1. 检查后端服务状态..."
if curl -s http://localhost:8000/api/ > /dev/null 2>&1; then
    echo "✅ 后端服务正常运行"
else
    echo "❌ 后端服务未运行，请先启动: make dev-up"
    exit 1
fi

# 检查前端是否运行  
echo "2. 检查前端服务状态..."
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ 前端服务正常运行"
else
    echo "❌ 前端服务未运行，请先启动: cd frontend && npm run dev"
    exit 1
fi

echo ""
echo "🧪 验证步骤："
echo "1. 访问 http://localhost:3000/tools"
echo "2. 点击'添加工具'创建一个Jenkins工具"
echo "3. 填写所有信息包括密码/Token"
echo "4. 创建成功后，观察'认证状态'列应显示'已配置'"
echo "5. 点击'编辑'按钮，修改工具名称但保持密码为空"
echo "6. 更新后，'认证状态'应仍然显示'已配置'"
echo "7. 再次编辑，输入新的密码/Token"
echo "8. 更新后，应自动进行健康检查验证"
echo ""

echo "📋 期望结果："
echo "- ✅ 创建工具时密码正确保存"
echo "- ✅ 编辑时密码留空不会清空已保存密码"
echo "- ✅ 编辑时输入新密码会正确更新"
echo "- ✅ 认证状态正确显示'已配置'或'未配置'"
echo "- ✅ 更新密码后自动验证认证信息"
echo ""

echo "🔍 如果发现问题，请检查："
echo "1. 浏览器开发者工具的网络请求"
echo "2. 后端日志: docker logs ansflow-django-1 -f"
echo "3. API响应中是否包含has_token字段"
echo ""

echo "✨ 修复完成！请按照上述步骤进行验证。"
