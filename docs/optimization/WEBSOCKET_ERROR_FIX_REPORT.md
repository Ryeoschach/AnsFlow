# FastAPI WebSocket 错误修复报告

## 修复时间
2024年12月21日

## 问题描述

在流水线执行详情刷新时，FastAPI WebSocket 出现以下错误：

1. **"Cannot call 'send' once a close message has been sent."**
   - 在 WebSocket 连接已关闭后仍尝试发送消息
   - 连接状态管理不当

2. **"WebSocket is not connected. Need to call 'accept' first."**
   - 在未正确建立连接的情况下尝试发送消息
   - 连接初始化问题

3. **连接生命周期管理问题**
   - 断开的连接未及时清理
   - 重复操作已关闭的连接

## 根本原因分析

### 1. 连接状态检查缺失
- `send_personal_message` 方法未检查 WebSocket 连接状态
- 直接调用 `websocket.send_text()` 而不验证连接有效性

### 2. 异常处理不完整
- 未捕获特定的 WebSocket 断开异常
- 缺少对 RuntimeError 中连接相关错误的识别

### 3. 连接清理机制不及时
- 断开的连接未从所有连接集合中移除
- 空的房间和用户连接集合未被清理

### 4. 并发修改问题
- 在迭代连接集合时同时修改集合
- 可能导致运行时错误和不一致状态

## 修复方案

### 1. 改进连接状态检查

```python
async def send_personal_message(self, message: str, websocket: WebSocket):
    """Send a message to a specific WebSocket connection"""
    try:
        # Check if WebSocket is still connected before sending
        if hasattr(websocket, 'client_state') and hasattr(websocket.client_state, 'name'):
            if websocket.client_state.name != 'CONNECTED':
                logger.warning("Attempted to send message to disconnected WebSocket", 
                             state=websocket.client_state.name)
                return False
        
        await websocket.send_text(message)
        return True
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected during message send")
        self._cleanup_disconnected_websocket(websocket)
        return False
    except RuntimeError as e:
        if "WebSocket is disconnected" in str(e) or "close message has been sent" in str(e):
            logger.info("WebSocket connection closed during message send", error=str(e))
            self._cleanup_disconnected_websocket(websocket)
            return False
        else:
            logger.error("Runtime error sending personal message", error=str(e))
            return False
    except Exception as e:
        logger.error("Failed to send personal message", error=str(e), error_type=type(e).__name__)
        self._cleanup_disconnected_websocket(websocket)
        return False
```

### 2. 添加连接清理方法

```python
def _cleanup_disconnected_websocket(self, websocket: WebSocket):
    """Clean up a disconnected WebSocket from all connection sets"""
    # Remove from room connections
    for room in list(self.active_connections.keys()):
        if websocket in self.active_connections[room]:
            self.active_connections[room].discard(websocket)
            if not self.active_connections[room]:
                del self.active_connections[room]
    
    # Remove from user connections
    for user_id in list(self.user_connections.keys()):
        if websocket in self.user_connections[user_id]:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
```

### 3. 修复并发修改问题

```python
async def send_to_room(self, message: str, room: str):
    """Send a message to all connections in a room"""
    if room in self.active_connections:
        disconnected = set()
        for connection in self.active_connections[room].copy():  # Use copy to avoid modification during iteration
            success = await self.send_personal_message(message, connection)
            if not success:
                disconnected.add(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.active_connections[room].discard(connection)
            
        # Clean up empty room
        if not self.active_connections[room]:
            del self.active_connections[room]
```

### 4. 统一错误处理策略

- 所有 WebSocket 发送方法现在返回 `True`/`False` 表示成功/失败
- 统一的异常捕获和处理逻辑
- 自动清理断开的连接

## 修复的文件

### 1. `/backend/fastapi_service/ansflow_api/websockets/routes.py`
- 改进 `ConnectionManager.send_personal_message` 方法
- 添加 `_cleanup_disconnected_websocket` 方法
- 优化 `send_to_room`、`send_to_user`、`broadcast` 方法
- 使用 `.copy()` 避免迭代时修改集合

### 2. `/backend/fastapi_service/ansflow_api/websockets/manager.py`
- 同步修复 `ConnectionManager.send_personal_message` 方法
- 优化 `_broadcast_to_connections` 方法
- 统一错误处理逻辑

## 改进效果

### 1. 错误消除
- 消除 "Cannot call 'send' once a close message has been sent" 错误
- 解决 "WebSocket is not connected" 问题

### 2. 稳定性提升
- 自动检测和清理断开的连接
- 防止重复操作已关闭的连接
- 避免并发修改导致的运行时错误

### 3. 日志改进
- 更详细的错误日志记录
- 区分不同类型的连接问题
- 便于问题排查和监控

### 4. 资源管理
- 及时清理空的房间和用户连接集合
- 减少内存泄漏风险

## 测试验证

### 1. 连接状态测试
```python
# 测试连接状态检查
websocket = MockWebSocket(state="DISCONNECTED")
result = await manager.send_personal_message("test", websocket)
assert result == False  # 应该返回 False
```

### 2. 异常处理测试
```python
# 测试 RuntimeError 处理
websocket = MockWebSocket(exception="close message has been sent")
result = await manager.send_personal_message("test", websocket)
assert result == False  # 应该正确处理异常
```

### 3. 清理功能测试
```python
# 测试连接清理
manager.active_connections["room1"] = {websocket}
manager._cleanup_disconnected_websocket(websocket)
assert "room1" not in manager.active_connections  # 空房间应被删除
```

## 监控建议

### 1. 添加 WebSocket 健康监控
- 监控活跃连接数量
- 跟踪连接断开率
- 记录发送失败统计

### 2. 性能指标
- WebSocket 消息发送延迟
- 连接清理效率
- 内存使用情况

### 3. 告警规则
- 连接断开率异常告警
- 发送失败率过高告警
- 连接数量异常波动告警

## 后续优化建议

### 1. 连接池管理
- 实现连接池限制
- 添加连接生命周期管理
- 定期清理僵尸连接

### 2. 消息队列
- 对于重要消息，考虑添加重试机制
- 实现消息持久化（可选）
- 支持离线消息推送

### 3. 负载均衡
- 支持多实例 WebSocket 负载均衡
- 使用 Redis 作为消息广播中间件
- 实现跨实例连接管理

## 总结

本次修复彻底解决了 FastAPI WebSocket 在流水线执行详情刷新时的连接错误问题。通过改进连接状态检查、异常处理、连接清理和并发控制，显著提升了 WebSocket 连接的稳定性和可靠性。

修复后的 WebSocket 服务能够：
- 正确处理连接断开情况
- 及时清理无效连接
- 避免向已关闭的连接发送消息
- 提供更好的错误日志和监控支持

这些改进确保了 AnsFlow 实时通信功能的稳定运行，为用户提供更好的流水线监控体验。
