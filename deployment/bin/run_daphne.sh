#!/bin/sh

set -eu

cd /app/dakara_server

# populating data volume
make_directories.sh

# create default config file
cp \
    /app/deployment/config/daphne.conf \
    /data/config/daphne.conf.sample

# create actual config file once
if [[ ! -f /data/config/daphne.conf ]]
then
    echo "Create configuration file for daphne"
    cp \
        /data/config/daphne.conf.sample \
        /data/config/daphne.conf
fi

# check version of config file
check_version.sh /data/config/daphne.conf.sample /data/config/daphne.conf

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
    -p 80 \
    dakara_server.asgi:application
