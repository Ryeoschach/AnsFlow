# Generated migration for adding credential support to AnsibleHost

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ansible_integration', '0001_initial'),  # 调整为实际的最新迁移
    ]

    operations = [
        migrations.AddField(
            model_name='ansiblehost',
            name='credential',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='ansible_integration.ansiblecredential',
                verbose_name='认证凭据'
            ),
        ),
        # 为了向后兼容，添加临时密码字段（加密存储）
        migrations.AddField(
            model_name='ansiblehost',
            name='temp_password',
            field=models.TextField(blank=True, verbose_name='临时密码（加密）'),
        ),
        migrations.AddField(
            model_name='ansiblehost',
            name='temp_ssh_key',
            field=models.TextField(blank=True, verbose_name='临时SSH密钥（加密）'),
        ),
    ]
