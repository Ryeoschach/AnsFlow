#!/usr/bin/env python3
"""
AnsFlow 并行执行性能优化和压力测试
测试大规模并行组场景下的性能表现
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
from datetime import datetime, timedelta
import psutil
import gc

# 添加Django路径
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')

@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    execution_time: float
    memory_usage_mb: float
    cpu_usage_percent: float
    parallel_groups_count: int
    total_steps_count: int
    max_parallel_workers: int
    success_rate: float
    avg_step_time: float
    max_step_time: float
    min_step_time: float

@dataclass
class StressTestConfig:
    """压力测试配置"""
    parallel_groups_counts: List[int]
    steps_per_group_range: tuple
    max_workers_range: List[int]
    test_iterations: int
    timeout_seconds: int

class PerformanceOptimizer:
    """性能优化器"""
    
    def __init__(self):
        self.test_results: List[PerformanceMetrics] = []
        self.optimization_recommendations: List[str] = []
        
    def create_test_pipeline(self, num_groups: int, steps_per_group: int) -> Dict[str, Any]:
        """创建测试用的流水线配置"""
        steps = []
        parallel_groups = []
        
        # 创建并行组
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
            
            # 为每个组创建步骤
            for step_idx in range(steps_per_group):
                step_id = f"step_{group_idx}_{step_idx}"
                step = {
                    'id': step_id,
                    'name': f'测试步骤 {group_idx}-{step_idx}',
                    'type': 'test',
                    'order': group_idx + 1,
                    'parallel_group': group_id,
                    'parameters': {
                        'test_command': f'echo "执行步骤 {step_id}"; sleep {0.1 + (step_idx * 0.05)}; echo "完成"'
                    },
                    'estimated_duration': 0.1 + (step_idx * 0.05)
                }
                steps.append(step)
        
        return {
            'steps': steps,
            'parallel_groups': parallel_groups,
            'total_groups': num_groups,
            'total_steps': len(steps)
        }
    
    def monitor_system_resources(self) -> Dict[str, float]:
        """监控系统资源使用情况"""
        process = psutil.Process()
        
        return {
            'memory_mb': process.memory_info().rss / 1024 / 1024,
            'cpu_percent': process.cpu_percent(),
            'system_memory_percent': psutil.virtual_memory().percent,
            'system_cpu_percent': psutil.cpu_percent(interval=0.1)
        }
    
    async def simulate_parallel_execution(self, pipeline_config: Dict[str, Any], 
                                        max_workers: int) -> PerformanceMetrics:
        """模拟并行执行并收集性能指标"""
        start_time = time.time()
        start_resources = self.monitor_system_resources()
        
        steps = pipeline_config['steps']
        parallel_groups = pipeline_config['parallel_groups']
        
        step_execution_times = []
        successful_steps = 0
        
        try:
            # 使用ThreadPoolExecutor模拟并行执行
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 按组并行执行
                for group in parallel_groups:
                    group_steps = [s for s in steps if s.get('parallel_group') == group['id']]
                    
                    # 提交组内所有步骤到线程池
                    futures = []
                    for step in group_steps:
                        future = executor.submit(self._simulate_step_execution, step)
                        futures.append(future)
                    
                    # 等待组内所有步骤完成
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
        end_resources = self.monitor_system_resources()
        
        # 计算性能指标
        total_time = end_time - start_time
        avg_memory = (start_resources['memory_mb'] + end_resources['memory_mb']) / 2
        avg_cpu = (start_resources['cpu_percent'] + end_resources['cpu_percent']) / 2
        
        success_rate = successful_steps / len(steps) if steps else 0
        avg_step_time = statistics.mean(step_execution_times) if step_execution_times else 0
        max_step_time = max(step_execution_times) if step_execution_times else 0
        min_step_time = min(step_execution_times) if step_execution_times else 0
        
        return PerformanceMetrics(
            execution_time=total_time,
            memory_usage_mb=avg_memory,
            cpu_usage_percent=avg_cpu,
            parallel_groups_count=len(parallel_groups),
            total_steps_count=len(steps),
            max_parallel_workers=max_workers,
            success_rate=success_rate,
            avg_step_time=avg_step_time,
            max_step_time=max_step_time,
            min_step_time=min_step_time
        )
    
    def _simulate_step_execution(self, step: Dict[str, Any]) -> float:
        """模拟单个步骤的执行"""
        start_time = time.time()
        
        # 模拟执行时间
        execution_time = step.get('estimated_duration', 0.1)
        time.sleep(execution_time)
        
        # 模拟一些CPU密集型操作
        result = 0
        for i in range(1000):
            result += i * i
        
        return time.time() - start_time
    
    async def run_stress_test(self, config: StressTestConfig) -> List[PerformanceMetrics]:
        """运行压力测试"""
        print("=" * 60)
        print("AnsFlow 并行执行性能压力测试")
        print("=" * 60)
        
        test_results = []
        
        for groups_count in config.parallel_groups_counts:
            for max_workers in config.max_workers_range:
                print(f"\n🧪 测试配置: {groups_count}个并行组, {max_workers}个工作线程")
                
                iteration_results = []
                
                for iteration in range(config.test_iterations):
                    print(f"  迭代 {iteration + 1}/{config.test_iterations}")
                    
                    # 生成随机步骤数
                    import random
                    steps_per_group = random.randint(*config.steps_per_group_range)
                    
                    # 创建测试流水线
                    pipeline_config = self.create_test_pipeline(groups_count, steps_per_group)
                    
                    # 执行测试
                    try:
                        metrics = await asyncio.wait_for(
                            self.simulate_parallel_execution(pipeline_config, max_workers),
                            timeout=config.timeout_seconds
                        )
                        iteration_results.append(metrics)
                        
                        print(f"    ✅ 执行时间: {metrics.execution_time:.2f}s, "
                              f"成功率: {metrics.success_rate:.1%}, "
                              f"内存: {metrics.memory_usage_mb:.1f}MB")
                        
                    except asyncio.TimeoutError:
                        print(f"    ❌ 测试超时 ({config.timeout_seconds}s)")
                    except Exception as e:
                        print(f"    ❌ 测试失败: {e}")
                    
                    # 强制垃圾回收
                    gc.collect()
                    await asyncio.sleep(0.1)  # 短暂休息
                
                # 计算平均指标
                if iteration_results:
                    avg_metrics = self._calculate_average_metrics(iteration_results)
                    test_results.append(avg_metrics)
                    
                    print(f"  📊 平均性能: {avg_metrics.execution_time:.2f}s, "
                          f"{avg_metrics.memory_usage_mb:.1f}MB, "
                          f"{avg_metrics.success_rate:.1%} 成功率")
        
        self.test_results.extend(test_results)
        return test_results
    
    def _calculate_average_metrics(self, metrics_list: List[PerformanceMetrics]) -> PerformanceMetrics:
        """计算平均性能指标"""
        if not metrics_list:
            return PerformanceMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        return PerformanceMetrics(
            execution_time=statistics.mean([m.execution_time for m in metrics_list]),
            memory_usage_mb=statistics.mean([m.memory_usage_mb for m in metrics_list]),
            cpu_usage_percent=statistics.mean([m.cpu_usage_percent for m in metrics_list]),
            parallel_groups_count=metrics_list[0].parallel_groups_count,
            total_steps_count=metrics_list[0].total_steps_count,
            max_parallel_workers=metrics_list[0].max_parallel_workers,
            success_rate=statistics.mean([m.success_rate for m in metrics_list]),
            avg_step_time=statistics.mean([m.avg_step_time for m in metrics_list]),
            max_step_time=max([m.max_step_time for m in metrics_list]),
            min_step_time=min([m.min_step_time for m in metrics_list])
        )
    
    def analyze_performance_trends(self) -> Dict[str, Any]:
        """分析性能趋势并生成优化建议"""
        if not self.test_results:
            return {'error': '没有测试结果可供分析'}
        
        # 按并行组数量分组分析
        groups_performance = {}
        for result in self.test_results:
            key = f"{result.parallel_groups_count}groups"
            if key not in groups_performance:
                groups_performance[key] = []
            groups_performance[key].append(result)
        
        # 分析性能瓶颈
        analysis = {
            'performance_trends': {},
            'bottleneck_analysis': {},
            'optimization_recommendations': []
        }
        
        # 性能趋势分析
        for group_key, metrics_list in groups_performance.items():
            execution_times = [m.execution_time for m in metrics_list]
            memory_usage = [m.memory_usage_mb for m in metrics_list]
            success_rates = [m.success_rate for m in metrics_list]
            
            analysis['performance_trends'][group_key] = {
                'avg_execution_time': statistics.mean(execution_times),
                'execution_time_variance': statistics.variance(execution_times) if len(execution_times) > 1 else 0,
                'avg_memory_usage': statistics.mean(memory_usage),
                'avg_success_rate': statistics.mean(success_rates),
                'scalability_score': self._calculate_scalability_score(metrics_list)
            }
        
        # 瓶颈分析
        max_memory_result = max(self.test_results, key=lambda x: x.memory_usage_mb)
        max_time_result = max(self.test_results, key=lambda x: x.execution_time)
        min_success_result = min(self.test_results, key=lambda x: x.success_rate)
        
        analysis['bottleneck_analysis'] = {
            'memory_bottleneck': {
                'max_memory_mb': max_memory_result.memory_usage_mb,
                'config': f"{max_memory_result.parallel_groups_count}组/{max_memory_result.max_parallel_workers}线程"
            },
            'time_bottleneck': {
                'max_time_s': max_time_result.execution_time,
                'config': f"{max_time_result.parallel_groups_count}组/{max_time_result.max_parallel_workers}线程"
            },
            'reliability_bottleneck': {
                'min_success_rate': min_success_result.success_rate,
                'config': f"{min_success_result.parallel_groups_count}组/{min_success_result.max_parallel_workers}线程"
            }
        }
        
        # 生成优化建议
        analysis['optimization_recommendations'] = self._generate_optimization_recommendations()
        
        return analysis
    
    def _calculate_scalability_score(self, metrics_list: List[PerformanceMetrics]) -> float:
        """计算可扩展性评分（0-100）"""
        if len(metrics_list) < 2:
            return 50.0
        
        # 基于执行时间增长率和成功率稳定性计算
        execution_times = [m.execution_time for m in metrics_list]
        success_rates = [m.success_rate for m in metrics_list]
        
        # 时间增长率惩罚
        time_growth_penalty = statistics.variance(execution_times) * 10
        
        # 成功率稳定性奖励
        success_stability_bonus = statistics.mean(success_rates) * 50
        
        # 基础分数
        base_score = 50.0
        
        score = base_score + success_stability_bonus - time_growth_penalty
        return max(0.0, min(100.0, score))
    
    def _generate_optimization_recommendations(self) -> List[str]:
        """生成性能优化建议"""
        recommendations = []
        
        if not self.test_results:
            return ["无法生成建议：缺少测试数据"]
        
        # 内存使用分析
        avg_memory = statistics.mean([r.memory_usage_mb for r in self.test_results])
        if avg_memory > 500:
            recommendations.append(
                f"🔥 内存使用过高（平均 {avg_memory:.1f}MB）："
                "\n  - 实施步骤结果缓存机制"
                "\n  - 优化并行组批处理大小"
                "\n  - 考虑分批执行大型并行组"
            )
        
        # 执行时间分析
        max_time = max([r.execution_time for r in self.test_results])
        if max_time > 30:
            recommendations.append(
                f"⏱️ 执行时间过长（最大 {max_time:.1f}s）："
                "\n  - 增加并行工作线程数"
                "\n  - 优化步骤执行算法"
                "\n  - 实施异步执行模式"
            )
        
        # 成功率分析
        min_success_rate = min([r.success_rate for r in self.test_results])
        if min_success_rate < 0.9:
            recommendations.append(
                f"❌ 执行成功率偏低（最低 {min_success_rate:.1%}）："
                "\n  - 增加错误重试机制"
                "\n  - 实施熔断器模式"
                "\n  - 优化资源竞争处理"
            )
        
        # 可扩展性分析
        group_counts = [r.parallel_groups_count for r in self.test_results]
        if max(group_counts) > 10:
            recommendations.append(
                "📈 大规模并行组优化建议："
                "\n  - 实施分层并行调度"
                "\n  - 使用队列缓冲机制"
                "\n  - 考虑分布式执行架构"
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
                f"🚀 最佳工作线程数配置："
                f"\n  - 推荐使用 {best_workers} 个并行工作线程"
                f"\n  - 平均执行时间: {statistics.mean(worker_performance[best_workers]):.2f}s"
            )
        
        return recommendations
    
    def generate_performance_report(self) -> str:
        """生成性能测试报告"""
        if not self.test_results:
            return "没有可用的测试结果"
        
        analysis = self.analyze_performance_trends()
        
        report = []
        report.append("=" * 80)
        report.append("AnsFlow 并行执行性能测试报告")
        report.append("=" * 80)
        report.append(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"测试用例数: {len(self.test_results)}")
        report.append("")
        
        # 总体性能概览
        report.append("📊 总体性能概览")
        report.append("-" * 40)
        avg_exec_time = statistics.mean([r.execution_time for r in self.test_results])
        avg_memory = statistics.mean([r.memory_usage_mb for r in self.test_results])
        avg_success_rate = statistics.mean([r.success_rate for r in self.test_results])
        
        report.append(f"平均执行时间: {avg_exec_time:.2f}s")
        report.append(f"平均内存使用: {avg_memory:.1f}MB")
        report.append(f"平均成功率: {avg_success_rate:.1%}")
        report.append("")
        
        # 性能趋势分析
        if 'performance_trends' in analysis:
            report.append("📈 性能趋势分析")
            report.append("-" * 40)
            for group_key, trend in analysis['performance_trends'].items():
                report.append(f"{group_key}:")
                report.append(f"  执行时间: {trend['avg_execution_time']:.2f}s")
                report.append(f"  内存使用: {trend['avg_memory_usage']:.1f}MB")
                report.append(f"  成功率: {trend['avg_success_rate']:.1%}")
                report.append(f"  可扩展性评分: {trend['scalability_score']:.1f}/100")
                report.append("")
        
        # 瓶颈分析
        if 'bottleneck_analysis' in analysis:
            report.append("🔍 瓶颈分析")
            report.append("-" * 40)
            bottlenecks = analysis['bottleneck_analysis']
            
            report.append(f"内存瓶颈: {bottlenecks['memory_bottleneck']['max_memory_mb']:.1f}MB "
                         f"({bottlenecks['memory_bottleneck']['config']})")
            report.append(f"时间瓶颈: {bottlenecks['time_bottleneck']['max_time_s']:.2f}s "
                         f"({bottlenecks['time_bottleneck']['config']})")
            report.append(f"可靠性瓶颈: {bottlenecks['reliability_bottleneck']['min_success_rate']:.1%} "
                         f"({bottlenecks['reliability_bottleneck']['config']})")
            report.append("")
        
        # 优化建议
        if 'optimization_recommendations' in analysis:
            report.append("💡 性能优化建议")
            report.append("-" * 40)
            for recommendation in analysis['optimization_recommendations']:
                report.append(recommendation)
                report.append("")
        
        # 详细测试结果
        report.append("📋 详细测试结果")
        report.append("-" * 40)
        report.append(f"{'组数':<6} {'线程':<6} {'执行时间':<10} {'内存MB':<8} {'成功率':<8} {'平均步骤时间':<12}")
        report.append("-" * 70)
        
        for result in self.test_results:
            report.append(f"{result.parallel_groups_count:<6} "
                         f"{result.max_parallel_workers:<6} "
                         f"{result.execution_time:<10.2f} "
                         f"{result.memory_usage_mb:<8.1f} "
                         f"{result.success_rate:<8.1%} "
                         f"{result.avg_step_time:<12.3f}")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)

async def main():
    """主函数"""
    # 配置压力测试参数
    stress_config = StressTestConfig(
        parallel_groups_counts=[1, 3, 5, 8, 10, 15, 20],  # 不同的并行组数量
        steps_per_group_range=(2, 8),  # 每组步骤数范围
        max_workers_range=[4, 8, 12, 16],  # 不同的工作线程数
        test_iterations=3,  # 每种配置的迭代次数
        timeout_seconds=60  # 单次测试超时时间
    )
    
    # 创建性能优化器
    optimizer = PerformanceOptimizer()
    
    print("启动 AnsFlow 并行执行性能优化测试...")
    print(f"系统信息: CPU核心数={psutil.cpu_count()}, 内存={psutil.virtual_memory().total/1024/1024/1024:.1f}GB")
    print("")
    
    # 运行压力测试
    start_time = time.time()
    await optimizer.run_stress_test(stress_config)
    total_time = time.time() - start_time
    
    print(f"\n✅ 测试完成，总耗时: {total_time:.1f}s")
    
    # 生成并保存报告
    report = optimizer.generate_performance_report()
    
    # 保存到文件
    report_filename = f"ansflow_performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    report_path = os.path.join(script_dir, report_filename)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📄 性能报告已保存到: {report_path}")
    print("\n" + "=" * 80)
    print(report)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
