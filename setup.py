# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

import os
from pathlib import Path

from setuptools import PEP420PackageFinder, setup
from setuptools_scm import get_version

find_namespace_packages = PEP420PackageFinder.find

THIS_FILE_PATH = os.path.dirname(os.path.abspath(__file__))

package_version = "1.0.0"

data_files = {
    "/etc/osh": [
        "osh/client/client.conf",
        "osh/worker/worker.conf",
    ],
    "/usr/lib/systemd/system": [
        "osh/hub/osh-retention.service",
        "osh/hub/osh-retention.timer",
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
        "osh/hub/scripts/osh-worker-manager",
    ],
    "/usr/sbin": [
        "osh/hub/scripts/osh-retention",
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

# patterns to exclude from packaging
package_exclude = [
    "kobo*",
    "osh.testing",
]

hub_path = Path("osh/hub")
for folder in (
    "templates",
    "static-assets",
    "scan/fixtures",
    "waiving/fixtures",
):

    for path in (hub_path / folder).rglob("*"):
        if path.is_file():
            package_data["osh"].append(str(path.relative_to("osh")))

if os.path.isdir(".git"):
    package_version = get_version()

setup(
    name="osh",
    version=package_version,
    url="https://github.com/openscanhub/openscanhub",
    author="Red Hat, Inc.",
    author_email="openscanhub@lists.fedoraproject.org",
    description="OpenScanHub is a service for static and dynamic analysis.",
    packages=find_namespace_packages(exclude=package_exclude),
    package_data=package_data,
    data_files=data_files.items(),
)
