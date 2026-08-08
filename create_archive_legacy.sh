#!/bin/bash

# strict mode
set -eu

# create temporary directory
tmpdir=$(mktemp -dt dakara_server_build.XXXXXX)

# server version
if [[ -z $1 ]]
then
    >&2 echo 'Error: no version specified'
    exit 1
fi

version_number=$1
archive_prefix=dakara-server_$version_number
archive_name=$archive_prefix.zip

# client version
if [[ -z $2 ]]
then
    >&2 echo 'Error: no front version specified'
    exit 1
fi

front_version_number=$2
front_archive_name=dakara-client-web_$front_version_number.zip
front_archive_url=https://github.com/DakaraProject/dakara-client-web/releases/download/$front_version_number/$front_archive_name

# get client in temporary directory
wget -q "$front_archive_url" -O "$tmpdir/$front_archive_name"
mkdir -p "$tmpdir/$archive_prefix/dakara_server"
unzip -q "$tmpdir/$front_archive_name" -d "$tmpdir/$archive_prefix/dakara_server/"

# make server archive
git archive \
        --format zip \
        --prefix "$archive_prefix/" \
        --worktree-attributes \
        --output "$archive_name" \
        "refs/tags/$version_number"

# add client to server archive
curdir=$PWD
(cd "$tmpdir"; zip -qr "$curdir/$archive_name" "$archive_prefix")

# say something
echo "Archive created in $archive_name"

# delete temporary directory
rm -rf "$tmpdir"
