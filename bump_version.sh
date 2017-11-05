#!/bin/bash

if [[ -z $1 ]]
then
    >&2 echo 'Error: no version specified'
    exit 1
fi

version_number=$1
version_date=$(date -I -u)

cat <<EOF >dakara_server/dakara_server/version.py
__version__ = '$version_number'
__date__ = '$version_date'
EOF

sed -i "/^## Unreleased$/a \\
\\
## $version_number - $version_date" CHANGELOG.md 

echo "Version bumped to $version_number"

