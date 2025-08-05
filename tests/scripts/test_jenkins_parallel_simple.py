#!/usr/bin/env python3
"""
Jenkins并行组转换测试脚本（简化版）
直接测试Jenkins Pipeline代码生成逻辑
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
from cicd_integrations.models import CICDTool


class MockAtomicStep:
    """模拟原子步骤对象"""
    def __init__(self, name, step_type, order, parallel_group=None, config=None):
        self.name = name
        self.step_type = step_type
        self.order = order
        self.parallel_group = parallel_group
        self.config = config or {}


class MockQuerySet:
    """模拟查询集"""
    def __init__(self, steps):
        self._steps = steps
    
    def all(self):
        return self
    
    def order_by(self, field):
        if field == 'order':
            return MockQuerySet(sorted(self._steps, key=lambda x: x.order))
        return self
    
    def __iter__(self):
        return iter(self._steps)


class MockPipeline:
    """模拟流水线对象"""
    def __init__(self, name, steps):
        self.name = name
        self._steps = steps
        # 创建atomic_steps属性而不是方法
        self.atomic_steps = MockQuerySet(steps)


class JenkinsParallelTestSimple:
    """简化的Jenkins并行转换测试器"""
    
    def __init__(self):
        self.test_results = []
    
    def create_mock_pipeline(self):
        """创建模拟的流水线数据"""
        print("🔧 创建模拟流水线数据...")
        
        steps = [
            MockAtomicStep('1111', 'shell', 1, None, {'command': 'echo "Hello World"'}),
            MockAtomicStep('222-1', 'shell', 2, 'parallel-group-222', {'command': 'echo "Hello World2222"'}),
            MockAtomicStep('222-2', 'shell', 3, 'parallel-group-222', {'command': 'echo "Hello World222-2"'}),
            MockAtomicStep('333', 'shell', 4, None, {'command': 'echo "Hello World"'}),
        ]
        
        pipeline = MockPipeline("Jenkins并行测试流水线", steps)
        
        print(f"✅ 创建模拟流水线成功: {pipeline.name}")
        print(f"   - 步骤数量: {len(steps)}")
        print(f"   - 并行组: parallel-group-222 (包含 222-1, 222-2)")
        
        return pipeline
    
    def test_execution_plan_analysis(self):
        """测试执行计划分析"""
        print("\n🧪 测试执行计划分析...")
        
        try:
            pipeline = self.create_mock_pipeline()
            
            # 创建Jenkins同步服务
            tool = CICDTool(name="Test", tool_type="jenkins", base_url="http://test")
            jenkins_service = JenkinsPipelineSyncService(tool)
            
            # 获取原子步骤
            atomic_steps = list(pipeline.atomic_steps.order_by('order'))
            
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
    
    def test_jenkins_pipeline_generation(self):
        """测试Jenkins Pipeline生成"""
        print("\n🧪 测试Jenkins Pipeline生成...")
        
        try:
            pipeline = self.create_mock_pipeline()
            
            # 创建Jenkins同步服务
            tool = CICDTool(name="Test", tool_type="jenkins", base_url="http://test")
            jenkins_service = JenkinsPipelineSyncService(tool)
            
            # 生成Jenkins Pipeline脚本
            jenkins_script = jenkins_service._convert_steps_to_jenkins_script(pipeline)
            
            print("✅ Jenkins Pipeline脚本生成成功")
            print("\n📝 生成的Jenkins Pipeline脚本:")
            print("=" * 60)
            formatted_script = jenkins_script.replace('\\n', '\n')
            print(formatted_script)
            print("=" * 60)
            
            # 验证并行组是否正确生成
            self._validate_parallel_groups(formatted_script)
            
            self.test_results.append({
                'test': 'jenkins_pipeline_generation',
                'status': 'success'
            })
            
        except Exception as e:
            print(f"❌ Jenkins Pipeline生成失败: {e}")
            import traceback
            print(f"详细错误: {traceback.format_exc()}")
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
            print(f"脚本内容: {jenkins_script}")
            raise Exception("Jenkins脚本中缺少期望的并行步骤")
        
        # 检查顺序步骤是否存在
        if "stage('1111')" in jenkins_script and "stage('333')" in jenkins_script:
            print("✅ 检测到顺序步骤 1111 和 333")
        else:
            print("❌ 未检测到期望的顺序步骤")
            raise Exception("Jenkins脚本中缺少期望的顺序步骤")
        
        print("✅ 并行组转换验证通过")
    
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
    tester = JenkinsParallelTestSimple()
    
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
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main()
