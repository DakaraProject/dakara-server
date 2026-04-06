#!/bin/sh

set -eu

# Usage:
#
# extract_version.sh FILE
#
# Print the version in FILE as formated as: "# Version: <version>".

file=$1

grep "Version:" "$file" | cut -f 3 -d " " | head -n 1
