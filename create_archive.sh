#!/bin/bash

# strict mode
set -eu

# server version
if [[ -z ${1:-} ]]
then
    echo "Error: no version specified" >&2
    exit 1
fi

version_number=$1
front_version_number=${2:-$version_number}
image_name=dakaraproject/dakaraserver:$version_number
image_name_latest=dakaraproject/dakaraserver:latest

echo "Building with server version: $version_number"
echo "Building with front version: $front_version_number"

sudo docker build . \
    -t $image_name \
    -t $image_name_latest \
    --no-cache \
    --build-arg \
        FRONT_VERSION=$front_version_number

echo "Image created"

# upload to Docker Hub
echo "Copy pase the following command to upload the server image to Docker Hub:"
echo "  sudo docker login -u <username>"
echo "  sudo docker push $image_name"
echo "  sudo docker push $image_name_latest"
