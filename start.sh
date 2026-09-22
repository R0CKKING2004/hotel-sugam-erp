#!/usr/bin/env bash
set -e

python manage.py shell -c "import os; from django.contrib.auth import get_user_model; U=get_user_model(); username=os.environ.get('DJANGO_SUPERUSER_USERNAME'); email=os.environ.get('DJANGO_SUPERUSER_EMAIL'); password=os.environ.get('DJANGO_SUPERUSER_PASSWORD'); u, created=U.objects.get_or_create(username=username, defaults={'email':email}); u.email=email; u.set_password(password); u.is_staff=True; u.is_superuser=True; u.save()"

exec gunicorn hotel_sugam_erp.wsgi:application
