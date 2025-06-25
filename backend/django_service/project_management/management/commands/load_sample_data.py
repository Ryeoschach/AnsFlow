from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from project_management.models import Project, ProjectMembership, Environment
from pipelines.models import Pipeline, PipelineStep


class Command(BaseCommand):
    help = 'Load sample data for AnsFlow CI/CD platform'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Loading sample data...'))
        
        # Create sample users
        users = []
        user_data = [
            {'username': 'admin', 'email': 'admin@ansflow.com', 'first_name': 'Admin', 'last_name': 'User', 'is_superuser': True},
            {'username': 'john_doe', 'email': 'john@ansflow.com', 'first_name': 'John', 'last_name': 'Doe'},
            {'username': 'jane_smith', 'email': 'jane@ansflow.com', 'first_name': 'Jane', 'last_name': 'Smith'},
            {'username': 'bob_wilson', 'email': 'bob@ansflow.com', 'first_name': 'Bob', 'last_name': 'Wilson'},
        ]
        
        for user_info in user_data:
            user, created = User.objects.get_or_create(
                username=user_info['username'],
                defaults=user_info
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'Created user: {user.username}')
            else:
                self.stdout.write(f'User already exists: {user.username}')
            users.append(user)
        
        admin_user, john_user, jane_user, bob_user = users
        
        # Create sample projects
        projects_data = [
            {
                'name': 'E-Commerce Platform',
                'description': 'A modern e-commerce platform built with Django and React',
                'visibility': 'private',
                'repository_url': 'https://github.com/ansflow/ecommerce-platform.git',
                'default_branch': 'main',
                'owner': john_user,
                'settings': {
                    'auto_build': True,
                    'notification_enabled': True,
                    'code_quality_checks': True
                }
            },
            {
                'name': 'Mobile API Gateway',
                'description': 'API gateway for mobile applications with rate limiting and authentication',
                'visibility': 'internal',
                'repository_url': 'https://github.com/ansflow/mobile-api-gateway.git',
                'default_branch': 'develop',
                'owner': jane_user,
                'settings': {
                    'auto_build': False,
                    'notification_enabled': True,
                    'security_scans': True
                }
            },
            {
                'name': 'Data Analytics Dashboard',
                'description': 'Real-time analytics dashboard for business intelligence',
                'visibility': 'public',
                'repository_url': 'https://github.com/ansflow/analytics-dashboard.git',
                'default_branch': 'main',
                'owner': bob_user,
                'settings': {
                    'auto_build': True,
                    'notification_enabled': False,
                    'performance_tests': True
                }
            },
        ]
        
        projects = []
        for project_data in projects_data:
            project, created = Project.objects.get_or_create(
                name=project_data['name'],
                defaults=project_data
            )
            if created:
                self.stdout.write(f'Created project: {project.name}')
                
                # Create project membership for owner
                ProjectMembership.objects.get_or_create(
                    project=project,
                    user=project.owner,
                    defaults={'role': 'owner'}
                )
            else:
                self.stdout.write(f'Project already exists: {project.name}')
            projects.append(project)
        
        ecommerce_project, api_gateway_project, analytics_project = projects
        
        # Add additional project members
        memberships_data = [
            # E-Commerce Platform members
            {'project': ecommerce_project, 'user': jane_user, 'role': 'maintainer'},
            {'project': ecommerce_project, 'user': bob_user, 'role': 'developer'},
            
            # Mobile API Gateway members
            {'project': api_gateway_project, 'user': john_user, 'role': 'developer'},
            {'project': api_gateway_project, 'user': admin_user, 'role': 'maintainer'},
            
            # Analytics Dashboard members
            {'project': analytics_project, 'user': jane_user, 'role': 'developer'},
        ]
        
        for membership_data in memberships_data:
            membership, created = ProjectMembership.objects.get_or_create(
                project=membership_data['project'],
                user=membership_data['user'],
                defaults={'role': membership_data['role']}
            )
            if created:
                self.stdout.write(f'Added {membership.user.username} to {membership.project.name} as {membership.role}')
        
        # Create environments for projects
        environments_data = [
            # E-Commerce Platform environments
            {'project': ecommerce_project, 'name': 'development', 'env_type': 'development', 'url': 'https://dev.ecommerce.ansflow.com', 'auto_deploy': True, 'deploy_branch': 'develop'},
            {'project': ecommerce_project, 'name': 'staging', 'env_type': 'staging', 'url': 'https://staging.ecommerce.ansflow.com', 'auto_deploy': True, 'deploy_branch': 'main'},
            {'project': ecommerce_project, 'name': 'production', 'env_type': 'production', 'url': 'https://ecommerce.ansflow.com', 'auto_deploy': False, 'deploy_branch': 'main'},
            
            # API Gateway environments
            {'project': api_gateway_project, 'name': 'testing', 'env_type': 'testing', 'url': 'https://test.api.ansflow.com', 'auto_deploy': True, 'deploy_branch': 'develop'},
            {'project': api_gateway_project, 'name': 'production', 'env_type': 'production', 'url': 'https://api.ansflow.com', 'auto_deploy': False, 'deploy_branch': 'main'},
            
            # Analytics Dashboard environments
            {'project': analytics_project, 'name': 'development', 'env_type': 'development', 'url': 'https://dev.analytics.ansflow.com', 'auto_deploy': True, 'deploy_branch': 'main'},
            {'project': analytics_project, 'name': 'production', 'env_type': 'production', 'url': 'https://analytics.ansflow.com', 'auto_deploy': False, 'deploy_branch': 'main'},
        ]
        
        for env_data in environments_data:
            environment, created = Environment.objects.get_or_create(
                project=env_data['project'],
                name=env_data['name'],
                defaults=env_data
            )
            if created:
                self.stdout.write(f'Created environment: {environment.project.name} - {environment.name}')
        
        # Create sample pipelines
        pipelines_data = [
            {
                'name': 'E-Commerce Build & Deploy',
                'description': 'Build, test and deploy e-commerce platform',
                'project': ecommerce_project,
                'created_by': john_user,
                'config': {
                    'triggers': ['push', 'pull_request'],
                    'branches': ['main', 'develop'],
                    'notifications': {
                        'slack': True,
                        'email': True
                    }
                }
            },
            {
                'name': 'API Gateway Security Pipeline',
                'description': 'Security scanning and deployment pipeline for API gateway',
                'project': api_gateway_project,
                'created_by': jane_user,
                'config': {
                    'triggers': ['push'],
                    'branches': ['main'],
                    'security_scans': True,
                    'performance_tests': True
                }
            },
            {
                'name': 'Analytics Data Pipeline',
                'description': 'Data processing and dashboard deployment pipeline',
                'project': analytics_project,
                'created_by': bob_user,
                'config': {
                    'triggers': ['schedule'],
                    'schedule': '0 2 * * *',  # Daily at 2 AM
                    'data_validation': True
                }
            },
        ]
        
        pipelines = []
        for pipeline_data in pipelines_data:
            pipeline, created = Pipeline.objects.get_or_create(
                name=pipeline_data['name'],
                project=pipeline_data['project'],
                defaults=pipeline_data
            )
            if created:
                self.stdout.write(f'Created pipeline: {pipeline.name}')
            pipelines.append(pipeline)
        
        # Create pipeline steps
        ecommerce_pipeline, api_pipeline, analytics_pipeline = pipelines
        
        steps_data = [
            # E-Commerce pipeline steps
            {'pipeline': ecommerce_pipeline, 'name': 'Checkout Code', 'command': 'git clone $REPO_URL .', 'order': 1},
            {'pipeline': ecommerce_pipeline, 'name': 'Install Dependencies', 'command': 'npm install && pip install -r requirements.txt', 'order': 2},
            {'pipeline': ecommerce_pipeline, 'name': 'Run Tests', 'command': 'npm test && python manage.py test', 'order': 3},
            {'pipeline': ecommerce_pipeline, 'name': 'Build Frontend', 'command': 'npm run build', 'order': 4},
            {'pipeline': ecommerce_pipeline, 'name': 'Deploy to Staging', 'command': 'docker build -t ecommerce:latest . && kubectl apply -f k8s/', 'order': 5},
            
            # API Gateway pipeline steps
            {'pipeline': api_pipeline, 'name': 'Code Checkout', 'command': 'git clone $REPO_URL .', 'order': 1},
            {'pipeline': api_pipeline, 'name': 'Security Scan', 'command': 'bandit -r . && safety check', 'order': 2},
            {'pipeline': api_pipeline, 'name': 'Unit Tests', 'command': 'pytest tests/', 'order': 3},
            {'pipeline': api_pipeline, 'name': 'Performance Tests', 'command': 'locust -f load_tests.py --headless', 'order': 4},
            {'pipeline': api_pipeline, 'name': 'Deploy', 'command': 'docker-compose up -d', 'order': 5},
            
            # Analytics pipeline steps
            {'pipeline': analytics_pipeline, 'name': 'Data Validation', 'command': 'python validate_data.py', 'order': 1},
            {'pipeline': analytics_pipeline, 'name': 'Process Data', 'command': 'python process_analytics.py', 'order': 2},
            {'pipeline': analytics_pipeline, 'name': 'Update Dashboard', 'command': 'python update_dashboard.py', 'order': 3},
            {'pipeline': analytics_pipeline, 'name': 'Send Reports', 'command': 'python send_reports.py', 'order': 4},
        ]
        
        for step_data in steps_data:
            step, created = PipelineStep.objects.get_or_create(
                pipeline=step_data['pipeline'],
                name=step_data['name'],
                defaults=step_data
            )
            if created:
                self.stdout.write(f'Created pipeline step: {step.pipeline.name} - {step.name}')
        
        self.stdout.write(
            self.style.SUCCESS(
                '\nSample data loaded successfully!\n'
                'Created:\n'
                f'- {len(users)} users\n'
                f'- {len(projects)} projects\n'
                f'- {len(pipelines)} pipelines\n'
                f'- Multiple environments and pipeline steps\n\n'
                'You can now log in with:\n'
                'Username: admin, Password: password123 (superuser)\n'
                'Username: john_doe, Password: password123\n'
                'Username: jane_smith, Password: password123\n'
                'Username: bob_wilson, Password: password123'
            )
        )
