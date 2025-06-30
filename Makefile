# AnsFlow CI/CD Platform Makefile
# 便捷的开发和部署命令

.PHONY: help dev-up dev-down dev-restart dev-logs dev-clean
.PHONY: db-init db-migrate db-seed db-backup db-restore
.PHONY: test test-backend test-frontend lint format
.PHONY: build prod-deploy prod-logs prod-backup superuser
.PHONY: check verify health

# 默认目标
.DEFAULT_GOAL := help

# 颜色定义
YELLOW := \033[33m
GREEN := \033[32m
RED := \033[31m
BLUE := \033[34m
RESET := \033[0m

# 帮助信息
help: ## 显示帮助信息
	@echo "$(BLUE)AnsFlow CI/CD Platform - 可用命令:$(RESET)"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "$(GREEN)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ===========================================
# 开发环境管理
# ===========================================

dev-up: ## 启动开发环境
	@echo "$(YELLOW)🚀 启动 AnsFlow 开发环境...$(RESET)"
	@if [ ! -f .env ]; then cp .env.example .env && echo "$(GREEN)✅ 已创建 .env 文件$(RESET)"; fi
	docker-compose up -d
	@echo "$(GREEN)✅ 开发环境启动完成!$(RESET)"
	@echo "$(BLUE)📋 服务访问地址:$(RESET)"
	@echo "  - 前端界面: http://localhost:3000"
	@echo "  - Django 管理: http://localhost:8000/admin"
	@echo "  - FastAPI 文档: http://localhost:8001/docs"
	@echo "  - RabbitMQ 管理: http://localhost:15672"
	@echo "  - Grafana 监控: http://localhost:3001"

dev-down: ## 停止开发环境
	@echo "$(YELLOW)🛑 停止 AnsFlow 开发环境...$(RESET)"
	docker-compose down
	@echo "$(GREEN)✅ 开发环境已停止$(RESET)"

dev-restart: ## 重启开发环境
	@echo "$(YELLOW)🔄 重启 AnsFlow 开发环境...$(RESET)"
	docker-compose restart
	@echo "$(GREEN)✅ 开发环境重启完成$(RESET)"

dev-logs: ## 查看开发环境日志
	@echo "$(YELLOW)📋 查看服务日志...$(RESET)"
	docker-compose logs -f

dev-clean: ## 清理开发环境 (包括数据卷)
	@echo "$(RED)⚠️  这将删除所有数据，请确认继续 [y/N]:$(RESET)" && read ans && [ $${ans:-N} = y ]
	@echo "$(YELLOW)🧹 清理开发环境...$(RESET)"
	docker-compose down -v --remove-orphans
	docker system prune -f
	@echo "$(GREEN)✅ 开发环境清理完成$(RESET)"

# ===========================================
# 数据库管理
# ===========================================

db-init: ## 初始化数据库
	@echo "$(YELLOW)🗄️  初始化数据库...$(RESET)"
	docker-compose exec django_service python manage.py migrate
	@echo "$(GREEN)✅ 数据库初始化完成$(RESET)"

db-migrate: ## 运行数据库迁移
	@echo "$(YELLOW)🗄️  运行数据库迁移...$(RESET)"
	docker-compose exec django_service python manage.py makemigrations
	docker-compose exec django_service python manage.py migrate
	@echo "$(GREEN)✅ 数据库迁移完成$(RESET)"

db-seed: ## 填充测试数据
	@echo "$(YELLOW)🌱 填充测试数据...$(RESET)"
	docker-compose exec django_service python manage.py loaddata fixtures/sample_data.json
	@echo "$(GREEN)✅ 测试数据填充完成$(RESET)"

db-backup: ## 备份数据库
	@echo "$(YELLOW)💾 备份数据库...$(RESET)"
	mkdir -p backups
	docker-compose exec mysql mysqldump -u ansflow_user -pansflow_password_123 ansflow_db > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✅ 数据库备份完成$(RESET)"

db-restore: ## 恢复数据库 (需要指定备份文件)
	@echo "$(YELLOW)📥 恢复数据库...$(RESET)"
	@echo "请提供备份文件路径:" && read backup_file
	docker-compose exec -T mysql mysql -u ansflow_user -pansflow_password_123 ansflow_db < $$backup_file
	@echo "$(GREEN)✅ 数据库恢复完成$(RESET)"

superuser: ## 创建超级用户
	@echo "$(YELLOW)👤 创建超级用户...$(RESET)"
	docker-compose exec django_service python manage.py createsuperuser
	@echo "$(GREEN)✅ 超级用户创建完成$(RESET)"

# ===========================================
# 测试相关
# ===========================================

test: ## 运行所有测试
	@echo "$(YELLOW)🧪 运行所有测试...$(RESET)"
	$(MAKE) test-backend
	$(MAKE) test-frontend
	@echo "$(GREEN)✅ 所有测试完成$(RESET)"

test-backend: ## 运行后端测试
	@echo "$(YELLOW)🧪 运行后端测试...$(RESET)"
	docker-compose exec django_service python manage.py test
	docker-compose exec fastapi_service pytest
	@echo "$(GREEN)✅ 后端测试完成$(RESET)"

test-frontend: ## 运行前端测试
	@echo "$(YELLOW)🧪 运行前端测试...$(RESET)"
	docker-compose exec frontend npm run test
	@echo "$(GREEN)✅ 前端测试完成$(RESET)"

lint: ## 代码检查
	@echo "$(YELLOW)🔍 执行代码检查...$(RESET)"
	docker-compose exec django_service flake8 .
	docker-compose exec fastapi_service flake8 .
	docker-compose exec frontend npm run lint
	@echo "$(GREEN)✅ 代码检查完成$(RESET)"

format: ## 代码格式化
	@echo "$(YELLOW)🎨 执行代码格式化...$(RESET)"
	docker-compose exec django_service black .
	docker-compose exec fastapi_service black .
	docker-compose exec frontend npm run format
	@echo "$(GREEN)✅ 代码格式化完成$(RESET)"

# ===========================================
# 构建和部署
# ===========================================

build: ## 构建生产镜像
	@echo "$(YELLOW)🏗️  构建生产镜像...$(RESET)"
	docker-compose -f docker-compose.prod.yml build
	@echo "$(GREEN)✅ 生产镜像构建完成$(RESET)"

prod-deploy: ## 部署到生产环境
	@echo "$(YELLOW)🚀 部署到生产环境...$(RESET)"
	docker-compose -f docker-compose.prod.yml up -d
	@echo "$(GREEN)✅ 生产环境部署完成$(RESET)"

prod-logs: ## 查看生产环境日志
	@echo "$(YELLOW)📋 查看生产环境日志...$(RESET)"
	docker-compose -f docker-compose.prod.yml logs -f

prod-backup: ## 生产环境备份
	@echo "$(YELLOW)💾 生产环境备份...$(RESET)"
	mkdir -p backups/prod
	docker-compose -f docker-compose.prod.yml exec mysql mysqldump -u ansflow_user -pansflow_password_123 ansflow_db > backups/prod/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✅ 生产环境备份完成$(RESET)"

# ===========================================
# 实用工具
# ===========================================

shell-django: ## 进入 Django 容器 shell
	docker-compose exec django_service bash

shell-fastapi: ## 进入 FastAPI 容器 shell
	docker-compose exec fastapi_service bash

shell-frontend: ## 进入前端容器 shell
	docker-compose exec frontend bash

shell-mysql: ## 进入 MySQL 容器 shell
	docker-compose exec mysql mysql -u ansflow_user -pansflow_password_123 ansflow_db

shell-redis: ## 进入 Redis 容器 shell
	docker-compose exec redis redis-cli

status: ## 查看服务状态
	@echo "$(BLUE)📊 AnsFlow 服务状态:$(RESET)"
	docker-compose ps

logs-django: ## 查看 Django 服务日志
	docker-compose logs -f django_service

logs-fastapi: ## 查看 FastAPI 服务日志
	docker-compose logs -f fastapi_service

logs-frontend: ## 查看前端服务日志
	docker-compose logs -f frontend

# ===========================================
# 监控相关
# ===========================================

monitor: ## 打开监控面板
	@echo "$(BLUE)📊 打开监控面板...$(RESET)"
	@echo "Grafana: http://localhost:3001 (admin/admin123)"
	@echo "Prometheus: http://localhost:9090"
	@echo "RabbitMQ: http://localhost:15672 (ansflow/ansflow_rabbitmq_123)"

# ===========================================
# 系统检查和验证
# ===========================================

check: ## 运行完整系统状态检查
	@echo "$(YELLOW)🔍 运行完整系统状态检查...$(RESET)"
	@if [ -x "./scripts/check_system_status.sh" ]; then \
		./scripts/check_system_status.sh; \
	else \
		echo "$(RED)❌ 系统检查脚本不存在或无执行权限$(RESET)"; \
		echo "请运行: chmod +x scripts/check_system_status.sh"; \
	fi

verify: ## 运行核心功能快速验证
	@echo "$(YELLOW)🧪 运行核心功能快速验证...$(RESET)"
	@if command -v python3 >/dev/null 2>&1; then \
		python3 scripts/quick_verify.py; \
	elif command -v python >/dev/null 2>&1; then \
		python scripts/quick_verify.py; \
	else \
		echo "$(RED)❌ Python 未安装$(RESET)"; \
	fi

health: ## 快速健康检查
	@echo "$(BLUE)💓 AnsFlow 健康检查:$(RESET)"
	@echo "🔍 检查容器状态..."
	@docker-compose ps
	@echo ""
	@echo "🔍 检查服务可用性..."
	@echo -n "前端服务 (3000): "; curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 || echo "无法连接"
	@echo -n "Django服务 (8000): "; curl -s -o /dev/null -w "%{http_code}" http://localhost:8000 || echo "无法连接"
	@echo -n "FastAPI服务 (8001): "; curl -s -o /dev/null -w "%{http_code}" http://localhost:8001 || echo "无法连接"

dev-start: dev-up check ## 启动开发环境并进行系统检查
	@echo "$(GREEN)🎉 开发环境启动完成，系统检查已完成！$(RESET)"
