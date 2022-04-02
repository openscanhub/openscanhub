# -*- coding: utf-8 -*-
"""
Util functions related to processing data -- results of analysis
"""

import os
import pipes
import logging
import json

from covscanhub.other.decorators import public
from covscancommon.constants import *

from kobo.shortcuts import run
from covscanhub.service.path import TaskResultPaths


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


class TaskDiffer(object):
    def __init__(self, task, base_task):
        self.task = task
        self.base_task = base_task
        self.paths = TaskResultPaths(task)
        self.base_paths = TaskResultPaths(base_task)

    def generate_diff_files(self):
        """
        create diffs, html reports and .err files
        """
        succ = csdiff_new_defects(
            self.base_paths.get_json_results(),
            self.paths.get_json_results(),
            self.paths.get_json_added(),
            self.paths.task_dir
        )
        if succ:
            f_succ = csdiff_new_defects(
                self.paths.get_json_results(),
                self.base_paths.get_json_results(),
                self.paths.get_json_fixed(),
                self.paths.task_dir
            )

            if f_succ:
                # these are basicly optional, don't fail if one of them
                # was not successfull
                add_title_to_json(self.paths.get_json_added(), 'Newly introduced defects')
                add_title_to_json(self.paths.get_json_fixed(), 'Fixed defects')

                cshtml(self.paths.get_json_added(), self.paths.get_html_added(), self.paths.task_dir)
                cshtml(self.paths.get_json_fixed(), self.paths.get_html_fixed(), self.paths.task_dir)
                csgrep_err(self.paths.get_json_added(), self.paths.get_txt_added(), self.paths.task_dir)
                csgrep_err(self.paths.get_json_fixed(), self.paths.get_txt_fixed(), self.paths.task_dir)
            else:
                return False
        else:
            return False
        return True

    def diff_results(self):
        """ generate diff files for VersionDiffBuild task """
        try:
            self.paths.get_json_results()
        except RuntimeError:
            raise RuntimeError('Base results do not exist')
        try:
            self.base_paths.get_json_results()
        except RuntimeError:
            raise RuntimeError('Target results do not exist')
        return self.generate_diff_files()


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
def task_has_results(task):
    trp = TaskResultPaths(task)
    try:
        return os.path.exists(trp.get_json_results())
    except RuntimeError:
        return False


@public
def task_is_diffed(task):
    trp = TaskResultPaths(task)
    return os.path.exists(trp.get_json_added()) or os.path.exists(trp.get_json_fixed())
