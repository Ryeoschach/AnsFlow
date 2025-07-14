#!/usr/bin/env python3
"""
真实Jenkins环境集成测试
验证AnsFlow生成的Pipeline在真实Jenkins环境中的执行效果
"""

import sys
import os
import json
import requests
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 尝试设置 Django 环境，但允许失败
try:
    import django
    sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
    django.setup()
    DJANGO_AVAILABLE = True
except Exception as e:
    print(f"Django environment not available: {e}")
    DJANGO_AVAILABLE = False

class JenkinsIntegrationTester:
    """Jenkins集成测试器"""
    
    def __init__(self, jenkins_url, username, token):
        self.jenkins_url = jenkins_url.rstrip('/')
        self.username = username
        self.token = token
        self.auth = (username, token)
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'jenkins_url': jenkins_url,
            'tests': [],
            'summary': {}
        }
    
    def test_parallel_pipeline_creation(self):
        """测试并行Pipeline的创建和执行"""
        test_case = {
            'name': 'parallel_pipeline_creation',
            'description': '测试并行组Pipeline在Jenkins中的创建和执行',
            'start_time': datetime.now().isoformat(),
            'status': 'running'
        }
        
        try:
            # 1. 生成并行Pipeline配置
            parallel_pipeline = self._generate_test_parallel_pipeline()
            test_case['pipeline_content'] = parallel_pipeline
            
            # 2. 在Jenkins中创建Job
            job_name = f"ansflow-parallel-test-{int(time.time())}"
            creation_result = self._create_jenkins_job(job_name, parallel_pipeline)
            test_case['job_creation'] = creation_result
            
            if not creation_result['success']:
                test_case['status'] = 'failed'
                test_case['error'] = 'Job creation failed'
                return test_case
            
            # 3. 触发构建
            build_result = self._trigger_jenkins_build(job_name)
            test_case['build_trigger'] = build_result
            
            if not build_result['success']:
                test_case['status'] = 'failed'
                test_case['error'] = 'Build trigger failed'
                return test_case
            
            # 4. 监控构建过程
            build_number = build_result['build_number']
            monitoring_result = self._monitor_build_execution(job_name, build_number)
            test_case['build_monitoring'] = monitoring_result
            
            # 5. 验证并行执行效果
            parallel_verification = self._verify_parallel_execution(job_name, build_number)
            test_case['parallel_verification'] = parallel_verification
            
            # 6. 清理测试Job
            cleanup_result = self._cleanup_test_job(job_name)
            test_case['cleanup'] = cleanup_result
            
            # 确定最终状态
            if (creation_result['success'] and build_result['success'] and 
                monitoring_result['success'] and parallel_verification['parallel_detected']):
                test_case['status'] = 'passed'
            else:
                test_case['status'] = 'failed'
                
        except Exception as e:
            test_case['status'] = 'error'
            test_case['error'] = str(e)
            test_case['traceback'] = str(e.__traceback__)
        
        test_case['end_time'] = datetime.now().isoformat()
        return test_case
    
    def _generate_test_parallel_pipeline(self):
        """生成测试用的并行Pipeline"""
        try:
            if DJANGO_AVAILABLE:
                return self._generate_pipeline_via_api()
            else:
                print("Django环境不可用，使用静态Pipeline模板")
                return self._get_fallback_parallel_pipeline()
        except Exception as e:
            print(f"Pipeline生成失败，使用静态模板: {e}")
            return self._get_fallback_parallel_pipeline()
    
    def _generate_pipeline_via_api(self):
        """通过API生成Pipeline"""
        try:
            # 尝试调用本地API端点
            api_url = "http://localhost:8000/api/pipelines/preview/"
            test_steps = [
                {
                    "name": "代码检出",
                    "step_type": "fetch_code",
                    "parameters": {
                        "repository": "https://github.com/jenkinsci/pipeline-examples.git",
                        "branch": "master"
                    },
                    "order": 1
                },
                {
                    "name": "单元测试",
                    "step_type": "test", 
                    "parameters": {
                        "test_command": "echo '执行单元测试'; sleep 10; echo '单元测试完成'"
                    },
                    "order": 2
                },
                {
                    "name": "集成测试",
                    "step_type": "test",
                    "parameters": {
                        "test_command": "echo '执行集成测试'; sleep 15; echo '集成测试完成'"
                    },
                    "order": 2
                },
                {
                    "name": "安全扫描",
                    "step_type": "test",
                    "parameters": {
                        "test_command": "echo '执行安全扫描'; sleep 8; echo '安全扫描完成'"
                    },
                    "order": 2
                },
                {
                    "name": "构建应用",
                    "step_type": "build",
                    "parameters": {
                        "build_tool": "maven"
                    },
                    "order": 3
                },
                {
                    "name": "部署测试",
                    "step_type": "deploy",
                    "parameters": {
                        "deploy_command": "echo '部署到测试环境'; sleep 5; echo '部署完成'"
                    },
                    "order": 4
                }
            ]
            
            request_data = {
                'pipeline_id': 999,
                'steps': test_steps,
                'execution_mode': 'local',
                'preview_mode': True,
                'ci_tool_type': 'jenkins',
                'environment': {'TEST_ENV': 'jenkins_integration'},
                'timeout': 1800
            }
            
            response = requests.post(api_url, json=request_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('content', data.get('jenkinsfile', ''))
            else:
                raise Exception(f"API调用失败: {response.status_code}")
                
        except Exception as e:
            print(f"API调用失败: {e}")
            # 如果Django可用，尝试直接调用
            if DJANGO_AVAILABLE:
                try:
                    from cicd_integrations.views.pipeline_preview import pipeline_preview
                    from django.http import HttpRequest
                    
                    request = HttpRequest()
                    request.method = 'POST'
                    request._body = json.dumps(request_data).encode('utf-8')
                    
                    response = pipeline_preview(request)
                    
                    if response.status_code == 200:
                        data = json.loads(response.content)
                        return data.get('content', data.get('jenkinsfile', ''))
                    else:
                        raise Exception(f"Pipeline generation failed: {response.status_code}")
                except Exception as django_error:
                    print(f"Django Pipeline生成失败: {django_error}")
                    raise e
            else:
                raise e
    
    def _get_fallback_parallel_pipeline(self):
        """回退的并行Pipeline定义"""
        return """pipeline {
    agent any
    
    options {
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '5'))
    }
    
    environment {
        TEST_ENV = 'jenkins_integration'
    }
    
    stages {
        stage('代码检出') {
            steps {
                echo '开始代码检出'
                checkout scm
                echo '代码检出完成'
            }
        }
        
        stage('并行测试阶段') {
            parallel {
                '单元测试': {
                    steps {
                        echo '开始单元测试'
                        sleep 10
                        echo '单元测试完成'
                    }
                },
                '集成测试': {
                    steps {
                        echo '开始集成测试'
                        sleep 15
                        echo '集成测试完成'
                    }
                },
                '安全扫描': {
                    steps {
                        echo '开始安全扫描'
                        sleep 8
                        echo '安全扫描完成'
                    }
                }
            }
        }
        
        stage('构建应用') {
            steps {
                echo '开始构建应用'
                sleep 5
                echo '构建完成'
            }
        }
        
        stage('部署测试') {
            steps {
                echo '开始部署到测试环境'
                sleep 3
                echo '部署完成'
            }
        }
    }
    
    post {
        always {
            echo 'Pipeline执行完成'
        }
        success {
            echo 'Pipeline执行成功'
        }
        failure {
            echo 'Pipeline执行失败'
        }
    }
}"""
    
    def _create_jenkins_job(self, job_name, pipeline_content):
        """在Jenkins中创建Job"""
        try:
            job_config = f"""<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job@2.40">
  <description>AnsFlow自动生成的并行Pipeline测试</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@2.87">
    <script>{pipeline_content}</script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>"""
            
            url = f"{self.jenkins_url}/createItem?name={job_name}"
            headers = {
                'Content-Type': 'application/xml',
                'Jenkins-Crumb': self._get_crumb()
            }
            
            response = requests.post(
                url,
                data=job_config,
                headers=headers,
                auth=self.auth,
                timeout=30
            )
            
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'job_name': job_name,
                'url': f"{self.jenkins_url}/job/{job_name}"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_crumb(self):
        """获取Jenkins CSRF token"""
        try:
            response = requests.get(
                f"{self.jenkins_url}/crumbIssuer/api/json",
                auth=self.auth,
                timeout=10
            )
            if response.status_code == 200:
                return response.json()['crumb']
        except:
            pass
        return ''
    
    def _trigger_jenkins_build(self, job_name):
        """触发Jenkins构建"""
        try:
            url = f"{self.jenkins_url}/job/{job_name}/build"
            headers = {
                'Jenkins-Crumb': self._get_crumb()
            }
            
            response = requests.post(
                url,
                headers=headers,
                auth=self.auth,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                # 等待构建开始并获取构建号
                time.sleep(2)
                build_number = self._get_last_build_number(job_name)
                
                return {
                    'success': True,
                    'status_code': response.status_code,
                    'build_number': build_number
                }
            else:
                return {
                    'success': False,
                    'status_code': response.status_code
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_last_build_number(self, job_name):
        """获取最后的构建号"""
        try:
            response = requests.get(
                f"{self.jenkins_url}/job/{job_name}/api/json",
                auth=self.auth,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('lastBuild', {}).get('number', 1)
        except:
            pass
        return 1
    
    def _monitor_build_execution(self, job_name, build_number, timeout_minutes=10):
        """监控构建执行过程"""
        start_time = datetime.now()
        timeout = timedelta(minutes=timeout_minutes)
        
        monitoring_data = {
            'start_time': start_time.isoformat(),
            'timeout_minutes': timeout_minutes,
            'status_checks': [],
            'final_status': None,
            'execution_time_seconds': 0,
            'success': False
        }
        
        try:
            while datetime.now() - start_time < timeout:
                # 获取构建状态
                response = requests.get(
                    f"{self.jenkins_url}/job/{job_name}/{build_number}/api/json",
                    auth=self.auth,
                    timeout=10
                )
                
                if response.status_code == 200:
                    build_data = response.json()
                    is_building = build_data.get('building', True)
                    result = build_data.get('result')
                    duration = build_data.get('duration', 0)
                    
                    status_check = {
                        'timestamp': datetime.now().isoformat(),
                        'building': is_building,
                        'result': result,
                        'duration_ms': duration
                    }
                    monitoring_data['status_checks'].append(status_check)
                    
                    if not is_building:
                        # 构建完成
                        monitoring_data['final_status'] = result
                        monitoring_data['execution_time_seconds'] = duration / 1000 if duration else 0
                        monitoring_data['success'] = result == 'SUCCESS'
                        break
                
                time.sleep(5)  # 每5秒检查一次
            
            if not monitoring_data['final_status']:
                monitoring_data['final_status'] = 'TIMEOUT'
                monitoring_data['success'] = False
                
        except Exception as e:
            monitoring_data['error'] = str(e)
            monitoring_data['success'] = False
        
        monitoring_data['end_time'] = datetime.now().isoformat()
        return monitoring_data
    
    def _verify_parallel_execution(self, job_name, build_number):
        """验证并行执行效果"""
        verification_result = {
            'parallel_detected': False,
            'parallel_stages': [],
            'execution_timeline': [],
            'performance_analysis': {}
        }
        
        try:
            # 获取构建日志
            log_response = requests.get(
                f"{self.jenkins_url}/job/{job_name}/{build_number}/consoleText",
                auth=self.auth,
                timeout=30
            )
            
            if log_response.status_code == 200:
                log_content = log_response.text
                
                # 分析日志中的并行执行迹象
                parallel_indicators = [
                    'parallel {',
                    'Running in parallel',
                    'Branch:',
                    'Parallel execution'
                ]
                
                for indicator in parallel_indicators:
                    if indicator in log_content:
                        verification_result['parallel_detected'] = True
                        break
                
                # 提取并行阶段信息
                lines = log_content.split('\n')
                current_stage = None
                stage_start_times = {}
                
                for line in lines:
                    # 检测stage开始
                    if '[Pipeline] stage' in line and 'Starting' in line:
                        # 提取stage名称
                        import re
                        stage_match = re.search(r"stage \('(.+?)'\)", line)
                        if stage_match:
                            current_stage = stage_match.group(1)
                            timestamp = self._extract_timestamp_from_log_line(line)
                            stage_start_times[current_stage] = timestamp
                            
                            verification_result['parallel_stages'].append({
                                'name': current_stage,
                                'start_time': timestamp,
                                'type': 'parallel' if '并行' in current_stage else 'sequential'
                            })
                
                # 分析执行时间重叠（并行执行的证据）
                verification_result['performance_analysis'] = self._analyze_execution_timeline(
                    verification_result['parallel_stages']
                )
                
            # 获取更详细的构建信息
            build_response = requests.get(
                f"{self.jenkins_url}/job/{job_name}/{build_number}/api/json?tree=actions[*],duration,result",
                auth=self.auth,
                timeout=10
            )
            
            if build_response.status_code == 200:
                build_data = build_response.json()
                verification_result['build_duration_ms'] = build_data.get('duration', 0)
                verification_result['build_result'] = build_data.get('result')
                
        except Exception as e:
            verification_result['error'] = str(e)
        
        return verification_result
    
    def _extract_timestamp_from_log_line(self, line):
        """从日志行中提取时间戳"""
        import re
        # Jenkins日志通常包含时间戳格式：[2024-07-14T14:06:01.123Z]
        timestamp_match = re.search(r'\[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z)\]', line)
        if timestamp_match:
            return timestamp_match.group(1)
        return datetime.now().isoformat()
    
    def _analyze_execution_timeline(self, stages):
        """分析执行时间线，检测并行执行"""
        analysis = {
            'total_stages': len(stages),
            'parallel_stages_detected': 0,
            'sequential_stages_detected': 0,
            'estimated_parallel_time_saved': 0
        }
        
        # 简单的并行检测逻辑
        parallel_stages = [s for s in stages if s.get('type') == 'parallel']
        sequential_stages = [s for s in stages if s.get('type') == 'sequential']
        
        analysis['parallel_stages_detected'] = len(parallel_stages)
        analysis['sequential_stages_detected'] = len(sequential_stages)
        
        return analysis
    
    def _cleanup_test_job(self, job_name):
        """清理测试Job"""
        try:
            url = f"{self.jenkins_url}/job/{job_name}/doDelete"
            headers = {
                'Jenkins-Crumb': self._get_crumb()
            }
            
            response = requests.post(
                url,
                headers=headers,
                auth=self.auth,
                timeout=30
            )
            
            return {
                'success': response.status_code in [200, 302],
                'status_code': response.status_code
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def run_integration_tests(self):
        """运行完整的Jenkins集成测试"""
        print("🔧 Jenkins集成测试开始")
        print("=" * 60)
        
        # 测试Jenkins连接
        print("🔍 测试Jenkins连接...")
        connection_test = self._test_jenkins_connection()
        
        if not connection_test['success']:
            print(f"❌ Jenkins连接失败: {connection_test.get('error', 'Unknown error')}")
            return False
        
        print(f"✅ Jenkins连接成功 (版本: {connection_test.get('version', 'Unknown')})")
        
        # 执行并行Pipeline测试
        print("\n🚀 执行并行Pipeline测试...")
        parallel_test = self.test_parallel_pipeline_creation()
        self.test_results['tests'].append(parallel_test)
        
        # 生成测试报告
        self._generate_test_report()
        
        return parallel_test['status'] == 'passed'
    
    def _test_jenkins_connection(self):
        """测试Jenkins连接"""
        try:
            response = requests.get(
                f"{self.jenkins_url}/api/json",
                auth=self.auth,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'version': data.get('version', 'Unknown')
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}"
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_test_report(self):
        """生成测试报告"""
        summary = {
            'total_tests': len(self.test_results['tests']),
            'passed': sum(1 for t in self.test_results['tests'] if t['status'] == 'passed'),
            'failed': sum(1 for t in self.test_results['tests'] if t['status'] == 'failed'),
            'errors': sum(1 for t in self.test_results['tests'] if t['status'] == 'error')
        }
        
        self.test_results['summary'] = summary
        
        # 保存报告
        report_file = f"docs/testing/jenkins_integration_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 测试报告已保存: {report_file}")
        
        # 打印摘要
        print(f"\n📊 测试摘要:")
        print(f"   总测试数: {summary['total_tests']}")
        print(f"   通过: {summary['passed']}")
        print(f"   失败: {summary['failed']}")
        print(f"   错误: {summary['errors']}")

def main():
    """主函数"""
    # Jenkins配置 - 需要根据实际环境修改
    JENKINS_URL = os.getenv('JENKINS_URL', 'http://localhost:8080')
    JENKINS_USERNAME = os.getenv('JENKINS_USERNAME', 'admin')
    JENKINS_TOKEN = os.getenv('JENKINS_TOKEN', 'your-api-token')
    
    print("🧪 AnsFlow Jenkins集成测试")
    print("=" * 60)
    print(f"Jenkins URL: {JENKINS_URL}")
    print(f"用户名: {JENKINS_USERNAME}")
    print("=" * 60)
    
    # 创建测试器
    tester = JenkinsIntegrationTester(JENKINS_URL, JENKINS_USERNAME, JENKINS_TOKEN)
    
    # 运行测试
    success = tester.run_integration_tests()
    
    if success:
        print("\n✅ 所有测试通过！")
        sys.exit(0)
    else:
        print("\n❌ 测试失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()
