#!/bin/sh

set -e

# populating data volume
/app/deployment/bin/make_directories.sh

# production preset
export DJANGO_SETTINGS_MODULE="dakara_server.settings.production"

# create config file once
if [[ ! -f /data/config/daphne.conf ]]
then
    echo "Create default custom configuration file for daphne"
    cp \
        /app/deployment/config/daphne.conf \
        /data/config/daphne.conf
fi

# read config file
# remove comments and concat to one line
arguments=$(\
        sed \
            -e 's/[[:space:]]*#.*// ;/^[[:space:]]*$/d' \
            /data/config/daphne.conf \
        | awk '{printf("%s ", $0)}' \
    )

# wait for database
./manage.py wait_db_ready

# run daphne
daphne \
    $arguments \
    --log-fmt "[%(asctime)s] [%(process)d] %(levelname)s %(message)s" \
    -b 0.0.0.0 \
    -p 8001 \
    dakara_server.asgi:application
