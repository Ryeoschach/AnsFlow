from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Project, ProjectMembership, Environment
from .serializers import (
    ProjectSerializer, ProjectListSerializer,
    ProjectMembershipSerializer, EnvironmentSerializer
)


class ProjectViewSet(viewsets.ModelViewSet):
    """ViewSet for managing projects"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectListSerializer
        return ProjectSerializer
    
    def get_queryset(self):
        user = self.request.user
        # Users can see projects they own or are members of
        return Project.objects.filter(
            Q(owner=user) | Q(members=user)
        ).distinct().select_related('owner').prefetch_related('members')
    
    def perform_create(self, serializer):
        project = serializer.save(owner=self.request.user)
        # Automatically add the owner as a project member with 'owner' role
        ProjectMembership.objects.create(
            project=project,
            user=self.request.user,
            role='owner'
        )
    
    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """Add a member to the project"""
        project = self.get_object()
        
        # Check if user has permission to add members (owner or maintainer)
        membership = ProjectMembership.objects.filter(
            project=project, user=request.user
        ).first()
        
        if not membership or membership.role not in ['owner', 'maintainer']:
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ProjectMembershipSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(project=project)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['delete'])
    def remove_member(self, request, pk=None):
        """Remove a member from the project"""
        project = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check permissions
        membership = ProjectMembership.objects.filter(
            project=project, user=request.user
        ).first()
        
        if not membership or membership.role not in ['owner', 'maintainer']:
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Remove member
        try:
            member_to_remove = ProjectMembership.objects.get(
                project=project, user_id=user_id
            )
            # Can't remove the owner
            if member_to_remove.role == 'owner':
                return Response(
                    {'error': 'Cannot remove project owner'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            member_to_remove.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProjectMembership.DoesNotExist:
            return Response(
                {'error': 'Member not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def environments(self, request, pk=None):
        """Get project environments"""
        project = self.get_object()
        environments = project.environments.all()
        serializer = EnvironmentSerializer(environments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def create_environment(self, request, pk=None):
        """Create a new environment for the project"""
        project = self.get_object()
        
        # Check permissions
        membership = ProjectMembership.objects.filter(
            project=project, user=request.user
        ).first()
        
        if not membership or membership.role not in ['owner', 'maintainer']:
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = EnvironmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(project=project)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EnvironmentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing environments"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EnvironmentSerializer
    
    def get_queryset(self):
        user = self.request.user
        # Users can see environments of projects they have access to
        return Environment.objects.filter(
            project__in=Project.objects.filter(
                Q(owner=user) | Q(members=user)
            )
        ).select_related('project')
    
    def perform_create(self, serializer):
        # Ensure user has permission to create environments in this project
        project = serializer.validated_data['project']
        membership = ProjectMembership.objects.filter(
            project=project, user=self.request.user
        ).first()
        
        if not membership or membership.role not in ['owner', 'maintainer']:
            raise PermissionError('Permission denied')
        
        serializer.save()


class ProjectMembershipViewSet(viewsets.ModelViewSet):
    """ViewSet for managing project memberships"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProjectMembershipSerializer
    
    def get_queryset(self):
        user = self.request.user
        # Users can see memberships of projects they have access to
        return ProjectMembership.objects.filter(
            project__in=Project.objects.filter(
                Q(owner=user) | Q(members=user)
            )
        ).select_related('project', 'user')
