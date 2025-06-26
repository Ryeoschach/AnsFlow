#!/usr/bin/env python3
"""
WebSocket测试脚本
用于测试AnsFlow实时监控WebSocket功能
"""

import asyncio
import websockets
import json
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketTester:
    def __init__(self, base_url="ws://localhost:8000"):
        self.base_url = base_url
        
    async def test_global_monitor(self):
        """测试全局监控WebSocket连接"""
        uri = f"{self.base_url}/ws/monitor/"
        logger.info(f"连接到全局监控: {uri}")
        
        try:
            async with websockets.connect(uri) as websocket:
                logger.info("✅ 全局监控WebSocket连接成功")
                
                # 发送测试消息
                test_message = {
                    "type": "test_message",
                    "data": {
                        "message": "测试全局监控连接",
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
                await websocket.send(json.dumps(test_message))
                logger.info("📤 发送测试消息到全局监控")
                
                # 等待响应
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    logger.info(f"📥 收到响应: {response}")
                except asyncio.TimeoutError:
                    logger.warning("⚠️ 5秒内未收到响应")
                    
        except Exception as e:
            logger.error(f"❌ 全局监控连接失败: {e}")
            return False
            
        return True
    
    async def test_execution_monitor(self, execution_id=1):
        """测试执行监控WebSocket连接"""
        uri = f"{self.base_url}/ws/executions/{execution_id}/"
        logger.info(f"连接到执行监控: {uri}")
        
        try:
            async with websockets.connect(uri) as websocket:
                logger.info(f"✅ 执行监控WebSocket连接成功 (execution_id: {execution_id})")
                
                # 发送测试消息
                test_message = {
                    "type": "test_message",
                    "data": {
                        "execution_id": execution_id,
                        "message": "测试执行监控连接",
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
                await websocket.send(json.dumps(test_message))
                logger.info("📤 发送测试消息到执行监控")
                
                # 测试控制命令
                control_message = {
                    "type": "control_command",
                    "command": "test",
                    "execution_id": execution_id
                }
                
                await websocket.send(json.dumps(control_message))
                logger.info("📤 发送控制命令测试")
                
                # 等待响应
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    logger.info(f"📥 收到响应: {response}")
                except asyncio.TimeoutError:
                    logger.warning("⚠️ 5秒内未收到响应")
                    
        except Exception as e:
            logger.error(f"❌ 执行监控连接失败: {e}")
            return False
            
        return True
    
    async def simulate_execution_flow(self, execution_id=999):
        """模拟完整的执行流程"""
        logger.info(f"🚀 开始模拟执行流程 (execution_id: {execution_id})")
        
        # 模拟从后端发送WebSocket消息
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        if not channel_layer:
            logger.error("❌ Channel layer未配置")
            return False
        
        group_name = f'execution_{execution_id}'
        
        # 模拟执行开始
        await self._send_to_group(channel_layer, group_name, {
            'type': 'execution_update',
            'data': {
                'type': 'execution_status',
                'execution_id': execution_id,
                'status': 'starting',
                'timestamp': datetime.now().isoformat(),
                'message': '流水线执行开始'
            }
        })
        
        await asyncio.sleep(1)
        
        # 模拟步骤执行
        steps = [
            {'name': '代码检出', 'status': 'running'},
            {'name': '构建应用', 'status': 'running'},
            {'name': '运行测试', 'status': 'running'},
            {'name': '部署应用', 'status': 'running'}
        ]
        
        for i, step in enumerate(steps):
            # 步骤开始
            await self._send_to_group(channel_layer, group_name, {
                'type': 'step_update',
                'data': {
                    'type': 'step_progress',
                    'execution_id': execution_id,
                    'step_id': i + 1,
                    'step_name': step['name'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                }
            })
            
            # 模拟日志
            await self._send_to_group(channel_layer, group_name, {
                'type': 'log_update',
                'data': {
                    'type': 'log_entry',
                    'execution_id': execution_id,
                    'timestamp': datetime.now().isoformat(),
                    'level': 'info',
                    'message': f'正在执行步骤: {step["name"]}',
                    'step_name': step['name']
                }
            })
            
            await asyncio.sleep(2)
            
            # 步骤完成
            await self._send_to_group(channel_layer, group_name, {
                'type': 'step_update',
                'data': {
                    'type': 'step_progress',
                    'execution_id': execution_id,
                    'step_id': i + 1,
                    'step_name': step['name'],
                    'status': 'success',
                    'timestamp': datetime.now().isoformat(),
                    'execution_time': 2.0
                }
            })
        
        # 模拟执行完成
        await self._send_to_group(channel_layer, group_name, {
            'type': 'execution_update',
            'data': {
                'type': 'execution_status',
                'execution_id': execution_id,
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'total_steps': len(steps),
                'successful_steps': len(steps),
                'failed_steps': 0,
                'execution_time': 8.0,
                'message': '流水线执行成功完成'
            }
        })
        
        logger.info("✅ 执行流程模拟完成")
        return True
    
    async def _send_to_group(self, channel_layer, group_name, message):
        """发送消息到WebSocket组"""
        try:
            await channel_layer.group_send(group_name, message)
            logger.info(f"📤 发送消息到组 {group_name}: {message['data']['type']}")
        except Exception as e:
            logger.error(f"❌ 发送消息失败: {e}")
    
    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("🔧 开始WebSocket功能测试")
        
        # 测试1: 全局监控连接
        logger.info("\n" + "="*50)
        logger.info("测试1: 全局监控WebSocket连接")
        logger.info("="*50)
        global_test = await self.test_global_monitor()
        
        # 测试2: 执行监控连接
        logger.info("\n" + "="*50)
        logger.info("测试2: 执行监控WebSocket连接")
        logger.info("="*50)
        execution_test = await self.test_execution_monitor()
        
        # 测试3: 模拟执行流程
        logger.info("\n" + "="*50)
        logger.info("测试3: 模拟完整执行流程")
        logger.info("="*50)
        simulation_test = await self.simulate_execution_flow()
        
        # 测试结果
        logger.info("\n" + "="*50)
        logger.info("测试结果汇总")
        logger.info("="*50)
        logger.info(f"全局监控连接: {'✅ 通过' if global_test else '❌ 失败'}")
        logger.info(f"执行监控连接: {'✅ 通过' if execution_test else '❌ 失败'}")
        logger.info(f"执行流程模拟: {'✅ 通过' if simulation_test else '❌ 失败'}")
        
        all_passed = global_test and execution_test and simulation_test
        logger.info(f"\n总体结果: {'🎉 所有测试通过' if all_passed else '⚠️ 部分测试失败'}")
        
        return all_passed

async def main():
    """主函数"""
    print("🚀 AnsFlow WebSocket实时监控测试")
    print("="*60)
    
    tester = WebSocketTester()
    
    try:
        success = await tester.run_all_tests()
        if success:
            print("\n🎉 WebSocket实时监控功能测试完成！")
            print("✅ 您可以在前端页面查看实时更新效果")
            print("📱 前端地址: http://localhost:3000")
            print("🔗 测试执行详情页面: http://localhost:3000/executions/999")
        else:
            print("\n⚠️ 部分测试失败，请检查配置")
    except KeyboardInterrupt:
        print("\n👋 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    # 设置Django环境
    import os
    import django
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
    django.setup()
    
    # 运行测试
    asyncio.run(main())
