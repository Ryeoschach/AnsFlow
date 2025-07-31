#!/usr/bin/env python3
"""
Docker Push步骤添加问题诊断脚本
诊断添加Docker Push步骤时页面跳转和空白的问题
"""

import requests
import json
import time
import logging
from typing import Dict, Any, Optional

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DockerPushStepIssueDebugger:
    """Docker Push步骤问题调试器"""
    
    def __init__(self):
        self.base_url = 'http://127.0.0.1:8000/api/v1'
        self.frontend_url = 'http://127.0.0.1:5173'
        self.token = None
        
    def get_auth_token(self) -> Optional[str]:
        """获取认证token"""
        try:
            # 尝试登录获取token
            response = requests.post(f'{self.base_url}/auth/login/', {
                'username': 'admin',
                'password': 'admin'
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access')
                logger.info(f"✅ 获取认证token成功: {self.token[:20]}...")
                return self.token
            else:
                logger.error(f"❌ 登录失败: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 获取token失败: {e}")
            return None
    
    def get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        return headers
    
    def test_pipeline_creation(self) -> Optional[int]:
        """测试流水线创建"""
        logger.info("🧪 测试流水线创建")
        
        try:
            # 创建测试流水线
            pipeline_data = {
                'name': 'Docker Push Test Pipeline',
                'description': '测试Docker Push步骤添加的流水线',
                'execution_mode': 'local',
                'is_active': True
            }
            
            response = requests.post(
                f'{self.base_url}/pipelines/',
                json=pipeline_data,
                headers=self.get_headers()
            )
            
            if response.status_code == 201:
                pipeline = response.json()
                pipeline_id = pipeline['id']
                logger.info(f"✅ 流水线创建成功，ID: {pipeline_id}")
                return pipeline_id
            else:
                logger.error(f"❌ 流水线创建失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 流水线创建异常: {e}")
            return None
    
    def test_docker_push_step_creation(self, pipeline_id: int) -> bool:
        """测试Docker Push步骤创建"""
        logger.info("🧪 测试Docker Push步骤创建")
        
        try:
            # 获取Docker注册表列表
            response = requests.get(
                f'{self.base_url}/docker/registries/',
                headers=self.get_headers()
            )
            
            if response.status_code != 200:
                logger.error(f"❌ 获取Docker注册表失败: {response.status_code}")
                return False
                
            registries = response.json().get('results', [])
            if not registries:
                logger.warning("⚠️ 没有可用的Docker注册表")
                registry_id = None
            else:
                registry_id = registries[0]['id']
                logger.info(f"✅ 找到Docker注册表，ID: {registry_id}")
            
            # 创建Docker Push步骤
            step_data = {
                'name': 'Test Docker Push Step',
                'step_type': 'docker_push',
                'description': '测试Docker Push步骤',
                'pipeline': pipeline_id,
                'order': 1,
                'docker_image': 'nginx',
                'docker_tag': 'latest',
                'docker_registry': registry_id,
                'docker_config': {
                    'all_tags': False,
                    'platform': 'linux/amd64'
                },
                'timeout_seconds': 1800
            }
            
            response = requests.post(
                f'{self.base_url}/pipelines/{pipeline_id}/steps/',
                json=step_data,
                headers=self.get_headers()
            )
            
            logger.info(f"📡 步骤创建响应状态码: {response.status_code}")
            logger.info(f"📡 步骤创建响应内容: {response.text}")
            
            if response.status_code == 201:
                step = response.json()
                logger.info(f"✅ Docker Push步骤创建成功，ID: {step['id']}")
                return True
            else:
                logger.error(f"❌ Docker Push步骤创建失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Docker Push步骤创建异常: {e}")
            return False
    
    def test_frontend_routes(self) -> bool:
        """测试前端路由是否正常"""
        logger.info("🧪 测试前端路由")
        
        try:
            # 测试pipelines页面
            response = requests.get(f'{self.frontend_url}/pipelines')
            logger.info(f"📡 前端pipelines页面响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                content = response.text
                # 检查是否是HTML页面而不是空白页面
                if '<html' in content and 'pipelines' in content.lower():
                    logger.info("✅ 前端pipelines页面正常")
                    return True
                else:
                    logger.warning("⚠️ 前端pipelines页面返回了内容但可能不是预期的HTML")
                    return False
            else:
                logger.error(f"❌ 前端pipelines页面访问失败: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 前端路由测试异常: {e}")
            return False
    
    def check_server_status(self) -> Dict[str, bool]:
        """检查服务器状态"""
        logger.info("🧪 检查服务器状态")
        
        status = {
            'backend': False,
            'frontend': False
        }
        
        try:
            # 检查后端
            response = requests.get(f'{self.base_url}/health/', timeout=5)
            if response.status_code == 200:
                status['backend'] = True
                logger.info("✅ 后端服务正常")
            else:
                logger.error(f"❌ 后端服务异常: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ 后端服务连接失败: {e}")
        
        try:
            # 检查前端
            response = requests.get(self.frontend_url, timeout=5)
            if response.status_code == 200:
                status['frontend'] = True
                logger.info("✅ 前端服务正常")
            else:
                logger.error(f"❌ 前端服务异常: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ 前端服务连接失败: {e}")
        
        return status
    
    def debug_issue(self) -> Dict[str, Any]:
        """调试问题"""
        logger.info("🔍 开始Docker Push步骤添加问题调试")
        logger.info("=" * 60)
        
        results = {
            'server_status': {},
            'auth_success': False,
            'pipeline_creation': False,
            'step_creation': False,
            'frontend_routes': False,
            'recommendations': []
        }
        
        # 1. 检查服务器状态
        results['server_status'] = self.check_server_status()
        
        # 2. 获取认证token
        if self.get_auth_token():
            results['auth_success'] = True
        else:
            results['recommendations'].append("检查后端认证服务是否正常")
            return results
        
        # 3. 测试流水线创建
        pipeline_id = self.test_pipeline_creation()
        if pipeline_id:
            results['pipeline_creation'] = True
            
            # 4. 测试Docker Push步骤创建
            if self.test_docker_push_step_creation(pipeline_id):
                results['step_creation'] = True
            else:
                results['recommendations'].append("检查Docker Push步骤创建API")
        else:
            results['recommendations'].append("检查流水线创建API")
        
        # 5. 测试前端路由
        if self.test_frontend_routes():
            results['frontend_routes'] = True
        else:
            results['recommendations'].append("检查前端路由配置")
        
        return results
    
    def generate_report(self, results: Dict[str, Any]):
        """生成调试报告"""
        logger.info("\n" + "=" * 60)
        logger.info("📋 Docker Push步骤添加问题调试报告")
        logger.info("=" * 60)
        
        # 服务器状态
        logger.info("🖥️ 服务器状态:")
        logger.info(f"   后端服务: {'✅ 正常' if results['server_status'].get('backend') else '❌ 异常'}")
        logger.info(f"   前端服务: {'✅ 正常' if results['server_status'].get('frontend') else '❌ 异常'}")
        
        # 功能测试
        logger.info("\n🧪 功能测试:")
        logger.info(f"   用户认证: {'✅ 成功' if results['auth_success'] else '❌ 失败'}")
        logger.info(f"   流水线创建: {'✅ 成功' if results['pipeline_creation'] else '❌ 失败'}")
        logger.info(f"   Docker Push步骤创建: {'✅ 成功' if results['step_creation'] else '❌ 失败'}")
        logger.info(f"   前端路由: {'✅ 正常' if results['frontend_routes'] else '❌ 异常'}")
        
        # 问题分析
        logger.info("\n🔍 问题分析:")
        if not results['frontend_routes']:
            logger.warning("   ⚠️ 前端页面跳转到127.0.0.1:5173/pipelines且空白可能原因:")
            logger.warning("      1. 前端路由配置问题")
            logger.warning("      2. React组件渲染异常")
            logger.warning("      3. JavaScript错误导致页面空白")
            logger.warning("      4. 前端服务器配置问题")
        
        if not results['step_creation']:
            logger.warning("   ⚠️ Docker Push步骤创建失败可能原因:")
            logger.warning("      1. 后端API异常")
            logger.warning("      2. 数据验证失败")
            logger.warning("      3. 数据库连接问题")
        
        # 建议
        logger.info("\n💡 问题解决建议:")
        for i, recommendation in enumerate(results['recommendations'], 1):
            logger.info(f"   {i}. {recommendation}")
        
        if results['frontend_routes'] and results['step_creation']:
            logger.info("   ✨ 所有测试通过，问题可能在于:")
            logger.info("      1. 前端状态管理异常")
            logger.info("      2. 组件生命周期问题")
            logger.info("      3. 浏览器缓存问题")
            logger.info("   建议: 清除浏览器缓存并重新加载页面")

def main():
    """主函数"""
    debugger = DockerPushStepIssueDebugger()
    results = debugger.debug_issue()
    debugger.generate_report(results)

if __name__ == '__main__':
    main()
