#!/bin/bash

set -e

# server version
if [[ -z $1 ]]
then
    >&2 echo 'Error: no version specified'
    exit 1
fi

# next server version
if [[ -z $2 ]]
then
    >&2 echo 'Error: no next version specified'
    exit 1
fi

version_number=$1
dev_version_number=$2-dev
version_date=$(date -I -u)

# patch version file
version_file=dakara_server/dakara_server/version.py
cat <<EOF >$version_file
__version__ = "$version_number"
__date__ = "$version_date"
EOF

# patch changelog
changelog_file=CHANGELOG.md
sed -i "/^## Unreleased$/a \\
\\
## $version_number - $version_date" $changelog_file

# change version in appveyor config file
appveyor_file=.appveyor.yml
sed -i "s/^version: .*-{build}$/version: $version_number-{build}/" $appveyor_file

# create commit and tag
git add $version_file $changelog_file $appveyor_file
git commit -m "Version $version_number" --no-verify
git tag "$version_number"

# say something
echo "Version bumped to $version_number"

# patch version file for dev version
cat <<EOF >$version_file
__version__ = "$dev_version_number"
__date__ = "$version_date"
EOF

# change version in appveyor config file for dev version
sed -i "s/^version: .*-{build}$/version: $dev_version_number-{build}/" $appveyor_file

# create commit
git add $version_file $appveyor_file
git commit -m "Dev version $dev_version_number" --no-verify

# say something
echo "Updated to dev version $dev_version_number"
