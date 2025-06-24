# 🎨 AnsFlow Frontend - React Application

基于 React + TypeScript + Vite 构建的现代化前端应用

## 🏗️ 目录结构

```
frontend/
├── 📦 package.json                  # 项目依赖和脚本
├── ⚙️ vite.config.ts               # Vite 构建配置
├── ⚙️ tsconfig.json                # TypeScript 配置
├── ⚙️ tailwind.config.js           # Tailwind CSS 配置
├── 🎨 postcss.config.js            # PostCSS 配置
├── 🧪 vitest.config.ts             # 单元测试配置
├── 📄 index.html                   # HTML 模板
├── 🐳 Dockerfile                   # 容器化配置
├── 📋 README.md                    # 前端文档
├── 📁 public/                      # 静态资源
│   ├── favicon.ico                 # 网站图标
│   └── logo.png                    # 项目Logo
├── 📁 src/                         # 源代码
│   ├── 🎯 main.tsx                 # 应用入口点
│   ├── 🎨 App.tsx                  # 根组件
│   ├── 🎨 App.css                  # 全局样式
│   ├── 📁 components/              # 可复用组件
│   │   ├── common/                 # 通用组件
│   │   │   ├── Layout.tsx          # 页面布局
│   │   │   ├── Header.tsx          # 顶部导航
│   │   │   ├── Sidebar.tsx         # 侧边栏
│   │   │   ├── Loading.tsx         # 加载组件
│   │   │   ├── ErrorBoundary.tsx   # 错误边界
│   │   │   └── index.ts            # 导出文件
│   │   ├── pipeline/               # 流水线相关组件
│   │   │   ├── PipelineCanvas.tsx  # 流水线画布
│   │   │   ├── StepCard.tsx        # 步骤卡片
│   │   │   ├── StepLibrary.tsx     # 步骤库
│   │   │   ├── PipelineEditor.tsx  # 流水线编辑器
│   │   │   └── index.ts            # 导出文件
│   │   ├── execution/              # 执行相关组件
│   │   │   ├── ExecutionLog.tsx    # 执行日志
│   │   │   ├── StatusIndicator.tsx # 状态指示器
│   │   │   ├── ProgressBar.tsx     # 进度条
│   │   │   └── index.ts            # 导出文件
│   │   ├── dashboard/              # 仪表盘组件
│   │   │   ├── MetricsCard.tsx     # 指标卡片
│   │   │   ├── TrendChart.tsx      # 趋势图表
│   │   │   ├── RecentActivity.tsx  # 最近活动
│   │   │   └── index.ts            # 导出文件
│   │   └── auth/                   # 认证相关组件
│   │       ├── LoginForm.tsx       # 登录表单
│   │       ├── UserProfile.tsx     # 用户资料
│   │       └── index.ts            # 导出文件
│   ├── 📁 pages/                   # 页面组件
│   │   ├── Dashboard.tsx           # 仪表盘页面
│   │   ├── PipelineList.tsx        # 流水线列表
│   │   ├── PipelineDetail.tsx      # 流水线详情
│   │   ├── ExecutionHistory.tsx    # 执行历史
│   │   ├── Settings.tsx            # 设置页面
│   │   ├── Login.tsx               # 登录页面
│   │   └── NotFound.tsx            # 404页面
│   ├── 📁 services/                # API 服务
│   │   ├── api.ts                  # API 基础配置
│   │   ├── auth.ts                 # 认证服务
│   │   ├── pipeline.ts             # 流水线服务
│   │   ├── execution.ts            # 执行服务
│   │   ├── websocket.ts            # WebSocket 服务
│   │   └── index.ts                # 导出文件
│   ├── 📁 stores/                  # 状态管理
│   │   ├── auth.ts                 # 认证状态
│   │   ├── pipeline.ts             # 流水线状态
│   │   ├── execution.ts            # 执行状态
│   │   ├── ui.ts                   # UI状态
│   │   └── index.ts                # 导出文件
│   ├── 📁 hooks/                   # 自定义Hook
│   │   ├── useAuth.ts              # 认证Hook
│   │   ├── usePipeline.ts          # 流水线Hook
│   │   ├── useWebSocket.ts         # WebSocket Hook
│   │   ├── useLocalStorage.ts      # 本地存储Hook
│   │   └── index.ts                # 导出文件
│   ├── 📁 types/                   # TypeScript 类型定义
│   │   ├── auth.ts                 # 认证相关类型
│   │   ├── pipeline.ts             # 流水线相关类型
│   │   ├── execution.ts            # 执行相关类型
│   │   ├── api.ts                  # API 响应类型
│   │   └── index.ts                # 导出文件
│   ├── 📁 utils/                   # 工具函数
│   │   ├── format.ts               # 格式化工具
│   │   ├── validation.ts           # 表单验证
│   │   ├── storage.ts              # 存储工具
│   │   ├── constants.ts            # 常量定义
│   │   └── index.ts                # 导出文件
│   ├── 📁 styles/                  # 样式文件
│   │   ├── globals.css             # 全局样式
│   │   ├── components.css          # 组件样式
│   │   └── utilities.css           # 工具样式
│   └── 📁 assets/                  # 静态资源
│       ├── images/                 # 图片资源
│       ├── icons/                  # 图标资源
│       └── fonts/                  # 字体资源
├── 📁 tests/                       # 测试文件
│   ├── components/                 # 组件测试
│   ├── pages/                      # 页面测试
│   ├── services/                   # 服务测试
│   ├── utils/                      # 工具测试
│   └── __mocks__/                  # Mock 文件
├── 📁 cypress/                     # E2E 测试
│   ├── e2e/                        # 端到端测试
│   ├── fixtures/                   # 测试数据
│   └── support/                    # 测试支持文件
└── 📁 .vscode/                     # VS Code 配置
    ├── settings.json               # 编辑器设置
    └── extensions.json             # 推荐扩展
```

## 🛠️ 技术栈

- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **状态管理**: Zustand
- **UI 组件库**: Ant Design
- **样式**: Tailwind CSS
- **图表**: ECharts/Recharts
- **测试**: Vitest + Testing Library + Cypress
- **代码质量**: ESLint + Prettier

## 🚀 快速开始

```bash
# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev

# 构建生产版本
pnpm build

# 运行测试
pnpm test

# E2E 测试
pnpm test:e2e
```

## 📦 主要依赖

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.8.0",
    "antd": "^5.0.0",
    "zustand": "^4.3.0",
    "axios": "^1.3.0",
    "@ant-design/icons": "^5.0.0",
    "echarts": "^5.4.0",
    "tailwindcss": "^3.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.0.0",
    "@types/react-dom": "^18.0.0",
    "@vitejs/plugin-react": "^3.1.0",
    "typescript": "^4.9.0",
    "vite": "^4.1.0",
    "vitest": "^0.28.0",
    "cypress": "^12.0.0",
    "eslint": "^8.35.0",
    "prettier": "^2.8.0"
  }
}
```
