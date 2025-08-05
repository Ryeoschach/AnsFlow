#!/usr/bin/env python3
"""
AnsFlow 并行组功能演示脚本
展示并行组的创建、执行和监控
"""

import asyncio
import time
import json
from datetime import datetime
from typing import Dict, List, Any

class ParallelGroupDemo:
    """并行组功能演示类"""
    
    def __init__(self):
        self.demo_results = []
    
    def create_demo_pipeline(self) -> Dict[str, Any]:
        """创建演示用的流水线"""
        # 模拟一个完整的CI/CD流水线
        steps = [
            # 第一阶段：代码检出
            {
                'id': 'checkout',
                'name': '代码检出',
                'type': 'fetch_code',
                'order': 1,
                'estimated_duration': 2.0,
                'parameters': {'repository': 'https://github.com/example/project.git'}
            },
            # 第二阶段：并行测试组
            {
                'id': 'unit_test',
                'name': '单元测试',
                'type': 'test',
                'order': 2,
                'parallel_group': 'test_group',
                'estimated_duration': 8.0,
                'parameters': {'test_type': 'unit', 'coverage': True}
            },
            {
                'id': 'integration_test',
                'name': '集成测试',
                'type': 'test',
                'order': 2,
                'parallel_group': 'test_group',
                'estimated_duration': 12.0,
                'parameters': {'test_type': 'integration', 'database': 'postgres'}
            },
            {
                'id': 'security_scan',
                'name': '安全扫描',
                'type': 'security',
                'order': 2,
                'parallel_group': 'test_group',
                'estimated_duration': 6.0,
                'parameters': {'scan_type': 'sast', 'tools': ['sonarqube', 'snyk']}
            },
            {
                'id': 'lint_check',
                'name': '代码检查',
                'type': 'lint',
                'order': 2,
                'parallel_group': 'test_group',
                'estimated_duration': 3.0,
                'parameters': {'linters': ['eslint', 'prettier', 'pylint']}
            },
            # 第三阶段：构建
            {
                'id': 'build_app',
                'name': '构建应用',
                'type': 'build',
                'order': 3,
                'estimated_duration': 10.0,
                'parameters': {'build_tool': 'docker', 'optimize': True}
            },
            # 第四阶段：并行部署组
            {
                'id': 'deploy_staging',
                'name': '部署到测试环境',
                'type': 'deploy',
                'order': 4,
                'parallel_group': 'deploy_group',
                'estimated_duration': 5.0,
                'parameters': {'environment': 'staging', 'health_check': True}
            },
            {
                'id': 'deploy_preview',
                'name': '部署预览环境',
                'type': 'deploy',
                'order': 4,
                'parallel_group': 'deploy_group',
                'estimated_duration': 4.0,
                'parameters': {'environment': 'preview', 'temporary': True}
            }
        ]
        
        parallel_groups = [
            {
                'id': 'test_group',
                'name': '测试并行组',
                'description': '并行执行各种测试以提高效率',
                'sync_policy': 'wait_all',
                'timeout_seconds': 900,
                'order': 2,
                'color': '#52c41a'
            },
            {
                'id': 'deploy_group',
                'name': '部署并行组',
                'description': '同时部署到多个环境',
                'sync_policy': 'wait_all',
                'timeout_seconds': 300,
                'order': 4,
                'color': '#1890ff'
            }
        ]
        
        return {
            'name': 'AnsFlow 并行组演示流水线',
            'description': '展示并行组功能的完整CI/CD流水线',
            'steps': steps,
            'parallel_groups': parallel_groups
        }
    
    async def simulate_step_execution(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """模拟步骤执行"""
        step_name = step['name']
        duration = step['estimated_duration']
        
        print(f"  🚀 开始执行: {step_name}")
        
        # 模拟执行过程
        start_time = time.time()
        
        # 分段显示进度
        segments = 4
        for i in range(segments):
            await asyncio.sleep(duration / segments)
            progress = ((i + 1) / segments) * 100
            print(f"     📊 {step_name} 进度: {progress:.0f}%")
        
        execution_time = time.time() - start_time
        
        # 模拟偶尔的失败（5%概率）
        import random
        success = random.random() > 0.05
        
        if success:
            print(f"  ✅ 完成: {step_name} ({execution_time:.2f}s)")
            return {
                'success': True,
                'execution_time': execution_time,
                'output': f'{step_name} 执行成功'
            }
        else:
            print(f"  ❌ 失败: {step_name} ({execution_time:.2f}s)")
            return {
                'success': False,
                'execution_time': execution_time,
                'error': f'{step_name} 模拟执行失败'
            }
    
    async def execute_parallel_group(self, group: Dict[str, Any], group_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """执行并行组"""
        group_name = group['name']
        sync_policy = group['sync_policy']
        
        print(f"\n🔀 开始并行组: {group_name}")
        print(f"   策略: {sync_policy}, 步骤数: {len(group_steps)}")
        
        start_time = time.time()
        
        # 并行执行所有步骤
        tasks = [self.simulate_step_execution(step) for step in group_steps]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # 分析结果
        successful_steps = 0
        failed_steps = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"   ❌ 步骤异常: {group_steps[i]['name']} - {result}")
                failed_steps += 1
            elif result.get('success', False):
                successful_steps += 1
            else:
                failed_steps += 1
        
        # 根据同步策略判断成功
        group_success = False
        if sync_policy == 'wait_all':
            group_success = failed_steps == 0
        elif sync_policy == 'wait_any':
            group_success = successful_steps > 0
        elif sync_policy == 'fail_fast':
            group_success = failed_steps == 0
        
        status_emoji = "✅" if group_success else "❌"
        print(f"\n{status_emoji} 并行组完成: {group_name}")
        print(f"   执行时间: {execution_time:.2f}s")
        print(f"   成功步骤: {successful_steps}/{len(group_steps)}")
        
        return {
            'group_name': group_name,
            'success': group_success,
            'execution_time': execution_time,
            'successful_steps': successful_steps,
            'total_steps': len(group_steps),
            'results': results
        }
    
    async def execute_demo_pipeline(self) -> Dict[str, Any]:
        """执行演示流水线"""
        pipeline = self.create_demo_pipeline()
        
        print("=" * 80)
        print(f"🎬 AnsFlow 并行组功能演示")
        print(f"流水线: {pipeline['name']}")
        print(f"描述: {pipeline['description']}")
        print("=" * 80)
        
        steps = pipeline['steps']
        parallel_groups = {group['id']: group for group in pipeline['parallel_groups']}
        
        # 分析执行计划
        execution_plan = self.analyze_execution_plan(steps, parallel_groups)
        
        print(f"\n📋 执行计划:")
        for stage in execution_plan['stages']:
            stage_type = "并行" if stage['is_parallel'] else "顺序"
            print(f"   阶段 {stage['order']}: {stage_type} - {len(stage['steps'])} 步骤")
        
        total_start_time = time.time()
        stage_results = []
        
        # 按阶段执行
        for stage in execution_plan['stages']:
            stage_start_time = time.time()
            
            if stage['is_parallel']:
                # 并行执行
                group_info = parallel_groups[stage['group_id']]
                result = await self.execute_parallel_group(group_info, stage['steps'])
                stage_results.append(result)
                
                if not result['success']:
                    print(f"\n💥 流水线失败于并行组: {group_info['name']}")
                    break
            else:
                # 顺序执行
                print(f"\n➡️ 顺序执行阶段 {stage['order']}")
                for step in stage['steps']:
                    result = await self.simulate_step_execution(step)
                    if not result['success']:
                        print(f"\n💥 流水线失败于步骤: {step['name']}")
                        stage_results.append({'success': False, 'failed_step': step['name']})
                        break
                else:
                    stage_time = time.time() - stage_start_time
                    stage_results.append({
                        'success': True,
                        'execution_time': stage_time,
                        'stage_type': 'sequential'
                    })
        
        total_time = time.time() - total_start_time
        
        # 生成执行报告
        return self.generate_execution_report(pipeline, stage_results, total_time)
    
    def analyze_execution_plan(self, steps: List[Dict[str, Any]], parallel_groups: Dict[str, Any]) -> Dict[str, Any]:
        """分析执行计划"""
        # 按order分组
        order_groups = {}
        for step in steps:
            order = step['order']
            if order not in order_groups:
                order_groups[order] = []
            order_groups[order].append(step)
        
        stages = []
        for order in sorted(order_groups.keys()):
            stage_steps = order_groups[order]
            
            # 检查是否为并行组
            parallel_group_id = stage_steps[0].get('parallel_group')
            is_parallel = parallel_group_id is not None
            
            if is_parallel:
                # 确保所有步骤都属于同一个并行组
                assert all(step.get('parallel_group') == parallel_group_id for step in stage_steps)
            
            stages.append({
                'order': order,
                'is_parallel': is_parallel,
                'group_id': parallel_group_id,
                'steps': stage_steps
            })
        
        return {'stages': stages}
    
    def generate_execution_report(self, pipeline: Dict[str, Any], stage_results: List[Dict[str, Any]], total_time: float) -> Dict[str, Any]:
        """生成执行报告"""
        successful_stages = sum(1 for result in stage_results if result.get('success', False))
        total_stages = len(stage_results)
        
        overall_success = successful_stages == total_stages
        
        print("\n" + "=" * 80)
        print("📊 流水线执行报告")
        print("=" * 80)
        print(f"流水线名称: {pipeline['name']}")
        print(f"执行状态: {'✅ 成功' if overall_success else '❌ 失败'}")
        print(f"总执行时间: {total_time:.2f}s")
        print(f"成功阶段: {successful_stages}/{total_stages}")
        
        # 并行组性能分析
        parallel_results = [r for r in stage_results if 'group_name' in r]
        if parallel_results:
            print(f"\n🔀 并行组性能:")
            for result in parallel_results:
                efficiency = (result['successful_steps'] / result['total_steps']) * 100
                print(f"   {result['group_name']}: {result['execution_time']:.2f}s, {efficiency:.1f}% 效率")
        
        # 性能建议
        print(f"\n💡 性能分析:")
        if total_time < 30:
            print("   ✅ 执行时间理想，并行组优化效果显著")
        elif total_time < 60:
            print("   ⚠️ 执行时间可接受，考虑进一步优化")
        else:
            print("   🔥 执行时间较长，建议增加并行度")
        
        if overall_success:
            print("   ✅ 所有步骤执行成功，流水线稳定可靠")
        else:
            print("   ❌ 存在失败步骤，建议增加重试机制")
        
        print("=" * 80)
        
        return {
            'pipeline_name': pipeline['name'],
            'success': overall_success,
            'total_time': total_time,
            'successful_stages': successful_stages,
            'total_stages': total_stages,
            'parallel_efficiency': self.calculate_parallel_efficiency(stage_results),
            'timestamp': datetime.now().isoformat()
        }
    
    def calculate_parallel_efficiency(self, stage_results: List[Dict[str, Any]]) -> float:
        """计算并行执行效率"""
        parallel_results = [r for r in stage_results if 'group_name' in r]
        if not parallel_results:
            return 0.0
        
        total_efficiency = 0.0
        for result in parallel_results:
            efficiency = (result['successful_steps'] / result['total_steps']) * 100
            total_efficiency += efficiency
        
        return total_efficiency / len(parallel_results)

async def main():
    """主函数"""
    demo = ParallelGroupDemo()
    
    print("🎭 AnsFlow 并行组功能演示开始...")
    print("这个演示将展示:")
    print("  1. 并行组的创建和配置")
    print("  2. 并行步骤的执行过程")
    print("  3. 性能优化效果")
    print("  4. 执行结果分析")
    print()
    
    try:
        result = await demo.execute_demo_pipeline()
        
        print(f"\n🎉 演示完成!")
        print(f"整体成功率: {'✅ 成功' if result['success'] else '❌ 失败'}")
        print(f"并行效率: {result['parallel_efficiency']:.1f}%")
        print(f"总执行时间: {result['total_time']:.2f}s")
        
        # 保存结果
        with open(f"demo_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 详细结果已保存到 demo_result_*.json")
        
    except Exception as e:
        print(f"\n❌ 演示执行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
