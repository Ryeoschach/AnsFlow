# AnsFlow API 参数详细说明

## 流水线步骤参数说明

### 1. fetch_code (代码拉取)

#### 基础参数
```json
{
  "repository": "string",          // 必填：Git仓库URL
  "branch": "string",             // 可选：分支名称，默认为 "main"
  "tag": "string",                // 可选：标签名称
  "commit": "string",             // 可选：具体commit ID
  "clone_depth": "integer",       // 可选：克隆深度，默认为 1
  "submodules": "boolean",        // 可选：是否拉取子模块，默认 false
  "lfs": "boolean",               // 可选：是否支持Git LFS，默认 false
  "clean": "boolean",             // 可选：是否清理工作目录，默认 true
  "checkout_path": "string",      // 可选：检出到指定路径
  "timeout": "integer"            // 可选：超时时间（秒），默认 300
}
```

#### 高级参数
```json
{
  "fetch_strategy": "clone|checkout|merge",  // 拉取策略
  "merge_target": "string",                  // 合并目标分支
  "skip_verification": "boolean",            // 跳过SSL验证
  "include_patterns": ["string"],            // 包含文件模式
  "exclude_patterns": ["string"],            // 排除文件模式
  "post_clone_commands": ["string"]          // 克隆后执行的命令
}
```

#### 使用示例
```json
{
  "repository": "https://github.com/company/webapp.git",
  "branch": "develop",
  "clone_depth": 1,
  "submodules": true,
  "checkout_path": "./source",
  "timeout": 600,
  "include_patterns": ["src/**", "package.json"],
  "post_clone_commands": [
    "git config user.email 'ci@company.com'",
    "git config user.name 'CI Bot'"
  ]
}
```

### 2. build (构建)

#### Node.js 项目
```json
{
  "build_tool": "npm|yarn|pnpm",     // 构建工具
  "build_command": "string",          // 构建命令
  "install_command": "string",        // 安装依赖命令
  "working_directory": "string",      // 工作目录
  "node_version": "string",           // Node.js版本
  "cache_dependencies": "boolean",    // 缓存依赖
  "production_build": "boolean",      // 生产构建
  "build_args": ["string"],          // 构建参数
  "environment_variables": "object", // 环境变量
  "artifact_path": "string",         // 构建产物路径
  "timeout": "integer"               // 超时时间
}
```

#### Java 项目
```json
{
  "build_tool": "maven|gradle",      // 构建工具
  "build_command": "string",          // 构建命令
  "java_version": "string",           // Java版本
  "maven_profile": "string",          // Maven Profile
  "gradle_task": "string",           // Gradle任务
  "skip_tests": "boolean",           // 跳过测试
  "clean_build": "boolean",          // 清理构建
  "parallel_build": "boolean",       // 并行构建
  "build_options": ["string"]        // 构建选项
}
```

#### Docker 构建
```json
{
  "dockerfile_path": "string",        // Dockerfile路径
  "build_context": "string",          // 构建上下文
  "image_name": "string",             // 镜像名称
  "image_tag": "string",              // 镜像标签
  "build_args": "object",             // 构建参数
  "no_cache": "boolean",              // 不使用缓存
  "platform": "string",              // 目标平台
  "registry_url": "string",           // 镜像仓库URL
  "push_image": "boolean"             // 是否推送镜像
}
```

### 3. test (测试)

#### 单元测试
```json
{
  "test_framework": "jest|mocha|pytest|junit",  // 测试框架
  "test_command": "string",                      // 测试命令
  "test_pattern": "string",                     // 测试文件模式
  "coverage": "boolean",                        // 生成覆盖率报告
  "coverage_threshold": "integer",              // 覆盖率阈值
  "test_results_path": "string",               // 测试结果文件路径
  "coverage_report_path": "string",            // 覆盖率报告路径
  "parallel_tests": "boolean",                 // 并行测试
  "max_workers": "integer",                    // 最大工作进程数
  "timeout": "integer",                        // 超时时间
  "retry_on_failure": "integer"                // 失败重试次数
}
```

#### 集成测试
```json
{
  "test_environment": "string",        // 测试环境
  "database_url": "string",           // 测试数据库URL
  "setup_commands": ["string"],       // 环境准备命令
  "teardown_commands": ["string"],    // 环境清理命令
  "test_data_path": "string",         // 测试数据路径
  "service_dependencies": ["string"], // 服务依赖
  "wait_for_services": "boolean",     // 等待服务启动
  "health_check_url": "string"        // 健康检查URL
}
```

#### E2E测试
```json
{
  "browser": "chrome|firefox|safari", // 浏览器类型
  "headless": "boolean",              // 无头模式
  "viewport_size": "string",          // 视口大小
  "test_url": "string",               // 测试URL
  "screenshot_on_failure": "boolean", // 失败时截图
  "video_recording": "boolean",       // 录制视频
  "test_spec_pattern": "string",      // 测试规范模式
  "parallel_sessions": "integer"      // 并行会话数
}
```

### 4. security_scan (安全扫描)

#### 依赖漏洞扫描
```json
{
  "scan_tool": "npm audit|yarn audit|safety|snyk",  // 扫描工具
  "severity_threshold": "low|moderate|high|critical", // 严重性阈值
  "fail_on_critical": "boolean",                      // 发现严重漏洞时失败
  "ignore_vulnerabilities": ["string"],               // 忽略的漏洞ID
  "scan_command": "string",                           // 自定义扫描命令
  "report_format": "json|xml|html",                   // 报告格式
  "report_path": "string",                            // 报告保存路径
  "update_dependencies": "boolean"                    // 自动更新依赖
}
```

#### 代码扫描
```json
{
  "scan_tool": "sonarqube|codeql|eslint|bandit",  // 代码扫描工具
  "ruleset": "string",                             // 规则集
  "scan_patterns": ["string"],                     // 扫描文件模式
  "exclude_patterns": ["string"],                  // 排除文件模式
  "quality_gate": "boolean",                       // 质量门禁
  "max_issues": "integer",                         // 最大问题数
  "severity_levels": ["string"],                   // 严重性级别
  "custom_rules": "object"                         // 自定义规则
}
```

#### 容器安全扫描
```json
{
  "image_name": "string",              // 镜像名称
  "scan_tool": "trivy|clair|anchore", // 扫描工具
  "scan_layers": "boolean",           // 扫描镜像层
  "scan_secrets": "boolean",          // 扫描敏感信息
  "fail_on_high": "boolean",          // 高危漏洞时失败
  "whitelist_cves": ["string"],       // 白名单CVE
  "scan_timeout": "integer"           // 扫描超时
}
```

### 5. deploy (部署)

#### Kubernetes部署
```json
{
  "deployment_strategy": "rolling|blue-green|canary",  // 部署策略
  "namespace": "string",                                // 命名空间
  "cluster_config": "string",                          // 集群配置路径
  "manifest_path": "string",                           // 清单文件路径
  "image_tag": "string",                               // 镜像标签
  "environment": "development|staging|production",     // 环境
  "replicas": "integer",                               // 副本数
  "rolling_update": {
    "max_surge": "string",                             // 最大增加数
    "max_unavailable": "string"                        // 最大不可用数
  },
  "health_check": {
    "enabled": "boolean",                              // 启用健康检查
    "path": "string",                                  // 健康检查路径
    "timeout": "integer"                               // 超时时间
  },
  "rollback_on_failure": "boolean"                     // 失败时回滚
}
```

#### Docker部署
```json
{
  "image_name": "string",             // 镜像名称
  "container_name": "string",         // 容器名称
  "ports": ["string"],               // 端口映射
  "volumes": ["string"],             // 卷挂载
  "environment_vars": "object",       // 环境变量
  "network": "string",               // 网络配置
  "restart_policy": "string",        // 重启策略
  "memory_limit": "string",          // 内存限制
  "cpu_limit": "string",             // CPU限制
  "host": "string",                  // 目标主机
  "registry_auth": "object"          // 镜像仓库认证
}
```

#### 传统服务器部署
```json
{
  "deploy_method": "rsync|scp|ftp",   // 部署方法
  "source_path": "string",            // 源路径
  "target_path": "string",            // 目标路径
  "servers": ["string"],              // 目标服务器
  "backup_before_deploy": "boolean",  // 部署前备份
  "backup_path": "string",            // 备份路径
  "pre_deploy_commands": ["string"],  // 部署前命令
  "post_deploy_commands": ["string"], // 部署后命令
  "file_permissions": "string",       // 文件权限
  "owner": "string",                  // 文件所有者
  "exclude_files": ["string"]         // 排除文件
}
```

### 6. ansible (Ansible自动化)

#### 基础参数
```json
{
  "playbook_id": "integer",           // 必填：Playbook ID
  "inventory_id": "integer",          // 可选：Inventory ID
  "credential_id": "integer",         // 可选：凭据ID
  "variables": "object",              // 可选：变量
  "tags": ["string"],                // 可选：标签
  "skip_tags": ["string"],           // 可选：跳过的标签
  "limit": "string",                 // 可选：限制主机
  "vault_password": "string",        // 可选：Vault密码
  "become": "boolean",               // 可选：提权执行
  "become_user": "string",           // 可选：提权用户
  "timeout": "integer",              // 可选：超时时间
  "verbosity": "integer"             // 可选：详细级别 (0-4)
}
```

#### 高级参数
```json
{
  "ansible_config": "string",         // Ansible配置文件路径
  "ssh_args": "string",              // SSH参数
  "connection_timeout": "integer",    // 连接超时
  "gather_facts": "boolean",         // 收集系统信息
  "check_mode": "boolean",           // 检查模式（干运行）
  "diff_mode": "boolean",            // 差异模式
  "force_handlers": "boolean",       // 强制执行处理器
  "start_at_task": "string",         // 从指定任务开始
  "step": "boolean",                 // 步进模式
  "syntax_check": "boolean"          // 语法检查
}
```

### 7. notify (通知)

#### Slack通知
```json
{
  "notification_type": "slack",       // 通知类型
  "webhook_url": "string",           // Webhook URL
  "channel": "string",               // 频道名称
  "username": "string",              // 用户名
  "icon_emoji": "string",            // 表情图标
  "message": "string",               // 消息内容
  "attachments": "array",            // 附件
  "thread_ts": "string",             // 线程时间戳
  "link_names": "boolean"            // 链接用户名
}
```

#### 邮件通知
```json
{
  "notification_type": "email",      // 通知类型
  "smtp_server": "string",           // SMTP服务器
  "smtp_port": "integer",            // SMTP端口
  "smtp_username": "string",         // SMTP用户名
  "smtp_password": "string",         // SMTP密码
  "from_email": "string",            // 发件人邮箱
  "to_emails": ["string"],           // 收件人邮箱
  "cc_emails": ["string"],           // 抄送邮箱
  "subject": "string",               // 邮件主题
  "body": "string",                  // 邮件正文
  "html_body": "string",             // HTML正文
  "attachments": ["string"]          // 附件路径
}
```

#### 企业微信通知
```json
{
  "notification_type": "wechat",     // 通知类型
  "webhook_url": "string",           // Webhook URL
  "msgtype": "text|markdown|image|news",  // 消息类型
  "content": "string",               // 消息内容
  "mentioned_list": ["string"],      // @成员列表
  "mentioned_mobile_list": ["string"]  // @手机号列表
}
```

### 8. custom (自定义)

#### Shell命令
```json
{
  "command": "string",               // 必填：执行命令
  "working_directory": "string",     // 工作目录
  "shell": "bash|sh|zsh|fish",      // Shell类型
  "environment_variables": "object", // 环境变量
  "timeout": "integer",              // 超时时间
  "retry_on_failure": "integer",     // 失败重试次数
  "ignore_errors": "boolean",        // 忽略错误
  "capture_output": "boolean",       // 捕获输出
  "output_file": "string",           // 输出文件
  "input_data": "string"             // 输入数据
}
```

#### 脚本执行
```json
{
  "script_type": "python|nodejs|ruby|go",  // 脚本类型
  "script_content": "string",              // 脚本内容
  "script_file": "string",                 // 脚本文件路径
  "interpreter_version": "string",         // 解释器版本
  "script_args": ["string"],               // 脚本参数
  "requirements_file": "string",           // 依赖文件
  "virtual_env": "boolean",                // 虚拟环境
  "install_dependencies": "boolean"        // 安装依赖
}
```

#### HTTP请求
```json
{
  "http_method": "GET|POST|PUT|DELETE",  // HTTP方法
  "url": "string",                       // 请求URL
  "headers": "object",                   // 请求头
  "body": "string",                      // 请求体
  "query_params": "object",              // 查询参数
  "auth_type": "basic|bearer|oauth",     // 认证类型
  "auth_credentials": "object",          // 认证凭据
  "timeout": "integer",                  // 超时时间
  "follow_redirects": "boolean",         // 跟随重定向
  "verify_ssl": "boolean",               // 验证SSL
  "expected_status": ["integer"]         // 期望状态码
}
```

## 全局参数说明

### 环境变量
所有步骤都支持以下环境变量：
```json
{
  "BUILD_NUMBER": "构建号",
  "BUILD_ID": "构建ID",
  "BUILD_URL": "构建URL",
  "PROJECT_NAME": "项目名称",
  "PIPELINE_NAME": "流水线名称",
  "GIT_COMMIT": "Git提交ID",
  "GIT_BRANCH": "Git分支",
  "GIT_URL": "Git仓库URL",
  "WORKSPACE": "工作空间路径",
  "NODE_NAME": "节点名称",
  "EXECUTOR_NUMBER": "执行器编号"
}
```

### 条件执行
所有步骤都支持条件执行：
```json
{
  "condition": "string",                 // 执行条件表达式
  "condition_type": "expression|script", // 条件类型
  "on_skip": "continue|fail|stop"        // 跳过时的行为
}
```

### 并行执行
支持步骤并行执行：
```json
{
  "parallel_group": "string",           // 并行组名称
  "max_parallel": "integer",            // 最大并行数
  "wait_for_completion": "boolean"      // 等待组内所有步骤完成
}
```

### 错误处理
所有步骤都支持错误处理：
```json
{
  "continue_on_error": "boolean",       // 出错时继续
  "retry_count": "integer",             // 重试次数
  "retry_delay": "integer",             // 重试延迟（秒）
  "failure_action": "stop|continue|retry",  // 失败时的行为
  "error_handler": "string"             // 错误处理器
}
```

### 缓存配置
支持步骤结果缓存：
```json
{
  "cache_enabled": "boolean",           // 启用缓存
  "cache_key": "string",               // 缓存键
  "cache_ttl": "integer",              // 缓存TTL（秒）
  "cache_paths": ["string"],           // 缓存路径
  "cache_scope": "pipeline|project|global"  // 缓存范围
}
```

## 参数验证规则

### 字符串参数
- `required`: 是否必填
- `min_length`: 最小长度
- `max_length`: 最大长度
- `pattern`: 正则表达式模式
- `enum`: 枚举值列表

### 数值参数
- `required`: 是否必填
- `min_value`: 最小值
- `max_value`: 最大值
- `decimal_places`: 小数位数

### 数组参数
- `required`: 是否必填
- `min_items`: 最小项目数
- `max_items`: 最大项目数
- `item_type`: 项目类型

### 对象参数
- `required`: 是否必填
- `properties`: 属性定义
- `additional_properties`: 是否允许额外属性

## 参数示例模板

### 完整的Node.js Web应用流水线参数
```json
{
  "steps": [
    {
      "name": "代码拉取",
      "step_type": "fetch_code",
      "parameters": {
        "repository": "https://github.com/company/webapp.git",
        "branch": "main",
        "clone_depth": 1,
        "submodules": false,
        "timeout": 300
      }
    },
    {
      "name": "安装依赖",
      "step_type": "build",
      "parameters": {
        "build_tool": "npm",
        "build_command": "npm ci",
        "cache_dependencies": true,
        "node_version": "18",
        "timeout": 600
      }
    },
    {
      "name": "代码检查",
      "step_type": "test",
      "parameters": {
        "test_framework": "eslint",
        "test_command": "npm run lint",
        "fail_on_errors": true
      }
    },
    {
      "name": "单元测试",
      "step_type": "test",
      "parameters": {
        "test_framework": "jest",
        "test_command": "npm test",
        "coverage": true,
        "coverage_threshold": 80,
        "parallel_tests": true
      }
    },
    {
      "name": "安全扫描",
      "step_type": "security_scan",
      "parameters": {
        "scan_tool": "npm audit",
        "severity_threshold": "moderate",
        "fail_on_critical": true
      }
    },
    {
      "name": "构建应用",
      "step_type": "build",
      "parameters": {
        "build_command": "npm run build",
        "production_build": true,
        "artifact_path": "dist/",
        "environment_variables": {
          "NODE_ENV": "production"
        }
      }
    },
    {
      "name": "部署到生产",
      "step_type": "deploy",
      "parameters": {
        "deployment_strategy": "rolling",
        "namespace": "production",
        "replicas": 3,
        "health_check": {
          "enabled": true,
          "path": "/health",
          "timeout": 30
        },
        "rollback_on_failure": true
      }
    },
    {
      "name": "部署通知",
      "step_type": "notify",
      "parameters": {
        "notification_type": "slack",
        "webhook_url": "https://hooks.slack.com/...",
        "channel": "#deployments",
        "message": "🚀 应用已成功部署到生产环境"
      }
    }
  ]
}
```
