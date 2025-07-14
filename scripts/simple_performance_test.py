#!/usr/bin/env python3
"""
AnsFlow 并行执行性能测试（简化版）
在不依赖外部库的情况下测试并行组执行性能
"""

import asyncio
import time
import json
import sys
import os
import statistics
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime

@dataclass
class SimplePerformanceMetrics:
    """简化的性能指标"""
    execution_time: float
    parallel_groups_count: int
    total_steps_count: int
    max_parallel_workers: int
    success_rate: float
    avg_step_time: float
    max_step_time: float

class SimplePerformanceTester:
    """简化的性能测试器"""
    
    def __init__(self):
        self.test_results: List[SimplePerformanceMetrics] = []
        
    def create_test_pipeline(self, num_groups: int, steps_per_group: int) -> Dict[str, Any]:
        """创建测试用的流水线配置"""
        steps = []
        parallel_groups = []
        
        for group_idx in range(num_groups):
            group_id = f"test_group_{group_idx}"
            group = {
                'id': group_id,
                'name': f'并行组 {group_idx + 1}',
                'sync_policy': 'wait_all',
                'order': group_idx + 1,
                'timeout_seconds': 300
            }
            parallel_groups.append(group)
            
            for step_idx in range(steps_per_group):
                step_id = f"step_{group_idx}_{step_idx}"
                step = {
                    'id': step_id,
                    'name': f'测试步骤 {group_idx}-{step_idx}',
                    'type': 'test',
                    'order': group_idx + 1,
                    'parallel_group': group_id,
                    'estimated_duration': 0.1 + (step_idx * 0.05)
                }
                steps.append(step)
        
        return {
            'steps': steps,
            'parallel_groups': parallel_groups,
            'total_groups': num_groups,
            'total_steps': len(steps)
        }
    
    async def simulate_parallel_execution(self, pipeline_config: Dict[str, Any], 
                                        max_workers: int) -> SimplePerformanceMetrics:
        """模拟并行执行"""
        start_time = time.time()
        
        steps = pipeline_config['steps']
        parallel_groups = pipeline_config['parallel_groups']
        
        step_execution_times = []
        successful_steps = 0
        
        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                for group in parallel_groups:
                    group_steps = [s for s in steps if s.get('parallel_group') == group['id']]
                    
                    futures = []
                    for step in group_steps:
                        future = executor.submit(self._simulate_step_execution, step)
                        futures.append(future)
                    
                    for future in as_completed(futures):
                        try:
                            step_time = future.result(timeout=30)
                            step_execution_times.append(step_time)
                            successful_steps += 1
                        except Exception as e:
                            print(f"步骤执行失败: {e}")
        
        except Exception as e:
            print(f"并行执行失败: {e}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        success_rate = successful_steps / len(steps) if steps else 0
        avg_step_time = statistics.mean(step_execution_times) if step_execution_times else 0
        max_step_time = max(step_execution_times) if step_execution_times else 0
        
        return SimplePerformanceMetrics(
            execution_time=total_time,
            parallel_groups_count=len(parallel_groups),
            total_steps_count=len(steps),
            max_parallel_workers=max_workers,
            success_rate=success_rate,
            avg_step_time=avg_step_time,
            max_step_time=max_step_time
        )
    
    def _simulate_step_execution(self, step: Dict[str, Any]) -> float:
        """模拟单个步骤的执行"""
        start_time = time.time()
        
        execution_time = step.get('estimated_duration', 0.1)
        time.sleep(execution_time)
        
        # 模拟CPU操作
        result = 0
        for i in range(1000):
            result += i * i
        
        return time.time() - start_time
    
    async def run_comprehensive_test(self) -> List[SimplePerformanceMetrics]:
        """运行综合性能测试"""
        print("=" * 60)
        print("AnsFlow 并行执行性能测试（简化版）")
        print("=" * 60)
        
        test_configurations = [
            # (并行组数, 每组步骤数, 工作线程数)
            (1, 3, 4),
            (2, 4, 8),
            (3, 5, 8),
            (5, 3, 12),
            (8, 4, 16),
            (10, 3, 20),
        ]
        
        test_results = []
        
        for groups_count, steps_per_group, max_workers in test_configurations:
            print(f"\n🧪 测试配置: {groups_count}个并行组, {steps_per_group}步骤/组, {max_workers}个工作线程")
            
            iteration_results = []
            for iteration in range(3):  # 每个配置测试3次
                print(f"  迭代 {iteration + 1}/3", end=" ")
                
                pipeline_config = self.create_test_pipeline(groups_count, steps_per_group)
                
                try:
                    metrics = await asyncio.wait_for(
                        self.simulate_parallel_execution(pipeline_config, max_workers),
                        timeout=60
                    )
                    iteration_results.append(metrics)
                    
                    print(f"✅ {metrics.execution_time:.2f}s ({metrics.success_rate:.1%})")
                    
                except asyncio.TimeoutError:
                    print("❌ 超时")
                except Exception as e:
                    print(f"❌ 失败: {e}")
            
            # 计算平均值
            if iteration_results:
                avg_metrics = SimplePerformanceMetrics(
                    execution_time=statistics.mean([m.execution_time for m in iteration_results]),
                    parallel_groups_count=groups_count,
                    total_steps_count=groups_count * steps_per_group,
                    max_parallel_workers=max_workers,
                    success_rate=statistics.mean([m.success_rate for m in iteration_results]),
                    avg_step_time=statistics.mean([m.avg_step_time for m in iteration_results]),
                    max_step_time=max([m.max_step_time for m in iteration_results])
                )
                test_results.append(avg_metrics)
                
                print(f"  📊 平均性能: {avg_metrics.execution_time:.2f}s, {avg_metrics.success_rate:.1%}成功率")
        
        self.test_results = test_results
        return test_results
    
    def analyze_results(self) -> Dict[str, Any]:
        """分析测试结果"""
        if not self.test_results:
            return {'error': '没有测试结果'}
        
        # 性能趋势分析
        execution_times = [r.execution_time for r in self.test_results]
        success_rates = [r.success_rate for r in self.test_results]
        
        # 找到最佳配置
        best_time_result = min(self.test_results, key=lambda x: x.execution_time)
        best_success_result = max(self.test_results, key=lambda x: x.success_rate)
        
        # 可扩展性分析
        scalability_score = self._calculate_scalability_score()
        
        return {
            'performance_summary': {
                'avg_execution_time': statistics.mean(execution_times),
                'min_execution_time': min(execution_times),
                'max_execution_time': max(execution_times),
                'avg_success_rate': statistics.mean(success_rates),
                'min_success_rate': min(success_rates)
            },
            'best_configurations': {
                'fastest': {
                    'groups': best_time_result.parallel_groups_count,
                    'workers': best_time_result.max_parallel_workers,
                    'time': best_time_result.execution_time
                },
                'most_reliable': {
                    'groups': best_success_result.parallel_groups_count,
                    'workers': best_success_result.max_parallel_workers,
                    'success_rate': best_success_result.success_rate
                }
            },
            'scalability_score': scalability_score,
            'recommendations': self._generate_recommendations()
        }
    
    def _calculate_scalability_score(self) -> float:
        """计算可扩展性评分"""
        if len(self.test_results) < 2:
            return 50.0
        
        # 基于执行时间增长率计算
        execution_times = [r.execution_time for r in self.test_results]
        groups_counts = [r.parallel_groups_count for r in self.test_results]
        
        # 计算时间与组数的相关性
        time_variance = statistics.variance(execution_times)
        groups_variance = statistics.variance(groups_counts)
        
        # 理想情况下，时间增长应该与组数成比例
        # 评分基于时间稳定性和成功率
        avg_success_rate = statistics.mean([r.success_rate for r in self.test_results])
        
        base_score = avg_success_rate * 50  # 成功率贡献50分
        stability_score = max(0, 50 - time_variance * 10)  # 稳定性贡献50分
        
        return min(100.0, base_score + stability_score)
    
    def _generate_recommendations(self) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        if not self.test_results:
            return ["无法生成建议：缺少测试数据"]
        
        # 执行时间分析
        max_time = max([r.execution_time for r in self.test_results])
        if max_time > 10:
            recommendations.append(
                f"⏱️ 执行时间过长（最大 {max_time:.1f}s）：建议优化步骤并行度或增加工作线程"
            )
        
        # 成功率分析
        min_success_rate = min([r.success_rate for r in self.test_results])
        if min_success_rate < 0.9:
            recommendations.append(
                f"❌ 执行成功率偏低（最低 {min_success_rate:.1%}）：建议增加错误处理和重试机制"
            )
        
        # 工作线程优化
        worker_performance = {}
        for result in self.test_results:
            workers = result.max_parallel_workers
            if workers not in worker_performance:
                worker_performance[workers] = []
            worker_performance[workers].append(result.execution_time)
        
        if len(worker_performance) > 1:
            best_workers = min(worker_performance.keys(), 
                             key=lambda w: statistics.mean(worker_performance[w]))
            recommendations.append(
                f"🚀 最佳工作线程数配置：推荐使用 {best_workers} 个并行工作线程"
            )
        
        # 可扩展性建议
        scalability_score = self._calculate_scalability_score()
        if scalability_score < 60:
            recommendations.append(
                "📈 可扩展性待改进：考虑实施批处理和资源池管理"
            )
        
        return recommendations
    
    def generate_report(self) -> str:
        """生成测试报告"""
        if not self.test_results:
            return "没有可用的测试结果"
        
        analysis = self.analyze_results()
        
        report = []
        report.append("=" * 70)
        report.append("AnsFlow 并行执行性能测试报告")
        report.append("=" * 70)
        report.append(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"测试用例数: {len(self.test_results)}")
        report.append("")
        
        # 性能概览
        if 'performance_summary' in analysis:
            summary = analysis['performance_summary']
            report.append("📊 性能概览")
            report.append("-" * 40)
            report.append(f"平均执行时间: {summary['avg_execution_time']:.2f}s")
            report.append(f"最快执行时间: {summary['min_execution_time']:.2f}s")
            report.append(f"最慢执行时间: {summary['max_execution_time']:.2f}s")
            report.append(f"平均成功率: {summary['avg_success_rate']:.1%}")
            report.append(f"可扩展性评分: {analysis['scalability_score']:.1f}/100")
            report.append("")
        
        # 最佳配置
        if 'best_configurations' in analysis:
            best = analysis['best_configurations']
            report.append("🏆 最佳配置")
            report.append("-" * 40)
            report.append(f"最快配置: {best['fastest']['groups']}组/{best['fastest']['workers']}线程 "
                         f"({best['fastest']['time']:.2f}s)")
            report.append(f"最可靠配置: {best['most_reliable']['groups']}组/"
                         f"{best['most_reliable']['workers']}线程 "
                         f"({best['most_reliable']['success_rate']:.1%})")
            report.append("")
        
        # 优化建议
        if 'recommendations' in analysis:
            report.append("💡 优化建议")
            report.append("-" * 40)
            for recommendation in analysis['recommendations']:
                report.append(f"  • {recommendation}")
            report.append("")
        
        # 详细结果
        report.append("📋 详细测试结果")
        report.append("-" * 40)
        report.append(f"{'组数':<6} {'步骤数':<8} {'线程数':<8} {'执行时间':<10} {'成功率':<8} {'平均步骤时间':<12}")
        report.append("-" * 65)
        
        for result in self.test_results:
            steps_per_group = result.total_steps_count // result.parallel_groups_count
            report.append(f"{result.parallel_groups_count:<6} "
                         f"{steps_per_group:<8} "
                         f"{result.max_parallel_workers:<8} "
                         f"{result.execution_time:<10.2f} "
                         f"{result.success_rate:<8.1%} "
                         f"{result.avg_step_time:<12.3f}")
        
        report.append("")
        report.append("=" * 70)
        
        return "\n".join(report)

async def main():
    """主函数"""
    tester = SimplePerformanceTester()
    
    print("启动 AnsFlow 并行执行性能测试...")
    
    start_time = time.time()
    await tester.run_comprehensive_test()
    total_time = time.time() - start_time
    
    print(f"\n✅ 测试完成，总耗时: {total_time:.1f}s")
    
    # 生成报告
    report = tester.generate_report()
    
    # 保存到文件
    report_filename = f"ansflow_simple_performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    report_path = os.path.join(script_dir, report_filename)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📄 性能报告已保存到: {report_path}")
    print("\n" + report)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
