#!/bin/bash
# AnsFlow UV 环境设置脚本

set -e

echo "🚀 设置 AnsFlow UV 开发环境..."

# 检查 uv 是否安装
if ! command -v uv &> /dev/null; then
    echo "❌ UV 未安装，正在安装..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
    echo "✅ UV 安装完成"
else
    echo "✅ UV 已安装: $(uv --version)"
fi

echo "📦 配置 Django 服务依赖..."

# 进入 Django 服务目录
cd backend/django_service

# 创建虚拟环境
echo "🔧 创建虚拟环境..."
uv venv

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source .venv/bin/activate

# 安装依赖
echo "📥 安装项目依赖..."
uv pip install -e .

# 安装开发依赖
echo "🛠️  安装开发依赖..."
uv pip install -e ".[dev]"

echo "📦 验证关键依赖..."

# 验证关键依赖是否安装成功
uv pip list | grep -E "django|kubernetes|celery|redis|mysqlclient" || echo "⚠️  某些依赖可能未正确安装"

echo "✅ Django 服务依赖配置完成"

echo "📦 配置 FastAPI 服务依赖..."

# 进入 FastAPI 服务目录
cd ../fastapi_service

# 创建虚拟环境
echo "🔧 创建虚拟环境..."
uv venv

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source .venv/bin/activate

# 安装依赖
echo "📥 安装项目依赖..."
uv pip install -e .

# 安装开发依赖
echo "🛠️  安装开发依赖..."
uv pip install -e ".[dev]"

echo "✅ FastAPI 服务依赖配置完成"

# 返回根目录
cd ../..

echo "🎉 UV 环境设置完成！"
echo ""
echo "📋 下一步操作:"
echo "1. Django 服务: cd backend/django_service && source .venv/bin/activate"
echo "2. FastAPI 服务: cd backend/fastapi_service && source .venv/bin/activate"
echo "3. 运行 Django 服务: python manage.py runserver"
echo "4. 运行 FastAPI 服务: uvicorn main:app --reload"
echo ""
echo "🔗 Kubernetes 集成已就绪，可开始本地流水线开发！"