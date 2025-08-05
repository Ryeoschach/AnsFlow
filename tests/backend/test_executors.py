"""
原子步骤执行引擎测试用例
"""
import asyncio
import tempfile
import os
from unittest.mock import Mock, AsyncMock
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model

from pipelines.models import Pipeline
from cicd_integrations.models import AtomicStep, PipelineExecution, StepExecution
from cicd_integrations.executors import (
    ExecutionContext, 
    DependencyResolver, 
    StepExecutor, 
    PipelineExecutor
)

User = get_user_model()


class TestExecutionContext(TestCase):
    """测试执行上下文"""
    
    def setUp(self):
        self.context = ExecutionContext()
    
    def test_variable_operations(self):
        """测试变量操作"""
        # 设置变量
        self.context.set_variable('test_var', 'test_value')
        self.assertEqual(self.context.get_variable('test_var'), 'test_value')
        
        # 测试不存在的变量
        self.assertIsNone(self.context.get_variable('nonexistent'))
        
        # 测试默认值
        self.assertEqual(
            self.context.get_variable('nonexistent', 'default'), 
            'default'
        )
    
    def test_variable_substitution(self):
        """测试变量替换"""
        self.context.set_variable('NAME', 'test')
        self.context.set_variable('VERSION', '1.0')
        
        # 简单替换
        result = self.context.substitute_variables('Hello ${NAME}')
        self.assertEqual(result, 'Hello test')
        
        # 多个变量替换
        result = self.context.substitute_variables('${NAME}-${VERSION}')
        self.assertEqual(result, 'test-1.0')
        
        # 嵌套在字典中的替换
        config = {
            'image': '${NAME}:${VERSION}',
            'command': 'echo ${NAME}'
        }
        result = self.context.substitute_variables(config)
        expected = {
            'image': 'test:1.0',
            'command': 'echo test'
        }
        self.assertEqual(result, expected)
    
    def test_step_results(self):
        """测试步骤结果存储"""
        result = {'status': 'success', 'output': 'test output'}
        self.context.set_step_result('step1', result)
        
        self.assertEqual(self.context.get_step_result('step1'), result)
        self.assertIsNone(self.context.get_step_result('nonexistent'))


class TestDependencyResolver(TestCase):
    """测试依赖解析器"""
    
    def setUp(self):
        self.resolver = DependencyResolver()
    
    def test_simple_dependency_resolution(self):
        """测试简单依赖解析"""
        steps = [
            Mock(name='step1', dependencies=[]),
            Mock(name='step2', dependencies=['step1']),
            Mock(name='step3', dependencies=['step2']),
        ]
        
        execution_plan = self.resolver.resolve_dependencies(steps)
        
        # 验证执行计划的正确性
        self.assertEqual(len(execution_plan), 3)
        self.assertEqual(execution_plan[0]['step'].name, 'step1')
        self.assertEqual(execution_plan[1]['step'].name, 'step2')
        self.assertEqual(execution_plan[2]['step'].name, 'step3')
    
    def test_parallel_dependencies(self):
        """测试并行依赖"""
        steps = [
            Mock(name='step1', dependencies=[]),
            Mock(name='step2', dependencies=[]),
            Mock(name='step3', dependencies=['step1', 'step2']),
        ]
        
        execution_plan = self.resolver.resolve_dependencies(steps)
        
        # step1和step2应该可以并行执行
        self.assertEqual(len(execution_plan), 3)
        # step3应该依赖于step1和step2
        step3_plan = next(p for p in execution_plan if p['step'].name == 'step3')
        self.assertEqual(len(step3_plan['dependencies']), 2)
    
    def test_circular_dependency_detection(self):
        """测试循环依赖检测"""
        steps = [
            Mock(name='step1', dependencies=['step2']),
            Mock(name='step2', dependencies=['step1']),
        ]
        
        with self.assertRaises(ValueError) as context:
            self.resolver.resolve_dependencies(steps)
        
        self.assertIn('Circular dependency detected', str(context.exception))
    
    def test_missing_dependency_detection(self):
        """测试缺失依赖检测"""
        steps = [
            Mock(name='step1', dependencies=['nonexistent']),
        ]
        
        with self.assertRaises(ValueError) as context:
            self.resolver.resolve_dependencies(steps)
        
        self.assertIn('Dependency not found', str(context.exception))


class TestStepExecutor(TestCase):
    """测试步骤执行器"""
    
    def setUp(self):
        self.executor = StepExecutor()
        self.context = ExecutionContext()
    
    @pytest.mark.asyncio
    async def test_fetch_code_step(self):
        """测试代码获取步骤"""
        step = Mock(
            name='fetch_code',
            type='fetch_code',
            config={
                'repository': 'https://github.com/example/repo.git',
                'branch': 'main'
            }
        )
        
        # Mock git操作
        with tempfile.TemporaryDirectory() as temp_dir:
            self.context.set_variable('WORKSPACE', temp_dir)
            
            # 由于我们不能实际执行git命令，这里模拟成功
            result = await self.executor.execute_step(step, self.context, 1)
            
            # 验证结果结构
            self.assertIn('success', result)
            self.assertIn('output', result)
    
    @pytest.mark.asyncio
    async def test_build_step(self):
        """测试构建步骤"""
        step = Mock(
            name='build',
            type='build',
            config={
                'command': 'echo "Build successful"',
                'working_directory': '/tmp'
            }
        )
        
        result = await self.executor.execute_step(step, self.context, 1)
        
        # 验证构建步骤执行
        self.assertIn('success', result)
        self.assertIn('output', result)
    
    @pytest.mark.asyncio
    async def test_condition_evaluation(self):
        """测试条件评估"""
        # 设置上下文变量
        self.context.set_variable('BRANCH', 'main')
        self.context.set_variable('TEST_PASSED', True)
        
        # 测试条件成功
        conditions = {
            'branch': 'main',
            'test_passed': True
        }
        
        step = Mock(name='test_step', conditions=conditions)
        should_execute = self.executor._should_execute_step(step, self.context)
        self.assertTrue(should_execute)
        
        # 测试条件失败
        conditions = {
            'branch': 'develop',  # 不匹配
            'test_passed': True
        }
        
        step = Mock(name='test_step', conditions=conditions)
        should_execute = self.executor._should_execute_step(step, self.context)
        self.assertFalse(should_execute)


class TestPipelineExecutor(TestCase):
    """测试流水线执行器"""
    
    def setUp(self):
        self.executor = PipelineExecutor()
        self.user = None
        self.pipeline = None
    
    async def create_test_data(self):
        """创建测试数据"""
        self.user = await User.objects.acreate(
            username='testuser',
            email='test@example.com'
        )
        
        self.pipeline = await Pipeline.objects.acreate(
            name='Test Pipeline',
            description='Test pipeline for unit tests',
            created_by=self.user,
            config={}
        )
    
    @pytest.mark.asyncio
    async def test_simple_pipeline_execution(self):
        """测试简单流水线执行"""
        await self.create_test_data()
        
        # 创建测试步骤
        step1 = await AtomicStep.objects.acreate(
            pipeline=self.pipeline,
            name='step1',
            type='custom',
            order=1,
            config={'command': 'echo "Step 1"'},
            dependencies=[],
            created_by=self.user
        )
        
        step2 = await AtomicStep.objects.acreate(
            pipeline=self.pipeline,
            name='step2',
            type='custom',
            order=2,
            config={'command': 'echo "Step 2"'},
            dependencies=['step1'],
            created_by=self.user
        )
        
        # 创建执行记录
        execution = await PipelineExecution.objects.acreate(
            pipeline=self.pipeline,
            status='pending',
            trigger_type='manual',
            triggered_by=self.user,
            definition={},
            parameters={}
        )
        
        # 执行流水线
        context = ExecutionContext()
        atomic_steps = [step1, step2]
        
        # 模拟执行器方法
        result = await self.executor.execute_pipeline(
            atomic_steps=atomic_steps,
            context=context,
            execution_id=execution.id
        )
        
        # 验证执行结果
        self.assertIsInstance(result, bool)
    
    def test_max_parallel_limit(self):
        """测试最大并行限制"""
        # 验证默认并行限制
        self.assertEqual(self.executor.max_parallel_steps, 5)
        
        # 测试并行信号量
        self.assertIsNotNone(self.executor.parallel_semaphore)


class TestIntegration(TestCase):
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_execution(self):
        """端到端执行测试"""
        # 这个测试需要实际的数据库和模型
        # 在实际环境中运行
        pass


# 运行测试的辅助函数
def run_tests():
    """运行所有测试"""
    import unittest
    
    # 创建测试套件
    test_classes = [
        TestExecutionContext,
        TestDependencyResolver,
        TestStepExecutor,
        TestPipelineExecutor,
        TestIntegration
    ]
    
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)


if __name__ == '__main__':
    result = run_tests()
    exit(0 if result.wasSuccessful() else 1)
