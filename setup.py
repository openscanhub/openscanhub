# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

import os
from glob import glob
from pathlib import Path

from setuptools import PEP420PackageFinder, setup

from scripts.include import (get_git_date_and_time, get_git_version,
                             git_check_tag_for_HEAD)

find_namespace_packages = PEP420PackageFinder.find

THIS_FILE_PATH = os.path.dirname(os.path.abspath(__file__))

package_version = [0, 9, 4]
data_files = {
    "/etc/osh": [
        "osh/client/client.conf",
        "osh/worker/worker.conf",
    ],
    "/usr/lib/systemd/system": [
        "osh/hub/osh-stats.service",
        "osh/hub/osh-stats.timer",
        "osh/worker/osh-worker.service",
    ],
    "/usr/share/bash-completion/completions": [
        "osh/client/completion/osh-cli.bash",
    ],
    "/usr/share/zsh/site-functions": [
        "osh/client/completion/_osh-cli"
    ],
    "/usr/bin": [
        "osh/client/osh-cli",
    ],
    "/usr/sbin": [
        "osh/hub/scripts/osh-stats",
        "osh/worker/osh-worker",
    ],
}
package_data = {
    "osh": [
        "hub/osh-hub.wsgi",
        "hub/scripts/checker_groups.txt",
    ]
}

hub_path = Path("osh/hub")
for folder in (
    "templates",
    "static-assets",
    "scan/fixtures",
    "errata/fixtures",
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
    name="osh",
    version=".".join(map(str, package_version)),
    url="https://github.com/openscanhub/openscanhub",
    author="Red Hat, Inc.",
    author_email="openscanhub-devel@redhat.com",
    description="OpenScanHub is a service for static and dynamic analysis.",
    packages=find_namespace_packages(exclude=["kobo*"]),
    package_data=package_data,
    data_files=data_files.items(),
)
