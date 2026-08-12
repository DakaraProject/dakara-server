#!/bin/sh

set -eu

# set ownership of volume to user
chown -R appuser:appgroup /data

# run command as user, preserve the full environment
sudo \
    --preserve-env \
    --user=appuser \
    --group=appgroup \
    env \
        "PATH=$PATH" \
        "$@"
