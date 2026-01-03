#!/bin/sh

set -e

cd /app/dakara_server

# populating data volume
/app/deployment/bin/make_directories.sh

# production preset
export DJANGO_SETTINGS_MODULE="dakara_server.settings.production"

# create config file once
if [[ ! -f /data/config/gunicorn.conf.py ]]
then
    echo "Create default custom configuration file for gunicorn"
    cp \
        /app/deployment/config/gunicorn.conf.py \
        /data/config/gunicorn.conf.py
fi

# collect static files
./manage.py collectstatic --noinput

# wait for database
./manage.py wait_db_ready

# apply migrations
./manage.py makemigrations
./manage.py migrate

# create superuser once
if [[ ! -f /data/state/gunicorn_first_superuser ]]
then
    # create the superuser with a dummy password
    echo \
        "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('root', 'root@localhost', 'root')" \
    | ./manage.py shell

    touch /data/state/gunicorn_first_superuser
fi

# run gunicorn
gunicorn \
    -c /data/config/gunicorn.conf.py \
    -b :8000 \
    dakara_server.wsgi:application
