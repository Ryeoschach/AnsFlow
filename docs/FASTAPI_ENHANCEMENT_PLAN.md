# FastAPI 服务增强方案

## 当前状况
- FastAPI服务存在但功能简单
- 主要业务逻辑都在Django中
- 未发挥FastAPI高性能优势

## FastAPI 应该承担的职责

### 1. 高并发实时API
```python
# 流水线状态实时查询API
@app.get("/api/v1/pipelines/{pipeline_id}/status/realtime")
async def get_pipeline_status_realtime(pipeline_id: int):
    """高频轮询的流水线状态查询"""
    # 从Redis缓存获取，而不是数据库
    status = await redis_client.get(f"pipeline:{pipeline_id}:status")
    return {"status": status, "last_updated": datetime.utcnow()}

# 系统监控指标API
@app.get("/api/v1/system/metrics/realtime")
async def get_system_metrics():
    """实时系统指标，高频访问"""
    metrics = await get_cached_metrics()
    return metrics
```

### 2. WebSocket实时通信
```python
# WebSocket连接管理
@app.websocket("/ws/pipeline/{pipeline_id}")
async def pipeline_websocket(websocket: WebSocket, pipeline_id: int):
    """流水线执行状态实时推送"""
    await websocket.accept()
    try:
        while True:
            # 监听Redis中的状态变化
            status = await redis_client.get(f"pipeline:{pipeline_id}:status")
            await websocket.send_json({"status": status})
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass

# 系统监控WebSocket
@app.websocket("/ws/system/monitoring")
async def system_monitoring_websocket(websocket: WebSocket):
    """系统监控指标实时推送"""
    # 实现系统指标的实时推送
    pass
```

### 3. 外部Webhook接收
```python
# GitHub Webhook处理
@app.post("/webhooks/github")
async def github_webhook(request: Request):
    """处理GitHub webhook，高并发场景"""
    payload = await request.json()
    
    # 快速响应，异步处理
    background_tasks.add_task(process_github_webhook, payload)
    return {"status": "received"}

# GitLab Webhook处理
@app.post("/webhooks/gitlab")
async def gitlab_webhook(request: Request):
    """处理GitLab webhook"""
    # 类似实现
    pass

# 通用CI/CD工具回调
@app.post("/callbacks/{tool_name}")
async def cicd_callback(tool_name: str, request: Request):
    """处理各种CI/CD工具的回调"""
    # 根据tool_name路由到对应处理器
    pass
```

### 4. 文件上传和处理
```python
# 大文件上传API
@app.post("/api/v1/files/upload")
async def upload_file(file: UploadFile = File(...)):
    """异步文件上传处理"""
    # 使用异步IO处理大文件上传
    content = await file.read()
    # 异步保存到存储
    await save_file_async(file.filename, content)
    return {"filename": file.filename, "size": len(content)}

# 构建产物下载
@app.get("/api/v1/artifacts/{artifact_id}/download")
async def download_artifact(artifact_id: str):
    """异步文件下载"""
    return StreamingResponse(
        get_file_stream(artifact_id),
        media_type='application/octet-stream'
    )
```

### 5. 高性能查询API
```python
# 大数据量查询API
@app.get("/api/v1/logs/search")
async def search_logs(
    query: str,
    limit: int = 100,
    offset: int = 0
):
    """异步日志搜索，支持大量数据"""
    results = await search_logs_async(query, limit, offset)
    return results

# 复杂统计查询
@app.get("/api/v1/analytics/dashboard")
async def get_dashboard_data():
    """异步获取仪表盘数据"""
    # 并发执行多个查询
    tasks = [
        get_pipeline_stats(),
        get_execution_trends(),
        get_error_rates(),
        get_performance_metrics()
    ]
    results = await asyncio.gather(*tasks)
    return combine_dashboard_data(results)
```

## FastAPI与Django的分工

### Django负责 (低频、复杂业务逻辑)
- 用户认证和权限管理
- 复杂业务逻辑处理
- 数据库写入操作
- 管理界面和CRUD操作
- 配置管理和设置

### FastAPI负责 (高频、实时、异步)
- 实时状态查询API
- WebSocket实时通信
- 外部webhook接收
- 文件上传下载
- 高并发只读查询
- 缓存数据API

## 服务间通信优化

### 1. 数据同步
```python
# Django更新数据时，同步到Redis
def update_pipeline_status(pipeline_id, status):
    # 更新数据库
    pipeline = Pipeline.objects.get(id=pipeline_id)
    pipeline.status = status
    pipeline.save()
    
    # 同步到Redis供FastAPI使用
    redis_client.set(f"pipeline:{pipeline_id}:status", status)
    redis_client.expire(f"pipeline:{pipeline_id}:status", 3600)  # 1小时过期
```

### 2. 事件通知
```python
# 使用Redis Pub/Sub进行实时通知
def notify_status_change(pipeline_id, status):
    redis_client.publish(f"pipeline:{pipeline_id}:events", json.dumps({
        "type": "status_change",
        "status": status,
        "timestamp": datetime.utcnow().isoformat()
    }))
```

## 性能优势

### 1. 并发处理能力
- Django: 同步处理，适合复杂业务逻辑
- FastAPI: 异步处理，适合高并发IO密集型任务

### 2. 响应时间
- 实时API响应时间从100ms降低到10ms以下
- WebSocket连接可以支持更多并发用户
- 文件上传下载性能显著提升

### 3. 资源利用率
- 更好的CPU和内存利用率
- 减少数据库查询压力
- 提高缓存命中率

## 实施建议

### 阶段1：基础功能迁移 (1周)
1. 迁移实时状态查询API
2. 实现基础WebSocket功能
3. 设置Redis数据同步

### 阶段2：高级功能开发 (2周)
1. 开发Webhook接收功能
2. 实现文件上传下载
3. 优化缓存策略

### 阶段3：性能优化 (1周)
1. 性能测试和调优
2. 监控指标完善
3. 错误处理增强
