#!/bin/sh

set -eu

curl \
    --fail \
    --silent \
    --output /dev/null \
    "http://localhost/api/settings/"
