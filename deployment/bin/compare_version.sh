#!/bin/sh

set -eu

# Usage:
#
# compare_version.sh VERSION_REF VERSION_TEST
#
# Return 0 if VERSION_REF <= VERSION_TEST.
# Return 1 if VERSION_REF > VERSION_TEST.

requiredver=$1
currentver=$2

# See https://unix.stackexchange.com/a/285928
if [ "$(printf '%s\n' "$requiredver" "$currentver" | sort -V | head -n1)" = "$requiredver" ]; then
    exit 0
else
    exit 1
fi
