#!/bin/sh

set -eu

cd /app/dakara_server

# populating data volume
make_directories.sh

# create or update default config file
cp \
    /app/deployment/config/gunicorn.conf.py.sample \
    /data/config/

# create config file once
if [[ ! -f /data/config/gunicorn.conf.py ]]
then
    echo "Create default configuration file for gunicorn"
    cp \
        /data/config/gunicorn.conf.py.sample \
        /data/config/gunicorn.conf.py
fi

# check version of config file
check_version.py /data/config/gunicorn.conf.py.sample /data/config/gunicorn.conf.py

# wait for database
./manage.py wait_db_ready

# apply migrations
./manage.py migrate

# create superuser once
if [[ ! -f /data/state/gunicorn_first_superuser ]]
then
    DJANGO_SUPERUSER_USERNAME=${DAKARA_SUPERUSER_USERNAME:-admin} \
        DJANGO_SUPERUSER_EMAIL=${DAKARA_SUPERUSER_EMAIL:-admin@localhost} \
        DJANGO_SUPERUSER_PASSWORD=${DAKARA_SUPERUSER_PASSWORD} \
        ./manage.py createsuperuser --no-input

    echo "Superuser created; you should create manager accounts and remove the superuser account as soon as possible for security reasons"

    touch /data/state/gunicorn_first_superuser
fi

# run gunicorn
gunicorn \
    -c /data/config/gunicorn.conf.py \
    -b :80 \
    dakara_server.wsgi:application
