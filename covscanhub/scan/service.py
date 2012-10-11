# -*- coding: utf-8 -*-
"""
    This module contains several services provided to XML-RPC calls mostly
"""

import os
import pipes
#import messaging.send_message
import shutil
import copy

from kobo.hub.models import Task
from models import Scan, SCAN_STATES
from kobo.shortcuts import run
from covscanhub.other.shortcuts import get_mock_by_name, check_brew_build

ET_SCAN_PRIORITY = 20

__all__ = (
    "update_scans_state",
    "run_diff",
    "extract_logs_from_tarball",
    "create_diff_scan",
    "finish_scanning",
)


def update_scans_state(scan_id, state):
    """
    update state of scan with 'scan_id'

    TODO: add transaction most likely
    """
    scan = Scan.objects.get(id=scan_id)
    scan.state = state
    scan.save()


def run_diff(scan_id):
    """
        Runs 'csdiff' and 'csdiff -x' command for results of scan with id
        'scan_id' against its base scan
        Returns size of output file
    """
    scan = Scan.objects.get(id=scan_id)
    if not scan.base:
        print 'Cannot run diff command, there is no base scan \
for scan %s' % scan_id
        raise RuntimeError('Cannot run diff command, there is no base scan \
for scan %s' % scan_id)

    fixed_diff_file = 'csdiff_fixed.out'
    diff_file = 'csdiff.out'

    task_dir = Task.get_task_dir(scan.task.id)
    diff_file_path = os.path.join(task_dir, diff_file)
    fixed_diff_file_path = os.path.join(task_dir, fixed_diff_file)

    task_nvr = scan.nvr
    base_task_dir = Task.get_task_dir(scan.base.task.id)
    base_nvr = scan.base.nvr

    #<task_dir>/<nvr>/run1/<nvr>.err
    old_err = os.path.join(base_task_dir, base_nvr, 'run1', base_nvr + '.err')
    new_err = os.path.join(task_dir, task_nvr, 'run1', task_nvr + '.err')

    if not os.path.exists(old_err) or not os.path.exists(new_err):
        raise RuntimeError('Error output from coverity does not exist'
                               % scan_id)        

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
                          logfile='err_diff.log',
                          return_stdout=False,
                          show_cmd=False)
    #command wasn't successfull -- handle this somehow
    if retcode != 0:
        print "'%s' wasn't successfull; scan: %s path: %s, code: %s" % \
            (diff_cmd, scan_id, task_dir, retcode)
    else:
        retcode, output = run(fixed_diff_cmd,
                              workdir=task_dir,
                              stdout=False,
                              can_fail=False,
                              logfile='err_diff.log',
                              return_stdout=False,
                              show_cmd=False)
        if retcode != 0:
            print "'%s' wasn't successfull; scan: %s path: %s, code: %s" % \
                (fixed_diff_cmd, scan_id, task_dir, retcode)
    return os.path.getsize(diff_file_path)


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
        #label (nvr) + tar.xz|tar.lzma
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
#def send_qpid_message(message, key):
#    """
#        sends specified message to predefined broker, topic
#    """
#    messaging.send_message(django.conf.settings.qpid_connection, message, key)


def create_diff_base_scan(kwargs, parent_id):
    """
        create scan of a package and perform diff on results against specified
        version
        options of this scan are in dict 'kwargs'

        kwargs
         - scan_type - type of scan (SCAN_TYPES in covscanhub.scan.models)
         - task_user - username from request.user.username
         - username - name of user who is requesting scan
         - nvr - name, version, release of scanned package
         - base - nvr of previous version, the one to make diff against
         - nvr_mock - mock config
         - base_mock - mock config
    """
    options = {}

    #from request.user
    task_user = kwargs['task_user']

    #supplied by scan initiator
    #username = kwargs['username']
    #scan_type = kwargs['scan_type']
    nvr = kwargs['nvr']
    #base = kwargs['base']

    #Label, description or any reason for this task.
    task_label = nvr

    base_mock = kwargs['base_mock']
    priority = kwargs.get('priority', 10)
    comment = kwargs.get('comment', nvr)

    options["mock_config"] = base_mock

    task_id = Task.create_task(
        owner_name=task_user,
        label=task_label,
        method='VersionDiffBuild',
        args={},  # I want to add scan's id here, so I update it later
        comment=comment,
        state=SCAN_STATES["QUEUED"],
        priority=priority,
        parent_id=parent_id
    )
    task_dir = Task.get_task_dir(task_id)

    if not os.path.isdir(task_dir):
        try:
            os.makedirs(task_dir, mode=0755)
        except OSError, ex:
            if ex.errno != 17:
                raise
    """
    scan = Scan.create_scan(scan_type=scan_type, nvr=nvr, task_id=task_id,
                            tag=None, base=base_obj, username=username)

    options['scan_id'] = scan.id
    task = Task.objects.get(id=task_id)
    task.args = options
    task.save()
    """


def create_diff_scan(kwargs):
    """
        create scan of a package and perform diff on results against specified
        version
        options of this scan are in dict 'kwargs'

        kwargs
         - scan_type - type of scan (SCAN_TYPES in covscanhub.scan.models)
         - task_user - username from request.user.username
         - username - name of user who is requesting scan
         - nvr - name, version, release of scanned package
         - base - nvr of previous version, the one to make diff against
         - nvr_mock - mock config
         - base_mock - mock config
    """
    options = {}

    #from request.user
    task_user = kwargs['task_user']

    #supplied by scan initiator
    username = kwargs['username']
    scan_type = kwargs['scan_type']
    nvr = kwargs['nvr']
    base = kwargs['base']

    #Label, description or any reason for this task.
    task_label = nvr

    nvr_mock = kwargs['nvr_mock']
    base_mock = kwargs['base_mock']
    priority = kwargs.get('priority', 10)
    comment = kwargs.get('comment', nvr)

    #does mock config exist?
    get_mock_by_name(nvr_mock)
    options["mock_config"] = nvr_mock
    get_mock_by_name(base_mock)

    #Test if SRPM exists
    options['brew_build'] = check_brew_build(nvr)
    check_brew_build(base)

    task_id = Task.create_task(
        owner_name=task_user,
        label=task_label,
        method='VersionDiffBuild',
        args={},  # I want to add scan's id here, so I update it later
        comment=comment,
        state=SCAN_STATES["QUEUED"],
        priority=priority
    )
    task_dir = Task.get_task_dir(task_id)

    if not os.path.isdir(task_dir):
        try:
            os.makedirs(task_dir, mode=0755)
        except OSError, ex:
            if ex.errno != 17:
                raise

    parent_task = Task.objects.get(id=task_id)
    base_obj = None
    create_diff_base_scan(copy.deepcopy(kwargs), task_id)

    # wait has to be after creation of new subtask
    # TODO wait should be executed in one transaction with creation of
    # child
    parent_task.wait()

    scan = Scan.create_scan(scan_type=scan_type, nvr=nvr, task_id=task_id,
                            tag=None, base=base_obj, username=username)

    options['scan_id'] = scan.id
    task = Task.objects.get(id=task_id)
    task.args = options
    task.save()