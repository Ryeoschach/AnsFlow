#!/usr/bin/env python3
"""
Jenkins并行组转换测试脚本
用于验证Jenkins Pipeline的并行组转换功能
"""
import os
import sys

# 添加Django项目路径
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')

import django
django.setup()

from pipelines.services.jenkins_sync import JenkinsPipelineSyncService
from pipelines.models import Pipeline
from cicd_integrations.models import CICDTool, AtomicStep
from project_management.models import Project


class JenkinsParallelTest:
    """Jenkins并行转换测试器"""
    
    def __init__(self):
        self.test_results = []
    
    def create_test_pipeline_with_parallel_groups(self):
        """创建包含并行组的测试流水线"""
        print("🔧 创建测试流水线...")
        
        # 创建测试项目
        try:
            from project_management.models import Project
            project, created = Project.objects.get_or_create(
                name="测试项目",
                defaults={
                    'description': '用于测试的项目',
                    'status': 'active'
                }
            )
            project_id = project.id
        except ImportError:
            # 如果没有项目管理模块，使用默认值
            project_id = 1
        
        # 创建测试工具
        tool, created = CICDTool.objects.get_or_create(
            name="测试Jenkins",
            defaults={
                'tool_type': 'jenkins',
                'base_url': 'http://jenkins.test.com',
                'username': 'test_user',
                'token': 'test_token',
                'description': '测试用Jenkins服务器'
            }
        )
        
        # 创建测试流水线
        pipeline, created = Pipeline.objects.get_or_create(
            name="Jenkins并行测试流水线",
            defaults={
                'description': '用于测试Jenkins并行组转换的流水线',
                'execution_mode': 'remote',
                'execution_tool': tool,
                'project_id': project_id,
                'config': {}
            }
        )
        
        # 清理现有步骤
        AtomicStep.objects.filter(pipeline=pipeline).delete()
        
        # 创建测试步骤
        steps_data = [
            {
                'name': '1111',
                'step_type': 'shell',
                'order': 1,
                'parallel_group': None,
                'config': {'command': 'echo "Hello World"'}
            },
            {
                'name': '222-1',
                'step_type': 'shell',
                'order': 2,
                'parallel_group': 'parallel-group-222',
                'config': {'command': 'echo "Hello World2222"'}
            },
            {
                'name': '222-2',
                'step_type': 'shell',
                'order': 3,
                'parallel_group': 'parallel-group-222',
                'config': {'command': 'echo "Hello World222-2"'}
            },
            {
                'name': '333',
                'step_type': 'shell',
                'order': 4,
                'parallel_group': None,
                'config': {'command': 'echo "Hello World"'}
            }
        ]
        
        for step_data in steps_data:
            AtomicStep.objects.create(
                pipeline=pipeline,
                project_id=project_id,  # 添加项目ID
                **step_data
            )
        
        print(f"✅ 创建流水线成功: {pipeline.name}")
        print(f"   - 流水线ID: {pipeline.id}")
        print(f"   - 步骤数量: {len(steps_data)}")
        print(f"   - 并行组: parallel-group-222 (包含 222-1, 222-2)")
        
        return pipeline, tool
    
    def test_jenkins_pipeline_generation(self):
        """测试Jenkins Pipeline生成"""
        print("\n🧪 测试Jenkins Pipeline生成...")
        
        try:
            # 创建测试数据
            pipeline, tool = self.create_test_pipeline_with_parallel_groups()
            
            # 创建Jenkins同步服务
            jenkins_service = JenkinsPipelineSyncService(tool)
            
            # 生成Jenkins Pipeline脚本
            jenkins_script = jenkins_service._convert_steps_to_jenkins_script(pipeline)
            
            print("✅ Jenkins Pipeline脚本生成成功")
            print("\n📝 生成的Jenkins Pipeline脚本:")
            print("=" * 60)
            print(jenkins_script.replace('\\n', '\n'))
            print("=" * 60)
            
            # 验证并行组是否正确生成
            self._validate_parallel_groups(jenkins_script)
            
            self.test_results.append({
                'test': 'jenkins_pipeline_generation',
                'status': 'success',
                'pipeline_id': pipeline.id
            })
            
        except Exception as e:
            print(f"❌ Jenkins Pipeline生成失败: {e}")
            self.test_results.append({
                'test': 'jenkins_pipeline_generation',
                'status': 'failed',
                'error': str(e)
            })
    
    def _validate_parallel_groups(self, jenkins_script):
        """验证并行组是否正确生成"""
        print("\n🔍 验证并行组转换...")
        
        # 检查是否包含parallel关键字
        if 'parallel {' in jenkins_script:
            print("✅ 检测到parallel关键字")
        else:
            print("❌ 未检测到parallel关键字")
            raise Exception("Jenkins脚本中缺少parallel关键字")
        
        # 检查是否包含并行步骤
        if '"222_1":' in jenkins_script and '"222_2":' in jenkins_script:
            print("✅ 检测到并行步骤 222-1 和 222-2")
        else:
            print("❌ 未检测到期望的并行步骤")
            raise Exception("Jenkins脚本中缺少期望的并行步骤")
        
        # 检查顺序步骤是否存在
        if "stage('1111')" in jenkins_script and "stage('333')" in jenkins_script:
            print("✅ 检测到顺序步骤 1111 和 333")
        else:
            print("❌ 未检测到期望的顺序步骤")
            raise Exception("Jenkins脚本中缺少期望的顺序步骤")
        
        print("✅ 并行组转换验证通过")
    
    def test_execution_plan_analysis(self):
        """测试执行计划分析"""
        print("\n🧪 测试执行计划分析...")
        
        try:
            pipeline, tool = self.create_test_pipeline_with_parallel_groups()
            jenkins_service = JenkinsPipelineSyncService(tool)
            
            # 获取原子步骤
            atomic_steps = pipeline.atomic_steps.all().order_by('order')
            
            # 分析执行计划
            execution_plan = jenkins_service._analyze_execution_plan(atomic_steps)
            
            print(f"✅ 执行计划分析成功")
            print(f"   - 总阶段数: {len(execution_plan['stages'])}")
            
            # 验证执行计划
            parallel_stages = [s for s in execution_plan['stages'] if s['parallel']]
            sequential_stages = [s for s in execution_plan['stages'] if not s['parallel']]
            
            print(f"   - 并行阶段: {len(parallel_stages)}")
            print(f"   - 顺序阶段: {len(sequential_stages)}")
            
            if len(parallel_stages) == 1 and len(sequential_stages) == 2:
                print("✅ 执行计划结构正确")
            else:
                raise Exception(f"执行计划结构错误: 期望1个并行阶段和2个顺序阶段")
            
            # 检查并行阶段的步骤数量
            parallel_stage = parallel_stages[0]
            if len(parallel_stage['items']) == 2:
                print("✅ 并行阶段包含2个步骤")
            else:
                raise Exception(f"并行阶段步骤数量错误: 期望2个，实际{len(parallel_stage['items'])}个")
            
            self.test_results.append({
                'test': 'execution_plan_analysis',
                'status': 'success',
                'stages': len(execution_plan['stages']),
                'parallel_stages': len(parallel_stages),
                'sequential_stages': len(sequential_stages)
            })
            
        except Exception as e:
            print(f"❌ 执行计划分析失败: {e}")
            self.test_results.append({
                'test': 'execution_plan_analysis',
                'status': 'failed',
                'error': str(e)
            })
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始Jenkins并行组转换测试")
        print("=" * 60)
        
        # 执行测试
        self.test_execution_plan_analysis()
        self.test_jenkins_pipeline_generation()
        
        # 输出测试结果
        print("\n" + "=" * 60)
        print("📋 测试结果摘要")
        print("=" * 60)
        
        for result in self.test_results:
            test_name = result['test']
            status = result['status']
            status_icon = "✅" if status == "success" else "❌"
            
            print(f"{status_icon} {test_name}: {status}")
            
            if status != "success":
                print(f"   错误: {result.get('error', 'Unknown error')}")
        
        # 总结
        successful_tests = len([r for r in self.test_results if r['status'] == 'success'])
        total_tests = len(self.test_results)
        
        print(f"\n📊 测试完成: {successful_tests}/{total_tests} 通过")
        
        return successful_tests == total_tests


def main():
    """主函数"""
    tester = JenkinsParallelTest()
    
    try:
        success = tester.run_all_tests()
        
        if success:
            print("\n✅ 所有测试通过！Jenkins并行组转换功能正常")
            sys.exit(0)
        else:
            print("\n❌ 部分测试失败！请检查Jenkins并行组转换逻辑")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
