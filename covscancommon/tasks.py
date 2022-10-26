# -*- coding: utf-8 -*-
"""
Common functions for tasks, DRY
"""

import re
import os
from kobo.shortcuts import run


def downloadSRPM(tmp_dir, srpm_name):
    """
    Download SRPM from brew or koji. If disttag starts with 'fc', use koji,
    if it starts with 'el', use brew, if build is not there, use koji.
    """
    path = os.path.join(tmp_dir, "%s.src.rpm" % srpm_name)
    dist_tag = ''
    dist_tag_search = re.search('.*-.*-(.*)', srpm_name)
    if dist_tag_search:
        dist_tag = dist_tag_search.group(1)
    downloaded = True
    builder = 'brew'
    if 'fc' in dist_tag:
        builder = 'koji'
    cmd = [builder, "download-build", "--quiet", "--arch=src", srpm_name]
    try:
        run(cmd, workdir=tmp_dir, can_fail=False)
    except RuntimeError:
        downloaded = False
    if os.path.exists(path):
        return path
    else:
        downloaded = False
    if not downloaded:
        if builder == 'brew':
            builder = 'koji'
        else:
            builder = 'brew'
    cmd = [builder, "download-build", "--quiet", "--arch=src", srpm_name]
    run(cmd, workdir=tmp_dir, can_fail=False)
    return os.path.join(tmp_dir, "%s.src.rpm" % srpm_name)
