# 执行日志模块使用指南

## 概述

`ExecutionLogger` 是一个公共的执行日志记录模块，提供统一的日志记录功能，避免在各个执行器中重复编写相同的日志记录代码。

## 主要功能

### 1. 基本方法

#### `start_execution(execution, log_message=None)`
开始执行，设置状态为 `running` 并记录开始时间。

```python
from common.execution_logger import ExecutionLogger

# 开始执行
ExecutionLogger.start_execution(
    execution, 
    "开始执行Ansible playbook: example.yml"
)
```

#### `complete_execution(execution, result=None, status=None, ...)`
完成执行，记录执行结果和完成时间。

```python
# 处理subprocess结果
result = subprocess.run(['command'], capture_output=True, text=True)
ExecutionLogger.complete_execution(
    execution,
    result=result,  # 自动解析stdout、stderr、return_code
    log_message="执行完成"
)

# 手动指定状态
ExecutionLogger.complete_execution(
    execution,
    status='success',
    custom_logs="自定义日志内容",
    log_message="任务执行成功"
)
```

#### `fail_execution(execution, error_message, return_code=-1, log_message=None)`
标记执行失败。

```python
ExecutionLogger.fail_execution(
    execution,
    error_message="连接超时",
    log_message="执行失败：连接超时"
)
```

#### `timeout_execution(execution, timeout_message, timeout_seconds=None, log_message=None)`
标记执行超时。

```python
ExecutionLogger.timeout_execution(
    execution,
    timeout_seconds=300,
    log_message="执行超时"
)
```

#### `cancel_execution(execution, cancel_message, log_message=None)`
标记执行已取消。

```python
ExecutionLogger.cancel_execution(
    execution,
    cancel_message="用户取消执行",
    log_message="执行被用户取消"
)
```

### 2. 辅助方法

#### `update_execution_logs(execution, logs, append=False)`
更新或追加执行日志。

```python
ExecutionLogger.update_execution_logs(
    execution,
    "新的日志内容",
    append=True  # 追加到现有日志
)
```

#### `log_execution_info(execution, message, level='info')`
记录执行信息到日志系统。

```python
ExecutionLogger.log_execution_info(
    execution,
    "开始下载文件",
    level='info'
)
```

### 3. 上下文管理器

使用 `ExecutionContext` 自动处理执行开始和结束：

```python
from common.execution_logger import ExecutionContext

def my_task(execution_id):
    execution = MyExecution.objects.get(id=execution_id)
    
    with ExecutionContext(execution, "开始执行任务") as ctx:
        # 执行具体逻辑
        result = subprocess.run(['my-command'], capture_output=True, text=True)
        
        # 设置执行结果
        ctx.set_result(result)
        
        # 如果发生异常，会自动调用fail_execution
        # 如果正常完成，会自动调用complete_execution
```

## 使用示例

### 替换前的代码（重复的日志记录）

```python
@shared_task
def execute_my_task(execution_id):
    try:
        execution = MyExecution.objects.get(id=execution_id)
        
        # 手动设置开始状态
        execution.status = 'running'
        execution.started_at = timezone.now()
        execution.save()
        
        logger.info(f"开始执行任务: {execution.name}")
        
        # 执行逻辑
        result = subprocess.run(['my-command'], capture_output=True, text=True)
        
        # 手动保存结果
        execution.stdout = result.stdout
        execution.stderr = result.stderr
        execution.return_code = result.returncode
        
        if result.returncode == 0:
            execution.status = 'success'
            logger.info(f"任务执行成功: {execution.name}")
        else:
            execution.status = 'failed'
            logger.error(f"任务执行失败: {execution.name}")
            
    except subprocess.TimeoutExpired:
        execution.status = 'failed'
        execution.stderr = "执行超时"
        execution.return_code = -1
        logger.error(f"任务执行超时: {execution.name}")
        
    except Exception as e:
        execution.status = 'failed'
        execution.stderr = str(e)
        execution.return_code = -1
        logger.error(f"任务执行异常: {execution.name}, 错误: {str(e)}")
        
    finally:
        execution.completed_at = timezone.now()
        execution.save()
```

### 替换后的代码（使用ExecutionLogger）

```python
from common.execution_logger import ExecutionLogger

@shared_task
def execute_my_task(execution_id):
    try:
        execution = MyExecution.objects.get(id=execution_id)
        
        # 开始执行
        ExecutionLogger.start_execution(
            execution, 
            f"开始执行任务: {execution.name}"
        )
        
        # 执行逻辑
        result = subprocess.run(['my-command'], capture_output=True, text=True, timeout=300)
        
        # 完成执行（自动处理结果）
        ExecutionLogger.complete_execution(
            execution,
            result=result,
            log_message=f"任务执行完成: {execution.name}"
        )
            
    except subprocess.TimeoutExpired:
        ExecutionLogger.timeout_execution(
            execution,
            timeout_seconds=300,
            log_message=f"任务执行超时: {execution.name}"
        )
        
    except Exception as e:
        ExecutionLogger.fail_execution(
            execution,
            error_message=str(e),
            log_message=f"任务执行异常: {execution.name}, 错误: {str(e)}"
        )
```

## 兼容性

ExecutionLogger 自动检测执行对象的属性，并只设置存在的字段：

- `status`: 执行状态
- `started_at`: 开始时间
- `completed_at`: 完成时间
- `stdout`: 标准输出
- `stderr`: 标准错误输出
- `return_code`: 返回码
- `logs`: 日志内容（会合并stdout和stderr）

## 在现有执行器中的应用

### 1. local_executor.py
```python
from common.execution_logger import ExecutionLogger

def execute_step(self, step_execution):
    ExecutionLogger.start_execution(step_execution, f"开始执行步骤: {step_execution.step.name}")
    
    try:
        # 执行逻辑
        result = self._run_command(command)
        ExecutionLogger.complete_execution(step_execution, result=result)
    except Exception as e:
        ExecutionLogger.fail_execution(step_execution, str(e))
```

### 2. docker_executor.py
```python
from common.execution_logger import ExecutionLogger

def build_image(self, execution):
    ExecutionLogger.start_execution(execution, "开始Docker镜像构建")
    
    try:
        result = self._run_docker_build()
        ExecutionLogger.complete_execution(execution, result=result)
    except Exception as e:
        ExecutionLogger.fail_execution(execution, str(e))
```

### 3. kubernetes_executor.py
```python
from common.execution_logger import ExecutionLogger

def deploy_to_k8s(self, execution):
    with ExecutionContext(execution, "开始Kubernetes部署") as ctx:
        result = self._kubectl_apply()
        ctx.set_result(result)
```

## 优势

1. **代码复用**: 避免在每个执行器中重复编写相同的日志记录逻辑
2. **一致性**: 保证所有执行器的日志记录格式和行为一致
3. **维护性**: 修改日志记录逻辑只需要在一个地方进行
4. **可扩展性**: 易于添加新的日志记录功能，如WebSocket通知、监控指标等
5. **错误处理**: 统一的异常处理和错误记录
6. **灵活性**: 支持多种使用方式，从简单的方法调用到上下文管理器
