from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from pipelines.models import PipelineRun
from ..models import CICDTool


class AnalyticsViewSet(viewsets.ViewSet):
    """数据分析API视图集"""
    
    @action(detail=False, methods=['get'])
    def execution_stats(self, request):
        """获取执行统计数据"""
        time_range = request.GET.get('time_range', '7d')
        
        # 计算时间范围
        end_date = timezone.now()
        if time_range == '1d':
            start_date = end_date - timedelta(days=1)
        elif time_range == '7d':
            start_date = end_date - timedelta(days=7)
        elif time_range == '30d':
            start_date = end_date - timedelta(days=30)
        elif time_range == '90d':
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=7)
        
        # 查询指定时间范围内的执行记录
        executions = PipelineRun.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        # 计算统计数据
        total_executions = executions.count()
        successful_executions = executions.filter(status='success').count()
        failed_executions = executions.filter(status='failed').count()
        running_executions = executions.filter(status='running').count()
        
        success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
        
        # 计算平均执行时间
        completed_executions = executions.filter(
            status__in=['success', 'failed'],
            started_at__isnull=False,
            completed_at__isnull=False
        )
        
        avg_duration = 0
        total_duration = 0
        if completed_executions.exists():
            durations = []
            for execution in completed_executions:
                if execution.started_at and execution.completed_at:
                    duration = (execution.completed_at - execution.started_at).total_seconds()
                    durations.append(duration)
            
            if durations:
                avg_duration = sum(durations) / len(durations)
                total_duration = sum(durations)
        
        return Response({
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'failed_executions': failed_executions,
            'running_executions': running_executions,
            'success_rate': round(success_rate, 1),
            'avg_duration': round(avg_duration),
            'total_duration': round(total_duration)
        })
    
    @action(detail=False, methods=['get'])
    def execution_trends(self, request):
        """获取执行趋势数据"""
        time_range = request.GET.get('time_range', '7d')
        
        # 计算时间范围
        end_date = timezone.now().date()
        if time_range == '1d':
            days = 1
        elif time_range == '7d':
            days = 7
        elif time_range == '30d':
            days = 30
        elif time_range == '90d':
            days = 90
        else:
            days = 7
        
        trends = []
        for i in range(days):
            date = end_date - timedelta(days=days-1-i)
            
            # 查询当天的执行记录
            day_executions = PipelineRun.objects.filter(
                created_at__date=date
            )
            
            total = day_executions.count()
            successful = day_executions.filter(status='success').count()
            failed = day_executions.filter(status='failed').count()
            success_rate = (successful / total * 100) if total > 0 else 0
            
            # 计算当天平均执行时间
            completed = day_executions.filter(
                status__in=['success', 'failed'],
                started_at__isnull=False,
                completed_at__isnull=False
            )
            
            avg_duration = 0
            if completed.exists():
                durations = []
                for execution in completed:
                    if execution.started_at and execution.completed_at:
                        duration = (execution.completed_at - execution.started_at).total_seconds()
                        durations.append(duration)
                
                if durations:
                    avg_duration = sum(durations) / len(durations)
            
            trends.append({
                'date': date.isoformat(),
                'total': total,
                'successful': successful,
                'failed': failed,
                'success_rate': round(success_rate, 1),
                'avg_duration': round(avg_duration)
            })
        
        return Response(trends)
    
    @action(detail=False, methods=['get'])
    def pipeline_stats(self, request):
        """获取流水线统计数据"""
        from pipelines.models import Pipeline
        
        pipelines = Pipeline.objects.all()
        stats = []
        
        for pipeline in pipelines:
            executions = pipeline.pipelinerun_set.all()
            total_executions = executions.count()
            
            if total_executions > 0:
                successful = executions.filter(status='success').count()
                success_rate = (successful / total_executions * 100)
                
                # 计算平均执行时间
                completed = executions.filter(
                    status__in=['success', 'failed'],
                    started_at__isnull=False,
                    completed_at__isnull=False
                )
                
                avg_duration = 0
                if completed.exists():
                    durations = []
                    for execution in completed:
                        if execution.started_at and execution.completed_at:
                            duration = (execution.completed_at - execution.started_at).total_seconds()
                            durations.append(duration)
                    
                    if durations:
                        avg_duration = sum(durations) / len(durations)
                
                # 获取最近执行和状态
                last_execution = executions.order_by('-created_at').first()
                last_execution_time = last_execution.created_at if last_execution else timezone.now()
                last_status = last_execution.status if last_execution else 'unknown'
                
                stats.append({
                    'pipeline_id': pipeline.id,
                    'pipeline_name': pipeline.name,
                    'total_executions': total_executions,
                    'success_rate': round(success_rate, 1),
                    'avg_duration': round(avg_duration),
                    'last_execution': last_execution_time.isoformat(),
                    'status': last_status
                })
        
        # 按执行次数排序
        stats.sort(key=lambda x: x['total_executions'], reverse=True)
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def recent_executions(self, request):
        """获取最近执行记录"""
        limit = int(request.GET.get('limit', 10))
        
        executions = PipelineRun.objects.select_related('pipeline').order_by('-created_at')[:limit]
        
        results = []
        for execution in executions:
            duration = None
            if execution.started_at and execution.completed_at:
                duration = (execution.completed_at - execution.started_at).total_seconds()
            
            results.append({
                'id': execution.id,
                'pipeline_name': execution.pipeline.name if execution.pipeline else f'Pipeline {execution.pipeline_id}',
                'status': execution.status,
                'started_at': execution.started_at.isoformat() if execution.started_at else execution.created_at.isoformat(),
                'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
                'duration': round(duration) if duration else None,
                'triggered_by': execution.triggered_by if hasattr(execution, 'triggered_by') else 'system'
            })
        
        return Response(results)
