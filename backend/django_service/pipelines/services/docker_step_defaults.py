"""
Docker 流水线步骤默认参数配置
统一管理不同 Docker 步骤类型的默认参数和配置
"""

from typing import Dict, Any, List, Optional


class DockerStepDefaults:
    """Docker 步骤默认参数管理器"""
    
    @staticmethod
    def get_step_defaults(step_type: str) -> Dict[str, Any]:
        """
        获取指定步骤类型的默认参数
        
        Args:
            step_type: 步骤类型 (docker_build, docker_run, docker_push, docker_pull)
            
        Returns:
            Dict[str, Any]: 默认参数配置
        """
        defaults_map = {
            'docker_build': DockerStepDefaults._get_docker_build_defaults(),
            'docker_run': DockerStepDefaults._get_docker_run_defaults(),
            'docker_push': DockerStepDefaults._get_docker_push_defaults(),
            'docker_pull': DockerStepDefaults._get_docker_pull_defaults(),
        }
        
        return defaults_map.get(step_type, {})
    
    @staticmethod
    def _get_docker_build_defaults() -> Dict[str, Any]:
        """Docker Build 步骤默认参数"""
        return {
            'docker_tag': 'latest',
            'docker_config': {
                'dockerfile_path': 'Dockerfile',
                'context_path': '.',
                'target_stage': '',
                'platform': 'linux/amd64',
                'no_cache': False,
                'pull': True,
                'force_rm': True,
                'build_args': {},
                'labels': {},
                'network_mode': 'default',
                'extra_hosts': [],
                'shm_size': '64m',
                'isolation': '',
                'cpu_period': 0,
                'cpu_quota': 0,
                'cpu_shares': 0,
                'cpuset_cpus': '',
                'cpuset_mems': '',
                'memory': '',
                'memswap': '',
                'memory_swappiness': -1,
                'oom_kill_disable': False,
                'oom_score_adj': 0,
                'pids_limit': 0,
                'ulimits': [],
                'use_config_proxy': True,
                'squash': False,
                'cache_from': [],
                'compress': False,
                'security_opt': [],
                'shmsize': 67108864,
                'dockerfile_inline': ''
            },
            'timeout_seconds': 1800,  # 30 分钟
            'environment_vars': {
                'DOCKER_BUILDKIT': '1',
                'BUILDKIT_PROGRESS': 'plain'
            }
        }
    
    @staticmethod
    def _get_docker_run_defaults() -> Dict[str, Any]:
        """Docker Run 步骤默认参数"""
        return {
            'docker_tag': 'latest',
            'docker_config': {
                'container_name': '',
                'command': '',
                'entrypoint': [],
                'working_dir': '',
                'user': '',
                'environment': {},
                'ports': {},
                'volumes': [],
                'network_mode': 'default',
                'network': '',
                'hostname': '',
                'domainname': '',
                'mac_address': '',
                'extra_hosts': [],
                'dns': [],
                'dns_search': [],
                'dns_opt': [],
                'security_opt': [],
                'cap_add': [],
                'cap_drop': [],
                'privileged': False,
                'publish_all_ports': False,
                'read_only': False,
                'tmpfs': {},
                'ulimits': [],
                'log_config': {
                    'type': 'json-file',
                    'config': {}
                },
                'healthcheck': {},
                'stdin_open': False,
                'tty': False,
                'detach': True,
                'remove': True,
                'auto_remove': True,
                'stop_signal': 'SIGTERM',
                'stop_timeout': 10,
                'restart_policy': {
                    'Name': 'no',
                    'MaximumRetryCount': 0
                },
                'runtime': '',
                'sysctls': {},
                'cpu_count': 0,
                'cpu_percent': 0,
                'cpu_period': 0,
                'cpu_quota': 0,
                'cpu_rt_period': 0,
                'cpu_rt_runtime': 0,
                'cpu_shares': 0,
                'cpuset_cpus': '',
                'cpuset_mems': '',
                'device_cgroup_rules': [],
                'device_read_bps': [],
                'device_write_bps': [],
                'device_read_iops': [],
                'device_write_iops': [],
                'devices': [],
                'disk_quota': 0,
                'kernel_memory': '',
                'memory': '',
                'memory_reservation': '',
                'memory_swap': '',
                'memory_swappiness': -1,
                'nano_cpus': 0,
                'oom_kill_disable': False,
                'oom_score_adj': 0,
                'pid_mode': '',
                'pids_limit': 0,
                'platform': '',
                'shm_size': '64m',
                'storage_opt': {},
                'group_add': [],
                'ipc_mode': '',
                'isolation': '',
                'links': [],
                'name': '',
                'uts_mode': '',
                'volumes_from': []
            },
            'timeout_seconds': 3600,  # 60 分钟
            'environment_vars': {}
        }
    
    @staticmethod
    def _get_docker_push_defaults() -> Dict[str, Any]:
        """Docker Push 步骤默认参数"""
        return {
            'docker_tag': 'latest',
            'docker_config': {
                'registry_url': '',
                'username': '',
                'password': '',
                'auth_config': {},
                'insecure_registry': False,
                'decode': True,
                'platform': '',
                'all_tags': False,
                'tag': '',
                'stream': True,
                'decode': True
            },
            'timeout_seconds': 1800,  # 30 分钟
            'environment_vars': {}
        }
    
    @staticmethod
    def _get_docker_pull_defaults() -> Dict[str, Any]:
        """Docker Pull 步骤默认参数"""
        return {
            'docker_tag': 'latest',
            'docker_config': {
                'registry_url': '',
                'username': '',
                'password': '',
                'auth_config': {},
                'insecure_registry': False,
                'platform': '',
                'all_tags': False,
                'stream': True,
                'decode': True
            },
            'timeout_seconds': 1800,  # 30 分钟
            'environment_vars': {}
        }
    
    @staticmethod
    def get_registry_defaults() -> Dict[str, Any]:
        """获取注册表的默认配置"""
        return {
            'dockerhub': {
                'url': 'https://registry-1.docker.io',
                'registry_type': 'dockerhub',
                'description': 'Docker Hub 官方镜像仓库'
            },
            'aliyun_acr': {
                'url': 'registry.cn-hangzhou.aliyuncs.com',
                'registry_type': 'aliyun_acr',
                'description': '阿里云容器镜像服务'
            },
            'tencent_tcr': {
                'url': 'ccr.ccs.tencentyun.com',
                'registry_type': 'tencent_tcr',
                'description': '腾讯云容器镜像服务'
            },
            'aws_ecr': {
                'url': '',  # 需要根据区域和账户ID设置
                'registry_type': 'aws_ecr',
                'description': 'AWS Elastic Container Registry'
            },
            'azure_acr': {
                'url': '',  # 需要根据注册表名称设置
                'registry_type': 'azure_acr',
                'description': 'Azure Container Registry'
            },
            'google_gcr': {
                'url': 'gcr.io',
                'registry_type': 'google_gcr',
                'description': 'Google Container Registry'
            },
            'harbor': {
                'url': '',  # 需要根据部署地址设置
                'registry_type': 'harbor',
                'description': 'Harbor 企业级容器镜像仓库'
            },
            'private': {
                'url': '',  # 需要根据实际地址设置
                'registry_type': 'private',
                'description': '私有容器镜像仓库'
            }
        }
    
    @staticmethod
    def get_step_required_fields(step_type: str) -> List[str]:
        """
        获取指定步骤类型的必填字段
        
        Args:
            step_type: 步骤类型
            
        Returns:
            List[str]: 必填字段列表
        """
        required_fields_map = {
            'docker_build': ['docker_image', 'docker_config.dockerfile_path'],
            'docker_run': ['docker_image'],
            'docker_push': ['docker_image', 'docker_registry'],
            'docker_pull': ['docker_image'],
        }
        
        return required_fields_map.get(step_type, [])
    
    @staticmethod
    def get_step_optional_fields(step_type: str) -> List[str]:
        """
        获取指定步骤类型的可选字段
        
        Args:
            step_type: 步骤类型
            
        Returns:
            List[str]: 可选字段列表
        """
        optional_fields_map = {
            'docker_build': [
                'docker_tag', 'docker_config.context_path', 'docker_config.target_stage',
                'docker_config.platform', 'docker_config.build_args', 'docker_config.labels'
            ],
            'docker_run': [
                'docker_tag', 'docker_config.container_name', 'docker_config.command',
                'docker_config.ports', 'docker_config.volumes', 'docker_config.environment'
            ],
            'docker_push': [
                'docker_tag', 'docker_config.platform', 'docker_config.all_tags'
            ],
            'docker_pull': [
                'docker_tag', 'docker_config.platform', 'docker_config.all_tags'
            ],
        }
        
        return optional_fields_map.get(step_type, [])
    
    @staticmethod
    def get_step_validation_rules(step_type: str) -> Dict[str, Any]:
        """
        获取指定步骤类型的验证规则
        
        Args:
            step_type: 步骤类型
            
        Returns:
            Dict[str, Any]: 验证规则配置
        """
        validation_rules_map = {
            'docker_build': {
                'docker_image': {
                    'required': True,
                    'pattern': r'^[a-z0-9]+([-._][a-z0-9]+)*$',
                    'message': '镜像名称格式不正确'
                },
                'docker_tag': {
                    'pattern': r'^[a-zA-Z0-9]+([-._][a-zA-Z0-9]+)*$',
                    'message': '镜像标签格式不正确'
                }
            },
            'docker_run': {
                'docker_image': {
                    'required': True,
                    'pattern': r'^[a-z0-9]+([-._][a-z0-9]+)*$',
                    'message': '镜像名称格式不正确'
                }
            },
            'docker_push': {
                'docker_image': {
                    'required': True,
                    'pattern': r'^[a-z0-9]+([-._][a-z0-9]+)*$',
                    'message': '镜像名称格式不正确'
                },
                'docker_registry': {
                    'required': True,
                    'message': '必须选择 Docker 注册表'
                }
            },
            'docker_pull': {
                'docker_image': {
                    'required': True,
                    'pattern': r'^[a-z0-9]+([-._][a-z0-9]+)*$',
                    'message': '镜像名称格式不正确'
                }
            }
        }
        
        return validation_rules_map.get(step_type, {})
    
    @staticmethod
    def get_step_help_text(step_type: str) -> Dict[str, str]:
        """
        获取指定步骤类型的帮助文本
        
        Args:
            step_type: 步骤类型
            
        Returns:
            Dict[str, str]: 帮助文本配置
        """
        help_text_map = {
            'docker_build': {
                'docker_image': '镜像名称，例如: myapp, company/myapp',
                'docker_tag': '镜像标签，例如: latest, v1.0.0, develop',
                'dockerfile_path': 'Dockerfile 的路径，相对于构建上下文',
                'context_path': '构建上下文路径，包含 Dockerfile 和相关文件的目录',
                'target_stage': '多阶段构建的目标阶段名称',
                'platform': '目标平台，例如: linux/amd64, linux/arm64',
                'build_args': '构建参数，用于传递给 Dockerfile 中的 ARG 指令'
            },
            'docker_run': {
                'docker_image': '要运行的容器镜像名称',
                'docker_tag': '镜像标签，默认为 latest',
                'container_name': '容器名称，用于标识运行中的容器',
                'command': '容器启动时执行的命令',
                'ports': '端口映射，格式: {"宿主机端口": "容器端口"}',
                'volumes': '卷挂载，格式: [{"host": "宿主机路径", "container": "容器路径"}]',
                'environment': '环境变量，格式: {"变量名": "变量值"}'
            },
            'docker_push': {
                'docker_image': '要推送的镜像名称',
                'docker_tag': '镜像标签，默认为 latest',
                'docker_registry': '目标注册表，必须先在设置中配置',
                'all_tags': '是否推送镜像的所有标签'
            },
            'docker_pull': {
                'docker_image': '要拉取的镜像名称',
                'docker_tag': '镜像标签，默认为 latest',
                'docker_registry': '源注册表，可选择已配置的注册表',
                'all_tags': '是否拉取镜像的所有标签'
            }
        }
        
        return help_text_map.get(step_type, {})
    
    @staticmethod
    def merge_with_defaults(step_type: str, step_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将步骤数据与默认值合并
        
        Args:
            step_type: 步骤类型
            step_data: 步骤数据
            
        Returns:
            Dict[str, Any]: 合并后的数据
        """
        defaults = DockerStepDefaults.get_step_defaults(step_type)
        merged_data = defaults.copy()
        
        # 深度合并 docker_config
        if 'docker_config' in step_data and 'docker_config' in merged_data:
            merged_data['docker_config'].update(step_data['docker_config'])
            step_data = step_data.copy()
            del step_data['docker_config']
        
        # 合并其他字段
        merged_data.update(step_data)
        
        return merged_data
    
    @staticmethod
    def get_common_docker_images() -> List[Dict[str, str]]:
        """获取常用的 Docker 镜像列表"""
        return [
            {'name': 'node', 'description': 'Node.js 运行时环境', 'tags': ['18', '16', '14', 'alpine', 'latest']},
            {'name': 'python', 'description': 'Python 运行时环境', 'tags': ['3.11', '3.10', '3.9', 'alpine', 'latest']},
            {'name': 'nginx', 'description': 'Nginx Web 服务器', 'tags': ['1.24', '1.22', 'alpine', 'latest']},
            {'name': 'redis', 'description': 'Redis 内存数据库', 'tags': ['7', '6', 'alpine', 'latest']},
            {'name': 'mysql', 'description': 'MySQL 数据库', 'tags': ['8.0', '5.7', 'latest']},
            {'name': 'postgres', 'description': 'PostgreSQL 数据库', 'tags': ['15', '14', '13', 'alpine', 'latest']},
            {'name': 'openjdk', 'description': 'OpenJDK Java 运行时', 'tags': ['17', '11', '8', 'alpine', 'latest']},
            {'name': 'golang', 'description': 'Go 编程语言', 'tags': ['1.20', '1.19', 'alpine', 'latest']},
            {'name': 'alpine', 'description': 'Alpine Linux 基础镜像', 'tags': ['3.18', '3.17', 'latest']},
            {'name': 'ubuntu', 'description': 'Ubuntu Linux 系统', 'tags': ['22.04', '20.04', '18.04', 'latest']},
            {'name': 'centos', 'description': 'CentOS Linux 系统', 'tags': ['7', '8', 'latest']},
            {'name': 'busybox', 'description': '轻量级 Unix 工具集', 'tags': ['1.35', 'latest']},
        ]
