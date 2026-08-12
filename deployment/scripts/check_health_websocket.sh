#!/bin/sh

set -eu

{
    # see: https://stackoverflow.com/a/64766370
    curl \
        --fail \
        --silent \
        --output /dev/null \
        --max-time "0.1" \
        --include \
        --no-buffer \
        --header "Connection: Upgrade" \
        --header "Upgrade: websocket" \
        --header "Host: localhost:80" \
        --header "Origin: http://localhost:80" \
        --header "Sec-WebSocket-Key: x3JJHMbDL1EzLkh9GBhXDw==" \
        --header "Sec-WebSocket-Version: 13" \
        "http://localhost/ws/heartbeat/"
} || {
    case $? in
        # allow error code 28: Operation timed out
        28)
            true
            ;;
        0)
            true
            ;;
        *)
            false
    esac
}
