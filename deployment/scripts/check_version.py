#!/usr/bin/env python3

import re
import sys
from argparse import ArgumentParser
from pathlib import Path

from packaging.version import Version, parse


def extract_version(file_path: Path) -> Version:
    """Find the version within the file."""
    content = file_path.read_text()
    match = re.search(r"Version: (\d+\.\d+\.\d+)", content)
    if match is None:
        raise ValueError(f"No version found in {file_path}")

    return parse(match.group(1))


def check_version(file_path_ref: Path, file_path: Path, output=sys.stderr):
    """Display a warning if reference version is newer than candidate version."""
    version_ref = extract_version(file_path_ref)
    version = extract_version(file_path)

    if version_ref > version:
        print(
            "#########################################################################"
            f"WARNING: Configuration file {file_path} is outdated"
            f"You should update it from {file_path_ref}"
            "#########################################################################",
            file=output,
        )


if __name__ == "__main__":
    parser = ArgumentParser(
        description=(
            "Print a warning message if the reference file is "
            "newer than the candidate file"
        )
    )
    parser.add_argument("reference", type=Path, help="Reference file")
    parser.add_argument("candidate", type=Path, help="Candidate file")

    args = parser.parse_args()
    check_version(args.reference, args.candidate)
