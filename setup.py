#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from glob import glob
from pathlib import Path

from setuptools import PEP420PackageFinder, setup

from scripts.include import (get_git_date_and_time, get_git_version,
                             git_check_tag_for_HEAD)

find_namespace_packages = PEP420PackageFinder.find

THIS_FILE_PATH = os.path.dirname(os.path.abspath(__file__))

package_version = [0, 8, 2]
data_files = {
    "/etc/osh": [
        "osh/client/client.conf",
        "osh/worker/worker.conf",
        "osh/worker/worker.conf.prod",
        "osh/worker/worker.conf.stage",
    ],
    "/etc/httpd/conf.d": [
        "osh/hub/covscanhub-httpd.conf.prod",
        "osh/hub/covscanhub-httpd.conf.stage",
    ],
    "/usr/lib/systemd/system": [
        "files/etc/systemd/system/covscand.service",
    ],
    "/etc/bash_completion.d": [
        "osh/cli/bash_completion.d/osh-cli.bash",
    ],
    "/usr/bin": [
        "osh/client/osh-cli",
    ],
    "/usr/sbin": [
        "osh/worker/covscand",
    ],
}
package_data = {
    "osh": [
        "hub/covscanhub.wsgi",
        "hub/scripts/checker_groups.txt",
    ]
}

hub_path = Path("osh/hub")
for folder in (
    "static",
    "templates",
    "media",
    "scan/fixtures",
    "errata/fixtures",
    "fixtures",
):

    for path in glob(str(hub_path / folder / "**"), recursive=True):
        path = Path(path)
        if path.is_file():
            package_data["osh"].append(str(path.relative_to("osh")))

if os.path.isdir(".git"):
    if not git_check_tag_for_HEAD(THIS_FILE_PATH):
        package_version.append("git")
        git_version = get_git_version(THIS_FILE_PATH)
        git_date, git_time = get_git_date_and_time(THIS_FILE_PATH)
        package_version += [git_date, git_time, git_version]

setup(
    name="covscan",
    version=".".join(map(str, package_version)),
    url="https://gitlab.cee.redhat.com/covscan/covscan",
    author="Red Hat, Inc.",
    author_email="ttomecek@redhat.com",
    description="Coverity scan scheduler",
    packages=find_namespace_packages(exclude=["kobo*"]),
    package_data=package_data,
    data_files=data_files.items(),
)
