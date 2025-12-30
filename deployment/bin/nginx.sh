#!/bin/sh

set -e

# create config file once
if [[ ! -f /data/config/nginx.conf ]]
then
    echo "Create default custom configuration file for nginx"
    cp \
        /app/deployment/config/nginx.conf \
        /data/config/nginx.conf
fi

# run nginx
echo "Starting nginx"
/usr/sbin/nginx
