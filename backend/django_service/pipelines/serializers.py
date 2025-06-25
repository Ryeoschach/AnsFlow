from rest_framework import serializers
from .models import Pipeline, PipelineStep, PipelineRun


class PipelineStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = PipelineStep
        fields = [
            'id', 'name', 'description', 'status', 'command', 
            'environment_vars', 'timeout_seconds', 'order',
            'output_log', 'error_log', 'exit_code',
            'started_at', 'completed_at'
        ]
        read_only_fields = ['id', 'output_log', 'error_log', 'exit_code', 'started_at', 'completed_at']


class PipelineRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = PipelineRun
        fields = [
            'id', 'run_number', 'status', 'triggered_by', 'trigger_type',
            'trigger_data', 'started_at', 'completed_at', 'created_at', 'artifacts'
        ]
        read_only_fields = ['id', 'run_number', 'triggered_by', 'started_at', 'completed_at', 'created_at']


class PipelineSerializer(serializers.ModelSerializer):
    steps = PipelineStepSerializer(many=True, read_only=True)
    runs = PipelineRunSerializer(many=True, read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Pipeline
        fields = [
            'id', 'name', 'description', 'status', 'config',
            'project', 'project_name', 'created_by', 'created_by_username',
            'created_at', 'updated_at', 'started_at', 'completed_at',
            'steps', 'runs'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at', 'started_at', 'completed_at']
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class PipelineListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views"""
    project_name = serializers.CharField(source='project.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    steps_count = serializers.IntegerField(source='steps.count', read_only=True)
    runs_count = serializers.IntegerField(source='runs.count', read_only=True)
    
    class Meta:
        model = Pipeline
        fields = [
            'id', 'name', 'description', 'status',
            'project', 'project_name', 'created_by_username',
            'created_at', 'updated_at', 'steps_count', 'runs_count'
        ]
