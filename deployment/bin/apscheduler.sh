#!/bin/sh

set -e

# populating data volume
/app/deployment/bin/make_directories.sh

# production preset
export DJANGO_SETTINGS_MODULE="dakara_server.settings.production"

# wait for database
./manage.py wait_db_ready

# wait for migrations to be done
echo "Wating for migrations to be done..."
while ! ./manage.py migrate --check
do
    echo "Migrations not done, waiting for 5 seconds..."
    sleep 5
done
echo "Migrations done!"

# run apscheduler
echo "Starting scheduler"
/app/dakara_server/manage.py runapscheduler
