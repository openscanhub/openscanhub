#!/usr/bin/python
# -*- coding: utf-8 -*-


import os
import distutils.command.sdist
from distutils.core import setup
from distutils.command.install import INSTALL_SCHEMES
from scripts.include import *


project_name         = "covscan"
project_dirs         = ["covscan", "covscand", "covscanhub"]
project_url          = "https://gitlab.cee.redhat.com/covscan/covscan"
project_author       = "Red Hat, Inc."
project_author_email = "ttomecek@redhat.com"
project_description  = "Coverity scan scheduler"
package_name         = "%s" % project_name
package_module_name  = project_name
package_version      = [0, 6, 9, "final", ""]


script_files = []


data_files = {
    "/etc/covscan": [
        "covscan/covscan.conf",
        "covscand/covscand.conf",
        "covscand/prod_covscand.conf",
        "covscand/stage_covscand.conf",
        #"covscand/devel_covscand.conf",
    ],
    "/etc/httpd/conf.d": [
        "covscanhub/prod-covscanhub-httpd.conf",
        "covscanhub/stage-covscanhub-httpd.conf",
    ],
    "/etc/init.d": [
        "files/etc/init.d/covscand",
    ],
    "/etc/bash_completion.d": [
        "files/etc/bash_completion.d/covscan.bash",
    ],
    "/usr/bin": [
        "covscan/covscan",
    ],
    "/usr/sbin": [
        "covscand/covscand",
    ],
}


package_data = {
    "covscanhub": get_files("covscanhub", "static") + \
            get_files("covscanhub", "templates") + \
            get_files("covscanhub", "media") + \
            get_files("covscanhub", "scan/fixtures") + \
            get_files("covscanhub", "errata/fixtures") + \
            get_files("covscanhub", "fixtures") + \
            ["covscanhub.wsgi",
             'scripts/checker_groups.txt']
}


# override default tarball format with bzip2
distutils.command.sdist.sdist.default_format = { 'posix': 'bztar', }


if os.path.isdir(".git"):
    # we're building from a git repo -> store version tuple to __init__.py
    if package_version[3] == "git":
        force = True
        git_version = get_git_version(os.path.dirname(__file__))
        git_date = get_git_date(os.path.dirname(__file__))
        package_version[4] = "%s.%s" % (git_date, git_version)

    for i in project_dirs:
        file_name = os.path.join(i, "version.py")
        write_version(file_name, package_version)


# read package version from the module
package_module = __import__(project_dirs[0] + ".version")
package_version = get_version(package_module)
packages = get_packages(project_dirs)


root_dir = os.path.dirname(__file__)
if root_dir != "":
    os.chdir(root_dir)


# force to install data files to site-packages
for scheme in INSTALL_SCHEMES.values():
    scheme["data"] = scheme["purelib"]


setup(
    name         = package_name,
    version      = package_version.replace(" ", "_").replace("-", "_"),
    url          = project_url,
    author       = project_author,
    author_email = project_author_email,
    description  = project_description,
    packages     = packages,
    package_data = package_data,
    data_files   = data_files.items(),
    scripts      = script_files,
)
