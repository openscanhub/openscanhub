# -*- coding: utf-8 -*-
"""
    This module contains several services provided to XML-RPC calls mostly
"""

from __future__ import absolute_import

import copy
import logging
import os
import pipes
import shutil

from django.core.exceptions import ObjectDoesNotExist
from kobo.client.constants import TASK_STATES
from kobo.django.upload.models import FileUpload
from kobo.hub.models import Task
from kobo.shortcuts import run

from osh.hub.other.decorators import public
from osh.hub.other.exceptions import ScanException
from osh.hub.other.shortcuts import (check_and_create_dirs,
                                        check_brew_build, get_mock_by_name)
from osh.hub.service.processing import add_title_to_json
from osh.common.constants import (ERROR_DIFF_FILE, ERROR_HTML_FILE,
                                  ERROR_TXT_FILE, FIXED_DIFF_FILE,
                                  FIXED_HTML_FILE, FIXED_TXT_FILE)

from .models import (SCAN_STATES, SCAN_STATES_FINISHED_WELL, SCAN_TYPES_TARGET,
                     Analyzer, Scan, ScanBinding)

logger = logging.getLogger(__name__)


@public
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
    diff_cmd = ' '.join(['csdiff', '-jz', pipes.quote(old_err),
                         pipes.quote(new_err), '>', diff_file_path])
    fixed_diff_cmd = ' '.join(['csdiff', '-jxz', pipes.quote(old_err),
                              pipes.quote(new_err), '>',
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


@public
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
        command = ' '.join(['xz', '-cd', pipes.quote(tar_archive),
                            '|', 'tar', '-x', r'--exclude=\*.cov',
                            r'--exclude=\*cov-html',
                            '-C ' + pipes.quote(task_dir)])
    elif tar_archive.endswith('lzma'):
        command = ' '.join(['xz', '-cd', '--format=lzma',
                            pipes.quote(tar_archive),
                            '|', 'tar', '-x', r'--exclude=\*.cov',
                            r'--exclude=\*cov-html',
                            '-C ' + pipes.quote(task_dir)])
    elif tar_archive.endswith('gz'):
        command = ['tar', '-xzf',
                   pipes.quote(tar_archive),
                   r'--exclude=\*.cov', r'--exclude=\*cov-html',
                   '-C ' + pipes.quote(task_dir)]
    else:
        raise RuntimeError('Unsupported compression format (%s), task id: %s' %
                           (tar_archive, task_id))
    try:
        run(command, can_fail=False, stdout=False)
#            logfile='/tmp/covscanhub_extract_tarball.log')
    except RuntimeError:
        raise RuntimeError('[%s] Unable to extract tarball archive %s \
I have used this command: %s' % (task_id, tar_archive, command))


def create_base_diff_task(hub_opts, task_opts, parent_id):
    """
        create scan of a package and perform diff on results against specified
        version
        options of this scan are in dict 'kwargs'

        kwargs
         - task_user - username from request.user.username
         - nvr_srpm - name, version, release of scanned package
         - nvr_upload_id - upload id for target, so worker is able to download it
         - nvr_brew_build - NVR of package to be downloaded from brew
         - base_srpm - name, version, release of base package
         - base_upload_id - upload id for base, so worker is able to download it
         - base_brew_build - NVR of base package to be downloaded from brew
         - nvr_mock - mock config
         - base_mock - mock config
    """
    options = task_opts or {}

    base_srpm = hub_opts.get('base_srpm', None)
    base_brew_build = hub_opts.get('base_brew_build', None)
    base_upload_id = hub_opts.get('base_upload_id', None)

    # from request.user
    task_user = hub_opts['task_user']

    # Label, description or any reason for this task.
    task_label = base_srpm or base_brew_build

    base_mock = hub_opts['base_mock']
    priority = hub_opts.get('priority', 10) + 1
    comment = hub_opts.get('comment', '')

    options["mock_config"] = base_mock

    if base_brew_build:
        options['brew_build'] = check_brew_build(base_brew_build)
    elif base_upload_id:
        try:
            upload = FileUpload.objects.get(id=base_upload_id)
        except FileUpload.DoesNotExist:
            raise ObjectDoesNotExist("Can't find uploaded file with id: %s" % base_upload_id)

        if upload.owner.username != task_user:
            raise RuntimeError("Can't process a file uploaded by a different user")

        srpm_path = os.path.join(upload.target_dir, upload.name)
        options["srpm_name"] = upload.name
        # cut .src.rpm suffix, because run_diff and extractTarball rely on this
        task_label = options["srpm_name"][:-8]
    else:
        raise RuntimeError('Target build is not specified!')

    task_id = Task.create_task(
        owner_name=task_user,
        label=task_label,
        method='VersionDiffBuild',
        args=options,
        comment=comment,
        state=TASK_STATES["FREE"],
        priority=priority,
        parent_id=parent_id,
    )
    task_dir = Task.get_task_dir(task_id)

    check_and_create_dirs(task_dir)

    if base_upload_id:
        # move file to task dir, remove upload record and make the task available
        shutil.move(srpm_path, os.path.join(task_dir, os.path.basename(srpm_path)))
        upload.delete()


@public
def create_diff_task(hub_opts, task_opts):
    """
        create scan of a package and perform diff on results against specified
        version
        Options for task are stored in 'task_opts'
        options of this scan are in dict 'hub_opts':

        hub_opts
         - task_user - username from request.user.username
         - nvr_srpm - name, version, release of scanned package
         - nvr_upload_id - upload id for target, so worker is able to download it
         - nvr_brew_build - NVR of package to be downloaded from brew
         - base_srpm - name, version, release of base package
         - base_upload_id - upload id for base, so worker is able to download it
         - base_brew_build - NVR of base package to be downloaded from brew
         - nvr_mock - mock config
         - base_mock - mock config
    """
    options = task_opts or {}

    task_user = hub_opts['task_user']

    nvr_srpm = hub_opts.get('nvr_srpm', None)
    nvr_brew_build = hub_opts.get('nvr_brew_build', None)
    base_brew_build = hub_opts.get('base_brew_build', None)
    nvr_upload_id = hub_opts.get('nvr_upload_id', None)
    analyzers = hub_opts.pop("analyzers", None)

    # Label, description or any reason for this task.
    task_label = nvr_srpm or nvr_brew_build

    nvr_mock = hub_opts['nvr_mock']
    base_mock = hub_opts['base_mock']
    priority = hub_opts.get('priority', 10)
    comment = hub_opts.get('comment', '')

    # does mock config exist?
    get_mock_by_name(nvr_mock)
    options["mock_config"] = nvr_mock
    # if base config is invalid target task isn't submited, is this alright?
    get_mock_by_name(base_mock)

    # Test if SRPM exists
    if base_brew_build:
        check_brew_build(base_brew_build)
    if nvr_brew_build:
        options['brew_build'] = check_brew_build(nvr_brew_build)
    elif nvr_upload_id:
        try:
            upload = FileUpload.objects.get(id=nvr_upload_id)
        except FileUpload.DoesNotExist:
            raise ObjectDoesNotExist("Can't find uploaded file with id: %s" % nvr_upload_id)

        if upload.owner.username != task_user:
            raise RuntimeError("Can't process a file uploaded by a different user")

        srpm_path = os.path.join(upload.target_dir, upload.name)
        options["srpm_name"] = upload.name
        # cut .src.rpm suffix, because run_diff and extractTarball rely on this
        task_label = options["srpm_name"][:-8]
    else:
        raise RuntimeError('Target build is not specified!')

    if analyzers:
        an_conf = Analyzer.objects.get_opts(analyzers)
        options.update(an_conf)
        task_opts.update(an_conf)

    task_id = Task.create_task(
        owner_name=task_user,
        label=task_label,
        method='VersionDiffBuild',
        args=options,
        comment=comment,
        state=TASK_STATES["FREE"],
        priority=priority
    )
    task_dir = Task.get_task_dir(task_id)

    check_and_create_dirs(task_dir)

    if nvr_upload_id:
        # move file to task dir, remove upload record and make the task
        # available
        shutil.move(srpm_path, os.path.join(task_dir,
                                            os.path.basename(srpm_path)))
        upload.delete()

    parent_task = Task.objects.get(id=task_id)
    create_base_diff_task(copy.deepcopy(hub_opts), task_opts, task_id)

    # wait has to be after creation of new subtask
    # TODO wait should be executed in one transaction with creation of
    # child
    parent_task.wait()

    return task_id


@public
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


@public
def diff_new_defects_in_package(sb):
    try:
        return sb.scan.get_first_scan_binding().result.\
            new_defects_count() - sb.result.new_defects_count()
    except ObjectDoesNotExist:
        return 0
    except AttributeError:
        return 0


@public
def diff_fixed_defects_in_package(sb):
    try:
        return sb.scan.get_first_scan_binding().result.\
            fixed_defects_count() - sb.result.fixed_defects_count()
    except ObjectDoesNotExist:
        return 0
    except AttributeError:
        return 0


@public
def diff_defects_between_releases(sb, d_type):
    try:
        previous = ScanBinding.objects.get(scan__enabled=True,
                                           scan__package=sb.scan.package,
                                           scan__tag__release=sb.scan.tag.release.child)
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


@public
def diff_fixed_defects_between_releases(scan):
    return diff_defects_between_releases(scan, 'f')


@public
def diff_new_defects_between_releases(scan):
    return diff_defects_between_releases(scan, 'n')


@public
def get_latest_binding(scan_nvr, show_failed=False):
    """Return latest binding for specified nvr"""
    if show_failed:
        query = ScanBinding.objects.filter(scan__nvr=scan_nvr)
    else:
        query = ScanBinding.objects.filter(
            scan__nvr=scan_nvr,
            result__isnull=False).exclude(
                scan__state=SCAN_STATES['FAILED'])
    if query:
        # '-date' -- latest; 'date' -- oldest
        latest_submitted = query.order_by('-scan__date_submitted')[0]
        if (latest_submitted.scan.state == SCAN_STATES['QUEUED']
                or latest_submitted.scan.state == SCAN_STATES['SCANNING']
                or latest_submitted.result is None):
            return latest_submitted
        else:
            return query.latest()
    else:
        return None


@public
def get_used_releases():
    """ return tuple of used releases for search form """
    return list(Scan.targets.all().values_list('tag__release__id',
                'tag__release__product', 'tag__release__release').distinct()
                .filter(tag__release__product__isnull=False,
                        tag__release__release__isnull=False))
