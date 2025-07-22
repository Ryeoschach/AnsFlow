"""
Docker 注册表关联服务
处理流水线步骤与 Docker 注册表的关联逻辑
"""

from typing import Dict, Any, List, Optional, Union
from django.core.exceptions import ValidationError
from django.db import transaction

from docker_integration.models import DockerRegistry
from pipelines.models import PipelineStep


class DockerRegistryAssociationService:
    """Docker 注册表关联服务"""
    
    @staticmethod
    def get_available_registries() -> List[Dict[str, Any]]:
        """
        获取可用的 Docker 注册表列表
        
        Returns:
            List[Dict[str, Any]]: 注册表列表
        """
        registries = DockerRegistry.objects.filter(
            status__in=['active', 'inactive']
        ).order_by('-is_default', 'name')
        
        return [
            {
                'id': registry.id,
                'name': registry.name,
                'url': registry.url,
                'registry_type': registry.registry_type,
                'status': registry.status,
                'is_default': registry.is_default,
                'description': registry.description,
                'created_at': registry.created_at.isoformat(),
            }
            for registry in registries
        ]
    
    @staticmethod
    def get_default_registry() -> Optional[Dict[str, Any]]:
        """
        获取默认 Docker 注册表
        
        Returns:
            Optional[Dict[str, Any]]: 默认注册表信息
        """
        try:
            registry = DockerRegistry.objects.get(is_default=True, status='active')
            return {
                'id': registry.id,
                'name': registry.name,
                'url': registry.url,
                'registry_type': registry.registry_type,
                'status': registry.status,
                'is_default': registry.is_default,
                'description': registry.description,
            }
        except DockerRegistry.DoesNotExist:
            return None
    
    @staticmethod
    def get_registry_by_step(step: PipelineStep) -> Optional[Dict[str, Any]]:
        """
        根据流水线步骤获取关联的注册表
        
        Args:
            step: 流水线步骤对象
            
        Returns:
            Optional[Dict[str, Any]]: 注册表信息
        """
        if step.docker_registry:
            registry = step.docker_registry
            return {
                'id': registry.id,
                'name': registry.name,
                'url': registry.url,
                'registry_type': registry.registry_type,
                'status': registry.status,
                'is_default': registry.is_default,
                'username': registry.username,
                'auth_config': registry.auth_config,
            }
        return None
    
    @staticmethod
    def associate_registry_to_step(step: PipelineStep, registry_id: Optional[int]) -> bool:
        """
        将注册表关联到流水线步骤
        
        Args:
            step: 流水线步骤对象
            registry_id: 注册表ID，None 表示取消关联
            
        Returns:
            bool: 关联是否成功
        """
        try:
            with transaction.atomic():
                if registry_id:
                    # 验证注册表是否存在且可用
                    registry = DockerRegistry.objects.get(id=registry_id)
                    if registry.status == 'error':
                        raise ValidationError(f"注册表 {registry.name} 状态异常，无法使用")
                    
                    step.docker_registry = registry
                else:
                    step.docker_registry = None
                
                step.save(update_fields=['docker_registry'])
                return True
                
        except DockerRegistry.DoesNotExist:
            raise ValidationError(f"注册表 ID {registry_id} 不存在")
        except Exception as e:
            raise ValidationError(f"关联注册表失败: {str(e)}")
    
    @staticmethod
    def get_registry_auth_info(registry: DockerRegistry) -> Dict[str, Any]:
        """
        获取注册表认证信息
        
        Args:
            registry: 注册表对象
            
        Returns:
            Dict[str, Any]: 认证信息
        """
        auth_info = {
            'url': registry.url,
            'username': registry.username,
            'registry_type': registry.registry_type,
        }
        
        # 根据注册表类型添加特定配置
        if registry.registry_type == 'dockerhub':
            auth_info['serveraddress'] = 'https://index.docker.io/v1/'
        elif registry.registry_type in ['aws_ecr', 'azure_acr', 'google_gcr']:
            # 云服务商注册表需要特殊认证处理
            auth_info['auth_config'] = registry.auth_config
        else:
            auth_info['serveraddress'] = registry.url
        
        return auth_info
    
    @staticmethod
    def validate_step_registry_compatibility(step: PipelineStep) -> List[str]:
        """
        验证步骤与注册表的兼容性
        
        Args:
            step: 流水线步骤对象
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 检查是否需要注册表
        if step.step_type in ['docker_push']:
            if not step.docker_registry:
                errors.append("Push 步骤必须配置 Docker 注册表")
            elif step.docker_registry.status != 'active':
                errors.append(f"注册表 {step.docker_registry.name} 状态不可用")
        
        # 检查镜像名称格式是否与注册表匹配
        if step.docker_registry and step.docker_image:
            registry_url = step.docker_registry.url
            image_name = step.docker_image
            
            # 如果是私有注册表，镜像名称应该包含注册表地址
            if (step.docker_registry.registry_type not in ['dockerhub'] and 
                not image_name.startswith(registry_url.replace('https://', '').replace('http://', ''))):
                errors.append(f"镜像名称 {image_name} 与注册表 {registry_url} 不匹配")
        
        return errors
    
    @staticmethod
    def auto_select_registry_for_step(step: PipelineStep) -> Optional[DockerRegistry]:
        """
        为步骤自动选择合适的注册表
        
        Args:
            step: 流水线步骤对象
            
        Returns:
            Optional[DockerRegistry]: 选择的注册表
        """
        # 如果步骤已经有注册表，直接返回
        if step.docker_registry:
            return step.docker_registry
        
        # 根据镜像名称推断注册表
        if step.docker_image:
            image_name = step.docker_image
            
            # 检查镜像名称是否包含注册表地址
            for registry in DockerRegistry.objects.filter(status='active'):
                registry_host = registry.url.replace('https://', '').replace('http://', '')
                if image_name.startswith(registry_host):
                    return registry
        
        # 返回默认注册表
        try:
            return DockerRegistry.objects.get(is_default=True, status='active')
        except DockerRegistry.DoesNotExist:
            return None
    
    @staticmethod
    def get_registry_usage_stats() -> Dict[str, Any]:
        """
        获取注册表使用统计
        
        Returns:
            Dict[str, Any]: 使用统计信息
        """
        from django.db.models import Count
        
        stats = {}
        
        # 按注册表统计步骤数量
        registry_usage = (
            PipelineStep.objects
            .values('docker_registry__name', 'docker_registry__id')
            .annotate(step_count=Count('id'))
            .filter(docker_registry__isnull=False)
        )
        
        stats['registry_usage'] = [
            {
                'registry_id': item['docker_registry__id'],
                'registry_name': item['docker_registry__name'],
                'step_count': item['step_count']
            }
            for item in registry_usage
        ]
        
        # 按步骤类型统计
        step_type_usage = (
            PipelineStep.objects
            .filter(docker_registry__isnull=False)
            .values('step_type')
            .annotate(step_count=Count('id'))
        )
        
        stats['step_type_usage'] = [
            {
                'step_type': item['step_type'],
                'step_count': item['step_count']
            }
            for item in step_type_usage
        ]
        
        # 总体统计
        stats['total_registries'] = DockerRegistry.objects.count()
        stats['active_registries'] = DockerRegistry.objects.filter(status='active').count()
        stats['steps_with_registry'] = PipelineStep.objects.filter(docker_registry__isnull=False).count()
        stats['steps_without_registry'] = PipelineStep.objects.filter(
            step_type__in=['docker_build', 'docker_run', 'docker_push', 'docker_pull'],
            docker_registry__isnull=True
        ).count()
        
        return stats
    
    @staticmethod
    def suggest_registry_for_image(image_name: str) -> List[Dict[str, Any]]:
        """
        根据镜像名称推荐合适的注册表
        
        Args:
            image_name: 镜像名称
            
        Returns:
            List[Dict[str, Any]]: 推荐的注册表列表
        """
        suggestions = []
        
        # 获取所有可用注册表
        registries = DockerRegistry.objects.filter(status='active')
        
        for registry in registries:
            score = 0
            reason = []
            
            # 检查镜像名称是否包含注册表地址
            registry_host = registry.url.replace('https://', '').replace('http://', '')
            if image_name.startswith(registry_host):
                score += 10
                reason.append("镜像名称匹配注册表地址")
            
            # 默认注册表优先级
            if registry.is_default:
                score += 5
                reason.append("默认注册表")
            
            # 根据注册表类型评分
            if registry.registry_type == 'dockerhub' and '/' not in image_name:
                score += 8
                reason.append("官方镜像适合 Docker Hub")
            elif registry.registry_type in ['private', 'harbor'] and '/' in image_name:
                score += 6
                reason.append("私有镜像适合私有注册表")
            
            # 注册表状态
            if registry.status == 'active':
                score += 3
                reason.append("注册表状态正常")
            
            if score > 0:
                suggestions.append({
                    'registry_id': registry.id,
                    'registry_name': registry.name,
                    'registry_url': registry.url,
                    'registry_type': registry.registry_type,
                    'score': score,
                    'reasons': reason
                })
        
        # 按评分排序
        suggestions.sort(key=lambda x: x['score'], reverse=True)
        
        return suggestions[:3]  # 返回前3个推荐
    
    @staticmethod
    def update_step_image_with_registry(step: PipelineStep, registry: DockerRegistry) -> str:
        """
        根据注册表更新步骤的镜像名称
        
        Args:
            step: 流水线步骤对象
            registry: 注册表对象
            
        Returns:
            str: 更新后的镜像名称
        """
        if not step.docker_image:
            return ''
        
        image_name = step.docker_image
        registry_host = registry.url.replace('https://', '').replace('http://', '')
        
        # 如果是 Docker Hub，不需要添加前缀
        if registry.registry_type == 'dockerhub':
            # 移除其他注册表的前缀（如果有）
            if '/' in image_name and not image_name.startswith('library/'):
                parts = image_name.split('/', 1)
                if '.' in parts[0] or ':' in parts[0]:  # 可能是注册表地址
                    image_name = parts[1]
        else:
            # 私有注册表需要添加前缀
            if not image_name.startswith(registry_host):
                # 移除其他注册表前缀
                if '/' in image_name:
                    parts = image_name.split('/', 1)
                    if '.' in parts[0] or ':' in parts[0]:  # 是注册表地址
                        image_name = parts[1]
                
                # 添加当前注册表前缀
                image_name = f"{registry_host}/{image_name}"
        
        return image_name
