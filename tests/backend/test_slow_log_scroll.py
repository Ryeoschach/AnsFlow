#!/usr/bin/env python3
"""
AnsFlow 实时日志滚动测试脚本
模拟缓慢的日志推送，便于观察前端自动滚动效果
"""

import asyncio
import websockets
import json
from datetime import datetime
import time

async def slow_log_test():
    """慢速日志推送测试"""
    uri = "ws://localhost:8001/ws/execution/123"
    
    try:
        print("🧪 开始慢速日志推送测试...")
        print(f"🔗 连接到: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket 连接成功！")
            
            # 发送订阅消息
            subscribe_msg = {
                "type": "subscribe",
                "events": ["execution_status", "step_progress", "log_entry"]
            }
            await websocket.send(json.dumps(subscribe_msg))
            print("📡 已发送订阅消息")
            
            print("\n🎬 开始缓慢推送日志，每3秒一条...")
            print("📖 请在浏览器中观察日志是否自动滚动到最新")
            print("🔍 测试要点:")
            print("   1. 日志应该逐条出现，不是一次性显示全部")
            print("   2. 每次新日志出现时，页面应该自动滚动到底部")
            print("   3. 用户向上滚动时，自动滚动应该暂停")
            print("   4. 用户滚动到底部时，自动滚动应该恢复")
            print("-" * 60)
            
            # 接收连接确认消息
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                print(f"📨 连接确认: {json.loads(response).get('message', 'Unknown')}")
            except asyncio.TimeoutError:
                print("⚠️ 未收到连接确认消息")
            
            # 模拟缓慢的日志生成
            log_messages = [
                "🚀 开始执行流水线任务...",
                "📋 正在加载配置文件...",
                "🔍 开始环境检查...",
                "✅ Python 环境检查通过",
                "✅ Docker 环境检查通过", 
                "✅ 网络连接检查通过",
                "📦 开始拉取代码...",
                "🔗 连接到 Git 仓库...",
                "📥 正在下载最新代码...",
                "✅ 代码拉取完成",
                "🏗️ 开始构建应用...",
                "📦 安装依赖包...",
                "🔧 编译前端资源...",
                "🛠️ 构建 Docker 镜像...",
                "✅ 应用构建完成",
                "🧪 开始运行测试...",
                "🔬 执行单元测试...",
                "📊 生成测试报告...",
                "✅ 所有测试通过",
                "🚀 开始部署应用...",
                "☁️ 连接到部署环境...",
                "📤 上传应用镜像...",
                "🔄 重启应用服务...",
                "🔍 健康检查中...",
                "✅ 部署完成！应用运行正常"
            ]
            
            for i, message in enumerate(log_messages, 1):
                # 发送日志条目
                log_entry = {
                    "type": "log_entry",
                    "data": {
                        "id": f"log_{int(time.time() * 1000)}_{i}",
                        "timestamp": datetime.now().isoformat(),
                        "level": "info",
                        "message": message,
                        "stepName": "测试步骤",
                        "source": "test"
                    }
                }
                
                await websocket.send(json.dumps(log_entry))
                print(f"📝 [{i:2d}/25] 已发送: {message}")
                
                # 每3秒发送一条日志
                await asyncio.sleep(3)
            
            print("\n🎉 测试完成！")
            print("🔍 请检查前端页面:")
            print("   ✅ 日志是否逐条显示")
            print("   ✅ 是否自动滚动到最新日志")
            print("   ✅ 用户滚动时是否能暂停自动滚动")
            
            # 保持连接30秒以便观察
            print("\n⏳ 保持连接30秒以便测试...")
            await asyncio.sleep(30)
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    print("🧪 AnsFlow 实时日志自动滚动测试")
    print("=" * 60)
    asyncio.run(slow_log_test())
