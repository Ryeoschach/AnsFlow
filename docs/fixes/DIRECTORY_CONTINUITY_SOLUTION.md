# 工作目录延续性解决方案

## 问题分析

当前流水线执行器存在工作目录状态无法延续的问题：

1. **现状**：每个步骤都在独立的shell环境中执行
2. **问题**：`cd`命令无法影响后续步骤的工作目录
3. **需求**：实现步骤间工作目录状态的延续

## 解决方案

### 1. 执行上下文增强

在`ExecutionContext`中添加当前工作目录跟踪：

```python
@dataclass
class ExecutionContext:
    # 新增字段
    current_working_directory: Optional[str] = None
    
    def get_current_directory(self) -> str:
        """获取当前工作目录"""
        if self.current_working_directory is None:
            self.current_working_directory = self.get_workspace_path()
        return self.current_working_directory
    
    def set_current_directory(self, path: str) -> None:
        """设置当前工作目录"""
        if not os.path.isabs(path):
            # 相对路径转为绝对路径
            workspace = self.get_workspace_path()
            path = os.path.join(self.get_current_directory(), path)
            path = os.path.abspath(path)
        self.current_working_directory = path
```

### 2. 命令执行器改进

改进`_run_command`方法，支持目录延续：

```python
def _run_command(
    self,
    command: str,
    execution_env: Dict[str, str],
    timeout: Optional[int] = None,
    update_working_dir: bool = True
) -> Dict[str, Any]:
    """运行命令，支持工作目录延续"""
    try:
        if timeout is None:
            timeout = self.default_timeout
        
        # 获取当前工作目录
        current_dir = self.context.get_current_directory()
        
        # 构造完整命令，包含目录切换
        full_command = f"cd '{current_dir}' && {command}"
        
        logger.info(f"在目录 {current_dir} 执行命令: {command}")
        
        process = subprocess.run(
            full_command,
            shell=True,
            capture_output=True,
            text=True,
            env=execution_env,
            timeout=timeout
        )
        
        # 检测目录变化
        if update_working_dir and process.returncode == 0:
            self._detect_directory_change(command, current_dir)
        
        result = {
            'success': process.returncode == 0,
            'output': process.stdout,
            'return_code': process.returncode,
            'working_directory': self.context.get_current_directory()
        }
        
        if process.stderr:
            result['error_output'] = process.stderr
            if not result['success']:
                result['error_message'] = process.stderr
        
        return result
        
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error_message': f'命令执行超时 ({timeout}秒)',
            'output': '',
            'return_code': -1,
            'working_directory': self.context.get_current_directory()
        }
    except Exception as e:
        return {
            'success': False,
            'error_message': str(e),
            'output': '',
            'return_code': -1,
            'working_directory': self.context.get_current_directory()
        }

def _detect_directory_change(self, command: str, previous_dir: str) -> None:
    """检测命令是否改变了工作目录"""
    # 简单的cd命令检测
    import re
    cd_pattern = r'\bcd\s+([^\s;&|]+)'
    match = re.search(cd_pattern, command)
    
    if match:
        target_dir = match.group(1).strip('\'"')
        
        if target_dir.startswith('/'):
            # 绝对路径
            new_dir = target_dir
        elif target_dir == '..':
            # 上级目录
            new_dir = os.path.dirname(previous_dir)
        elif target_dir == '.':
            # 当前目录，无变化
            return
        else:
            # 相对路径
            new_dir = os.path.join(previous_dir, target_dir)
        
        # 标准化路径
        new_dir = os.path.abspath(new_dir)
        
        # 确保目录存在
        if os.path.exists(new_dir) and os.path.isdir(new_dir):
            self.context.set_current_directory(new_dir)
            logger.info(f"工作目录已更新: {new_dir}")
```

### 3. 高级解决方案：shell会话管理

更完善的解决方案是维护一个持久的shell会话：

```python
class PersistentShellExecutor:
    """持久化Shell执行器"""
    
    def __init__(self, context: ExecutionContext):
        self.context = context
        self.shell_process = None
        self.current_directory = None
    
    def start_shell_session(self):
        """启动持久化shell会话"""
        workspace_path = self.context.get_workspace_path()
        
        self.shell_process = subprocess.Popen(
            ['bash', '-i'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=workspace_path
        )
        
        self.current_directory = workspace_path
        
        # 初始化shell环境
        self._execute_shell_command(f"cd '{workspace_path}'")
    
    def execute_command(self, command: str, timeout: int = 300) -> Dict[str, Any]:
        """在持久化shell中执行命令"""
        if self.shell_process is None:
            self.start_shell_session()
        
        try:
            # 添加命令结束标记
            marked_command = f"{command}\necho '<<<COMMAND_DONE>>>'\n"
            
            self.shell_process.stdin.write(marked_command)
            self.shell_process.stdin.flush()
            
            # 读取输出直到结束标记
            output_lines = []
            while True:
                line = self.shell_process.stdout.readline()
                if '<<<COMMAND_DONE>>>' in line:
                    break
                output_lines.append(line.rstrip())
            
            # 获取工作目录
            self._update_current_directory()
            
            return {
                'success': True,
                'output': '\n'.join(output_lines),
                'working_directory': self.current_directory
            }
            
        except Exception as e:
            return {
                'success': False,
                'error_message': str(e),
                'output': '',
                'working_directory': self.current_directory
            }
    
    def _update_current_directory(self):
        """更新当前工作目录"""
        try:
            self.shell_process.stdin.write("pwd\necho '<<<PWD_DONE>>>'\n")
            self.shell_process.stdin.flush()
            
            while True:
                line = self.shell_process.stdout.readline().strip()
                if '<<<PWD_DONE>>>' in line:
                    break
                if line and not line.startswith('<<<'):
                    self.current_directory = line
                    self.context.set_current_directory(line)
                    break
        except Exception as e:
            logger.warning(f"Failed to update working directory: {e}")
    
    def close_shell_session(self):
        """关闭shell会话"""
        if self.shell_process:
            self.shell_process.terminate()
            self.shell_process = None
```

## 实施步骤

### 步骤1：简单方案实施

1. 修改`ExecutionContext`类，添加工作目录跟踪
2. 改进`_run_command`方法，支持目录前缀
3. 添加目录变化检测逻辑

### 步骤2：测试验证

创建测试用例验证目录延续功能：

```python
def test_directory_continuity():
    """测试目录延续性"""
    # 步骤1: cd到子目录
    # 步骤2: pwd验证目录
    # 步骤3: 在子目录执行命令
```

### 步骤3：高级方案

如果简单方案无法满足需求，实施持久化shell会话方案。

## 优缺点分析

### 简单方案
**优点**：
- 实现简单
- 向后兼容
- 低资源占用

**缺点**：
- 只能检测简单的cd命令
- 无法处理复杂的目录变化

### 持久化shell方案
**优点**：
- 完全模拟真实shell行为
- 支持所有类型的目录变化
- 环境变量也能延续

**缺点**：
- 实现复杂
- 资源占用较高
- 错误处理复杂

## 推荐方案

建议先实施简单方案，满足大部分使用场景。如果后续有更复杂的需求，再考虑持久化shell方案。
