# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

"""
    This module contains several services provided to XML-RPC calls mostly
"""


import logging
import os
import shlex

from django.core.exceptions import ObjectDoesNotExist
from kobo.hub.models import Task
from kobo.shortcuts import run

from osh.common.constants import (ERROR_DIFF_FILE, ERROR_HTML_FILE,
                                  ERROR_TXT_FILE, FIXED_DIFF_FILE,
                                  FIXED_HTML_FILE, FIXED_TXT_FILE)
from osh.hub.other.exceptions import ScanException
from osh.hub.service.processing import add_title_to_json

from .models import (SCAN_STATES, SCAN_STATES_FINISHED_WELL, SCAN_TYPES_TARGET,
                     Scan, ScanBinding)

logger = logging.getLogger(__name__)


def run_diff(task_dir, base_task_dir, nvr, base_nvr):
    """
        Runs 'csdiff' and 'csdiff -x' command for results of scan with id
        'scan_id' against its base scan
        Also executes command cshtml so users are able to browse files
        Returns size of output file
    """
    diff_file_path = os.path.join(task_dir, ERROR_DIFF_FILE)
    fixed_diff_file_path = os.path.join(task_dir, FIXED_DIFF_FILE)
    html_file_path = os.path.join(task_dir, ERROR_HTML_FILE)
    fixed_html_file_path = os.path.join(task_dir, FIXED_HTML_FILE)
    txt_file_path = os.path.join(task_dir, ERROR_TXT_FILE)
    fixed_txt_file_path = os.path.join(task_dir, FIXED_TXT_FILE)
    compl_html_file_path = os.path.join(task_dir, nvr + '.html')
    # <task_dir>/<nvr>/run1/<nvr>.js
    old_err = os.path.join(base_task_dir, base_nvr, 'run1', base_nvr + '.js')
    new_err = os.path.join(task_dir, nvr, 'run1', nvr + '.js')

    if not os.path.exists(old_err) or not os.path.exists(new_err):
        logger.critical('Error output from csmock does not exist: \
old: %s new: %s', old_err, new_err)
        raise ScanException('Error output from csmock does not exist: \
old: %s new: %s', old_err, new_err)

    # csdiff [options] old.err new.err
    # whole csdiff call must be in one string, because character '>' cannot be
    # enclosed into quotes -- command '"csdiff" "-j" "old.err" "new.err" ">"
    # "csdiff.out"' does not work
    diff_cmd = ' '.join(['csdiff', '-jz', shlex.quote(old_err),
                         shlex.quote(new_err), '>', diff_file_path])
    fixed_diff_cmd = ' '.join(['csdiff', '-jxz', shlex.quote(old_err),
                              shlex.quote(new_err), '>',
                              fixed_diff_file_path])
    retcode, output = run(diff_cmd,
                          workdir=task_dir,
                          stdout=False,
                          can_fail=False,
                          logfile='csdiff.log',
                          return_stdout=False,
                          show_cmd=False)
    # command wasn't successfull -- handle this somehow
    if retcode != 0:
        logger.critical("'%s' wasn't successfull; path: %s, code: %s",
                        diff_cmd, task_dir, retcode)
        raise RuntimeError("'%s' wasn't successfull; path: %s, code: %s" %
                           (diff_cmd, task_dir, retcode))
    else:
        retcode, output = run(fixed_diff_cmd,
                              workdir=task_dir,
                              stdout=False,
                              can_fail=False,
                              logfile='csdiff_fixed.log',
                              return_stdout=False,
                              show_cmd=False)
        if retcode != 0:
            logger.critical("'%s' wasn't successfull; path: %s, code: %s",
                            fixed_diff_cmd, task_dir, retcode)
            raise RuntimeError("'%s' wasn't successfull; path: %s, code: %s" %
                               (fixed_diff_cmd, task_dir, retcode))

        add_title_to_json(diff_file_path, 'Newly introduced defects')
        add_title_to_json(fixed_diff_file_path, 'Fixed defects')

        run('cshtml --scan-props-placement bottom %s > %s' %
            (diff_file_path, html_file_path),
            workdir=task_dir, can_fail=True)
        run('cshtml --scan-props-placement bottom %s > %s' %
            (fixed_diff_file_path, fixed_html_file_path),
            workdir=task_dir, can_fail=True)
        run('cshtml --scan-props-placement bottom %s > %s' %
            (new_err, compl_html_file_path),
            workdir=task_dir, can_fail=True)
        run('csgrep %s > %s' %
            (diff_file_path, txt_file_path),
            workdir=task_dir, can_fail=True)
        run('csgrep %s > %s' %
            (fixed_diff_file_path, fixed_txt_file_path),
            workdir=task_dir, can_fail=True)


def extract_logs_from_tarball(task_id, name=None):
    """
        Extracts files from tarball for specified task.

        currently (sep 2012) module tarfile does not support lzma compression
        so I used program tar (and xz, because RHEL5 does not have latest tar
        program with lzma compression support)
    """
    task = Task.objects.get(id=task_id)
    task_dir = task.get_task_dir(task.id)

    tar_archive = None

    # name was specified
    if name is not None and len(name) > 0:
        if os.path.isfile(os.path.join(task_dir, name)):
            tar_archive = os.path.join(task_dir, name)
        else:
            raise RuntimeError(
                'There is no tar ball with name %s for task %s'
                % (name, task_id))
    else:
        # name wasn't specified, guess tarball name:
        # file_base (nvr without srcrpm) + tar.xz|tar.lzma
        file_base = task.label
        if file_base.endswith('.src.rpm'):
            file_base = file_base[:-8]
        tarball_logs = os.path.join(task_dir, file_base + '.tar.xz')
        tarball_logs2 = os.path.join(task_dir, file_base + '.tar.lzma')
        if os.path.isfile(tarball_logs):
            tar_archive = tarball_logs
        elif os.path.isfile(tarball_logs2):
            tar_archive = tarball_logs2
        else:
            error_string = 'There is no tarball (%s, %s) for task %s' % \
                (tarball_logs, tarball_logs2, task_id)
            logger.error(error_string)
            raise RuntimeError(error_string)

    if tar_archive is None:
        raise RuntimeError('There is no tarball specfied for task %s' %
                           (task_id))

    # xz -cd asd.tar.xz | tar -x --exclude=\*.cov -C ./test/
    # tar -xzf file.tar.gz -C /output/directory
    if tar_archive.endswith('xz'):
        command = ' '.join(['xz', '-cd', shlex.quote(tar_archive),
                            '|', 'tar', '-x', r'--exclude=\*.cov',
                            r'--exclude=\*cov-html',
                            '-C ' + shlex.quote(task_dir)])
    elif tar_archive.endswith('lzma'):
        command = ' '.join(['xz', '-cd', '--format=lzma',
                            shlex.quote(tar_archive),
                            '|', 'tar', '-x', r'--exclude=\*.cov',
                            r'--exclude=\*cov-html',
                            '-C ' + shlex.quote(task_dir)])
    elif tar_archive.endswith('gz'):
        command = ['tar', '-xzf',
                   shlex.quote(tar_archive),
                   r'--exclude=\*.cov', r'--exclude=\*cov-html',
                   '-C ' + shlex.quote(task_dir)]
    else:
        raise RuntimeError('Unsupported compression format (%s), task id: %s' %
                           (tar_archive, task_id))
    try:
        run(command, can_fail=False, stdout=False)
    except RuntimeError:
        raise RuntimeError('[%s] Unable to extract tarball archive %s \
I have used this command: %s' % (task_id, tar_archive, command))


def get_latest_sb_by_package(release, package):
    """
    return latest scan for specified package and release.
    This function should be called when creating new scan and setting this one
    as a child
    """
    bindings = ScanBinding.objects.filter(
        scan__package=package,
        scan__tag__release=release,
        scan__state__in=SCAN_STATES_FINISHED_WELL,
        scan__scan_type__in=SCAN_TYPES_TARGET,
    )
    if bindings:
        return bindings.latest()


def diff_new_defects_in_package(sb):
    try:
        return sb.scan.get_first_scan_binding().result.\
            new_defects_count() - sb.result.new_defects_count()
    except ObjectDoesNotExist:
        return 0
    except AttributeError:
        return 0


def diff_fixed_defects_in_package(sb):
    try:
        return sb.scan.get_first_scan_binding().result.\
            fixed_defects_count() - sb.result.fixed_defects_count()
    except ObjectDoesNotExist:
        return 0
    except AttributeError:
        return 0


def diff_defects_between_releases(sb, d_type):
    try:
        previous = ScanBinding.objects.filter(scan__enabled=True,
                                              scan__package=sb.scan.package,
                                              scan__tag__release=sb.scan.tag.release.child).latest()
        if d_type == 'f':
            return sb.result.fixed_defects_count() - \
                previous.result.fixed_defects_count()
        elif d_type == "n":
            return sb.result.new_defects_count() - \
                previous.result.new_defects_count()
    except ObjectDoesNotExist:
        return 0
    except AttributeError:
        return 0


def diff_fixed_defects_between_releases(scan):
    return diff_defects_between_releases(scan, 'f')


def diff_new_defects_between_releases(scan):
    return diff_defects_between_releases(scan, 'n')


def get_latest_binding(scan_nvr):
    """Return latest binding for specified nvr"""
    query = ScanBinding.objects.filter(
        scan__nvr=scan_nvr,
        result__isnull=False).exclude(scan__state=SCAN_STATES['FAILED'])

    if not query:
        return None

    # '-date' -- latest; 'date' -- oldest
    latest_submitted = query.order_by('-scan__date_submitted')[0]
    if (latest_submitted.scan.state == SCAN_STATES['QUEUED']
            or latest_submitted.scan.state == SCAN_STATES['SCANNING']
            or latest_submitted.result is None):
        return latest_submitted

    return query.latest()


def get_used_releases():
    """ return tuple of used releases for search form """
    return list(Scan.targets.all().values_list('tag__release__id',
                'tag__release__product', 'tag__release__release').distinct()
                .filter(tag__release__product__isnull=False,
                        tag__release__release__isnull=False))
