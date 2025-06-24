# 🚀 AnsFlow 开发指南

## 📋 目录
- [开发环境设置](#开发环境设置)
- [项目结构说明](#项目结构说明)
- [开发工作流](#开发工作流)
- [编码规范](#编码规范)
- [测试指南](#测试指南)
- [调试技巧](#调试技巧)

## 🛠️ 开发环境设置

### 系统要求

- **操作系统**: macOS, Linux, Windows 10+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Git**: 2.30+
- **Node.js**: 16+ (可选，本地开发)
- **Python**: 3.8+ (可选，本地开发)

### 快速开始

```bash
# 1. 克隆项目
git clone https://github.com/your-org/ansflow.git
cd ansflow

# 2. 运行安装脚本
chmod +x scripts/setup.sh
./scripts/setup.sh

# 3. 或者手动启动
make dev-up
```

### 本地开发模式

如果您希望在本地环境进行开发：

#### 后端开发 (Django + FastAPI)

```bash
# 创建 Python 虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装 Python 依赖
pip install -r requirements.txt

# 设置环境变量
export DB_HOST=localhost
export REDIS_HOST=localhost
export RABBITMQ_HOST=localhost

# 启动基础服务（只启动数据库等）
docker-compose up -d mysql redis rabbitmq

# 启动 Django 服务
cd backend/django_service
python manage.py migrate
python manage.py runserver 8000

# 启动 FastAPI 服务（新终端）
cd backend/fastapi_service
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

#### 前端开发 (React)

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 打开浏览器访问 http://localhost:3000
```

## 🏗️ 项目结构说明

```
ansflow/
├── backend/                    # 后端微服务
│   ├── django_service/         # Django 管理服务
│   │   ├── apps/              # Django 应用模块
│   │   ├── config/            # 配置文件
│   │   ├── requirements.txt   # Django 依赖
│   │   └── manage.py          # Django 管理脚本
│   ├── fastapi_service/       # FastAPI 高性能服务
│   │   ├── app/              # FastAPI 应用
│   │   ├── requirements.txt  # FastAPI 依赖
│   │   └── main.py           # 应用入口
│   └── shared/               # 共享代码库
│       ├── models/           # 数据模型
│       ├── utils/            # 工具函数
│       └── constants/        # 常量定义
├── frontend/                  # React 前端
│   ├── src/                  # 源代码
│   ├── public/               # 静态文件
│   ├── package.json          # Node.js 依赖
│   └── vite.config.ts        # Vite 配置
└── deployment/               # 部署配置
    ├── docker/              # Docker 配置
    ├── kubernetes/          # K8s 配置
    └── terraform/           # 基础设施配置
```

## 🔄 开发工作流

### Git 工作流

我们使用 GitFlow 工作流：

```bash
# 1. 从主分支创建功能分支
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# 2. 开发您的功能
# ... 编写代码 ...

# 3. 提交代码
git add .
git commit -m "feat: add amazing feature"

# 4. 推送分支
git push origin feature/your-feature-name

# 5. 创建 Pull Request
```

### 分支命名规范

- `feature/功能名称` - 新功能开发
- `bugfix/问题描述` - Bug 修复
- `hotfix/紧急修复` - 紧急修复
- `refactor/重构说明` - 代码重构
- `docs/文档更新` - 文档更新

### 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

类型说明：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

示例：
```
feat(pipeline): add drag-and-drop pipeline editor

- Implement drag-and-drop interface for pipeline steps
- Add validation for step connections
- Update UI components for better UX

Closes #123
```

## 📝 编码规范

### Python 编码规范

遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 标准：

```python
# 使用 4 个空格缩进
# 类名使用 PascalCase
class PipelineManager:
    """流水线管理器"""
    
    def __init__(self, name: str) -> None:
        self.name = name
    
    # 方法名使用 snake_case
    def create_pipeline(self, config: dict) -> Pipeline:
        """创建新的流水线"""
        pass

# 常量使用 UPPER_CASE
MAX_PIPELINE_STEPS = 100

# 变量使用 snake_case
pipeline_config = {"name": "test-pipeline"}
```

### JavaScript/TypeScript 编码规范

遵循 [ESLint](https://eslint.org/) 和 [Prettier](https://prettier.io/) 配置：

```typescript
// 接口使用 PascalCase
interface PipelineConfig {
  name: string;
  steps: PipelineStep[];
}

// 组件名使用 PascalCase
const PipelineEditor: React.FC<Props> = ({ config }) => {
  // 变量使用 camelCase
  const [pipelineSteps, setPipelineSteps] = useState<PipelineStep[]>([]);
  
  // 函数名使用 camelCase
  const handleStepAdd = useCallback((step: PipelineStep) => {
    setPipelineSteps(prev => [...prev, step]);
  }, []);
  
  return (
    <div className="pipeline-editor">
      {/* JSX 内容 */}
    </div>
  );
};
```

## 🧪 测试指南

### 后端测试

#### Django 测试

```bash
# 运行所有测试
python manage.py test

# 运行特定应用的测试
python manage.py test apps.pipelines

# 运行特定测试类
python manage.py test apps.pipelines.tests.TestPipelineModel

# 生成覆盖率报告
coverage run --source='.' manage.py test
coverage report
coverage html
```

示例测试：

```python
# apps/pipelines/tests/test_models.py
from django.test import TestCase
from apps.pipelines.models import Pipeline

class TestPipelineModel(TestCase):
    def setUp(self):
        self.pipeline = Pipeline.objects.create(
            name="Test Pipeline",
            description="Test Description"
        )
    
    def test_pipeline_creation(self):
        """测试流水线创建"""
        self.assertEqual(self.pipeline.name, "Test Pipeline")
        self.assertTrue(self.pipeline.is_active)
    
    def test_pipeline_str(self):
        """测试字符串表示"""
        self.assertEqual(str(self.pipeline), "Test Pipeline")
```

#### FastAPI 测试

```bash
# 运行 FastAPI 测试
cd backend/fastapi_service
pytest

# 运行特定测试文件
pytest tests/test_webhooks.py

# 生成覆盖率报告
pytest --cov=app tests/
```

示例测试：

```python
# tests/test_webhooks.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_webhook_endpoint():
    """测试 Webhook 端点"""
    payload = {
        "event": "push",
        "repository": "test-repo"
    }
    
    response = client.post("/api/v1/webhooks/github", json=payload)
    
    assert response.status_code == 200
    assert response.json()["status"] == "received"
```

### 前端测试

```bash
# 运行所有测试
npm test

# 运行特定测试文件
npm test -- --testPathPattern=PipelineEditor

# 生成覆盖率报告
npm run test:coverage

# E2E 测试
npm run test:e2e
```

示例测试：

```typescript
// src/components/pipeline/__tests__/PipelineEditor.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { PipelineEditor } from '../PipelineEditor';

describe('PipelineEditor', () => {
  it('renders pipeline editor', () => {
    render(<PipelineEditor />);
    
    expect(screen.getByText('Pipeline Editor')).toBeInTheDocument();
  });
  
  it('adds new step when button clicked', () => {
    render(<PipelineEditor />);
    
    const addButton = screen.getByText('Add Step');
    fireEvent.click(addButton);
    
    expect(screen.getByTestId('pipeline-step')).toBeInTheDocument();
  });
});
```

## 🐛 调试技巧

### 后端调试

#### Django 调试

```python
# 使用 Django Debug Toolbar
# settings.py 中添加：
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

# 使用 pdb 调试
import pdb; pdb.set_trace()

# 使用 logging
import logging
logger = logging.getLogger(__name__)
logger.debug("Debug message")
```

#### FastAPI 调试

```python
# 使用 print 调试（开发环境）
print(f"Debug: {variable}")

# 使用 logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 使用 pdb
import pdb; pdb.set_trace()
```

### 前端调试

```typescript
// 使用 console 调试
console.log('Debug:', variable);
console.table(arrayData);
console.group('Group Name');

// 使用 React DevTools
// 在浏览器中安装 React Developer Tools 扩展

// 使用 Redux DevTools
// 配置 Redux store 以支持 DevTools
```

### 容器调试

```bash
# 查看容器日志
docker-compose logs django_service
docker-compose logs -f fastapi_service

# 进入容器调试
docker-compose exec django_service bash
docker-compose exec fastapi_service bash

# 查看容器状态
docker-compose ps
docker stats
```

## 🔧 开发工具推荐

### IDE/编辑器

- **VS Code**: 推荐使用，配置了项目相关的扩展
- **PyCharm**: Python 开发的强大 IDE
- **WebStorm**: 前端开发的专业 IDE

### VS Code 扩展推荐

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.flake8",
    "ms-python.black-formatter",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
    "ms-vscode.vscode-typescript-next",
    "ms-azuretools.vscode-docker"
  ]
}
```

### 浏览器扩展

- **React Developer Tools**: React 组件调试
- **Redux DevTools**: Redux 状态管理调试
- **Vue.js devtools**: Vue 组件调试（如果使用 Vue）

---

📚 **更多资源**:
- [API 文档](../api/README.md)
- [部署指南](../deployment/README.md)
- [项目架构](../../项目说明/技术架构分析报告.md)
