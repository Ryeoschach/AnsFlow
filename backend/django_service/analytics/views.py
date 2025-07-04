from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from datetime import timedelta, datetime
from pipelines.models import PipelineRun, Pipeline


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def execution_stats(request):
    """获取执行统计数据"""
    try:
        # 时间范围参数
        time_range = request.GET.get('time_range', '7d')
        
        # 计算时间范围
        if time_range == '1d':
            start_date = timezone.now() - timedelta(days=1)
        elif time_range == '7d':
            start_date = timezone.now() - timedelta(days=7)
        elif time_range == '30d':
            start_date = timezone.now() - timedelta(days=30)
        elif time_range == '90d':
            start_date = timezone.now() - timedelta(days=90)
        else:
            start_date = timezone.now() - timedelta(days=7)
        
        # 基础查询集
        executions = PipelineRun.objects.filter(created_at__gte=start_date)
        
        # 统计数据
        total_executions = executions.count()
        successful_executions = executions.filter(status='success').count()
        failed_executions = executions.filter(status='failed').count()
        running_executions = executions.filter(status='running').count()
        
        # 计算成功率
        success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
        
        # 计算平均执行时间（秒）
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
        
        stats = {
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'failed_executions': failed_executions,
            'running_executions': running_executions,
            'success_rate': round(success_rate, 1),
            'avg_duration': round(avg_duration),
            'total_duration': round(total_duration)
        }
        
        return Response(stats)
        
    except Exception as e:
        return Response({
            'error': str(e),
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'running_executions': 0,
            'success_rate': 0,
            'avg_duration': 0,
            'total_duration': 0
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def execution_trends(request):
    """获取执行趋势数据"""
    try:
        # 时间范围参数
        time_range = request.GET.get('time_range', '7d')
        
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
            date = timezone.now().date() - timedelta(days=days-1-i)
            start_datetime = timezone.make_aware(datetime.combine(date, datetime.min.time()))
            end_datetime = start_datetime + timedelta(days=1)
            
            day_executions = PipelineRun.objects.filter(
                created_at__gte=start_datetime,
                created_at__lt=end_datetime
            )
            
            total = day_executions.count()
            successful = day_executions.filter(status='success').count()
            failed = day_executions.filter(status='failed').count()
            success_rate = (successful / total * 100) if total > 0 else 0
            
            # 计算平均执行时间
            completed_day_executions = day_executions.filter(
                status__in=['success', 'failed'],
                started_at__isnull=False,
                completed_at__isnull=False
            )
            
            avg_duration = 0
            if completed_day_executions.exists():
                durations = []
                for execution in completed_day_executions:
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
        
    except Exception as e:
        return Response({'error': str(e), 'trends': []}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pipeline_stats(request):
    """获取流水线统计数据"""
    try:
        # 时间范围参数
        time_range = request.GET.get('time_range', '7d')
        
        if time_range == '1d':
            start_date = timezone.now() - timedelta(days=1)
        elif time_range == '7d':
            start_date = timezone.now() - timedelta(days=7)
        elif time_range == '30d':
            start_date = timezone.now() - timedelta(days=30)
        elif time_range == '90d':
            start_date = timezone.now() - timedelta(days=90)
        else:
            start_date = timezone.now() - timedelta(days=7)
        
        pipelines = Pipeline.objects.all()
        pipeline_stats = []
        
        for pipeline in pipelines:
            executions = PipelineRun.objects.filter(
                pipeline=pipeline,
                created_at__gte=start_date
            )
            
            total_executions = executions.count()
            successful_executions = executions.filter(status='success').count()
            success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
            
            # 计算平均执行时间
            completed_executions = executions.filter(
                status__in=['success', 'failed'],
                started_at__isnull=False,
                completed_at__isnull=False
            )
            
            avg_duration = 0
            if completed_executions.exists():
                durations = []
                for execution in completed_executions:
                    if execution.started_at and execution.completed_at:
                        duration = (execution.completed_at - execution.started_at).total_seconds()
                        durations.append(duration)
                
                if durations:
                    avg_duration = sum(durations) / len(durations)
            
            # 最后执行时间
            last_execution = executions.order_by('-created_at').first()
            last_execution_time = last_execution.created_at if last_execution else None
            last_execution_status = last_execution.status if last_execution else 'unknown'
            
            if total_executions > 0:  # 只返回有执行记录的流水线
                pipeline_stats.append({
                    'pipeline_id': pipeline.id,
                    'pipeline_name': pipeline.name,
                    'total_executions': total_executions,
                    'success_rate': round(success_rate, 1),
                    'avg_duration': round(avg_duration),
                    'last_execution': last_execution_time.isoformat() if last_execution_time else None,
                    'status': last_execution_status
                })
        
        # 按执行次数排序
        pipeline_stats.sort(key=lambda x: x['total_executions'], reverse=True)
        
        return Response(pipeline_stats)
        
    except Exception as e:
        return Response({'error': str(e), 'pipeline_stats': []}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recent_executions(request):
    """获取最近执行记录"""
    try:
        limit = int(request.GET.get('limit', 10))
        
        executions = PipelineRun.objects.select_related('pipeline').order_by('-created_at')[:limit]
        
        recent_executions = []
        for execution in executions:
            duration = None
            if execution.started_at and execution.completed_at:
                duration = (execution.completed_at - execution.started_at).total_seconds()
            
            recent_executions.append({
                'id': execution.id,
                'pipeline_name': execution.pipeline.name,
                'status': execution.status,
                'started_at': execution.started_at.isoformat() if execution.started_at else None,
                'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
                'duration': round(duration) if duration else None,
                'triggered_by': execution.created_by.username if execution.created_by else 'system'
            })
        
        return Response(recent_executions)
        
    except Exception as e:
        return Response({'error': str(e), 'recent_executions': []}, status=500)
