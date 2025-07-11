# Generated by Django 4.2.23 on 2025-07-10 02:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('settings_management', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='apiendpoint',
            name='avg_response_time',
            field=models.FloatField(default=0, help_text='平均响应时间(ms)'),
        ),
        migrations.AddField(
            model_name='apiendpoint',
            name='call_count',
            field=models.IntegerField(default=0, help_text='调用次数'),
        ),
        migrations.AddField(
            model_name='apiendpoint',
            name='deprecated',
            field=models.BooleanField(default=False, help_text='是否废弃'),
        ),
        migrations.AddField(
            model_name='apiendpoint',
            name='examples',
            field=models.JSONField(default=dict, help_text='使用示例'),
        ),
        migrations.AddField(
            model_name='apiendpoint',
            name='last_called_at',
            field=models.DateTimeField(blank=True, help_text='最后调用时间', null=True),
        ),
        migrations.AddField(
            model_name='apiendpoint',
            name='parameters',
            field=models.JSONField(default=list, help_text='参数说明'),
        ),
        migrations.AddField(
            model_name='apiendpoint',
            name='request_schema',
            field=models.JSONField(default=dict, help_text='请求体Schema'),
        ),
        migrations.AddField(
            model_name='apiendpoint',
            name='response_schema',
            field=models.JSONField(default=dict, help_text='响应体Schema'),
        ),
        migrations.AddField(
            model_name='apiendpoint',
            name='service_type',
            field=models.CharField(choices=[('django', 'Django Service'), ('fastapi', 'FastAPI Service'), ('external', 'External API')], default='django', help_text='服务类型', max_length=20),
        ),
        migrations.AddField(
            model_name='apiendpoint',
            name='tags',
            field=models.JSONField(default=list, help_text='标签'),
        ),
        migrations.AddField(
            model_name='apiendpoint',
            name='version',
            field=models.CharField(default='v1', help_text='API版本', max_length=20),
        ),
        migrations.AlterField(
            model_name='apiendpoint',
            name='description',
            field=models.TextField(blank=True, help_text='端点描述'),
        ),
        migrations.AlterField(
            model_name='apiendpoint',
            name='method',
            field=models.CharField(choices=[('GET', 'GET'), ('POST', 'POST'), ('PUT', 'PUT'), ('DELETE', 'DELETE'), ('PATCH', 'PATCH'), ('OPTIONS', 'OPTIONS'), ('HEAD', 'HEAD')], help_text='HTTP方法', max_length=10),
        ),
        migrations.AlterField(
            model_name='apiendpoint',
            name='name',
            field=models.CharField(help_text='端点名称', max_length=200),
        ),
        migrations.AlterField(
            model_name='apiendpoint',
            name='path',
            field=models.CharField(help_text='API路径', max_length=500),
        ),
        migrations.AddIndex(
            model_name='apiendpoint',
            index=models.Index(fields=['service_type', 'is_enabled'], name='settings_ap_service_c30437_idx'),
        ),
        migrations.AddIndex(
            model_name='apiendpoint',
            index=models.Index(fields=['method', 'path'], name='settings_ap_method_74b72e_idx'),
        ),
    ]
