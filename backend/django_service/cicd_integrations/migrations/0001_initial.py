# Generated by Django 4.2.23 on 2025-06-25 06:23

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('pipelines', '0002_auto_20250625_1159'),
        ('project_management', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AtomicStep',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='步骤名称', max_length=255)),
                ('step_type', models.CharField(choices=[('fetch_code', 'Fetch Code'), ('build', 'Build'), ('test', 'Test'), ('security_scan', 'Security Scan'), ('deploy', 'Deploy'), ('notify', 'Notify'), ('custom', 'Custom')], help_text='步骤类型', max_length=50)),
                ('description', models.TextField(blank=True, help_text='步骤描述')),
                ('parameters', models.JSONField(default=dict, help_text='步骤参数配置')),
                ('conditions', models.JSONField(default=dict, help_text='执行条件')),
                ('is_public', models.BooleanField(default=False, help_text='是否为公共步骤')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='atomic_steps', to=settings.AUTH_USER_MODEL)),
                ('dependencies', models.ManyToManyField(blank=True, help_text='依赖的步骤', related_name='dependent_steps', to='cicd_integrations.atomicstep')),
            ],
            options={
                'verbose_name': 'Atomic Step',
                'verbose_name_plural': 'Atomic Steps',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='CICDTool',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='工具实例名称', max_length=255)),
                ('tool_type', models.CharField(choices=[('jenkins', 'Jenkins'), ('gitlab_ci', 'GitLab CI'), ('circleci', 'CircleCI'), ('github_actions', 'GitHub Actions'), ('azure_devops', 'Azure DevOps'), ('custom', 'Custom Tool')], help_text='工具类型', max_length=50)),
                ('base_url', models.URLField(help_text='工具服务器基础URL')),
                ('username', models.CharField(blank=True, help_text='用户名', max_length=255)),
                ('token', models.CharField(help_text='API令牌或密码', max_length=500)),
                ('config', models.JSONField(default=dict, help_text='工具特定配置')),
                ('metadata', models.JSONField(default=dict, help_text='额外的元数据')),
                ('status', models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive'), ('error', 'Error')], default='active', max_length=20)),
                ('last_health_check', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_tools', to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(help_text='关联项目', on_delete=django.db.models.deletion.CASCADE, related_name='cicd_tools', to='project_management.project')),
            ],
            options={
                'verbose_name': 'CI/CD Tool',
                'verbose_name_plural': 'CI/CD Tools',
                'ordering': ['-created_at'],
                'unique_together': {('project', 'name')},
            },
        ),
        migrations.CreateModel(
            name='PipelineExecution',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('external_id', models.CharField(help_text='外部工具中的执行ID', max_length=255)),
                ('external_url', models.URLField(blank=True, help_text='外部工具中的执行URL')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('running', 'Running'), ('success', 'Success'), ('failed', 'Failed'), ('cancelled', 'Cancelled'), ('timeout', 'Timeout')], default='pending', max_length=20)),
                ('trigger_type', models.CharField(choices=[('manual', 'Manual'), ('webhook', 'Webhook'), ('schedule', 'Schedule'), ('api', 'API')], default='manual', max_length=20)),
                ('definition', models.JSONField(default=dict, help_text='执行时的流水线定义')),
                ('parameters', models.JSONField(default=dict, help_text='执行参数')),
                ('logs', models.TextField(blank=True, help_text='执行日志')),
                ('artifacts', models.JSONField(default=list, help_text='构建产物')),
                ('test_results', models.JSONField(default=dict, help_text='测试结果')),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('trigger_data', models.JSONField(default=dict, help_text='触发时的数据')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('cicd_tool', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='executions', to='cicd_integrations.cicdtool')),
                ('pipeline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='executions', to='pipelines.pipeline')),
                ('triggered_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='triggered_executions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Pipeline Execution',
                'verbose_name_plural': 'Pipeline Executions',
                'ordering': ['-created_at'],
                'unique_together': {('cicd_tool', 'external_id')},
            },
        ),
        migrations.CreateModel(
            name='StepExecution',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('external_id', models.CharField(blank=True, help_text='外部工具中的步骤ID', max_length=255)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('running', 'Running'), ('success', 'Success'), ('failed', 'Failed'), ('skipped', 'Skipped'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('order', models.IntegerField(help_text='执行顺序')),
                ('logs', models.TextField(blank=True, help_text='步骤日志')),
                ('output', models.JSONField(default=dict, help_text='步骤输出')),
                ('error_message', models.TextField(blank=True, help_text='错误信息')),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('atomic_step', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='executions', to='cicd_integrations.atomicstep')),
                ('pipeline_execution', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='step_executions', to='cicd_integrations.pipelineexecution')),
            ],
            options={
                'verbose_name': 'Step Execution',
                'verbose_name_plural': 'Step Executions',
                'ordering': ['order'],
                'unique_together': {('pipeline_execution', 'order')},
            },
        ),
    ]
