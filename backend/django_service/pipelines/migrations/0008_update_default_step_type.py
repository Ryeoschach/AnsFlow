# Generated by Django 4.2.23 on 2025-07-04 06:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pipelines', '0007_remove_command_step_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pipelinestep',
            name='step_type',
            field=models.CharField(choices=[('fetch_code', 'Code Fetch'), ('build', 'Build'), ('test', 'Test Execution'), ('security_scan', 'Security Scan'), ('deploy', 'Deployment'), ('ansible', 'Ansible Playbook'), ('notify', 'Notification'), ('custom', 'Custom Step'), ('script', 'Script Execution')], default='custom', help_text='Type of step to execute', max_length=20),
        ),
    ]
