#!/bin/sh

set -e

# populating data volume
/app/deployment/bin/make_directories.sh

# run supervisor
exec /usr/bin/supervisord -n
