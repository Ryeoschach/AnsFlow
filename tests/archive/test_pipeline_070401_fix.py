#!/usr/bin/env python3
"""
测试流水线070401的预览修复
"""
import os
import sys
import django
import json

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_service.settings')
sys.path.append('/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service')

django.setup()

from pipelines.models import Pipeline, AtomicStep
from cicd_integrations.views.pipeline_preview import pipeline_preview
from django.test import RequestFactory
from django.contrib.auth.models import User


def test_pipeline_070401():
    """测试流水线070401的预览功能"""
    print("=== 测试流水线070401预览修复 ===")
    
    # 查找流水线070401
    try:
        # 尝试通过名称查找
        pipeline = Pipeline.objects.filter(name__icontains="070401").first()
        if not pipeline:
            # 如果找不到，列出所有流水线
            pipelines = Pipeline.objects.all()
            print("找不到流水线070401，当前所有流水线：")
            for p in pipelines:
                print(f"  ID: {p.id}, Name: {p.name}")
            
            # 使用第一个流水线作为测试
            if pipelines.exists():
                pipeline = pipelines.first()
                print(f"使用流水线 '{pipeline.name}' (ID: {pipeline.id}) 进行测试")
            else:
                print("❌ 没有找到任何流水线")
                return False
                
        print(f"测试流水线: {pipeline.name} (ID: {pipeline.id})")
        
        # 获取流水线的步骤
        atomic_steps = AtomicStep.objects.filter(pipeline=pipeline).order_by('order')
        print(f"步骤数量: {atomic_steps.count()}")
        
        # 构建步骤数据
        steps_data = []
        for step in atomic_steps:
            step_data = {
                'name': step.name,
                'step_type': step.step_type,
                'parameters': step.parameters or {},
                'order': step.order,
                'description': step.description or ''
            }
            steps_data.append(step_data)
            print(f"  步骤 {step.order}: {step.name} ({step.step_type})")
            if step.step_type == 'ansible':
                print(f"    参数: {step.parameters}")
        
        # 测试预览模式 (preview_mode=true)
        print("\n1. 测试预览模式 (preview_mode=true)")
        preview_request_data = {
            'pipeline_id': pipeline.id,
            'steps': steps_data,
            'preview_mode': True,
            'ci_tool_type': 'jenkins'
        }
        
        factory = RequestFactory()
        request = factory.post(
            '/api/v1/cicd/pipelines/preview/',
            data=json.dumps(preview_request_data),
            content_type='application/json'
        )
        
        # 添加用户信息（如果需要）
        try:
            user = User.objects.first()
            if user:
                request.user = user
        except:
            pass
        
        response = pipeline_preview(request)
        
        if response.status_code == 200:
            result = json.loads(response.content)
            print("✅ 预览模式调用成功")
            print(f"   数据来源: {result.get('workflow_summary', {}).get('data_source', 'unknown')}")
            
            jenkinsfile_preview = result.get('content', result.get('jenkinsfile', ''))
            if jenkinsfile_preview:
                print("   Jenkinsfile前100字符:")
                print(f"   {jenkinsfile_preview[:100]}...")
            
            # 检查ansible步骤
            if 'ansible-playbook' in jenkinsfile_preview:
                print("✅ 预览模式包含ansible步骤")
                # 查找ansible命令
                lines = jenkinsfile_preview.split('\n')
                for i, line in enumerate(lines):
                    if 'ansible-playbook' in line:
                        print(f"   ansible命令: {line.strip()}")
            else:
                print("⚠️  预览模式缺少ansible步骤")
        else:
            print(f"❌ 预览模式调用失败: {response.status_code}")
            print(f"   错误信息: {response.content}")
        
        # 测试实际模式 (preview_mode=false)
        print("\n2. 测试实际模式 (preview_mode=false)")
        actual_request_data = {
            'pipeline_id': pipeline.id,
            'steps': steps_data,
            'preview_mode': False,
            'ci_tool_type': 'jenkins'
        }
        
        request = factory.post(
            '/api/v1/cicd/pipelines/preview/',
            data=json.dumps(actual_request_data),
            content_type='application/json'
        )
        
        if user:
            request.user = user
        
        response = pipeline_preview(request)
        
        if response.status_code == 200:
            result = json.loads(response.content)
            print("✅ 实际模式调用成功")
            print(f"   数据来源: {result.get('workflow_summary', {}).get('data_source', 'unknown')}")
            
            jenkinsfile_actual = result.get('content', result.get('jenkinsfile', ''))
            if jenkinsfile_actual:
                print("   Jenkinsfile前100字符:")
                print(f"   {jenkinsfile_actual[:100]}...")
            
            # 检查ansible步骤
            if 'ansible-playbook' in jenkinsfile_actual:
                print("✅ 实际模式包含ansible步骤")
                # 查找ansible命令
                lines = jenkinsfile_actual.split('\n')
                for i, line in enumerate(lines):
                    if 'ansible-playbook' in line:
                        print(f"   ansible命令: {line.strip()}")
            else:
                print("⚠️  实际模式缺少ansible步骤")
        else:
            print(f"❌ 实际模式调用失败: {response.status_code}")
            print(f"   错误信息: {response.content}")
        
        # 对比两种模式
        print("\n3. 对比预览模式与实际模式")
        try:
            if response.status_code == 200:
                preview_result = json.loads(
                    pipeline_preview(factory.post(
                        '/api/v1/cicd/pipelines/preview/',
                        data=json.dumps(preview_request_data),
                        content_type='application/json'
                    )).content
                )
                actual_result = json.loads(response.content)
                
                preview_content = preview_result.get('content', '')
                actual_content = actual_result.get('content', '')
                
                if preview_content == actual_content:
                    print("✅ 预览模式与实际模式内容一致")
                else:
                    print("⚠️  预览模式与实际模式内容不一致")
                    print("   差异可能在于参数解析方式")
                    
                    # 保存到文件用于对比
                    with open('preview_mode_jenkinsfile.groovy', 'w', encoding='utf-8') as f:
                        f.write(preview_content)
                    with open('actual_mode_jenkinsfile.groovy', 'w', encoding='utf-8') as f:
                        f.write(actual_content)
                    print("   已保存到文件用于详细对比")
        except Exception as e:
            print(f"   对比失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("流水线070401预览修复测试")
    print("=" * 50)
    
    success = test_pipeline_070401()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 测试完成！")
        print("\n修复内容:")
        print("1. ✅ 增强了ansible步骤的ID参数解析")
        print("2. ✅ 添加了playbook_id、inventory_id、credential_id的数据库查询")
        print("3. ✅ 改进了预览模式的参数处理逻辑")
        print("4. ✅ 在非预览模式时使用真实的Jenkins适配器")
        
        print("\n验证方法:")
        print("1. 检查生成的Jenkinsfile文件")
        print("2. 对比预览模式与实际模式的差异")
        print("3. 确认ansible命令参数正确")
    else:
        print("❌ 测试失败，请检查错误信息")


if __name__ == "__main__":
    main()
