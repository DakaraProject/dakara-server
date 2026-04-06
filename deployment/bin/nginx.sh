#!/bin/sh

set -eu

# populating data volume
make_directories.sh

# create default config files
cp \
    /app/deployment/config/nginx_main.conf \
    /data/config/nginx_main.conf.sample
cp \
    /app/deployment/config/nginx_server.conf \
    /data/config/nginx_server.conf.sample

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
check_version.sh /data/config/nginx_main.conf.sample /data/config/nginx_main.conf
check_version.sh /data/config/nginx_server.conf.sample /data/config/nginx_server.conf

# run nginx
echo "Starting nginx"
/usr/sbin/nginx
