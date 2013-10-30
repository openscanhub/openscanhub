# -*- coding: utf-8 -*-
"""
Util functions related to processing data -- results of analysis
"""

import os
import pipes
import logging
from django.utils import simplejson as json

from covscanhub.other.decorators import public
from covscanhub.other.constants import *

from kobo.shortcuts import run


logger = logging.getLogger(__name__)


def _run(command, workdir):
    """ kobo.shortcuts.run wrapper with predefined setup and logging """
    retcode, output = run(command,
                          workdir=workdir,
                          stdout=False,
                          can_fail=True,
                          return_stdout=False,
                          show_cmd=False)
    if retcode != 0:
        logger.critical("'%s' wasn't successfull; path: %s, code: %s",
                        command, workdir, retcode)
    return retcode == 0


def csdiff(old, new, result, workdir):
    """
    use csdiff with constants.CSDIFF_ARGS arguments
    compare `old` and `new` files and store the diff in `result`
    all three files have '.err' type
    """
    #whole csdiff call must be in one string, because character '>' cannot be
    #enclosed into quotes -- command '"csdiff" "-j" "old.err" "new.err" ">"
    #"csdiff.out"' does not work
    diff_cmd = ' '.join(['csdiff', CSDIFF_ARGS, pipes.quote(old),
                         pipes.quote(new), '>', result])
    return _run(diff_cmd, workdir)


def csdiff_new_defects(old, new, result, task_dir):
    """ create file with newly introduced defects """
    return csdiff(old, new, result, task_dir)


def csdiff_fixed_defects(old, new, result, task_dir):
    """ create file with fixed defects """
    return csdiff(new, old, result, task_dir)


def cshtml(input_file, output_file, workdir):
    """ generate HTML report """
    cmd = 'csgrep --prune-events 1 --mode json %s | cshtml - > %s' % \
        (input_file, output_file)
    return _run(cmd, workdir)


def csgrep_err(input_file, output_file, workdir):
    """ generate ERR text files """
    cmd = 'csgrep --prune-events 1 %s > %s' % (input_file, output_file)
    return _run(cmd, workdir)


def generate_diff_files(paths, task_dir):
    """
    create diffs, html reports and .err files using provided 'paths' (dict):
    { 'new': err file of newer run
      'old': err file of older run
      'added': js file of newly introduced defects
      'fixed': js file of fixed defects
      'added_err': err text file of newly introduced defects
      'fixed_err': err text file of fixed defects
      'added_html': HTML report of newly introduced defects
      'fixed_html': HTML report of fixed defects
    }
    taskdir -- name of dir where all the files exist
    """
    p = paths  # shortcut
    succ = csdiff_new_defects(p['old'], p['new'], p['added'], task_dir)
    if succ:
        f_succ = csdiff_fixed_defects(p['old'], p['new'], p['fixed'], task_dir)

        if f_succ:
            # these are basicly optional, don't fail if one of them
            # was not successfull
            add_title_to_json(p['added'], 'Newly introduced defects')
            add_title_to_json(p['fixed'], 'Fixed defects')

            cshtml(p['added'], p['added_html'], task_dir)
            cshtml(p['fixed'], p['fixed_html'], task_dir)
            csgrep_err(p['added'], p['added_err'], task_dir)
            csgrep_err(p['fixed'], p['fixed_err'], task_dir)
        else:
            return False
    else:
        return False
    return True


def get_output_filenames(path):
    """ build path names for output files """
    p = {}
    p['added'] = os.path.join(path, ERROR_DIFF_FILE)
    p['fixed'] = os.path.join(path, FIXED_DIFF_FILE)
    p['added_html'] = os.path.join(path, ERROR_HTML_FILE)
    p['fixed_html'] = os.path.join(path, FIXED_HTML_FILE)
    p['added_err'] = os.path.join(path, ERROR_TXT_FILE)
    p['fixed_err'] = os.path.join(path, FIXED_TXT_FILE)
    return p


def get_input_filenames_task(base_path, base_nvr, path, nvr):
    """ build path names for VersionDiffBuild task """
    p = {}
    # task dir structure: <task_dir>/<nvr>/run1/<nvr>.js
    p['old'] = os.path.join(base_path, base_nvr, 'run1', SCAN_RESULTS_FILENAME)
    p['new'] = os.path.join(path, nvr, 'run1', SCAN_RESULTS_FILENAME)
    return p


def get_input_filenames_scan(base_path, base_nvr, path, nvr):
    """ build path names for ErrataDiffBuild task """
    p = {}
    # task dir structure: <task_dir>/<nvr>/run1/<nvr>.js
    p['old'] = os.path.join(base_path, base_nvr, 'run1', base_nvr + '.js')
    p['new'] = os.path.join(path, nvr, 'run1', nvr + '.js')
    return p


@public
def diff_results(task_dir, base_task_dir, nvr, base_nvr):
    """ generate diff files for VersionDiffBuild task """
    p = get_output_filenames(task_dir)
    p.update(get_input_filenames_task(base_task_dir, base_nvr, task_dir, nvr))
    return generate_diff_files(p, task_dir)


@public
def scan_diff(task_dir, base_task_dir, nvr, base_nvr):
    """ generate diff files for ErrataDiffBuild task """
    p = get_output_filenames(task_dir)
    p.update(get_input_filenames_scan(base_task_dir, base_nvr, task_dir, nvr))
    return generate_diff_files(p, task_dir)


@public
def add_title_to_json(path, title):
    fd = open(path, "r+")
    loaded_json = json.load(fd)
    loaded_json['scan']['title'] = title
    fd.seek(0)
    fd.truncate()
    json.dump(loaded_json, fd, indent=4)
    fd.close()


@public
def task_has_newstyle_results(task):
    logs_list = task.logs.list

    res_3 = lambda x: x.endswith(('results.html',
                                  'results.err', 'results.js'))
    return len(filter(res_3, logs_list)) >= 3
