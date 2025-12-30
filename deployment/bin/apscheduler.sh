#!/bin/sh

set -e

# production preset
export DJANGO_SETTINGS_MODULE="dakara_server.settings.production"

# run apscheduler
/app/dakara_server/manage.py runapscheduler
