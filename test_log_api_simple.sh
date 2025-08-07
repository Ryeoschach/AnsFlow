#!/bin/bash

echo "🚀 测试日志管理API..."
echo "=========================================="

# 获取Django管理员token（如果可用）
echo "🔑 尝试获取管理员访问权限..."

# 测试1: 检查日志索引API（不需要复杂认证）
echo -e "\n📁 测试日志文件索引API..."
curl -s -w "HTTP Status: %{http_code}\n" \
  -H "Content-Type: application/json" \
  "http://localhost:8000/api/v1/settings/logging/index/" | head -20

# 测试2: 检查日志统计API
echo -e "\n📊 测试日志统计API..."
curl -s -w "HTTP Status: %{http_code}\n" \
  -H "Content-Type: application/json" \
  "http://localhost:8000/api/v1/settings/logging/stats/" | head -10

# 测试3: 测试搜索API（POST请求）
echo -e "\n🔍 测试日志搜索API..."
curl -s -w "HTTP Status: %{http_code}\n" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{
    "start_time": null,
    "end_time": null,
    "levels": ["INFO", "ERROR"],
    "services": [],
    "keywords": "",
    "limit": 5,
    "offset": 0
  }' \
  "http://localhost:8000/api/v1/settings/logging/search/" | head -20

echo -e "\n=========================================="
echo "📋 API测试完成!"
echo "如果看到401错误，说明需要认证；如果看到200响应，说明API正常工作。"
