from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from project_management.serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for managing users and authentication"""
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'], url_path='me')
    def current_user(self, request):
        """Get current authenticated user information"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
