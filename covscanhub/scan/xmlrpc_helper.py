# -*- coding: utf-8 -*-

"""these functions are exported via XML-RPC"""


from kobo.client.constants import TASK_STATES
from kobo.hub.models import Task

from covscanhub.other.exceptions import ScanException
from covscanhub.scan.service import update_scans_state, \
    prepare_and_execute_diff, post_qpid_message, get_latest_binding
from covscanhub.waiving.service import create_results, get_unwaived_rgs
from covscanhub.scan.models import SCAN_STATES, Scan, ScanBinding


def finish_scan(scan_id, task_id):
    """analysis ended, so process results"""
    sb = ScanBinding.objects.get(scan=scan_id, task=task_id)
    scan = sb.scan

    if sb.task.state == TASK_STATES['FAILED'] or \
            sb.task.state == TASK_STATES['CANCELED']:
        scan.state = SCAN_STATES['FAILED']
        scan.enabled = False
    else:
        if scan.is_errata_scan() and scan.base:
            try:
                prepare_and_execute_diff(
                    sb.task,
                    get_latest_binding(scan.base.nvr).task,
                    scan.nvr, scan.base.nvr
                )
            except ScanException:
                scan.state = SCAN_STATES['FAILED']
                scan.save()
                return

        result = create_results(scan, sb)

        if scan.is_errata_scan():
            # if there are no missing waivers = there are some newly added
            # unwaived defects
            if not get_unwaived_rgs(result):
                scan.state = SCAN_STATES['PASSED']
            else:
                scan.state = SCAN_STATES['NEEDS_INSPECTION']

            post_qpid_message(sb.id,
                              SCAN_STATES.get_value(scan.state),
                              sb.scan.get_errata_id())
        elif scan.is_errata_base_scan():
            scan.state = SCAN_STATES['FINISHED']
    scan.save()


def fail_scan(scan_id, reason=None):
    """analysis didn't finish successfully, so process it appropriately"""
    update_scans_state(scan_id, SCAN_STATES['FAILED'])
    Scan.objects.filter(id=scan_id).update(enabled=False)
    if reason:
        scan = Scan.objects.get(id=scan_id)
        Task.objects.filter(id=scan.scanbinding.task.id).update(
            result="Scan failed due to: %s" % reason)
    post_qpid_message(
        scan.scanbinding.id,
        SCAN_STATES.get_value(scan.state),
        scan.get_errata_id()
    )
