"""
URL configuration for Ansible Integration module.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'inventories', views.AnsibleInventoryViewSet, basename='inventory')
router.register(r'playbooks', views.AnsiblePlaybookViewSet, basename='playbook')
router.register(r'credentials', views.AnsibleCredentialViewSet, basename='credential')
router.register(r'executions', views.AnsibleExecutionViewSet, basename='ansible-execution')
router.register(r'hosts', views.AnsibleHostViewSet, basename='ansible-host')
router.register(r'host-groups', views.AnsibleHostGroupViewSet, basename='ansible-host-group')
router.register(r'inventory-hosts', views.InventoryHostViewSet, basename='inventory-host')
router.register(r'inventory-groups', views.InventoryGroupViewSet, basename='inventory-group')

app_name = 'ansible_integration'

urlpatterns = [
    # API routes
    path('', include(router.urls)),
    
    # Custom endpoints
    path('playbooks/<int:playbook_id>/execute/', 
         views.ExecutePlaybookView.as_view(), 
         name='execute-playbook'),
    
    path('executions/<int:execution_id>/logs/', 
         views.ExecutionLogsView.as_view(), 
         name='execution-logs'),
    
    path('executions/<int:execution_id>/cancel/', 
         views.CancelExecutionView.as_view(), 
         name='cancel-execution'),
    
    path('playbooks/validate/', 
         views.ValidatePlaybookView.as_view(), 
         name='validate-playbook'),
    
    # Statistics and monitoring
    path('stats/overview/', 
         views.AnsibleStatsView.as_view(), 
         name='ansible-stats'),
    
    path('executions/recent/', 
         views.RecentExecutionsView.as_view(), 
         name='recent-executions'),
]
