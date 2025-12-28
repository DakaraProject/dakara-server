#!/bin/sh

set -e

# production preset
export DJANGO_SETTINGS_MODULE="dakara_server.settings.production"

# run daphne
daphne -b 0.0.0.0 -p 8001 dakara_server.asgi:application
