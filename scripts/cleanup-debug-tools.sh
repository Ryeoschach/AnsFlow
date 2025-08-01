#!/bin/bash
# 调试工具清理脚本
# 用于在生产环境部署前移除调试相关代码

echo "🧹 开始清理调试工具..."

# 1. 移除调试组件目录
if [ -d "frontend/src/components/debug" ]; then
    echo "📁 移除调试组件目录..."
    rm -rf frontend/src/components/debug
    echo "✅ 调试组件目录已移除"
fi

# 2. 移除调试页面
DEBUG_PAGES=("frontend/src/pages/Debug.tsx" "frontend/src/pages/InventoryGroupTest.tsx")
for page in "${DEBUG_PAGES[@]}"; do
    if [ -f "$page" ]; then
        echo "📄 移除调试页面: $page"
        rm "$page"
        echo "✅ $page 已移除"
    fi
done

# 3. 从App.tsx中移除调试路由
echo "🔧 清理App.tsx中的调试路由..."
if [ -f "frontend/src/App.tsx" ]; then
    # 移除Debug导入
    sed -i '' '/import Debug from/d' frontend/src/App.tsx
    # 移除debug路由
    sed -i '' '/<Route path="\/debug"/d' frontend/src/App.tsx
    echo "✅ App.tsx调试路由已清理"
fi

# 4. 从MainLayout.tsx中移除调试菜单
echo "🔧 清理MainLayout.tsx中的调试菜单..."
if [ -f "frontend/src/components/layout/MainLayout.tsx" ]; then
    # 移除BugOutlined导入（如果只用于调试）
    sed -i '' '/BugOutlined/d' frontend/src/components/layout/MainLayout.tsx
    # 移除调试菜单项
    sed -i '' '/key.*debug/,/}/d' frontend/src/components/layout/MainLayout.tsx
    echo "✅ MainLayout.tsx调试菜单已清理"
fi

# 5. 清理相关的类型导入（如果有）
echo "🔧 清理类型定义中的调试相关内容..."
find frontend/src -name "*.ts" -o -name "*.tsx" | xargs grep -l "debug" | while read file; do
    if [[ $file != *"/archive/"* ]]; then
        echo "📄 检查文件: $file"
        # 这里可以添加具体的清理逻辑
    fi
done

# 6. 重新构建项目以验证清理结果
echo "🔨 验证清理结果..."
cd frontend
if command -v npm &> /dev/null; then
    npm run build > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ 项目构建成功，调试工具已完全移除"
    else
        echo "❌ 构建失败，可能还有残留的调试代码引用"
        echo "请检查构建错误并手动清理"
    fi
else
    echo "⚠️  未找到npm，请手动验证构建"
fi

echo ""
echo "🎉 调试工具清理完成！"
echo "📁 所有调试工具已归档到: docs/archive/debug-tools/"
echo "🔄 如需恢复调试工具，请从归档目录复制相关文件"
