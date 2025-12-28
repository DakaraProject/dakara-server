#!/bin/sh

set -e

# create config file if needed
if [[ ! -f /data/config/nginx-custom.conf ]]
then
    echo "Create default custom configuration file for nginx"
    cat >/data/config/nginx-custom.conf <<EOF
# Custom configuration file for nginx

worker_processes 1;
EOF
fi

# run nginx
/usr/sbin/nginx
