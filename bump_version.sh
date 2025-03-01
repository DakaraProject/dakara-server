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
version_year=$(date +%Y -u)

# patch version and date in version file
version_file=src/dakara_server/version.py
cat <<EOF >$version_file
# this file is automatically updated by bump_version.sh, do not edit it!
__version__ = "$version_number"
__date__ = "$version_date"
EOF

# patch changelog
changelog_file=CHANGELOG.md
sed -i "/^## Unreleased$/a \\
\\
## $version_number - $version_date" $changelog_file

# change year in license file
license_file=LICENSE
sed -i -e "s/(c) [0-9]\{4\}/(c) $version_year/" $license_file

# create commit and tag
git add $version_file $changelog_file $license_file
git commit -m "Version $version_number" --no-verify
git tag "$version_number"

# say something
echo "Version bumped to $version_number"

# patch dev version and date in version file
cat <<EOF >$version_file
# this file is automatically updated by bump_version.sh, do not edit it!
__version__ = "$dev_version_number"
__date__ = "$version_date"
EOF

# create commit
git add $version_file
git commit -m "Dev version $dev_version_number" --no-verify

# say something
echo "Updated to dev version $dev_version_number"
