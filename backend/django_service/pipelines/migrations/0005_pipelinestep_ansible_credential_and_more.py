# Generated by Django 4.2.23 on 2025-07-04 03:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ansible_integration', '0002_ansibleexecution_pipeline_and_more'),
        ('pipelines', '0004_pipeline_execution_mode_pipeline_execution_tool_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='pipelinestep',
            name='ansible_credential',
            field=models.ForeignKey(blank=True, help_text='Ansible credential to use (for ansible step type)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pipeline_steps', to='ansible_integration.ansiblecredential'),
        ),
        migrations.AddField(
            model_name='pipelinestep',
            name='ansible_inventory',
            field=models.ForeignKey(blank=True, help_text='Ansible inventory to use (for ansible step type)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pipeline_steps', to='ansible_integration.ansibleinventory'),
        ),
        migrations.AddField(
            model_name='pipelinestep',
            name='ansible_parameters',
            field=models.JSONField(default=dict, help_text='Additional parameters for Ansible execution'),
        ),
        migrations.AddField(
            model_name='pipelinestep',
            name='ansible_playbook',
            field=models.ForeignKey(blank=True, help_text='Ansible playbook to execute (for ansible step type)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pipeline_steps', to='ansible_integration.ansibleplaybook'),
        ),
        migrations.AddField(
            model_name='pipelinestep',
            name='step_type',
            field=models.CharField(choices=[('command', 'Shell Command'), ('ansible', 'Ansible Playbook'), ('script', 'Script Execution'), ('deploy', 'Deployment'), ('test', 'Test Execution')], default='command', help_text='Type of step to execute', max_length=20),
        ),
        migrations.AlterField(
            model_name='pipelinestep',
            name='command',
            field=models.TextField(blank=True, help_text='Command or script to execute'),
        ),
    ]
