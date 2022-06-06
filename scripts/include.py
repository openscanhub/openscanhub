# -*- coding: utf-8 -*-


import os
import subprocess


def get_files(module_name, top_dir):
    """Return list of all files under top_dir."""
    result = []

    module = __import__(module_name)
    module_dir = os.path.dirname(module.__file__)

    for root, dirs, files in os.walk(os.path.join(module_dir, top_dir)):
        for fn in files:
            result.append(os.path.join(top_dir, root, fn)[len(module_dir) + 1:])
    return result


def get_git_date_and_time(git_repo_path):
    """Return git last commit date in YYYYMMDD format."""
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
