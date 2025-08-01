#!/bin/bash
# 调试工具恢复脚本
# 用于从归档中恢复调试工具到开发环境

echo "🔄 开始恢复调试工具..."

# 检查归档目录是否存在
if [ ! -d "docs/archive/debug-tools" ]; then
    echo "❌ 归档目录不存在: docs/archive/debug-tools"
    exit 1
fi

# 1. 恢复调试组件
echo "📁 恢复调试组件..."
mkdir -p frontend/src/components/debug
cp docs/archive/debug-tools/components/*.tsx frontend/src/components/debug/
echo "✅ 调试组件已恢复"

# 2. 恢复调试页面
echo "📄 恢复调试页面..."
cp docs/archive/debug-tools/pages/*.tsx frontend/src/pages/
echo "✅ 调试页面已恢复"

# 3. 提示需要手动添加的配置
echo ""
echo "⚠️  请手动完成以下配置："
echo ""
echo "1. 在 frontend/src/App.tsx 中添加："
echo "   import Debug from './pages/Debug'"
echo "   <Route path=\"/debug\" element={<Debug />} />"
echo ""
echo "2. 在 frontend/src/components/layout/MainLayout.tsx 中添加："
echo "   import { BugOutlined } from '@ant-design/icons'"
echo "   {"
echo "     key: '/debug',"
echo "     icon: <BugOutlined />,"
echo "     label: '调试工具',"
echo "   }"
echo ""
echo "🎉 调试工具恢复完成！"
echo "🔗 访问路径: http://localhost:3000/debug"
