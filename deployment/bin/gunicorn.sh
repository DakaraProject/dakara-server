#!/bin/sh

set -e

# production preset
export DJANGO_SETTINGS_MODULE="dakara_server.settings.production"

# create config file if needed
if [[ ! -f /data/config/gunicorn.conf.py ]]
    echo "Create default custom configuration file for gunicorn"
then
    cat >/data/config/gunicorn.conf.py <<EOF
# Custom configuration file for gunicorn

workers = 1
EOF
fi

# collect static files
/app/dakara_server/manage.py collectstatic --noinput

# apply migrations
/app/dakara_server/manage.py makemigrations
/app/dakara_server/manage.py migrate

# create superuser once
if [[ ! -f /data/NOT_FIRST_RUN_GUNICORN ]]
then
    echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('root', 'root@localhost', 'root')" | /app/dakara_server/manage.py shell

    touch /data/NOT_FIRST_RUN_GUNICORN
fi

# run gunicorn
gunicorn \
    -c /data/config/gunicorn.conf.py \
    -b :8000 \
    dakara_server.wsgi:application
