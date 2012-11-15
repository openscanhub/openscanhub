# -*- coding: utf-8 -*-
"""
    This module contains several services provided to XML-RPC calls mostly
"""

import os
import pipes
import shutil
import copy

from kobo.hub.models import Task
from kobo.shortcuts import run
from kobo.django.upload.models import FileUpload

from models import Scan, SCAN_STATES
from covscanhub.other.shortcuts import get_mock_by_name, check_brew_build,\
    check_and_create_dirs
from covscanhub.other.constants import ERROR_DIFF_FILE, FIXED_DIFF_FILE,\
    ERROR_HTML_FILE, FIXED_HTML_FILE

import django.utils.simplejson as json
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from messaging import send_message

__all__ = (
    "update_scans_state",
    "run_diff",
    "extract_logs_from_tarball",
    "create_diff_task",
    'prepare_and_execute_diff',
    'post_qpid_message',
)


def update_scans_state(scan_id, state):
    """
    update state of scan with 'scan_id'

    TODO: add transaction most likely
    """
    scan = Scan.objects.get(id=scan_id)
    scan.state = state
    scan.save()


def add_title_to_json(path, title):
    fd = open(path, "r+")
    loaded_json = json.load(fd)
    loaded_json['scan']['title'] = title
    fd.seek(0)
    fd.truncate()
    json.dump(loaded_json, fd, indent=4)
    fd.close()

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

    #<task_dir>/<nvr>/run1/<nvr>.js
    old_err = os.path.join(base_task_dir, base_nvr, 'run1', base_nvr + '.js')
    new_err = os.path.join(task_dir, nvr, 'run1', nvr + '.js')

    if not os.path.exists(old_err) or not os.path.exists(new_err):
        raise RuntimeError('Error output from coverity does not exist: \
old: %s new: %s' % (old_err, new_err))

    #csdiff [options] old.err new.err
    """
      -c [ --coverity-output ]  write the result in Coverity format
      -x [ --fixed ]            print fixed defects (just swaps the arguments)
      -z [ --ignore-path ]      ignore directory structure when matching
      -j [ --json-output ]      write the result in JSON format
      -q [ --quiet ]            do not report any parsing errors
      --help                    produce help message
    """
    #whole csdiff call must be in one string, because character '>' cannot be
    #enclosed into quotes -- command '"csdiff" "-j" "old.err" "new.err" ">"
    #"csdiff.out"' does not work
    diff_cmd = ' '.join(['csdiff', '-j', pipes.quote(old_err),
                         pipes.quote(new_err), '>', diff_file_path])
    fixed_diff_cmd = ' '.join(['csdiff', '-jx', pipes.quote(old_err),
                              pipes.quote(new_err), '>',
                              fixed_diff_file_path])
    retcode, output = run(diff_cmd,
                          workdir=task_dir,
                          stdout=False,
                          can_fail=False,
                          logfile='csdiff.log',
                          return_stdout=False,
                          show_cmd=False)
    #command wasn't successfull -- handle this somehow
    if retcode != 0:
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
            raise RuntimeError("'%s' wasn't successfull; path: %s, code: %s" %
                               (diff_cmd, task_dir, retcode))

        add_title_to_json(diff_file_path, 'Newly introduced defects')        
        add_title_to_json(fixed_diff_file_path, 'Fixed defects')        

        run('cshtml --scan-props-placement bottom %s > %s' %
            (diff_file_path, html_file_path),
            workdir=task_dir, can_fail=True)
        run('cshtml --scan-props-placement bottom %s > %s' %
            (fixed_diff_file_path, fixed_html_file_path),
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

    #name was specified
    if name is not None and len(name) > 0:
        if os.path.isfile(os.path.join(task_dir, name)):
            tar_archive = os.path.join(task_dir, name)
        else:
            raise RuntimeError(
                'There is no tar ball with name %s for task %s'
                % (name, task_id))
    else:
        #name wasn't specified, guess tarball name:
        #file_base (nvr without srcrpm) + tar.xz|tar.lzma
        tarball_logs = os.path.join(task_dir, task.label + '.tar.xz')
        tarball_logs2 = os.path.join(task_dir, task.label + '.tar.lzma')
        if os.path.isfile(tarball_logs):
            tar_archive = tarball_logs
        elif os.path.isfile(tarball_logs2):
            tar_archive = tarball_logs2
        else:
            raise RuntimeError('There is no tarball (%s, %s) for task %s' %
                               (tarball_logs, tarball_logs2, task_id))

    if tar_archive is None:
        raise RuntimeError('There is no tarball specfied for task %s' %
                           (task_id))

    tmp_tar_file_name = 'tmp_%s' % os.path.split(tar_archive)[1]
    tmp_tar_archive = os.path.join(task_dir, tmp_tar_file_name)
    shutil.copy2(tar_archive, tmp_tar_archive)

    # unxz file.tar.xz|lzma && tar xf file.tar -C /output/directory
    # tar xvf file.tar.gz -C /output/directory
    if tmp_tar_archive.endswith('xz'):
        command = ' '.join(['unxz', pipes.quote(tmp_tar_archive),
                            '&&', 'tar', '-xf',
                            pipes.quote(tmp_tar_archive[:-3]),
                            '-C ' + pipes.quote(task_dir)])
    elif tmp_tar_archive.endswith('lzma'):
        command = ' '.join(['unxz', pipes.quote(tmp_tar_archive),
                            '&&', 'tar', '-xf',
                            pipes.quote(tmp_tar_archive[:-5]),
                            '-C ' + pipes.quote(task_dir)])
    elif tmp_tar_archive.endswith('gz'):
        command = ['tar', '-xzf', pipes.quote(tmp_tar_archive),
                   '-C ' + pipes.quote(task_dir)]
    else:
        raise RuntimeError('Unsupported compression format (%s), task id: %s' %
                           (tmp_tar_archive, task_id))
    try:
        run(command, can_fail=False, stdout=False)
#            logfile='/tmp/covscanhub_extract_tarball.log')
    except RuntimeError:
        raise RuntimeError('[%s] Unable to extract tarball archive %s \
I have used this command: %s' % (task_id, tar_archive, command))

    #clean temporary file tmp_<nvr>.tar
    if os.path.exists(tmp_tar_archive):
        os.remove(tmp_tar_archive)
    if os.path.exists(tmp_tar_archive[:-5]) and \
            tmp_tar_archive[:-5].endswith('.tar'):
        os.remove(tmp_tar_archive[:-5])
    if os.path.exists(tmp_tar_archive[:-3]) and \
            tmp_tar_archive[:-3].endswith('.tar'):
        os.remove(tmp_tar_archive[:-3])


def create_base_diff_task(kwargs, parent_id):
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
    options = {}

    base_srpm = kwargs.get('base_srpm', None)
    base_brew_build = kwargs.get('base_brew_build', None)
    base_upload_id = kwargs.get('base_upload_id', None)

    #from request.user
    task_user = kwargs['task_user']

    #Label, description or any reason for this task.
    task_label = base_srpm or base_brew_build

    base_mock = kwargs['base_mock']
    priority = kwargs.get('priority', 10) + 1
    comment = kwargs.get('comment', '')

    options["mock_config"] = base_mock

    if base_brew_build:
        options['brew_build'] = check_brew_build(base_brew_build)
    elif base_upload_id:
        try:
            upload = FileUpload.objects.get(id=base_upload_id)
        except:
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
        state=SCAN_STATES["QUEUED"],
        priority=priority,
        parent_id=parent_id,
    )
    task_dir = Task.get_task_dir(task_id)

    check_and_create_dirs(task_dir)

    if base_upload_id:
        # move file to task dir, remove upload record and make the task available
        shutil.move(srpm_path, os.path.join(task_dir, os.path.basename(srpm_path)))
        upload.delete()


def create_diff_task(kwargs):
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
    options = {}

    task_user = kwargs['task_user']

    nvr_srpm = kwargs.get('nvr_srpm', None)
    nvr_brew_build = kwargs.get('nvr_brew_build', None)
    nvr_upload_id = kwargs.get('nvr_upload_id', None)

    options['keep_covdata'] = kwargs.pop("keep_covdata", False)
    options['all'] = kwargs.pop("all", False)
    options['security'] = kwargs.pop("security", False)

    #Label, description or any reason for this task.
    task_label = nvr_srpm or nvr_brew_build

    nvr_mock = kwargs['nvr_mock']
    base_mock = kwargs['base_mock']
    priority = kwargs.get('priority', 10)
    comment = kwargs.get('comment', '')

    #does mock config exist?
    get_mock_by_name(nvr_mock)
    options["mock_config"] = nvr_mock
    #if base config is invalid target task isn't submited, is this alright?
    get_mock_by_name(base_mock)

    #Test if SRPM exists
    if nvr_brew_build:
        options['brew_build'] = check_brew_build(nvr_brew_build)
    elif nvr_upload_id:
        try:
            upload = FileUpload.objects.get(id=nvr_upload_id)
        except:
            raise ObjectDoesNotExist("Can't find uploaded file with id: %s" % nvr_upload_id)

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
        state=SCAN_STATES["QUEUED"],
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
    create_base_diff_task(copy.deepcopy(kwargs), task_id)

    # wait has to be after creation of new subtask
    # TODO wait should be executed in one transaction with creation of
    # child
    parent_task.wait()

    return task_id


def prepare_and_execute_diff(task, base_task, nvr, base_nvr):
    task_dir = Task.get_task_dir(task.id)
    base_task_dir = Task.get_task_dir(base_task.id)

    return run_diff(task_dir, base_task_dir, nvr, base_nvr)


def post_qpid_message(scan_id, scan_state):
    s = copy.deepcopy(settings.QPID_CONNECTION)
    s['KRB_PRINCIPAL'] = settings.KRB_AUTH_PRINCIPAL
    s['KRB_KEYTAB'] = settings.KRB_AUTH_KEYTAB
    send_message(s, {'scan_id': scan_id, 'scan_state': scan_state}, 'finished')


def get_latest_scan_by_package(tag, package):
    """
    return latest scan for specified package and tag. This function should be
    called when creating new scan and setting this one as a child
    """
    try:
        return Scan.objects.get(package=package, tag=tag, parent=None)
    except ObjectDoesNotExist:
        return None