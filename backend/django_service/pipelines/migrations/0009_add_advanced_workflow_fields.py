# Generated manually for advanced workflow features
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pipelines', '0008_update_default_step_type'),
    ]

    operations = [
        # 为PipelineStep添加高级工作流字段
        migrations.AddField(
            model_name='pipelinestep',
            name='dependencies',
            field=models.JSONField(default=list, help_text='List of step IDs this step depends on'),
        ),
        migrations.AddField(
            model_name='pipelinestep',
            name='parallel_group',
            field=models.CharField(blank=True, help_text='Parallel execution group name', max_length=100),
        ),
        migrations.AddField(
            model_name='pipelinestep',
            name='conditions',
            field=models.JSONField(default=list, help_text='Execution conditions'),
        ),
        migrations.AddField(
            model_name='pipelinestep',
            name='approval_required',
            field=models.BooleanField(default=False, help_text='Whether this step requires approval'),
        ),
        migrations.AddField(
            model_name='pipelinestep',
            name='approval_users',
            field=models.JSONField(default=list, help_text='List of usernames who can approve'),
        ),
        migrations.AddField(
            model_name='pipelinestep',
            name='approval_status',
            field=models.CharField(blank=True, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('timeout', 'Timeout')], help_text='Approval status', max_length=20),
        ),
        migrations.AddField(
            model_name='pipelinestep',
            name='approved_by',
            field=models.CharField(blank=True, help_text='Username of approver', max_length=100),
        ),
        migrations.AddField(
            model_name='pipelinestep',
            name='approved_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='pipelinestep',
            name='retry_policy',
            field=models.JSONField(default=dict, help_text='Retry configuration'),
        ),
        migrations.AddField(
            model_name='pipelinestep',
            name='notification_config',
            field=models.JSONField(default=dict, help_text='Notification configuration'),
        ),
        
        # 创建新的模型
        migrations.CreateModel(
            name='ParallelGroup',
            fields=[
                ('id', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('sync_policy', models.CharField(choices=[('wait_all', 'Wait All'), ('wait_any', 'Wait Any'), ('fail_fast', 'Fail Fast')], default='wait_all', max_length=20)),
                ('timeout_seconds', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('pipeline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='parallel_groups', to='pipelines.pipeline')),
            ],
            options={
                'verbose_name': 'Parallel Group',
                'verbose_name_plural': 'Parallel Groups',
            },
        ),
        
        migrations.CreateModel(
            name='ApprovalRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('execution_id', models.CharField(help_text='Pipeline execution ID', max_length=100)),
                ('requester_username', models.CharField(help_text='Username of the requester', max_length=100)),
                ('approvers', models.JSONField(default=list, help_text='List of approved usernames')),
                ('required_approvals', models.IntegerField(default=1)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('timeout', 'Timeout')], default='pending', max_length=20)),
                ('approval_message', models.TextField(blank=True)),
                ('timeout_hours', models.IntegerField(blank=True, null=True)),
                ('auto_approve_on_timeout', models.BooleanField(default=False)),
                ('approved_by', models.CharField(blank=True, max_length=100)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('response_comment', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('pipeline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='approval_requests', to='pipelines.pipeline')),
                ('step', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='approval_requests', to='pipelines.pipelinestep')),
            ],
            options={
                'verbose_name': 'Approval Request',
                'verbose_name_plural': 'Approval Requests',
            },
        ),
        
        migrations.CreateModel(
            name='WorkflowExecution',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('execution_id', models.CharField(max_length=100, unique=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('running', 'Running'), ('success', 'Success'), ('failed', 'Failed'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('trigger_data', models.JSONField(default=dict)),
                ('context_variables', models.JSONField(default=dict, help_text='Workflow context variables')),
                ('step_results', models.JSONField(default=dict, help_text='Results from each step')),
                ('failed_steps', models.JSONField(default=list, help_text='List of failed step IDs')),
                ('pending_approvals', models.JSONField(default=list, help_text='List of step IDs waiting for approval')),
                ('recovery_point', models.IntegerField(blank=True, help_text='Step ID to resume from', null=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('pipeline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workflow_executions', to='pipelines.pipeline')),
                ('current_step', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='pipelines.pipelinestep')),
            ],
            options={
                'verbose_name': 'Workflow Execution',
                'verbose_name_plural': 'Workflow Executions',
            },
        ),
        
        migrations.CreateModel(
            name='StepExecutionHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('running', 'Running'), ('success', 'Success'), ('failed', 'Failed'), ('skipped', 'Skipped')], default='pending', max_length=20)),
                ('retry_count', models.IntegerField(default=0)),
                ('max_retries', models.IntegerField(default=0)),
                ('logs', models.TextField(blank=True)),
                ('error_message', models.TextField(blank=True)),
                ('output_data', models.JSONField(default=dict)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('duration_seconds', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('workflow_execution', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='step_histories', to='pipelines.workflowexecution')),
                ('step', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pipelines.pipelinestep')),
            ],
            options={
                'verbose_name': 'Step Execution History',
                'verbose_name_plural': 'Step Execution Histories',
                'ordering': ['-created_at'],
            },
        ),
    ]
