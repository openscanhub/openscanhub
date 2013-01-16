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
    dist_tag = re.search('.*-.*-(.*).', srpm_name).group(1)
    builder = 'brew'
    if 'fc' in dist_tag:
        builder = 'koji'
    cmd = [builder, "download-build", "--quiet", "--arch=src", srpm_name]
    try:
        run(cmd, workdir=tmp_dir, can_fail=False)
    except RuntimeError:
        if builder == 'brew':
            builder = 'koji'
            cmd = [builder, "download-build", "--quiet",
                   "--arch=src", srpm_name]
            run(cmd, workdir=tmp_dir, can_fail=False)
        else:
            raise
    return os.path.join(tmp_dir, "%s.src.rpm" % srpm_name)