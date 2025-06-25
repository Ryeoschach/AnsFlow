"""
原子步骤管理视图
负责原子步骤的CRUD操作、测试、分类管理等功能
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view
from django.db.models import Q
import logging

from ..models import AtomicStep, CICDTool
from ..serializers import AtomicStepSerializer, AtomicStepSimpleSerializer
from ..services import cicd_engine

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(summary="List atomic steps", description="Get a list of atomic steps"),
    create=extend_schema(summary="Create atomic step", description="Create a new atomic step"),
    retrieve=extend_schema(summary="Get atomic step", description="Get a specific atomic step"),
    update=extend_schema(summary="Update atomic step", description="Update an atomic step"),
    destroy=extend_schema(summary="Delete atomic step", description="Delete an atomic step"),
)
class AtomicStepViewSet(viewsets.ModelViewSet):
    """原子步骤管理视图集"""
    
    queryset = AtomicStep.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action in ['list']:
            return AtomicStepSimpleSerializer
        return AtomicStepSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 根据类别过滤
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # 根据CI/CD工具类型过滤
        tool_type = self.request.query_params.get('tool_type')
        if tool_type:
            queryset = queryset.filter(supported_tools__contains=[tool_type])
        
        # 搜索
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(tags__icontains=search)
            )
        
        # 按是否启用过滤
        enabled = self.request.query_params.get('enabled')
        if enabled is not None:
            is_enabled = enabled.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_enabled=is_enabled)
        
        return queryset.order_by('category', 'name')
    
    def perform_create(self, serializer):
        """创建原子步骤"""
        serializer.save(created_by=self.request.user)
    
    @extend_schema(
        summary="Test atomic step",
        description="Test an atomic step with sample parameters",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'tool_id': {'type': 'string', 'description': 'CI/CD tool ID to test with'},
                    'parameters': {'type': 'object', 'description': 'Test parameters'}
                },
                'required': ['tool_id']
            }
        }
    )
    @action(detail=True, methods=['post'])
    async def test(self, request, pk=None):
        """测试原子步骤"""
        step = self.get_object()
        tool_id = request.data.get('tool_id')
        parameters = request.data.get('parameters', {})
        
        if not tool_id:
            return Response(
                {'error': 'tool_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            tool = CICDTool.objects.get(id=tool_id)
        except CICDTool.DoesNotExist:
            return Response(
                {'error': 'CI/CD tool not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 检查步骤是否支持该工具类型
        if tool.tool_type not in step.supported_tools:
            return Response(
                {'error': f'Step "{step.name}" does not support {tool.tool_type} tools'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 使用统一引擎测试步骤
            result = await cicd_engine.test_atomic_step(
                step=step,
                tool=tool,
                parameters=parameters,
                user=request.user
            )
            
            return Response({
                'step_id': step.id,
                'step_name': step.name,
                'tool_id': tool.id,
                'tool_name': tool.name,
                'test_result': result,
                'message': 'Atomic step test completed'
            })
            
        except Exception as e:
            logger.error(f"Failed to test atomic step {step.id}: {e}")
            return Response(
                {'error': f"Failed to test step: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Get step categories",
        description="Get available atomic step categories"
    )
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """获取原子步骤类别"""
        categories = AtomicStep.objects.values_list('category', flat=True).distinct()
        
        category_stats = []
        for category in categories:
            total_count = AtomicStep.objects.filter(category=category).count()
            enabled_count = AtomicStep.objects.filter(category=category, is_enabled=True).count()
            
            category_stats.append({
                'name': category,
                'total_count': total_count,
                'enabled_count': enabled_count,
                'disabled_count': total_count - enabled_count
            })
        
        return Response({
            'categories': category_stats,
            'total_categories': len(categories)
        })
    
    @extend_schema(
        summary="Validate step configuration",
        description="Validate step configuration without executing",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'parameters': {'type': 'object', 'description': 'Parameters to validate'},
                    'tool_type': {'type': 'string', 'description': 'Target tool type'}
                }
            }
        }
    )
    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        """验证步骤配置"""
        step = self.get_object()
        parameters = request.data.get('parameters', {})
        tool_type = request.data.get('tool_type')
        
        validation_result = {
            'step_id': step.id,
            'step_name': step.name,
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # 检查必需参数
            required_params = step.parameters.get('required', [])
            for param in required_params:
                if param not in parameters:
                    validation_result['errors'].append(f'Required parameter "{param}" is missing')
                    validation_result['is_valid'] = False
            
            # 检查工具类型支持
            if tool_type and tool_type not in step.supported_tools:
                validation_result['errors'].append(f'Step does not support tool type "{tool_type}"')
                validation_result['is_valid'] = False
            
            # 检查参数类型和格式
            param_schema = step.parameters.get('properties', {})
            for param_name, param_value in parameters.items():
                if param_name in param_schema:
                    expected_type = param_schema[param_name].get('type')
                    
                    # 简单的类型检查
                    if expected_type == 'string' and not isinstance(param_value, str):
                        validation_result['warnings'].append(f'Parameter "{param_name}" should be a string')
                    elif expected_type == 'integer' and not isinstance(param_value, int):
                        validation_result['warnings'].append(f'Parameter "{param_name}" should be an integer')
                    elif expected_type == 'boolean' and not isinstance(param_value, bool):
                        validation_result['warnings'].append(f'Parameter "{param_name}" should be a boolean')
            
            # 检查步骤是否启用
            if not step.is_enabled:
                validation_result['warnings'].append('Step is currently disabled')
            
            return Response(validation_result)
            
        except Exception as e:
            logger.error(f"Failed to validate step {step.id}: {e}")
            return Response(
                {'error': f"Failed to validate step: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Get step usage statistics",
        description="Get usage statistics for atomic steps"
    )
    @action(detail=False, methods=['get'])
    def usage_statistics(self, request):
        """获取原子步骤使用统计"""
        from django.db.models import Count
        from ..models import StepExecution
        
        # 统计每个步骤的使用次数
        step_usage = AtomicStep.objects.annotate(
            usage_count=Count('executions')
        ).order_by('-usage_count')[:20]  # 取前20个最常用的步骤
        
        # 按类别统计
        category_usage = {}
        for step in AtomicStep.objects.all():
            category = step.category
            if category not in category_usage:
                category_usage[category] = {
                    'total_steps': 0,
                    'total_executions': 0,
                    'enabled_steps': 0
                }
            
            category_usage[category]['total_steps'] += 1
            if step.is_enabled:
                category_usage[category]['enabled_steps'] += 1
            
            # 统计执行次数
            execution_count = StepExecution.objects.filter(step=step).count()
            category_usage[category]['total_executions'] += execution_count
        
        # 成功率统计
        success_stats = []
        for step in step_usage:
            total_executions = step.executions.count()
            if total_executions > 0:
                successful_executions = step.executions.filter(status='completed').count()
                success_rate = (successful_executions / total_executions) * 100
            else:
                success_rate = 0
            
            success_stats.append({
                'step_id': step.id,
                'step_name': step.name,
                'category': step.category,
                'total_executions': total_executions,
                'success_rate': round(success_rate, 2),
                'is_enabled': step.is_enabled
            })
        
        return Response({
            'most_used_steps': [
                {
                    'step_id': step.id,
                    'step_name': step.name,
                    'category': step.category,
                    'usage_count': step.usage_count,
                    'is_enabled': step.is_enabled
                }
                for step in step_usage
            ],
            'category_statistics': [
                {
                    'category': category,
                    **stats
                }
                for category, stats in category_usage.items()
            ],
            'success_rates': success_stats
        })
    
    @extend_schema(
        summary="Clone atomic step",
        description="Create a copy of an atomic step",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'new_name': {'type': 'string', 'description': 'Name for the cloned step'},
                    'new_description': {'type': 'string', 'description': 'Description for the cloned step'}
                },
                'required': ['new_name']
            }
        }
    )
    @action(detail=True, methods=['post'])
    def clone(self, request, pk=None):
        """克隆原子步骤"""
        original_step = self.get_object()
        new_name = request.data.get('new_name')
        new_description = request.data.get('new_description')
        
        if not new_name:
            return Response(
                {'error': 'new_name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 检查名称是否已存在
        if AtomicStep.objects.filter(name=new_name).exists():
            return Response(
                {'error': f'Step with name "{new_name}" already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 创建克隆步骤
            cloned_step = AtomicStep.objects.create(
                name=new_name,
                description=new_description or f"Cloned from {original_step.name}",
                category=original_step.category,
                script_content=original_step.script_content,
                parameters=original_step.parameters.copy(),
                supported_tools=original_step.supported_tools.copy(),
                tags=original_step.tags.copy(),
                is_enabled=False,  # 克隆的步骤默认禁用
                created_by=request.user
            )
            
            serializer = AtomicStepSerializer(cloned_step)
            return Response({
                'message': f'Step "{new_name}" cloned successfully from "{original_step.name}"',
                'original_step_id': original_step.id,
                'cloned_step': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Failed to clone step {original_step.id}: {e}")
            return Response(
                {'error': f"Failed to clone step: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
