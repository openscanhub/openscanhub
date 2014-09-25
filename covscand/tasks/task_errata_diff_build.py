# -*- coding: utf-8 -*-

import tempfile
import os
from kobo.shortcuts import run
import pipes
import sys
import grp
import shutil
from kobo.rpmlib import get_rpm_header
from kobo.worker import TaskBase
import kobo.tback
from covscanhub.service.csmock_parser import CsmockRunner

kobo.tback.set_except_hook()


class ErrataDiffBuild(TaskBase):
    """
        Execute diff scan between two versions/releases of a package for
        Errata Tool
    """
    enabled = True

    # list of supported architectures
    arches = ["noarch"]
    # list of channels
    channels = ["default"]
    # leave False here unless you really know what you're doing
    exclusive = False
    # if True the task is not forked and runs in the worker process
    # (no matter you run worker without -f)
    foreground = False
    priority = 20
    weight = 1.0

    def run(self):
        scan_id = self.args.pop('scan_id')
        mock_config = self.args.pop("mock_config")
        scanning_session_id = self.args.pop("scanning_session")
        build = self.args.pop("build")
        su_user = self.args.pop("su_user", None)

        self.hub.worker.set_scan_to_scanning(scan_id)

        # update analyzers version cache if needed
        cache_task_args = self.hub.worker.ensure_cache(mock_config, scanning_session_id)
        if cache_task_args is not None:
            cache_subtask_id = self.spawn_subtask(*tuple(cache_task_args))
            self.hub.worker.assign_task(cache_subtask_id)
            self.wait()

        # (re)scan base if needed
        base_task_args = self.hub.worker.ensure_base_is_scanned_properly(scan_id, self.task_id)
        if base_task_args is not None:
            subtask_id = self.spawn_subtask(*tuple(base_task_args))
            self.hub.worker.set_scan_to_basescanning(scan_id)
            self.hub.worker.assign_task(subtask_id)
            self.hub.worker.create_sb(subtask_id)
            self.wait()
            self.hub.worker.set_scan_to_scanning(scan_id)

        self.hub.worker.set_scan_to_scanning(scan_id)

        scanning_args = self.hub.worker.get_scanning_args(scanning_session_id)
        add_args = scanning_args.get('csmock_args', '')
        koji_bin = scanning_args.get('koji_bin', 'koji')

        with CsmockRunner() as runner:
            results, retcode = runner.koji_analyze(scanning_args['analyzers'],
                                                   build,
                                                   profile=mock_config,
                                                   additional_arguments=add_args,
                                                   koji_bin=koji_bin,
                                                   su_user=su_user)
            base_results = os.path.basename(results)
            self.hub.upload_task_log(open(results, "r"),
                                     self.task_id, base_results)
            if retcode > 0:
                print >> sys.stderr, "Scanning have not completed successfully (%d)" % retcode
                self.hub.worker.fail_scan(scan_id,
                                          'csmock return code: %d' % retcode)
                self.fail()

        self.hub.worker.finish_scan(scan_id, base_results)

    @classmethod
    def cleanup(cls, hub, conf, task_info):
        pass
        # remove temp files, etc.

    @classmethod
    def notification(cls, hub, conf, task_info):
        hub.worker.email_scan_notification(task_info['args']['scan_id'])
