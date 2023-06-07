# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

import logging

from kobo.hub.models import TASK_STATES, Task

from osh.hub.other.exceptions import ScanException
from osh.hub.other.shortcuts import check_and_create_dirs
from osh.hub.scan.models import SCAN_STATES, ETMapping, ScanBinding
from osh.hub.scan.service import get_latest_binding

logger = logging.getLogger(__name__)


def rescan(scan, user):
    """
        Rescan supplied scan.

        @param scan - scan to be rescanned
        @type scan - osh.hub.scan.models.Scan
        @param user - user that triggered resubmit
        @type user - django...User
    """
    # FIXME: The function sometimes resturns the oldest binding...
    latest_binding = get_latest_binding(scan.nvr, show_failed=True)
    assert latest_binding is not None, "At least one binding must exist!"

    logger.info('Rescheduling scan with nvr %s, latest binding %s',
                scan.nvr, latest_binding)

    latest_scan = latest_binding.scan
    latest_task = latest_binding.task

    if latest_scan.state != SCAN_STATES['FAILED']:
        raise ScanException(f"Latest scan {latest_scan.id} of {scan.nvr} haven't \
failed. This is not supported.")

    # scan is base scan
    if latest_scan.is_errata_base_scan():
        # clone does not support cloning of child tasks only
        task_id = Task.create_task(
            owner_name=latest_task.owner.username,
            label=latest_task.label,
            method=latest_task.method,
            args={},
            comment=f"Rescan of base {latest_scan.nvr}",
            state=TASK_STATES["CREATED"],
            priority=latest_task.priority,
            resubmitted_by=user,
            resubmitted_from=latest_task)

        new_scan = latest_scan.clone_scan()

    # scan is errata scan
    # do not forget to set up parent id for task
    else:
        if latest_task.parent:
            raise ScanException('You want to rescan a scan that has a parent. \
Unsupported.')

        latest_base_binding = get_latest_binding(scan.base.nvr)
        if not latest_base_binding:
            latest_failed_base_binding = get_latest_binding(scan.base.nvr, show_failed=True)
            raise RuntimeError(f'It looks like that any of base scans of {scan.base.nvr} \
did not finish successfully; reschedule base (latest base: {latest_failed_base_binding})')

        task_id = latest_task.clone_task(
            user,
            state=TASK_STATES["CREATED"],
            args={},
            comment=f"Rescan of {latest_scan.nvr}")

        # update child
        child = scan.get_child_scan()

        new_scan = latest_scan.clone_scan(
            base=latest_base_binding.scan)

        if child:
            child.parent = scan
            child.save()

    task_dir = Task.get_task_dir(task_id)
    check_and_create_dirs(task_dir)

    options = latest_task.args
    options.update({'scan_id': new_scan.id})
    task = Task.objects.get(id=task_id)
    task.args = options
    task.save()
    task.free_task()

    sb = ScanBinding()
    sb.task = task
    sb.scan = new_scan
    sb.save()

    if scan.is_errata_scan():
        ETMapping.objects.filter(
            latest_run=latest_binding).update(latest_run=sb)

    return sb
