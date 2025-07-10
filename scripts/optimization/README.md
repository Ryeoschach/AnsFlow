# AnsFlow 优化脚本集合

## 📋 脚本概览

这个目录包含了 AnsFlow 平台微服务优化相关的所有自动化脚本，用于性能测试、环境配置和服务管理。

## 🚀 可用脚本

### 🧪 性能测试脚本
**[test_optimization.py](./test_optimization.py)**
- **功能**: 全面的性能优化测试套件
- **测试内容**:
  - Redis 多数据库连接测试
  - FastAPI 服务性能基准测试
  - WebSocket 连接测试
  - 系统集成验证
- **使用方法**:
  ```bash
  cd /Users/creed/Workspace/OpenSource/ansflow
  python scripts/optimization/test_optimization.py
  ```

### ⚡ UV 别名配置脚本
**[setup-uv-aliases.sh](./setup-uv-aliases.sh)**
- **功能**: 配置便捷的 UV 包管理器别名
- **包含别名**:
  - `ansflow-*` - 项目导航别名
  - `uv*` - UV 命令简化别名
  - `ansflow-test` - 快速测试别名
  - `ansflow-start-*` - 服务启动别名
- **使用方法**:
  ```bash
  ./scripts/optimization/setup-uv-aliases.sh
  source ~/.zshrc  # 重新加载配置
  ```

### 🔄 优化服务启动脚本
**[start_optimized.sh](./start_optimized.sh)**
- **功能**: 按优化后的配置启动所有服务
- **启动顺序**:
  1. Redis 服务检查
  2. RabbitMQ 服务检查  
  3. Django 服务 (端口 8000)
  4. FastAPI 服务 (端口 8001)
  5. 前端开发服务 (端口 5173)
- **使用方法**:
  ```bash
  ./scripts/optimization/start_optimized.sh
  ```

## 📊 脚本使用场景

### 日常开发工作流
```bash
# 1. 配置开发环境 (首次使用)
./scripts/optimization/setup-uv-aliases.sh
source ~/.zshrc

# 2. 启动所有服务
./scripts/optimization/start_optimized.sh

# 3. 运行性能测试验证
python scripts/optimization/test_optimization.py
```

### 持续集成/部署
```bash
# CI 管道中的测试步骤
python scripts/optimization/test_optimization.py
if [ $? -eq 0 ]; then
    echo "✅ 性能测试通过"
else
    echo "❌ 性能测试失败"
    exit 1
fi
```

### 性能监控
```bash
# 定期运行性能测试 (可加入 cron job)
*/30 * * * * cd /path/to/ansflow && python scripts/optimization/test_optimization.py >> logs/performance.log 2>&1
```

## 🔧 脚本配置

### 环境要求
- **Python 3.11+**: 运行 Python 脚本
- **UV**: 包管理器 (自动安装)
- **Node.js 16+**: 前端开发环境
- **Redis**: 缓存服务
- **RabbitMQ**: 消息队列服务

### 端口配置
| 服务 | 端口 | 说明 |
|------|------|------|
| Django | 8000 | 主要业务逻辑服务 |
| FastAPI | 8001 | 高性能 API 和 WebSocket |
| Frontend | 5173 | Vite 开发服务器 |
| Redis | 6379 | 缓存服务 |
| RabbitMQ | 5672 | 消息队列 |
| RabbitMQ Management | 15672 | Web 管理界面 |

## 📋 脚本输出说明

### test_optimization.py 输出
```
🚀 Starting AnsFlow Optimization Tests...
⏰ Test started at: 2025-07-10T15:04:35
------------------------------------------------------------
🔍 Testing Redis multi-database connections...
  ✅ default database: OK (0.34ms)
  ✅ session database: OK (0.21ms)
  ✅ api database: OK (0.18ms)
  ✅ pipeline database: OK (0.19ms)
  ✅ channels database: OK (0.18ms)
🔍 Testing FastAPI performance...
  ✅ Health check: 57.61ms
  📊 Concurrent: 34.91 req/sec
============================================================
Overall Status: ✅ EXCELLENT (100% success rate)
```

### setup-uv-aliases.sh 输出
```
正在配置 AnsFlow UV 便捷别名...
✅ AnsFlow UV 别名配置完成！

使用方法：
1. source ~/.zshrc  # 重新加载配置
2. ansflow-help     # 查看所有可用命令
3. ansflow-test     # 运行性能测试验证优化效果
```

### start_optimized.sh 输出
```
🚀 启动 AnsFlow 优化服务...
✅ Redis 服务运行中
✅ RabbitMQ 服务运行中
🔄 启动 Django 服务 (端口 8000)
🔄 启动 FastAPI 服务 (端口 8001)
🔄 启动前端服务 (端口 5173)
🎉 所有服务启动完成！
```

## 🐛 故障排除

### 常见问题
1. **权限错误**: 确保脚本有执行权限
   ```bash
   chmod +x scripts/optimization/*.sh
   ```

2. **端口被占用**: 检查并释放相关端口
   ```bash
   lsof -ti:8000,8001,5173 | xargs kill -9
   ```

3. **服务依赖失败**: 确保 Redis 和 RabbitMQ 服务运行
   ```bash
   brew services start redis
   brew services start rabbitmq
   ```

### 调试模式
```bash
# 启用详细输出
DEBUG=1 python scripts/optimization/test_optimization.py

# 检查脚本语法
bash -n scripts/optimization/setup-uv-aliases.sh
```

## 📚 相关文档

- **[优化文档](../../docs/optimization/README.md)** - 完整的优化实施指南
- **[测试文档](../../docs/testing/README.md)** - 测试报告和结果分析
- **[UV 快速参考](../../docs/optimization/UV_QUICK_REFERENCE.md)** - UV 包管理器使用指南

---

最后更新: 2025年7月10日  
脚本状态: ✅ **全部可用**
