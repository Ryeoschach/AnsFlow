"""
Settings package for AnsFlow Django service.

This package contains multiple settings modules for different environments:
- base.py: Base settings shared across all environments
- development.py: Development environment settings
- production.py: Production environment settings
- test.py: Test environment settings
"""

import os

# Default to development settings if DJANGO_SETTINGS_MODULE is not set
env = os.environ.get('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')

if env.endswith('.development'):
    from .development import *
elif env.endswith('.production'):
    from .production import *
elif env.endswith('.test'):
    from .test import *
else:
    from .base import *
