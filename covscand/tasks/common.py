# -*- coding: utf-8 -*-
"""
Common functions for tasks, DRY
"""

import re
import os
from kobo.shortcuts import run


def construct_cim_string(cim_dict):
    """
        cim_dict = {
            'user': 'user',
            'passwd': 'passwd',
            'server': 'server',
            'port': '1234',
            'stream': 'stream',
        }
        None if there is no value for the option

        construct string:
            user:passwd[@server:port[/stream]]
    """
    # user wants default options, we have to suply empty string
    if cim_dict['user'] is None:
        return ''
    else:
        result_string = "%s:%s" % (cim_dict['user'], cim_dict['passwd'])
        if cim_dict['server'] is not None:
            result_string += "@%s:%s" % (cim_dict['server'], cim_dict['port'])
            if cim_dict['stream'] is not None:
                result_string += "/%s" % cim_dict['stream']
    return result_string


def downloadSRPM(tmp_dir, srpm_name):
    """
    Download SRPM from brew or koji. If disttag starts with 'fc', use koji,
    if it starts with 'el', use brew, if build is not there, use koji.
    """
    path = os.path.join(tmp_dir, "%s.src.rpm" % srpm_name)
    dist_tag = re.search('.*-.*-(.*)', srpm_name).group(1)
    downloaded = True
    builder = 'brew'
    if 'fc' in dist_tag:
        builder = 'koji'
    cmd = [builder, "download-build", "--quiet", "--arch=src", srpm_name]
    try:
        run(cmd, workdir=tmp_dir, can_fail=False)
        if os.path.exists(path):
            return path
        else:
            downloaded = False
    except RuntimeError:
        downloaded = False
    if not downloaded:
        if builder == 'brew':
            builder = 'koji'
        else:
            builder = 'brew'
    cmd = [builder, "download-build", "--quiet", "--arch=src", srpm_name]
    run(cmd, workdir=tmp_dir, can_fail=False)
    return os.path.join(tmp_dir, "%s.src.rpm" % srpm_name)
