#!/usr/bin/env python3
"""
WebSocket 连接测试脚本
用于测试 AnsFlow 流水线执行详情页面的 WebSocket 功能
"""

import asyncio
import json
import websockets
from datetime import datetime

async def test_websocket_connection(execution_id: int = 1):
    """测试 WebSocket 连接和数据接收"""
    uri = f"ws://localhost:8001/ws/execution/{execution_id}"
    
    print(f"🔗 正在连接到 WebSocket: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket 连接成功！")
            
            # 发送 ping 消息
            ping_message = {
                "type": "ping",
                "timestamp": datetime.utcnow().isoformat()
            }
            await websocket.send(json.dumps(ping_message))
            print(f"📤 发送 ping: {ping_message}")
            
            # 监听消息
            message_count = 0
            max_messages = 20  # 监听20条消息后停止
            
            print("👂 开始监听消息...")
            print("-" * 60)
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    message_count += 1
                    
                    print(f"📥 消息 #{message_count} ({data.get('type', 'unknown')}):")
                    
                    if data.get('type') == 'connection':
                        print(f"   🎉 连接确认: {data.get('message')}")
                        print(f"   🔐 认证状态: {data.get('authenticated')}")
                        print(f"   🏷️  服务: {data.get('service')}")
                    
                    elif data.get('type') == 'execution_status':
                        exec_data = data.get('data', {})
                        print(f"   📊 执行状态: {exec_data.get('status')}")
                        print(f"   📝 流水线: {exec_data.get('pipeline_name')}")
                        print(f"   📈 步骤数: {exec_data.get('total_steps')}")
                        print(f"   ✅ 完成步骤: {exec_data.get('completed_steps')}")
                    
                    elif data.get('type') == 'execution_update':
                        print(f"   🔄 执行更新: {data.get('status')}")
                        print(f"   ⏱️  执行时间: {data.get('execution_time'):.2f}s")
                        print(f"   📊 步骤进度: {data.get('completed_steps')}/{data.get('total_steps')}")
                    
                    elif data.get('type') == 'step_progress':
                        print(f"   🎯 步骤进度: {data.get('step_name')}")
                        print(f"   📍 状态: {data.get('status')}")
                        if data.get('execution_time'):
                            print(f"   ⏲️  时间: {data.get('execution_time'):.2f}s")
                    
                    elif data.get('type') == 'log_entry':
                        print(f"   📝 日志: [{data.get('level', 'info').upper()}] {data.get('message')}")
                        if data.get('step_name'):
                            print(f"       🏷️  步骤: {data.get('step_name')}")
                    
                    elif data.get('type') == 'pong':
                        print(f"   🏓 收到 pong 响应")
                    
                    else:
                        print(f"   📦 其他消息: {json.dumps(data, indent=2, ensure_ascii=False)}")
                    
                    print(f"   🕐 时间戳: {data.get('timestamp', 'N/A')}")
                    print("-" * 60)
                    
                    if message_count >= max_messages:
                        print(f"📊 已接收 {max_messages} 条消息，测试完成")
                        break
                        
                except json.JSONDecodeError as e:
                    print(f"❌ JSON 解析错误: {e}")
                    print(f"   原始消息: {message}")
                except Exception as e:
                    print(f"❌ 处理消息时出错: {e}")
            
            print("\n✅ WebSocket 测试完成")
            
    except ConnectionRefusedError:
        print("❌ WebSocket 连接被拒绝，请确保 FastAPI 服务正在运行")
        print("   启动命令: cd /Users/creed/Workspace/OpenSource/ansflow/backend/fastapi_service && uv run python main.py")
    except websockets.exceptions.InvalidURI:
        print(f"❌ WebSocket URI 无效: {uri}")
    except OSError as e:
        if "Connection refused" in str(e):
            print("❌ WebSocket 连接被拒绝，请确保 FastAPI 服务正在运行")
            print("   启动命令: cd /Users/creed/Workspace/OpenSource/ansflow/backend/fastapi_service && uv run python main.py")
        else:
            print(f"❌ 网络连接错误: {e}")
    except Exception as e:
        print(f"❌ WebSocket 连接错误: {e}")

async def test_get_status_message(execution_id: int = 1):
    """测试发送获取状态消息"""
    uri = f"ws://localhost:8001/ws/execution/{execution_id}"
    
    print(f"\n🔍 测试获取状态消息...")
    
    try:
        async with websockets.connect(uri) as websocket:
            # 等待连接确认
            await asyncio.sleep(1)
            
            # 发送获取状态消息
            status_message = {
                "type": "get_status",
                "timestamp": datetime.utcnow().isoformat()
            }
            await websocket.send(json.dumps(status_message))
            print(f"📤 发送状态请求: {status_message}")
            
            # 等待响应
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📥 收到状态响应: {data.get('type')}")
            
            if data.get('type') == 'execution_status':
                exec_data = data.get('data', {})
                print(f"   📊 执行状态: {exec_data.get('status')}")
                print(f"   📝 流水线: {exec_data.get('pipeline_name')}")
                steps = exec_data.get('steps', [])
                print(f"   📈 步骤详情:")
                for step in steps:
                    print(f"     • {step.get('name')}: {step.get('status')}")
            
    except Exception as e:
        print(f"❌ 获取状态测试失败: {e}")

def main():
    """主函数"""
    print("🧪 AnsFlow WebSocket 功能测试")
    print("=" * 60)
    
    try:
        # 测试基本 WebSocket 连接
        asyncio.run(test_websocket_connection(execution_id=1))
        
        # 测试获取状态消息
        asyncio.run(test_get_status_message(execution_id=1))
        
        print("\n🎉 所有测试完成！")
        
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")

if __name__ == "__main__":
    main()
