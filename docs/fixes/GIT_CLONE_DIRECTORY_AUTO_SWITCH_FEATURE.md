# Git Clone 目录自动切换功能

## 📖 问题描述

在使用AnsFlow流水线执行Git代码拉取时，遇到以下问题：

```bash
# 执行命令
git clone ssh://git@gitlab.cyfee.com:2424/root/test.git

# 实际结果
工作目录: /tmp/本地docker测试_38
├── test/           # Git clone创建的目录
│   ├── README.md
│   ├── src/
│   └── .git/

# 问题现象
后续步骤执行 ls -la 时显示空目录，无法看到代码文件
因为工作目录仍在 /tmp/本地docker测试_38，而不是 /tmp/本地docker测试_38/test
```

## ✨ 解决方案

实现了**Git Clone目录自动检测和切换**功能：

### 🔧 核心功能

1. **自动检测Git Clone目录**
   - 分析Git clone命令，提取仓库名称
   - 检测工作目录中新创建的仓库目录
   - 支持多种Git URL格式

2. **自动切换工作目录**
   - Git clone执行后自动切换到仓库目录
   - 更新执行上下文的当前工作目录
   - 后续步骤在正确的目录中执行

3. **智能目录识别**
   - 验证目录确实是Git仓库（检查.git目录）
   - 支持自定义目标目录
   - 详细的日志记录

## 🎯 支持的Git URL格式

| 格式 | 示例 | 检测结果 |
|------|------|----------|
| SSH协议 | `ssh://git@gitlab.com:2424/user/repo.git` | `repo` |
| HTTPS协议 | `https://github.com/user/project.git` | `project` |
| SSH简化格式 | `git@github.com:user/repo-name.git` | `repo-name` |
| 指定目标目录 | `git clone <url> custom-dir` | `custom-dir` |
| 克隆到当前目录 | `git clone <url> .` | 从URL提取仓库名 |

## 🚀 实际效果

### 修复前
```bash
=== 拉取代码 ===
$ git clone ssh://git@gitlab.cyfee.com:2424/root/test.git
工作目录: /tmp/本地docker测试_38

=== 测试 ===
$ ls -la && pwd
工作目录: /tmp/本地docker测试_38
输出: 
total 0
drwxr-xr-x@  2 creed  wheel   64 Jul 22 07:15 .
drwxrwxrwt  14 root   wheel  448 Jul 22 07:15 ..
/tmp/本地docker测试_38

❌ 看不到代码文件！
```

### 修复后
```bash
=== 拉取代码 ===
$ git clone ssh://git@gitlab.cyfee.com:2424/root/test.git
🔄 检测到Git clone创建了目录 'test'，自动切换工作目录到: /tmp/本地docker测试_38/test
✅ 确认 'test' 是有效的Git仓库

=== 测试 ===
$ ls -la && pwd
工作目录: /tmp/本地docker测试_38/test
输出:
total 12
drwxr-xr-x@ 5 creed  wheel  160 Jul 22 15:15 .
drwxr-xr-x@ 3 creed  wheel   96 Jul 22 15:15 ..
drwxr-xr-x@ 8 creed  wheel  256 Jul 22 15:15 .git
-rw-r--r--@ 1 creed  wheel   28 Jul 22 15:15 README.md
drwxr-xr-x@ 3 creed  wheel   96 Jul 22 15:15 src
/tmp/本地docker测试_38/test

✅ 可以看到所有代码文件！
```

## 🔧 技术实现

### 1. 检测逻辑
```python
def _detect_and_handle_git_clone_directory(self, git_command: str, workspace_path: str):
    """检测Git clone命令创建的目录并自动切换"""
    # 1. 解析Git clone命令
    # 2. 提取仓库URL和目标目录
    # 3. 计算预期的目录名
    # 4. 检查目录是否存在
    # 5. 验证是否为Git仓库
    # 6. 自动切换工作目录
```

### 2. URL解析
- 正则表达式匹配Git clone命令
- 支持SSH、HTTPS、简化SSH格式
- 处理自定义目标目录
- 提取仓库名称作为默认目录名

### 3. 目录验证
- 检查目录是否存在
- 验证.git目录存在
- 确保是有效的Git仓库
- 详细的日志记录

## 📝 修改文件

### `sync_step_executor.py`
```python
# 在 _execute_fetch_code 方法中添加：
self._detect_and_handle_git_clone_directory(
    custom_command or f'git clone {repository_url}', 
    workspace_path
)

# 新增方法：
def _detect_and_handle_git_clone_directory(self, git_command, workspace_path):
    # 实现Git clone目录检测和切换逻辑
```

## 🎯 使用场景

### 1. 标准Git Clone
```bash
git clone https://github.com/user/project.git
# 自动切换到 project/ 目录
```

### 2. SSH协议
```bash
git clone ssh://git@gitlab.com:2424/user/repo.git  
# 自动切换到 repo/ 目录
```

### 3. 自定义目录
```bash
git clone <url> my-custom-dir
# 自动切换到 my-custom-dir/ 目录
```

### 4. 复杂项目结构
```bash
git clone ssh://git@gitlab.cyfee.com:2424/root/test.git
cd test
npm install
npm run build
# 所有命令都在正确的目录中执行
```

## ✅ 验证测试

提供了完整的测试套件：

1. **单元测试** (`test_git_clone_detection.py`)
   - 测试URL解析逻辑
   - 验证目录名提取
   - 支持多种Git格式

2. **集成测试** (`test_git_clone_integration.py`) 
   - 模拟完整流水线执行
   - 验证目录切换效果
   - 对比修复前后的差异

## 🎉 总结

这个功能解决了Git clone后工作目录不匹配的问题，让AnsFlow流水线可以：

- ✅ 自动检测Git clone创建的目录
- ✅ 智能切换到正确的工作目录  
- ✅ 确保后续步骤在代码目录中执行
- ✅ 支持所有常见的Git URL格式
- ✅ 提供详细的执行日志
- ✅ 与现有目录连续性功能完美集成

现在您的流水线执行 `git clone ssh://git@gitlab.cyfee.com:2424/root/test.git` 后，后续的 `ls -la` 命令将能正确显示仓库中的所有文件！
