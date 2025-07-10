from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import serializers
from django.contrib.auth.models import User


class CompleteUserSerializer(serializers.ModelSerializer):
    """完整的用户序列化器，包含所有权限字段"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login']
        read_only_fields = ['id', 'date_joined', 'last_login']


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for managing users and authentication"""
    
    queryset = User.objects.all()
    serializer_class = CompleteUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'], url_path='me')
    def current_user(self, request):
        """Get current authenticated user information"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
