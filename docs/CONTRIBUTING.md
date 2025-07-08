# 🤝 AnsFlow 贡献指南

> **感谢您对 AnsFlow CI/CD 平台的贡献兴趣！**  
> 本指南将帮助您了解如何参与项目开发，共同构建更优秀的CI/CD平台。

## 🎯 贡献方式

### 🐛 报告问题
- **Bug 报告**: 在 [Issues](https://github.com/your-org/ansflow/issues) 中详细描述问题
- **功能请求**: 提出新功能建议和改进意见
- **文档改进**: 指出文档中的错误或建议优化

### 💻 代码贡献
- **Bug 修复**: 解决已知问题
- **新功能开发**: 实现计划中的功能
- **性能优化**: 提升系统性能和稳定性
- **测试完善**: 增加单元测试和集成测试

### 📚 文档贡献
- **API 文档**: 完善接口文档和示例
- **使用指南**: 编写教程和最佳实践
- **代码注释**: 改进代码可读性

## 🚀 快速开始

### 1. 开发环境搭建

```bash
# 1. Fork 项目到你的 GitHub 账户
# 2. 克隆你的 Fork
git clone https://github.com/your-username/ansflow.git
cd ansflow

# 3. 添加上游仓库
git remote add upstream https://github.com/your-org/ansflow.git

# 4. 启动开发环境
make dev-start

# 5. 验证环境
make check
```

### 2. 分支管理策略

```bash
# 创建功能分支
git checkout -b feature/your-feature-name

# 创建修复分支
git checkout -b fix/issue-number-description

# 创建文档分支
git checkout -b docs/document-improvement
```

### 3. 开发流程

```bash
# 1. 同步最新代码
git fetch upstream
git checkout main
git merge upstream/main

# 2. 创建功能分支
git checkout -b feature/new-awesome-feature

# 3. 进行开发
# ... 编写代码 ...

# 4. 运行测试
make test
make lint

# 5. 提交更改
git add .
git commit -m "feat: add awesome new feature"

# 6. 推送分支
git push origin feature/new-awesome-feature

# 7. 创建 Pull Request
```

## 📝 开发规范

### 🎨 代码风格

#### Python (Django/FastAPI)
```python
# 遵循 PEP 8 规范
# 使用类型提示
def create_pipeline(name: str, description: str) -> Pipeline:
    """创建新的流水线
    
    Args:
        name: 流水线名称
        description: 流水线描述
        
    Returns:
        Pipeline: 创建的流水线对象
    """
    return Pipeline.objects.create(
        name=name,
        description=description
    )

# 使用 Black 格式化
make format
```

#### TypeScript/React
```typescript
// 使用 TypeScript 严格模式
interface PipelineProps {
  pipeline: Pipeline;
  onSave: (pipeline: Pipeline) => void;
  onClose: () => void;
}

// 使用函数组件和 Hooks
const PipelineEditor: React.FC<PipelineProps> = ({ 
  pipeline, 
  onSave, 
  onClose 
}) => {
  const [loading, setLoading] = useState(false);
  
  // 组件逻辑
  
  return (
    <div className="pipeline-editor">
      {/* JSX 内容 */}
    </div>
  );
};
```

### 📋 提交信息规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```bash
# 功能添加
git commit -m "feat: add pipeline execution mode editing"

# Bug 修复
git commit -m "fix: resolve pipeline editor data sync issue"

# 文档更新
git commit -m "docs: update API documentation"

# 样式改进
git commit -m "style: improve pipeline list UI layout"

# 重构
git commit -m "refactor: optimize pipeline serializer structure"

# 测试
git commit -m "test: add unit tests for execution engine"

# 构建相关
git commit -m "build: update Docker configuration"

# CI 相关
git commit -m "ci: add automated testing workflow"
```

### 🧪 测试要求

#### 单元测试
```python
# Django 测试示例
class PipelineTestCase(TestCase):
    def setUp(self):
        self.pipeline = Pipeline.objects.create(
            name="test_pipeline",
            description="Test pipeline"
        )
    
    def test_pipeline_creation(self):
        """测试流水线创建"""
        self.assertEqual(self.pipeline.name, "test_pipeline")
        self.assertTrue(self.pipeline.is_active)
    
    def test_pipeline_execution(self):
        """测试流水线执行"""
        result = self.pipeline.execute()
        self.assertTrue(result.success)
```

#### 前端测试
```typescript
// React 组件测试示例
import { render, screen, fireEvent } from '@testing-library/react';
import PipelineEditor from '../PipelineEditor';

describe('PipelineEditor', () => {
  test('renders pipeline editor correctly', () => {
    const mockPipeline = { id: 1, name: 'Test Pipeline' };
    render(<PipelineEditor pipeline={mockPipeline} />);
    
    expect(screen.getByText('Test Pipeline')).toBeInTheDocument();
  });
  
  test('saves pipeline changes', async () => {
    const mockOnSave = jest.fn();
    render(<PipelineEditor onSave={mockOnSave} />);
    
    fireEvent.click(screen.getByText('保存'));
    expect(mockOnSave).toHaveBeenCalled();
  });
});
```

### 📖 文档要求

#### API 文档
```python
# Django REST 序列化器文档
class PipelineSerializer(serializers.ModelSerializer):
    """流水线序列化器
    
    用于流水线数据的序列化和反序列化。
    支持创建、更新和查询流水线信息。
    
    Fields:
        name: 流水线名称 (必填)
        description: 流水线描述 (可选)
        execution_mode: 执行模式 (local/remote/hybrid)
        steps: 流水线步骤列表
    """
    
    class Meta:
        model = Pipeline
        fields = ['id', 'name', 'description', 'execution_mode', 'steps']
```

#### 函数文档
```python
def execute_pipeline(pipeline_id: int, parameters: Dict[str, Any]) -> ExecutionResult:
    """执行指定的流水线
    
    Args:
        pipeline_id: 流水线ID
        parameters: 执行参数字典
        
    Returns:
        ExecutionResult: 执行结果对象，包含状态和日志
        
    Raises:
        PipelineNotFoundError: 流水线不存在
        ExecutionError: 执行过程中出现错误
        
    Example:
        >>> result = execute_pipeline(1, {'env': 'prod'})
        >>> print(result.status)
        'success'
    """
```

## 🎯 重点开发领域

### 🔥 高优先级
1. **GitLab CI 集成** - 扩展多 CI/CD 工具支持
2. **GitHub Actions 集成** - 完善主流工具生态
3. **单元测试补充** - 提升测试覆盖率到 80%+
4. **性能优化** - 大规模并发处理优化

### ⚡ 中优先级
1. **高级流水线功能** - 条件分支、并行执行
2. **安全权限管理** - RBAC 模型实现
3. **系统监控仪表板** - 资源使用监控
4. **API 文档完善** - OpenAPI 规范和示例

### 💡 欢迎贡献的领域
- **插件系统开发** - 第三方工具适配器
- **国际化支持** - 多语言界面
- **移动端适配** - 响应式设计优化
- **AI 功能集成** - 智能推荐和分析

## 🔄 Pull Request 流程

### 1. 提交前检查清单
- [ ] 代码遵循项目规范
- [ ] 通过所有测试 (`make test`)
- [ ] 通过代码检查 (`make lint`)
- [ ] 添加必要的测试用例
- [ ] 更新相关文档
- [ ] 提交信息符合规范

### 2. PR 模板
```markdown
## 📝 变更描述
简要描述本次变更的内容和目的。

## 🎯 相关 Issue
修复 #123
实现 #456

## 🧪 测试说明
- [ ] 单元测试已通过
- [ ] 集成测试已通过
- [ ] 手动测试场景：...

## 📋 检查清单
- [ ] 代码遵循项目规范
- [ ] 已添加必要的测试
- [ ] 文档已更新
- [ ] 所有测试通过

## 📸 截图/演示
如果是 UI 相关变更，请提供截图或 GIF 演示。

## 📄 其他说明
其他需要说明的内容。
```

### 3. 代码审查
- 至少需要 1 位维护者批准
- 自动化测试必须通过
- 代码覆盖率不能下降
- 性能测试通过（如适用）

## 🛠️ 本地开发技巧

### 调试技巧
```bash
# 查看服务日志
docker-compose logs -f django
docker-compose logs -f fastapi

# 进入容器调试
make shell-django
make shell-frontend

# 重启特定服务
docker-compose restart django
```

### 数据库操作
```bash
# 创建新迁移
docker-compose exec django python manage.py makemigrations

# 应用迁移
make db-migrate

# 重置数据库
make db-reset
```

### 前端开发
```bash
# 热重载开发
cd frontend
npm run dev

# 构建优化
npm run build

# 类型检查
npm run type-check
```

## 🏆 贡献者荣誉

我们感谢每一位贡献者！您的贡献将会在以下地方得到认可：

- **README.md** - 贡献者列表
- **CHANGELOG.md** - 版本发布说明
- **GitHub 贡献图** - 提交统计
- **项目文档** - 特殊贡献说明

## 📞 获取帮助

如果您在贡献过程中遇到任何问题：

1. **查看文档** - 先查看相关文档和 FAQ
2. **搜索 Issues** - 看看是否已有相关讨论
3. **创建 Issue** - 描述您的问题或建议
4. **参与讨论** - GitHub Discussions 版块
5. **直接联系** - 通过邮件联系维护者

## 🌟 贡献激励

- **Code Review** - 参与代码审查获得经验
- **功能设计** - 参与新功能的设计讨论
- **社区建设** - 帮助其他开发者解决问题
- **技术分享** - 分享使用经验和最佳实践

---

**🎉 感谢您为 AnsFlow 的发展贡献力量！让我们一起构建更优秀的 CI/CD 平台！**
