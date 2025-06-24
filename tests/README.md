# 🧪 AnsFlow 测试指南

## 测试架构

AnsFlow 采用分层测试策略，确保代码质量和系统稳定性。

### 测试分类

```
tests/
├── unit/                    # 单元测试
│   ├── backend/
│   │   ├── django_service/
│   │   └── fastapi_service/
│   └── frontend/
├── integration/             # 集成测试
│   ├── api/
│   ├── database/
│   └── message_queue/
├── e2e/                     # 端到端测试
│   ├── pipeline_creation/
│   ├── execution_flow/
│   └── user_workflows/
├── performance/             # 性能测试
│   ├── load_testing/
│   └── stress_testing/
└── fixtures/                # 测试数据
    ├── sample_pipelines.json
    ├── test_users.json
    └── mock_webhooks.json
```

## 🔧 后端测试

### Django 服务测试

```bash
# 运行所有 Django 测试
cd backend/django_service
python manage.py test

# 运行特定应用测试
python manage.py test apps.pipelines.tests

# 生成覆盖率报告
coverage run --source='.' manage.py test
coverage report
coverage html
```

### FastAPI 服务测试

```bash
# 运行 FastAPI 测试
cd backend/fastapi_service
pytest

# 带覆盖率的测试
pytest --cov=app --cov-report=html

# 运行特定测试文件
pytest tests/test_webhooks.py -v
```

## 🎨 前端测试

### React 应用测试

```bash
# 运行前端测试
cd frontend
npm test

# 运行覆盖率测试
npm run test:coverage

# 运行端到端测试
npm run test:e2e
```

## 🔗 集成测试

### API 集成测试

测试不同服务之间的 API 调用和数据交换：

```python
# tests/integration/api/test_service_communication.py
import pytest
import httpx

@pytest.mark.asyncio
async def test_django_to_fastapi_communication():
    """测试 Django 服务与 FastAPI 服务的通信"""
    # 通过 Django 创建流水线
    django_response = await httpx.post(
        "http://django_service:8000/api/pipelines/",
        json={"name": "test-pipeline", "steps": [...]}
    )
    
    # 验证 FastAPI 能接收到触发事件
    fastapi_response = await httpx.get(
        f"http://fastapi_service:8001/execution/{pipeline_id}/status"
    )
    
    assert fastapi_response.status_code == 200
```

### 数据库集成测试

```python
# tests/integration/database/test_data_consistency.py
from django.test import TransactionTestCase
from apps.pipelines.models import Pipeline
from apps.executions.models import Execution

class DataConsistencyTestCase(TransactionTestCase):
    def test_pipeline_execution_consistency(self):
        """测试流水线和执行记录的数据一致性"""
        pipeline = Pipeline.objects.create(name="test")
        execution = Execution.objects.create(pipeline=pipeline)
        
        # 验证关联关系
        assert execution.pipeline.id == pipeline.id
        assert pipeline.executions.count() == 1
```

## 🌐 端到端测试

### Playwright 测试

```javascript
// tests/e2e/pipeline_creation.spec.js
const { test, expect } = require('@playwright/test');

test('用户可以创建新流水线', async ({ page }) => {
  // 登录
  await page.goto('http://localhost:3000/login');
  await page.fill('[data-testid=username]', 'admin');
  await page.fill('[data-testid=password]', 'admin123');
  await page.click('[data-testid=login-button]');

  // 创建流水线
  await page.goto('http://localhost:3000/pipelines/new');
  await page.fill('[data-testid=pipeline-name]', '测试流水线');
  
  // 拖拽步骤到画布
  await page.dragAndDrop(
    '[data-testid=step-git-clone]',
    '[data-testid=pipeline-canvas]'
  );
  
  // 保存流水线
  await page.click('[data-testid=save-pipeline]');
  
  // 验证结果
  await expect(page.locator('[data-testid=success-message]')).toBeVisible();
});
```

## ⚡ 性能测试

### 负载测试

```python
# tests/performance/load_testing/test_api_load.py
import asyncio
import aiohttp
import time
from statistics import mean

async def test_api_response_time():
    """测试 API 响应时间"""
    urls = [
        "http://localhost:8000/api/pipelines/",
        "http://localhost:8001/health",
    ]
    
    async with aiohttp.ClientSession() as session:
        response_times = []
        
        for _ in range(100):  # 100 个并发请求
            start_time = time.time()
            async with session.get(urls[0]) as response:
                await response.text()
            response_times.append(time.time() - start_time)
        
        avg_response_time = mean(response_times)
        assert avg_response_time < 0.5  # 平均响应时间小于 500ms
```

### 压力测试

使用 Locust 进行压力测试：

```python
# tests/performance/stress_testing/locustfile.py
from locust import HttpUser, task, between

class AnsFlowUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """用户登录"""
        self.client.post("/api/auth/login/", json={
            "username": "testuser",
            "password": "testpass"
        })
    
    @task(3)
    def view_pipelines(self):
        """查看流水线列表"""
        self.client.get("/api/pipelines/")
    
    @task(1)
    def create_pipeline(self):
        """创建流水线"""
        self.client.post("/api/pipelines/", json={
            "name": f"load-test-{int(time.time())}",
            "steps": [...]
        })
```

## 🔧 测试环境配置

### Docker 测试环境

```yaml
# docker-compose.test.yml
version: '3.8'
services:
  test_mysql:
    image: mysql:8.0
    environment:
      MYSQL_DATABASE: ansflow_test
      MYSQL_ROOT_PASSWORD: test_password
    tmpfs:
      - /var/lib/mysql  # 使用内存存储，提高测试速度

  test_redis:
    image: redis:7-alpine
    
  django_test:
    build: ./backend/django_service
    depends_on:
      - test_mysql
      - test_redis
    environment:
      - TESTING=true
      - DB_HOST=test_mysql
    command: python manage.py test
```

### 持续集成配置

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  backend_tests:
    runs-on: ubuntu-latest
    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: test_password
          MYSQL_DATABASE: ansflow_test
      redis:
        image: redis:7-alpine
    
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.8'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run Django tests
        run: |
          cd backend/django_service
          python manage.py test
      
      - name: Run FastAPI tests
        run: |
          cd backend/fastapi_service
          pytest

  frontend_tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '16'
      
      - name: Install dependencies
        run: |
          cd frontend
          npm install
      
      - name: Run tests
        run: |
          cd frontend
          npm test
```

## 📊 测试报告

### 覆盖率要求

- **后端代码覆盖率**: 最低 80%
- **前端代码覆盖率**: 最低 75%
- **集成测试覆盖率**: 关键业务流程 100%

### 测试指标

- **单元测试**: 快速反馈，执行时间 < 30秒
- **集成测试**: 中等反馈，执行时间 < 5分钟
- **端到端测试**: 完整验证，执行时间 < 15分钟

## 🚀 运行测试

### 本地开发测试

```bash
# 运行所有测试
make test

# 只运行后端测试
make test-backend

# 只运行前端测试
make test-frontend

# 运行特定测试
docker-compose exec django_service python manage.py test apps.pipelines
```

### CI/CD 环境测试

```bash
# 使用测试 Docker Compose 配置
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# 生成测试报告
docker-compose -f docker-compose.test.yml run --rm test_runner
```

## 🔍 调试测试

### 调试失败的测试

```bash
# Django 测试调试
python manage.py test apps.pipelines.tests.TestPipelineCreation --debug-mode --verbosity=2

# FastAPI 测试调试
pytest tests/test_webhooks.py -v -s --pdb

# 前端测试调试
npm test -- --watchAll=false --verbose
```

### 测试数据管理

```python
# tests/fixtures/factories.py
import factory
from apps.pipelines.models import Pipeline

class PipelineFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Pipeline
    
    name = factory.Sequence(lambda n: f"pipeline-{n}")
    description = factory.Faker('text')
    is_active = True
```

通过完善的测试体系，确保 AnsFlow 平台的稳定性和可靠性！
