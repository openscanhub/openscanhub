# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

"""these functions are exported via XML-RPC"""

import logging

from kobo.client.constants import TASK_STATES
from kobo.hub.models import Task
from kobo.tback import get_traceback

from osh.hub.scan.models import (SCAN_STATES, SCAN_STATES_SEND_MAIL, Scan,
                                 ScanBinding)
from osh.hub.scan.notify import send_scan_notification
from osh.hub.waiving.results_loader import process_scan
from osh.hub.waiving.service import get_unwaived_rgs

logger = logging.getLogger(__name__)


def finish_scan(request, scan_id, filename):
    """analysis ended, so process results"""
    sb = ScanBinding.objects.by_scan_id(scan_id)
    scan = sb.scan
    task = sb.task

    # scan failed, take this into account
    if scan.is_failed():
        if task.state == TASK_STATES['CLOSED']:
            # task is fine -- we are probably just resubmitting; allow this
            logger.info("Resubmitting previously failed scan (%s).", scan)
        else:
            # task is not fine, scan is not fine: do not process results
            return

    try:
        process_scan(sb)
    except Exception as ex:  # noqa: B902
        logger.error("got error while processing scan: %s", repr(ex))
        fail_scan(scan_id, get_traceback())
        return

    result = sb.result

    # TODO: create separate function
    if scan.is_errata_scan():
        # if there are no missing waivers = there are some newly added
        # unwaived defects
        if not get_unwaived_rgs(result):
            if result.has_bugs():
                # there are no new defects but some groups are marked as bugs from previous runs
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
        # set last successfully finished scan as enabled
        scan.enable_last_successfull()
    scan.save()
    if reason:
        Task.objects.filter(id=scan.scanbinding.task.id).update(
            result="Scan failed due to: %s" % reason)
    if scan.is_errata_base_scan():
        fail_scan(scan.scanbinding.task.parent.scanbinding.scan.id, "Base scan failed")


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


def prepare_version_retriever(mock_config, analyzers, su_user=None, csmock_args=None):
    method = 'AnalyzerVersionRetriever'
    args = {'mock_config': mock_config, 'analyzers': analyzers}
    if su_user:
        args['su_user'] = su_user
    if csmock_args:
        args['csmock_args'] = csmock_args
    label = 'Refresh version cache.'
    return method, args, label
