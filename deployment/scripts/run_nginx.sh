#!/bin/sh

set -eu

# populating data volume
make_directories.sh

# create or update default config files
cp \
    /app/deployment/config/nginx_main.conf.sample \
    /data/config/
cp \
    /app/deployment/config/nginx_server.conf.sample \
    /data/config/

# create actual config files once
if [[ ! -f /data/config/nginx_main.conf ]]
then
    echo "Create main configuration file for nginx"
    cp \
        /data/config/nginx_main.conf.sample \
        /data/config/nginx_main.conf
fi
if [[ ! -f /data/config/nginx_server.conf ]]
then
    echo "Create server configuration file for nginx"
    cp \
        /data/config/nginx_server.conf.sample \
        /data/config/nginx_server.conf
fi

# check version of config files
check_version.py /data/config/nginx_main.conf.sample /data/config/nginx_main.conf
check_version.py /data/config/nginx_server.conf.sample /data/config/nginx_server.conf

# collect static files
/app/dakara_server/manage.py collectstatic --noinput

# run nginx
echo "Starting nginx"
/usr/sbin/nginx
