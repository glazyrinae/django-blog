#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

#python manage.py shell
#python manage.py startapp blog
#python manage.py makemigrations blog
#python manage.py migrate
#python manage.py createsuperuser
#docker compose exec web sh
#import django
#django.setup()
def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tiny_cms.configs.dev')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
