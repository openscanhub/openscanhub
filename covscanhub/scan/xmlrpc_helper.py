# -*- coding: utf-8 -*-

"""these functions are exported via XML-RPC"""

import logging

from kobo.client.constants import TASK_STATES
from kobo.hub.models import Task

from covscanhub.other.exceptions import ScanException
from covscanhub.scan.service import prepare_and_execute_diff, \
    get_latest_binding, get_latest_sb_by_package
from covscanhub.waiving.service import create_results, get_unwaived_rgs
from covscanhub.scan.models import SCAN_STATES, Scan, ScanBinding, SCAN_STATES_SEND_MAIL
from covscanhub.scan.notify import send_scan_notification

logger = logging.getLogger(__name__)


def finish_scan(request, scan_id, task_id):
    """analysis ended, so process results"""
    sb = ScanBinding.objects.get(scan=scan_id, task=task_id)
    scan = sb.scan

    if sb.task.state == TASK_STATES['FAILED'] or \
            sb.task.state == TASK_STATES['CANCELED']:
        fail_scan(scan_id, "Task failed.")
        send_scan_notification(request, scan_id)
        return
    else:
        if not scan.is_newpkg_scan() and scan.is_errata_scan() and scan.base:
            try:
                prepare_and_execute_diff(
                    sb.task,
                    get_latest_binding(scan.base.nvr).task,
                    scan.nvr, scan.base.nvr
                )
            except ScanException, ex:
                fail_scan(scan_id, ex.message)
                return

        result = create_results(scan, sb)

        if scan.is_errata_scan():
            # if there are no missing waivers = there are some newly added
            # unwaived defects
            if not get_unwaived_rgs(result):
                if result.has_bugs():
                    # there are no new defects bug some groups are marked as bugs from previous runs
                    scan.set_state_bug_confirmed()
                else:
                    # result does not have bugs and new defects
                    scan.set_state(SCAN_STATES['PASSED'])
            else:
                # set newpkg scan to needs_insp too so e-mail will be sent
                scan.set_state(SCAN_STATES['NEEDS_INSPECTION'])

        elif scan.is_errata_base_scan():
            scan.set_state(SCAN_STATES['FINISHED'])
    scan.save()


def fail_scan(scan_id, reason=None):
    """analysis didn't finish successfully, so process it appropriately"""
    scan = Scan.objects.get(id=scan_id)
    scan.set_state(SCAN_STATES['FAILED'])
    if scan.is_errata_scan():
        scan.enabled = False
        scan.save()

        if reason:
            Task.objects.filter(id=scan.scanbinding.task.id).update(
                result="Scan failed due to: %s" % reason)

        #set last successfully finished scan as enabled
        scan.enable_last_successfull()
    else:
        scan.scanbinding.task.parent.cancel_task(recursive=False)
        fail_scan(scan.scanbinding.task.parent.scanbinding.scan.id,
                  "Base scan failed.")


def cancel_scan_tasks(task):
    if task.state in (TASK_STATES['OPEN'], TASK_STATES['FREE'],
                      TASK_STATES['CREATED'], TASK_STATES['ASSIGNED']):
        task.cancel_task(recursive=True)


def cancel_scan(binding):
    binding.scan.set_state(SCAN_STATES['CANCELED'])
    cancel_scan_tasks(binding.task)
    if binding.scan.is_errata_scan():
        Scan.objects.filter(id=binding.scan.id).update(
            enabled=False,
        )
        binding.scan.enable_last_successfull()
        if binding.scan.base and binding.scan.base.is_in_progress():
            binding.scan.base.set_state(SCAN_STATES['CANCELED'])
    return binding.scan


def scan_notification_email(request, scan_id):
    scan = Scan.objects.get(id=scan_id)
    logger.info("Send e-mail for scan %s", scan)
    if scan.is_errata_scan():
        if scan.state in SCAN_STATES_SEND_MAIL:
            return send_scan_notification(request, scan_id)
    elif scan.is_errata_base_scan():
        if scan.is_failed():
            return send_scan_notification(
                request,
                scan.scanbinding.task.parent.scanbinding.scan.id)
