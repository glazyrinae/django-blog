import os
environment = os.getenv('DJANGO_SETTINGS_MODULE', '')

if 'prod' in environment:
    from .production import *
elif 'dev' in environment:
    from .dev import *
else:
    from .dev import *
