# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

import subprocess


def get_git_date_and_time(git_repo_path):
    """Return git last commit date in YYYYMMDD format and time HHMMSS format."""
    cmd = "git log -n 1 --pretty=format:%ci"
    lines = subprocess.check_output(cmd.split(), universal_newlines=True, cwd=git_repo_path).split("\n")
    date = lines[0].split(" ")[0].replace("-", "")
    time = lines[0].split(" ")[1].replace(":", "")
    return date, time


def get_git_version(git_repo_path):
    """Return git abbreviated tree hash."""
    cmd = "git log -n 1 --pretty=format:%t"
    output = subprocess.check_output(cmd.split(), universal_newlines=True, cwd=git_repo_path)
    return output.strip()


def git_check_tag_for_HEAD(git_repo_path):
    """Returns True if HEAD has a tag, False otherwise. Also raises RuntimeError
    if the source tree is dirty."""
    dirty_cmd = "git describe --dirty"
    output = subprocess.check_output(dirty_cmd.split(), cwd=git_repo_path, universal_newlines=True)

    if output.strip().endswith("-dirty"):
        raise RuntimeError("Cannot create sdist/SRPM from a dirty source tree.")

    tag_cmd = "git describe --exact-match"

    try:
        subprocess.check_call(tag_cmd.split(), cwd=git_repo_path)
    except subprocess.CalledProcessError:
        return False
    return True
