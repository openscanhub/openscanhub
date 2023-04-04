import logging

from kobo.hub.models import TASK_STATES, Task

from osh.hub.other.exceptions import ScanException
from osh.hub.other.shortcuts import check_and_create_dirs
from osh.hub.scan.models import (SCAN_STATES, ETMapping, ReleaseMapping,
                                 ScanBinding)
from osh.hub.scan.service import get_latest_binding

logger = logging.getLogger(__name__)


def get_tag(release):
    for rm in ReleaseMapping.objects.all():
        tag = rm.get_tag(release)
        if tag:
            return tag
    logger.critical("Unable to assign proper product and release: %s", release)
    raise RuntimeError("Packages in this release are not being scanned.")


def return_or_raise(key, data):
    """Custom function for retrieving data from dict (mainly for logging)"""
    try:
        return data[key]
    except KeyError:
        logger.error("Key '%s' is missing from dict '%s'", key, data)
        raise RuntimeError("Key '%s' is missing from %s, invalid scan \
submission!" % (key, data))


def rescan(scan, user):
    """
        Rescan supplied scan.

        @param scan - scan to be rescanned
        @type scan - osh.hub.scan.models.Scan
        @param user - user that triggered resubmit
        @type user - django...User
    """
    latest_binding = get_latest_binding(scan.nvr, show_failed=True)
    logger.info('Rescheduling scan with nvr %s, latest binding %s',
                scan.nvr, latest_binding)

    if latest_binding.scan.state != SCAN_STATES['FAILED']:
        raise ScanException("Latest run %d of %s haven't \
failed. This is not supported." % (latest_binding.scan.id, scan.nvr))

    # scan is base scan
    if latest_binding.scan.is_errata_base_scan():
        # clone does not support cloning of child tasks only
        task_id = Task.create_task(
            owner_name=latest_binding.task.owner.username,
            label=latest_binding.task.label,
            method=latest_binding.task.method,
            args={},
            comment="Rescan of base %s" % latest_binding.scan.nvr,
            state=TASK_STATES["CREATED"],
            priority=latest_binding.task.priority,
            resubmitted_by=user,
            resubmitted_from=latest_binding.task,
        )

        task_dir = Task.get_task_dir(task_id)

        check_and_create_dirs(task_dir)
        new_scan = latest_binding.scan.clone_scan()

        options = latest_binding.task.args
        options.update({'scan_id': new_scan.id})
        task = Task.objects.get(id=task_id)
        task.args = options
        task.save()
        task.free_task()

        sb = ScanBinding()
        sb.task = task
        sb.scan = new_scan
        sb.save()

        return sb
    # scan is errata scan
    # do not forget to set up parent id for task
    else:
        if latest_binding.task.parent:
            raise ScanException('You want to rescan a scan that has a parent. \
Unsupported.')

        latest_base_binding = get_latest_binding(scan.base.nvr)
        if not latest_base_binding:
            raise RuntimeError('It looks like that any of base scans of %s \
did not finish successfully; reschedule base (latest base: %s)' % (
                scan.base.nvr,
                get_latest_binding(scan.base.nvr, show_failed=True))
            )

        task_id = latest_binding.task.clone_task(
            user,
            state=TASK_STATES["CREATED"],
            args={},
            comment="Rescan of %s" % latest_binding.scan.nvr,
        )

        task_dir = Task.get_task_dir(task_id)

        check_and_create_dirs(task_dir)

        # update child
        child = scan.get_child_scan()

        new_scan = latest_binding.scan.clone_scan(
            base=latest_base_binding.scan)

        if child:
            child.parent = scan
            child.save()

        options = latest_binding.task.args
        options.update({'scan_id': new_scan.id})
        task = Task.objects.get(id=task_id)
        task.args = options
        task.save()
        task.free_task()

        sb = ScanBinding()
        sb.task = task
        sb.scan = new_scan
        sb.save()

        ETMapping.objects.filter(
            latest_run=latest_binding).update(latest_run=sb)

        return sb
