# Django shell命令，用于创建Docker注册表测试数据

# 导入必要的模块
from docker_integration.models import DockerRegistry, DockerRegistryProject
from django.contrib.auth.models import User

# 获取或创建用户
user = User.objects.first()
if not user:
    user = User.objects.create_user(username='admin', email='admin@example.com', password='admin123')
    print(f"创建用户: {user.username}")
else:
    print(f"使用现有用户: {user.username}")

# 创建Docker注册表数据
registries_data = [
    {
        'name': 'Docker Hub',
        'url': 'https://registry-1.docker.io',
        'registry_type': 'dockerhub',
        'username': '',
        'description': '官方Docker Hub注册表',
        'is_default': True,
        'created_by': user,
        'auth_config': {}
    },
    {
        'name': '私有注册表',
        'url': 'https://registry.example.com',
        'registry_type': 'private',
        'username': 'admin',
        'description': '私有Docker注册表',
        'is_default': False,
        'created_by': user,
        'auth_config': {'username': 'admin', 'password': 'password123'}
    },
    {
        'name': 'Harbor注册表',
        'url': 'https://harbor.company.com',
        'registry_type': 'harbor',
        'username': 'harbor_user',
        'description': '企业级Harbor注册表',
        'is_default': False,
        'created_by': user,
        'auth_config': {'username': 'harbor_user', 'password': 'harbor_pass'}
    }
]

# 创建注册表
for registry_data in registries_data:
    registry, created = DockerRegistry.objects.get_or_create(
        name=registry_data['name'],
        defaults=registry_data
    )
    if created:
        print(f"✅ 创建注册表: {registry.name}")
    else:
        print(f"ℹ️ 注册表已存在: {registry.name}")

# 获取创建的注册表
docker_hub = DockerRegistry.objects.get(name='Docker Hub')
private_registry = DockerRegistry.objects.get(name='私有注册表')

# 创建项目数据
projects_data = [
    {
        'name': 'my-web-app',
        'registry': docker_hub,
        'description': '前端Web应用项目',
        'is_default': False,
        'config': {'auto_build': True, 'visibility': 'public', 'tags': ['web', 'frontend', 'react']},
        'created_by': user
    },
    {
        'name': 'api-server',
        'registry': docker_hub,
        'description': '后端API服务项目',
        'is_default': False,
        'config': {'auto_build': True, 'visibility': 'private', 'tags': ['api', 'backend', 'django']},
        'created_by': user
    },
    {
        'name': 'company-app',
        'registry': private_registry,
        'description': '企业内部应用',
        'is_default': True,
        'config': {'auto_build': False, 'visibility': 'private', 'tags': ['internal', 'enterprise']},
        'created_by': user
    }
]

# 创建项目
for project_data in projects_data:
    project, created = DockerRegistryProject.objects.get_or_create(
        name=project_data['name'],
        registry=project_data['registry'],
        defaults=project_data
    )
    if created:
        print(f"✅ 创建项目: {project.registry.name}/{project.name}")
    else:
        print(f"ℹ️ 项目已存在: {project.registry.name}/{project.name}")

# 显示创建结果
print("\n📊 创建结果汇总:")
print(f"注册表总数: {DockerRegistry.objects.count()}")
print(f"项目总数: {DockerRegistryProject.objects.count()}")

for registry in DockerRegistry.objects.all():
    project_count = DockerRegistryProject.objects.filter(registry=registry).count()
    print(f"  {registry.name}: {project_count} 个项目")

print("\n✅ 测试数据创建完成！")
