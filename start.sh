#!/usr/bin/env bash
set -e

echo "==> Preparing Django admin user..."

if [ -z "$DJANGO_SUPERUSER_USERNAME" ]; then
    echo "ERROR: DJANGO_SUPERUSER_USERNAME is not set."
    exit 1
fi

if [ -z "$DJANGO_SUPERUSER_EMAIL" ]; then
    echo "ERROR: DJANGO_SUPERUSER_EMAIL is not set."
    exit 1
fi

if [ -z "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "ERROR: DJANGO_SUPERUSER_PASSWORD is not set."
    exit 1
fi

python manage.py shell -c "import os; from django.contrib.auth import get_user_model; U=get_user_model(); username=os.environ['DJANGO_SUPERUSER_USERNAME'].strip(); email=os.environ['DJANGO_SUPERUSER_EMAIL'].strip(); password=os.environ['DJANGO_SUPERUSER_PASSWORD']; u,created=U.objects.get_or_create(username=username, defaults={'email':email}); u.email=email; u.set_password(password); u.is_staff=True; u.is_superuser=True; u.save(); print(f'==> Django admin user ready: {username} (created={created})')"

exec gunicorn hotel_sugam_erp.wsgi:application
