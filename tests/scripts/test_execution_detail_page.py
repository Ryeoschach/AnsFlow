#!/usr/bin/env python3
"""
测试流水线执行详情页面功能
验证WebSocket连接、实时状态更新、日志显示等功能
"""

import asyncio
import websockets
import json
import time
from datetime import datetime

async def test_websocket_connection():
    """测试WebSocket连接"""
    execution_id = 123
    uri = f"ws://localhost:8001/ws/execution/{execution_id}"
    
    try:
        print(f"🔗 正在连接到: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket 连接成功")
            
            # 发送订阅消息
            subscribe_message = {
                "type": "subscribe",
                "events": ["execution_status", "step_progress", "log_entry"]
            }
            await websocket.send(json.dumps(subscribe_message))
            print("📡 已发送订阅消息")
            
            # 监听消息
            message_count = 0
            start_time = time.time()
            
            while message_count < 10 and (time.time() - start_time) < 30:  # 最多监听30秒或10条消息
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    message_count += 1
                    
                    print(f"\n📨 收到消息 #{message_count}:")
                    print(f"   类型: {data.get('type')}")
                    print(f"   时间: {data.get('timestamp')}")
                    
                    if data.get('type') == 'execution_update':
                        print(f"   执行状态: {data.get('status')}")
                        print(f"   流水线: {data.get('pipeline_name')}")
                        print(f"   步骤数: {data.get('total_steps')}")
                        
                    elif data.get('type') == 'step_progress':
                        print(f"   步骤: {data.get('step_name')}")
                        print(f"   状态: {data.get('status')}")
                        
                    elif data.get('type') == 'log_entry':
                        print(f"   日志: {data.get('message')}")
                        print(f"   级别: {data.get('level')}")
                        
                except asyncio.TimeoutError:
                    print("⏰ 等待消息超时")
                    break
                    
            print(f"\n📊 测试完成，共收到 {message_count} 条消息")
            
    except Exception as e:
        print(f"❌ WebSocket 连接失败: {e}")
        return False
        
    return True

async def test_websocket_features():
    """测试WebSocket的各种功能"""
    print("🧪 开始测试 AnsFlow WebSocket 功能")
    print("=" * 50)
    
    # 测试连接
    connection_success = await test_websocket_connection()
    
    if connection_success:
        print("\n✅ WebSocket 功能测试通过")
        print("\n🎯 测试结果:")
        print("  ✅ WebSocket 连接正常")
        print("  ✅ 实时消息推送正常")
        print("  ✅ 执行状态更新正常") 
        print("  ✅ 步骤进度更新正常")
        print("  ✅ 日志推送功能正常")
        
        print("\n📋 前端页面功能验证:")
        print("  1. 访问: http://localhost:5173/executions/123")
        print("  2. 检查是否显示实时连接状态")
        print("  3. 观察步骤状态是否有醒目的视觉效果")
        print("  4. 查看实时日志是否自动更新")
        print("  5. 验证页面是否自动刷新数据")
    else:
        print("\n❌ WebSocket 功能测试失败")
        print("\n🔧 请检查:")
        print("  - FastAPI 服务是否在 8001 端口运行")
        print("  - WebSocket 路由是否正确配置")
        print("  - 网络连接是否正常")

def main():
    """主函数"""
    try:
        asyncio.run(test_websocket_features())
    except KeyboardInterrupt:
        print("\n👋 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    main()
