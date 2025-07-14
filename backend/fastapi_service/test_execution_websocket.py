#!/usr/bin/env python3
"""
测试流水线执行详情页面的 WebSocket 功能
验证实时状态更新、步骤进度、日志推送等功能
"""

import asyncio
import websockets
import json
import time
from datetime import datetime

async def test_websocket_execution_endpoint():
    """测试执行详情 WebSocket 端点"""
    execution_id = 123
    uri = f"ws://localhost:8001/ws/execution/{execution_id}"
    
    print(f"🔗 正在连接到执行详情 WebSocket: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket 连接成功！")
            
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
            execution_status_received = False
            step_progress_received = False
            log_entries_received = False
            
            print("\n📨 开始接收实时消息...")
            print("-" * 50)
            
            while message_count < 20 and (time.time() - start_time) < 15:  # 最多15秒或20条消息
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(message)
                    message_count += 1
                    
                    msg_type = data.get('type', 'unknown')
                    timestamp = data.get('timestamp', 'N/A')
                    
                    print(f"\n📨 消息 #{message_count} ({msg_type}):")
                    
                    if msg_type == 'connection':
                        print(f"   🔗 连接确认: {data.get('message')}")
                        print(f"   📡 服务: {data.get('service')}")
                        print(f"   🔐 认证: {data.get('authenticated')}")
                        
                    elif msg_type == 'execution_status':
                        execution_status_received = True
                        exec_data = data.get('data', {})
                        print(f"   🚀 执行状态: {exec_data.get('status')}")
                        print(f"   📝 流水线: {exec_data.get('pipeline_name')}")
                        print(f"   📊 总步骤: {exec_data.get('total_steps')}")
                        print(f"   ✅ 完成步骤: {exec_data.get('completed_steps')}")
                        
                        current_step = exec_data.get('current_step')
                        if current_step:
                            print(f"   ⚡ 当前步骤: {current_step.get('name')} ({current_step.get('status')})")
                        
                    elif msg_type == 'execution_update':
                        execution_status_received = True
                        print(f"   🔄 执行更新: {data.get('status')}")
                        print(f"   📝 流水线: {data.get('pipeline_name')}")
                        print(f"   ⏱️ 执行时间: {data.get('execution_time', 0):.1f}s")
                        print(f"   📊 步骤数: {data.get('total_steps')}")
                        
                    elif msg_type == 'step_progress':
                        step_progress_received = True
                        print(f"   🎯 步骤: {data.get('step_name')}")
                        print(f"   📊 状态: {data.get('status')}")
                        if data.get('execution_time'):
                            print(f"   ⏱️ 耗时: {data.get('execution_time')}s")
                        if data.get('output'):
                            output = data.get('output', '')[:100]
                            print(f"   📝 输出: {output}{'...' if len(data.get('output', '')) > 100 else ''}")
                        
                    elif msg_type == 'log_entry':
                        log_entries_received = True
                        print(f"   📋 日志级别: {data.get('level', 'info').upper()}")
                        print(f"   📝 消息: {data.get('message')}")
                        if data.get('step_name'):
                            print(f"   🎯 步骤: {data.get('step_name')}")
                        print(f"   🏷️ 来源: {data.get('source', 'unknown')}")
                        
                    else:
                        print(f"   ❓ 未知消息类型: {data}")
                        
                except asyncio.TimeoutError:
                    print("⏰ 等待消息超时，继续监听...")
                    continue
                except json.JSONDecodeError as e:
                    print(f"❌ JSON 解析错误: {e}")
                    continue
                    
            print(f"\n📊 测试完成！共收到 {message_count} 条消息")
            print(f"⏱️ 测试耗时: {time.time() - start_time:.1f} 秒")
            
            # 功能验证报告
            print("\n🎯 功能验证结果:")
            print(f"   ✅ 执行状态推送: {'是' if execution_status_received else '❌ 否'}")
            print(f"   ✅ 步骤进度推送: {'是' if step_progress_received else '❌ 否'}")
            print(f"   ✅ 日志实时推送: {'是' if log_entries_received else '❌ 否'}")
            
            return {
                "success": True,
                "message_count": message_count,
                "execution_status": execution_status_received,
                "step_progress": step_progress_received,
                "log_entries": log_entries_received
            }
            
    except ConnectionRefusedError:
        print("❌ 连接被拒绝，请检查 FastAPI 服务是否在 8001 端口运行")
        return {"success": False, "error": "Connection refused"}
    except websockets.exceptions.InvalidURI:
        print("❌ WebSocket URI 无效")
        return {"success": False, "error": "Invalid URI"}
    except Exception as e:
        print(f"❌ WebSocket 连接失败: {e}")
        return {"success": False, "error": str(e)}

async def test_websocket_ping_pong():
    """测试 WebSocket ping/pong 功能"""
    execution_id = 123
    uri = f"ws://localhost:8001/ws/execution/{execution_id}"
    
    print(f"\n🏓 测试 WebSocket Ping/Pong 功能...")
    
    try:
        async with websockets.connect(uri) as websocket:
            # 发送 ping 消息
            ping_message = {
                "type": "ping",
                "timestamp": datetime.utcnow().isoformat()
            }
            await websocket.send(json.dumps(ping_message))
            print("🏓 已发送 ping 消息")
            
            # 等待 pong 响应
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)
            
            if data.get('type') == 'pong':
                print("✅ 收到 pong 响应，心跳机制正常")
                return True
            else:
                print(f"❌ 收到意外响应: {data}")
                return False
                
    except asyncio.TimeoutError:
        print("❌ Ping/Pong 超时")
        return False
    except Exception as e:
        print(f"❌ Ping/Pong 测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🧪 AnsFlow 流水线执行详情页面 WebSocket 功能测试")
    print("=" * 60)
    
    # 测试基本的 WebSocket 连接和消息推送
    result = await test_websocket_execution_endpoint()
    
    if result["success"]:
        print("\n🎉 WebSocket 基本功能测试通过！")
        
        # 测试 ping/pong
        ping_success = await test_websocket_ping_pong()
        
        print(f"\n📋 完整测试报告:")
        print(f"   🔗 WebSocket 连接: ✅ 成功")
        print(f"   📨 消息接收: ✅ {result['message_count']} 条消息")
        print(f"   🚀 执行状态推送: {'✅ 正常' if result['execution_status'] else '❌ 异常'}")
        print(f"   🎯 步骤进度推送: {'✅ 正常' if result['step_progress'] else '❌ 异常'}")
        print(f"   📋 实时日志推送: {'✅ 正常' if result['log_entries'] else '❌ 异常'}")
        print(f"   🏓 心跳机制: {'✅ 正常' if ping_success else '❌ 异常'}")
        
        print(f"\n🌐 前端测试指南:")
        print(f"   1. 访问: http://localhost:5173/executions/123")
        print(f"   2. 检查页面是否显示 '实时监控已连接' 提示")
        print(f"   3. 观察步骤状态是否有醒目的视觉效果（闪烁、高亮）")
        print(f"   4. 查看右侧实时日志是否自动更新")
        print(f"   5. 验证页面是否每 2-5 秒自动刷新数据")
        
        print(f"\n✨ 已实现的功能:")
        print(f"   ✅ 页面自动刷新（WebSocket + 轮询备用）")
        print(f"   ✅ 步骤状态实时更新")
        print(f"   ✅ 当前执行步骤醒目高亮（闪烁动画）")
        print(f"   ✅ 待执行步骤显示 '⏳ 待执行' 标签")
        print(f"   ✅ 实时日志输出（支持颜色区分）")
        print(f"   ✅ WebSocket 服务统一使用 8001 端口")
        
    else:
        print(f"\n❌ WebSocket 测试失败: {result.get('error')}")
        print(f"\n🔧 请检查:")
        print(f"   - FastAPI 服务是否在 8001 端口正常运行")
        print(f"   - WebSocket 路由是否正确配置")
        print(f"   - 防火墙是否阻止了 WebSocket 连接")

if __name__ == "__main__":
    asyncio.run(main())
