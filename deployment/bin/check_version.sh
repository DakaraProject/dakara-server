#!/bin/sh

set -eu

# Usage:
#
# check_version.sh FILE_REF FILE_TEST
#
# Print a warning message if the version in FILE_REF is higher than in FILE_TEST.

file_ref=$1
file=$2

if ! compare_version.sh "$(extract_version.sh $file_ref)" "$(extract_version.sh $file)"
then
    echo "#########################################################################" >&2
    echo "WARNING: Configuration file $file is outdated" >&2
    echo "You should update it from $file_ref" >&2
    echo "#########################################################################" >&2
fi
