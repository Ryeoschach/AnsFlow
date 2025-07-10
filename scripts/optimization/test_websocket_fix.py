#!/usr/bin/env python3
"""
WebSocket 错误修复验证脚本
测试 FastAPI WebSocket 连接状态检查和错误处理
"""

import asyncio
import json
import websockets
import time
from datetime import datetime

class WebSocketTester:
    def __init__(self):
        self.base_url = "ws://localhost:8001/ws"
        self.results = []
    
    async def test_connection_lifecycle(self):
        """测试连接生命周期"""
        print("测试 WebSocket 连接生命周期...")
        
        try:
            # 测试正常连接
            uri = f"{self.base_url}/monitor"
            async with websockets.connect(uri) as websocket:
                print("✓ WebSocket 连接成功")
                
                # 发送 ping 消息
                ping_message = {
                    "type": "ping",
                    "timestamp": datetime.utcnow().isoformat()
                }
                await websocket.send(json.dumps(ping_message))
                print("✓ Ping 消息发送成功")
                
                # 等待 pong 响应
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)
                
                if response_data.get("type") == "pong":
                    print("✓ 收到 Pong 响应")
                    self.results.append(("connection_lifecycle", True, "正常连接和通信"))
                else:
                    print(f"✗ 未收到预期的 Pong 响应: {response_data}")
                    self.results.append(("connection_lifecycle", False, f"响应类型错误: {response_data.get('type')}"))
                
        except Exception as e:
            print(f"✗ 连接测试失败: {e}")
            self.results.append(("connection_lifecycle", False, str(e)))
    
    async def test_execution_websocket(self):
        """测试执行监控 WebSocket"""
        print("\n测试执行监控 WebSocket...")
        
        try:
            # 使用一个假的 execution_id
            execution_id = "test_execution_123"
            uri = f"{self.base_url}/execution/{execution_id}"
            
            async with websockets.connect(uri) as websocket:
                print("✓ 执行监控 WebSocket 连接成功")
                
                # 等待初始连接消息
                initial_message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                initial_data = json.loads(initial_message)
                
                if initial_data.get("type") == "connection":
                    print("✓ 收到初始连接消息")
                    
                    # 发送订阅消息
                    subscribe_message = {
                        "type": "subscribe",
                        "events": ["execution_update", "step_update", "log_update"]
                    }
                    await websocket.send(json.dumps(subscribe_message))
                    print("✓ 订阅消息发送成功")
                    
                    # 等待订阅确认
                    sub_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    sub_data = json.loads(sub_response)
                    
                    if sub_data.get("type") == "subscribed":
                        print("✓ 收到订阅确认")
                        self.results.append(("execution_websocket", True, "执行监控 WebSocket 正常"))
                    else:
                        print(f"✗ 订阅确认失败: {sub_data}")
                        self.results.append(("execution_websocket", False, f"订阅确认失败: {sub_data.get('type')}"))
                else:
                    print(f"✗ 初始消息类型错误: {initial_data}")
                    self.results.append(("execution_websocket", False, f"初始消息类型错误: {initial_data.get('type')}"))
                    
        except Exception as e:
            print(f"✗ 执行监控 WebSocket 测试失败: {e}")
            self.results.append(("execution_websocket", False, str(e)))
    
    async def test_pipeline_websocket(self):
        """测试流水线监控 WebSocket"""
        print("\n测试流水线监控 WebSocket...")
        
        try:
            # 使用一个假的 pipeline_id
            pipeline_id = "test_pipeline_456"
            uri = f"{self.base_url}/pipeline/{pipeline_id}"
            
            async with websockets.connect(uri) as websocket:
                print("✓ 流水线监控 WebSocket 连接成功")
                
                # 等待初始连接消息
                initial_message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                initial_data = json.loads(initial_message)
                
                if initial_data.get("type") == "connection":
                    print("✓ 收到流水线连接消息")
                    self.results.append(("pipeline_websocket", True, "流水线监控 WebSocket 正常"))
                else:
                    print(f"✗ 流水线连接消息类型错误: {initial_data}")
                    self.results.append(("pipeline_websocket", False, f"连接消息类型错误: {initial_data.get('type')}"))
                    
        except Exception as e:
            print(f"✗ 流水线监控 WebSocket 测试失败: {e}")
            self.results.append(("pipeline_websocket", False, str(e)))
    
    async def test_concurrent_connections(self):
        """测试并发连接"""
        print("\n测试并发连接...")
        
        try:
            # 创建多个并发连接
            connections = []
            tasks = []
            
            for i in range(5):
                uri = f"{self.base_url}/monitor"
                task = asyncio.create_task(self.create_connection(uri, f"client_{i}"))
                tasks.append(task)
            
            # 等待所有连接建立
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            success_count = sum(1 for r in results if r is True)
            print(f"✓ 成功建立 {success_count}/5 个并发连接")
            
            if success_count >= 3:  # 至少成功3个连接
                self.results.append(("concurrent_connections", True, f"成功建立 {success_count}/5 个并发连接"))
            else:
                self.results.append(("concurrent_connections", False, f"仅成功建立 {success_count}/5 个并发连接"))
                
        except Exception as e:
            print(f"✗ 并发连接测试失败: {e}")
            self.results.append(("concurrent_connections", False, str(e)))
    
    async def create_connection(self, uri, client_id):
        """创建单个 WebSocket 连接"""
        try:
            async with websockets.connect(uri) as websocket:
                # 发送标识消息
                identify_message = {
                    "type": "identify",
                    "client_id": client_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await websocket.send(json.dumps(identify_message))
                
                # 等待一小段时间
                await asyncio.sleep(1)
                return True
        except Exception as e:
            print(f"✗ 客户端 {client_id} 连接失败: {e}")
            return False
    
    def print_results(self):
        """打印测试结果"""
        print("\n" + "="*60)
        print("WebSocket 错误修复验证结果")
        print("="*60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for _, success, _ in self.results if success)
        
        for test_name, success, details in self.results:
            status = "✓ PASS" if success else "✗ FAIL"
            print(f"{status} {test_name}: {details}")
        
        print("-"*60)
        print(f"总计: {passed_tests}/{total_tests} 测试通过")
        
        if passed_tests == total_tests:
            print("🎉 所有测试通过！WebSocket 修复验证成功！")
        else:
            print("⚠️  部分测试失败，请检查 WebSocket 服务状态")
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("开始 WebSocket 错误修复验证...")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"目标服务: {self.base_url}")
        print("-"*60)
        
        # 运行各项测试
        await self.test_connection_lifecycle()
        await self.test_execution_websocket()
        await self.test_pipeline_websocket()
        await self.test_concurrent_connections()
        
        # 打印结果
        self.print_results()

async def main():
    """主函数"""
    tester = WebSocketTester()
    
    try:
        await tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试执行出错: {e}")

if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())
