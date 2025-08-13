"""
Kubernetes Token 智能管理器
解决 Token 过期问题，提供自动验证、刷新和回退机制
"""

import json
import jwt
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class TokenInfo:
    """Token 信息数据类"""
    token: str
    expires_at: Optional[datetime] = None
    is_valid: bool = True
    cluster_id: int = None
    last_validated: Optional[datetime] = None
    error_message: str = ""
    auto_refresh_enabled: bool = False
    refresh_token: Optional[str] = None


class KubernetesTokenManager:
    """Kubernetes Token 智能管理器"""
    
    # Token 验证缓存时间（秒）
    VALIDATION_CACHE_TTL = 300  # 5分钟
    
    # Token 过期前多长时间开始提醒（秒）
    EXPIRY_WARNING_THRESHOLD = 86400  # 24小时
    
    # Token 自动验证间隔（秒）
    AUTO_VALIDATION_INTERVAL = 3600  # 1小时
    
    def __init__(self, cluster):
        """初始化 Token 管理器"""
        self.cluster = cluster
        self.cache_key_prefix = f"k8s_token_{cluster.id}"
    
    def analyze_token(self, token: str) -> TokenInfo:
        """分析 Token 信息"""
        token_info = TokenInfo(
            token=token,
            cluster_id=self.cluster.id,
            last_validated=timezone.now()
        )
        
        try:
            # 尝试解析 JWT Token
            if token.startswith('eyJ'):
                # 这是一个 JWT Token
                decoded = jwt.decode(token, options={"verify_signature": False})
                
                # 提取过期时间
                if 'exp' in decoded:
                    # JWT exp 字段是 UTC 时间戳
                    token_info.expires_at = datetime.fromtimestamp(decoded['exp'], tz=timezone.utc)
                    
                    # 使用 UTC 时间进行比较
                    current_time_utc = datetime.now(timezone.utc)
                    time_to_expiry = token_info.expires_at - current_time_utc
                    
                    if time_to_expiry.total_seconds() < 0:
                        # JWT 显示已过期，但 Kubernetes Service Account Token 可能仍然有效
                        # 我们标记为警告状态，不直接设置为无效
                        token_info.error_message = "JWT 显示已过期，需要实际连接验证"
                        logger.warning(f"集群 {self.cluster.name} 的 JWT Token 显示已过期，但可能仍然有效（Service Account Token）")
                    elif time_to_expiry.total_seconds() < self.EXPIRY_WARNING_THRESHOLD:
                        logger.warning(f"集群 {self.cluster.name} 的 Token 将在 {time_to_expiry} 后过期")
                
                # 提取其他信息
                token_info.auto_refresh_enabled = 'refresh' in decoded
                
                logger.info(f"JWT Token 分析完成: 过期时间 {token_info.expires_at} (UTC)")
                
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token 不是有效的 JWT 格式: {e}")
            # 不是 JWT Token，可能是 Service Account Token 或其他格式
            # 这种情况下无法从 Token 本身获取过期信息
            token_info.error_message = f"无法解析 Token 过期时间: {e}"
        
        except Exception as e:
            logger.error(f"Token 分析失败: {e}")
            token_info.error_message = f"Token 分析失败: {e}"
        
        return token_info
    
    def validate_token_connection(self, token: str) -> Tuple[bool, Dict[str, Any]]:
        """验证 Token 是否可以连接到集群"""
        cache_key = f"{self.cache_key_prefix}_validation_{hash(token)}"
        
        # 检查缓存
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"使用缓存的验证结果: {cached_result['valid']}")
            return cached_result['valid'], cached_result['info']
        
        try:
            # 创建临时集群配置用于测试
            from .k8s_client import KubernetesManager
            
            # 创建临时集群对象
            temp_cluster = type('TempCluster', (), {
                'api_server': self.cluster.api_server,
                'auth_config': {'token': token},
                'name': f"{self.cluster.name}-token-test"
            })()
            
            # 测试连接
            k8s_manager = KubernetesManager(temp_cluster)
            cluster_info = k8s_manager.get_cluster_info()
            
            result = {
                'valid': cluster_info.get('connected', False),
                'info': {
                    'cluster_version': cluster_info.get('version'),
                    'total_nodes': cluster_info.get('total_nodes', 0),
                    'ready_nodes': cluster_info.get('ready_nodes', 0),
                    'connection_time': timezone.now().isoformat(),
                    'message': cluster_info.get('message', '连接成功')
                }
            }
            
            # 缓存结果
            cache.set(cache_key, result, self.VALIDATION_CACHE_TTL)
            
            logger.info(f"Token 连接验证成功: {result['info']['message']}")
            return result['valid'], result['info']
            
        except Exception as e:
            logger.error(f"Token 连接验证失败: {e}")
            error_info = {
                'error': str(e),
                'connection_time': timezone.now().isoformat(),
                'message': f'连接失败: {str(e)}'
            }
            return False, error_info
    
    def get_token_status(self) -> Dict[str, Any]:
        """获取当前 Token 状态"""
        auth_config = self.cluster.auth_config or {}
        current_token = auth_config.get('token')
        
        if not current_token:
            return {
                'status': 'no_token',
                'message': '未配置 Token',
                'recommendations': ['请配置有效的 Kubernetes Token']
            }
        
        # 分析 Token
        token_info = self.analyze_token(current_token)
        
        # 验证连接 - 这是最权威的验证方式
        is_valid, connection_info = self.validate_token_connection(current_token)
        
        # 判断过期状态的逻辑
        jwt_shows_expired = False
        if token_info.expires_at:
            current_time_utc = datetime.now(timezone.utc)
            time_to_expiry = token_info.expires_at - current_time_utc
            jwt_shows_expired = time_to_expiry.total_seconds() < 0
        
        # 确定整体状态
        if not is_valid:
            overall_status = 'invalid'
            status_message = 'Token 连接失败，无法访问集群'
        elif jwt_shows_expired and is_valid:
            overall_status = 'warning'
            status_message = 'JWT 层面显示已过期，但实际连接仍然有效'
        else:
            overall_status = 'valid'
            status_message = 'Token 正常工作'
        
        status_data = {
            'status': overall_status,
            'status_message': status_message,
            'token_info': {
                'has_expiry': token_info.expires_at is not None,
                'expires_at': token_info.expires_at.isoformat() if token_info.expires_at else None,
                'auto_refresh_available': token_info.auto_refresh_enabled,
                'last_validated': token_info.last_validated.isoformat(),
                'error_message': token_info.error_message,
                'jwt_shows_expired': jwt_shows_expired,
                'connection_valid': is_valid
            },
            'connection_info': connection_info,
            'recommendations': []
        }
        
        # 生成建议
        if not is_valid:
            status_data['recommendations'].append('Token 无法连接到集群，请检查 Token 是否正确')
        elif jwt_shows_expired and is_valid:
            status_data['recommendations'].append('JWT 显示已过期但连接仍有效，可能是 Service Account Token，建议定期检查实际有效性')
        
        if token_info.expires_at:
            current_time_utc = datetime.now(timezone.utc)
            time_to_expiry = token_info.expires_at - current_time_utc
            if time_to_expiry.total_seconds() < 0 and is_valid:
                status_data['recommendations'].append('Token 在 JWT 层面显示已过期，但仍可正常使用，建议关注集群端 Token 管理策略')
            elif 0 < time_to_expiry.total_seconds() < self.EXPIRY_WARNING_THRESHOLD:
                days_left = int(time_to_expiry.total_seconds() / 86400)
                status_data['recommendations'].append(f'Token 将在 {days_left} 天后过期，建议提前准备新 Token')
        
        if not token_info.auto_refresh_enabled:
            status_data['recommendations'].append('考虑使用支持自动刷新的 Token 类型')
        
        return status_data
    
    def suggest_token_renewal_strategy(self) -> Dict[str, Any]:
        """建议 Token 更新策略"""
        token_status = self.get_token_status()
        
        strategies = {
            'immediate_actions': [],
            'long_term_solutions': [],
            'automation_options': []
        }
        
        # 立即行动建议
        if token_status['status'] == 'invalid':
            strategies['immediate_actions'] = [
                {
                    'action': 'generate_new_token',
                    'title': '生成新 Token',
                    'description': '在 Kubernetes 集群中生成新的 Service Account Token',
                    'urgency': 'high',
                    'commands': [
                        'kubectl create serviceaccount ansflow-sa',
                        'kubectl create clusterrolebinding ansflow-binding --clusterrole=cluster-admin --serviceaccount=default:ansflow-sa',
                        'kubectl create token ansflow-sa --duration=8760h'  # 1年有效期
                    ]
                },
                {
                    'action': 'update_cluster_config',
                    'title': '更新集群配置',
                    'description': '在 AnsFlow 中更新集群的 Token 配置',
                    'urgency': 'high',
                    'steps': [
                        '1. 打开集群配置页面',
                        '2. 点击"编辑"按钮',
                        '3. 更新 Token 字段',
                        '4. 点击"测试连接"验证',
                        '5. 保存配置'
                    ]
                }
            ]
        
        # 长期解决方案
        strategies['long_term_solutions'] = [
            {
                'solution': 'use_kubeconfig',
                'title': '使用 Kubeconfig 认证',
                'description': '切换到 Kubeconfig 认证方式，减少 Token 管理复杂度',
                'benefits': ['更稳定的认证', '支持多种认证方式', '更好的安全性'],
                'implementation': 'export KUBECONFIG=/path/to/config && kubectl config view --raw'
            },
            {
                'solution': 'service_account_automation',
                'title': 'Service Account 自动化',
                'description': '设置自动化脚本定期更新 Service Account Token',
                'benefits': ['自动更新', '减少手动干预', '提高可用性'],
                'implementation': '创建 CronJob 定期更新 Token'
            },
            {
                'solution': 'certificate_auth',
                'title': '客户端证书认证',
                'description': '使用客户端证书进行认证，通常有更长的有效期',
                'benefits': ['长期有效', '更安全', '不易过期'],
                'implementation': '生成客户端证书并配置 TLS 认证'
            }
        ]
        
        # 自动化选项
        strategies['automation_options'] = [
            {
                'option': 'token_monitor',
                'title': 'Token 监控服务',
                'description': '实现 Token 状态监控和过期提醒',
                'features': ['定期检查 Token 状态', '过期前邮件提醒', '自动健康检查']
            },
            {
                'option': 'auto_refresh',
                'title': 'Token 自动刷新',
                'description': '如果 Token 支持，实现自动刷新机制',
                'features': ['自动刷新过期 Token', '无缝连接切换', '零停机时间']
            }
        ]
        
        return {
            'current_status': token_status,
            'strategies': strategies,
            'priority_actions': self._get_priority_actions(token_status)
        }
    
    def _get_priority_actions(self, token_status: Dict[str, Any]) -> list:
        """获取优先行动建议"""
        actions = []
        
        if token_status['status'] == 'invalid':
            actions.append({
                'priority': 1,
                'action': '立即生成新 Token 并更新配置',
                'reason': 'Token 无效，影响集群连接'
            })
        
        token_info = token_status.get('token_info', {})
        if token_info.get('jwt_shows_expired') and not token_info.get('connection_valid'):
            actions.append({
                'priority': 1,
                'action': '更新过期的 Token',
                'reason': 'Token 已过期且连接失败'
            })
        elif token_info.get('jwt_shows_expired') and token_info.get('connection_valid'):
            actions.append({
                'priority': 2,
                'action': '考虑更新 Token',
                'reason': 'JWT 显示已过期但连接仍有效，建议更新以确保长期稳定'
            })
        elif token_info.get('expires_at'):
            # 检查是否即将过期
            expires_at = datetime.fromisoformat(token_info['expires_at'].replace('Z', '+00:00'))
            current_time_utc = datetime.now(timezone.utc)
            time_to_expiry = expires_at - current_time_utc
            if time_to_expiry.total_seconds() < self.EXPIRY_WARNING_THRESHOLD:
                actions.append({
                    'priority': 2,
                    'action': '准备更新即将过期的 Token',
                    'reason': f'Token 将在 {int(time_to_expiry.total_seconds() / 86400)} 天后过期'
                })
        
        if not actions:
            actions.append({
                'priority': 3,
                'action': '考虑实施长期认证策略',
                'reason': '当前状态良好，建议优化认证方式'
            })
        
        return sorted(actions, key=lambda x: x['priority'])

    def create_token_renewal_guide(self) -> Dict[str, Any]:
        """创建 Token 更新指南"""
        return {
            'title': 'Kubernetes Token 更新指南',
            'steps': [
                {
                    'step': 1,
                    'title': '连接到 Kubernetes 集群',
                    'description': '确保您有管理员权限访问 Kubernetes 集群',
                    'commands': ['kubectl cluster-info', 'kubectl auth can-i "*" "*"'],
                    'expected_output': '显示集群信息和权限确认'
                },
                {
                    'step': 2,
                    'title': '创建或获取 Service Account',
                    'description': '为 AnsFlow 创建专用的 Service Account',
                    'commands': [
                        'kubectl create serviceaccount ansflow-sa -n default',
                        'kubectl create clusterrolebinding ansflow-binding --clusterrole=cluster-admin --serviceaccount=default:ansflow-sa'
                    ],
                    'notes': ['可以根据需要调整权限范围', '建议使用最小权限原则']
                },
                {
                    'step': 3,
                    'title': '生成新的 Token',
                    'description': '为 Service Account 生成长期有效的 Token',
                    'commands': [
                        'kubectl create token ansflow-sa --duration=8760h',  # 1年
                        '# 或者创建 Secret 获取永久 Token:',
                        'kubectl apply -f - <<EOF',
                        'apiVersion: v1',
                        'kind: Secret',
                        'metadata:',
                        '  name: ansflow-sa-token',
                        '  annotations:',
                        '    kubernetes.io/service-account.name: ansflow-sa',
                        'type: kubernetes.io/service-account-token',
                        'EOF',
                        'kubectl get secret ansflow-sa-token -o jsonpath="{.data.token}" | base64 -d'
                    ],
                    'notes': ['第一种方法生成有时间限制的 Token', '第二种方法生成永久 Token（推荐）']
                },
                {
                    'step': 4,
                    'title': '在 AnsFlow 中更新 Token',
                    'description': '将新生成的 Token 更新到 AnsFlow 集群配置中',
                    'instructions': [
                        '1. 登录 AnsFlow 管理界面',
                        '2. 进入 Kubernetes 集群管理页面',
                        '3. 找到对应的集群，点击"编辑"',
                        '4. 在认证配置中粘贴新的 Token',
                        '5. 点击"测试连接"验证新 Token',
                        '6. 确认连接成功后保存配置'
                    ]
                },
                {
                    'step': 5,
                    'title': '验证更新结果',
                    'description': '确认新 Token 工作正常',
                    'verification_steps': [
                        '在 AnsFlow 中查看集群状态应为"已连接"',
                        '尝试在流水线中使用 Kubernetes 步骤',
                        '检查集群资源同步是否正常'
                    ]
                }
            ],
            'troubleshooting': {
                'common_issues': [
                    {
                        'issue': 'Token 生成失败',
                        'solution': '检查 Service Account 是否存在，确认有足够权限'
                    },
                    {
                        'issue': '连接测试失败',
                        'solution': '检查 API Server 地址、Token 格式、网络连通性'
                    },
                    {
                        'issue': '权限不足错误',
                        'solution': '检查 ClusterRoleBinding，确保 Service Account 有足够权限'
                    }
                ]
            },
            'automation_script': self._generate_automation_script()
        }
    
    def _generate_automation_script(self) -> str:
        """生成自动化更新脚本"""
        return '''#!/bin/bash
# Kubernetes Token 自动更新脚本
# 用于定期更新 AnsFlow 的 Kubernetes Token

set -e

# 配置变量
SERVICE_ACCOUNT="ansflow-sa"
NAMESPACE="default"
TOKEN_DURATION="8760h"  # 1年
ANSFLOW_API_URL="http://your-ansflow-instance/api"
CLUSTER_ID="your-cluster-id"

# 函数：生成新 Token
generate_new_token() {
    echo "生成新的 Token..."
    NEW_TOKEN=$(kubectl create token $SERVICE_ACCOUNT -n $NAMESPACE --duration=$TOKEN_DURATION)
    
    if [ -z "$NEW_TOKEN" ]; then
        echo "错误：Token 生成失败"
        exit 1
    fi
    
    echo "新 Token 生成成功"
    return 0
}

# 函数：验证 Token
validate_token() {
    local token=$1
    echo "验证 Token 有效性..."
    
    # 使用 kubectl 验证 Token
    if kubectl auth can-i get nodes --token="$token" >/dev/null 2>&1; then
        echo "Token 验证成功"
        return 0
    else
        echo "错误：Token 验证失败"
        return 1
    fi
}

# 函数：更新 AnsFlow 配置
update_ansflow_config() {
    local token=$1
    echo "更新 AnsFlow 集群配置..."
    
    # 这里需要根据您的 AnsFlow API 进行调整
    curl -X PATCH "$ANSFLOW_API_URL/kubernetes/clusters/$CLUSTER_ID/" \\
         -H "Content-Type: application/json" \\
         -H "Authorization: Bearer $ANSFLOW_TOKEN" \\
         -d "{
             \\"auth_config\\": {
                 \\"token\\": \\"$token\\"
             }
         }"
    
    if [ $? -eq 0 ]; then
        echo "AnsFlow 配置更新成功"
        return 0
    else
        echo "错误：AnsFlow 配置更新失败"
        return 1
    fi
}

# 主流程
main() {
    echo "开始 Token 自动更新流程..."
    
    # 生成新 Token
    generate_new_token
    
    # 验证 Token
    if validate_token "$NEW_TOKEN"; then
        # 更新 AnsFlow 配置
        if update_ansflow_config "$NEW_TOKEN"; then
            echo "Token 更新完成！"
            
            # 记录日志
            echo "$(date): Token 更新成功" >> /var/log/ansflow-token-update.log
        else
            echo "错误：更新 AnsFlow 配置失败"
            exit 1
        fi
    else
        echo "错误：新 Token 验证失败"
        exit 1
    fi
}

# 如果作为 Cron 任务运行，添加日志
if [ "$1" = "--cron" ]; then
    main >> /var/log/ansflow-token-update.log 2>&1
else
    main
fi
'''


# 工具函数
def get_cluster_token_status(cluster_id: int) -> Dict[str, Any]:
    """获取指定集群的 Token 状态"""
    from .models import KubernetesCluster
    
    try:
        cluster = KubernetesCluster.objects.get(id=cluster_id)
        token_manager = KubernetesTokenManager(cluster)
        return token_manager.get_token_status()
    except KubernetesCluster.DoesNotExist:
        return {'error': f'集群 {cluster_id} 不存在'}
    except Exception as e:
        return {'error': f'获取 Token 状态失败: {str(e)}'}


def suggest_cluster_token_renewal(cluster_id: int) -> Dict[str, Any]:
    """为指定集群建议 Token 更新策略"""
    from .models import KubernetesCluster
    
    try:
        cluster = KubernetesCluster.objects.get(id=cluster_id)
        token_manager = KubernetesTokenManager(cluster)
        return token_manager.suggest_token_renewal_strategy()
    except KubernetesCluster.DoesNotExist:
        return {'error': f'集群 {cluster_id} 不存在'}
    except Exception as e:
        return {'error': f'生成更新建议失败: {str(e)}'}
