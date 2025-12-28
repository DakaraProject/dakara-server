#!/bin/sh

set -e

# populating data volume
mkdir -pv /data
mkdir -pv /data/logs
mkdir -pv /data/config

# run supervisor
exec /usr/bin/supervisord -n
