#!/bin/bash

# server version
if [[ -z $1 ]]
then
    >&2 echo 'Error: no version specified'
    exit 1
fi

version_number=$1
version_date=$(date -I -u)

# patch version file
version_file=dakara_server/dakara_server/version.py
cat <<EOF >$version_file
__version__ = '$version_number'
__date__ = '$version_date'
EOF

# patch changelog
changelog_file=CHANGELOG.md
sed -i "/^## Unreleased$/a \\
\\
## $version_number - $version_date" $changelog_file

# create commit and tag
git add $version_file $changelog_file
git commit -m "Version $version_number" --no-verify
git tag $version_number

# say something
echo "Version bumped to $version_number"
