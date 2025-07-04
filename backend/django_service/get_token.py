#!/usr/bin/env python3
import os
import sys
import django

# 添加项目路径
sys.path.append('/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

django.setup()

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

try:
    user = User.objects.get(username='admin')
    token, created = Token.objects.get_or_create(user=user)
    print(token.key)
except User.DoesNotExist:
    print("Admin user not found")
except Exception as e:
    print(f"Error: {e}")
