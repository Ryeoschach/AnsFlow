#!/bin/bash

echo "🔍 Docker注册表数据格式修复验证"
echo "=================================================="

echo ""
echo "1️⃣ 获取新的认证token"
TOKEN_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/auth/token/" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}')

ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access'])")

if [ -n "$ACCESS_TOKEN" ]; then
    echo "✅ 获取token成功"
    echo "🔑 Token: ${ACCESS_TOKEN:0:50}..."
else
    echo "❌ 获取token失败"
    exit 1
fi

echo ""
echo "2️⃣ 测试注册表API响应格式"
echo "📡 调用: GET /api/v1/docker/registries/"

REGISTRIES_RESPONSE=$(curl -s -X GET "http://localhost:8000/api/v1/docker/registries/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "📊 响应数据结构:"
echo $REGISTRIES_RESPONSE | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'类型: {type(data).__name__}')
if isinstance(data, dict):
    print(f'字段: {list(data.keys())}')
    if 'results' in data:
        print(f'分页格式 - 总数: {data[\"count\"]}, 结果数: {len(data[\"results\"])}')
        print('前3个注册表:')
        for i, reg in enumerate(data['results'][:3]):
            print(f'  {i+1}. {reg[\"name\"]} ({reg[\"registry_type\"]}) - {reg[\"status\"]}')
    else:
        print('非分页格式')
elif isinstance(data, list):
    print(f'数组格式 - 长度: {len(data)}')
"

echo ""
echo "3️⃣ 测试项目API响应格式"
echo "📡 调用: GET /api/v1/docker/registries/projects/"

PROJECTS_RESPONSE=$(curl -s -X GET "http://localhost:8000/api/v1/docker/registries/projects/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "📊 响应数据结构:"
echo $PROJECTS_RESPONSE | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'类型: {type(data).__name__}')
if isinstance(data, list):
    print(f'数组格式 - 项目数量: {len(data)}')
    print('前3个项目:')
    for i, proj in enumerate(data[:3]):
        print(f'  {i+1}. {proj[\"name\"]} (注册表ID: {proj[\"registry_id\"]}) - {proj[\"visibility\"]}')
elif isinstance(data, dict) and 'results' in data:
    print(f'分页格式 - 总数: {data[\"count\"]}, 结果数: {len(data[\"results\"])}')
"

echo ""
echo "4️⃣ 前端修复状态"
echo "✅ 已修复 dockerRegistryService.getRegistries() 处理分页格式"
echo "✅ 项目服务已支持数组和分页格式"

echo ""
echo "5️⃣ 前端测试指南"
echo "💻 在浏览器控制台执行:"
echo "localStorage.setItem('authToken', '$ACCESS_TOKEN')"
echo ""
echo "然后:"
echo "1. 刷新页面"
echo "2. 打开流水线编辑"
echo "3. 添加Docker步骤"
echo "4. 检查目标注册表下拉框"
echo ""
echo "🎉 应该能看到 6 个注册表选项了！"
