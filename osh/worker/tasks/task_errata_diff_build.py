# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

import os
import sys

from osh.worker.csmock_runner import CsmockRunner
from osh.worker.tasks.task_build import OSHTaskBase


class ErrataDiffBuild(OSHTaskBase):
    """
        Execute diff scan between two versions/releases of a package for
        Errata Tool
    """
    enabled = True

    def run(self):
        scan_id = self.args.pop('scan_id')
        mock_config = self.args.pop("mock_config")
        profile = self.args.pop("profile")
        build = self.args.pop("build")
        su_user = self.args.pop("su_user", None)

        self.hub.worker.set_scan_to_scanning(scan_id)

        # update analyzers version cache if needed
        cache_task_args = self.hub.worker.ensure_cache(mock_config, profile)
        if cache_task_args is not None:
            self.spawn_subtask(*cache_task_args, inherit_worker=True)
            self.wait()

        # (re)scan base if needed
        base_task_args = self.hub.worker.ensure_base_is_scanned_properly(scan_id, self.task_id)
        if base_task_args is not None:
            self.hub.worker.set_scan_to_basescanning(scan_id)

            subtask_id = self.spawn_subtask(*base_task_args, inherit_worker=True)
            self.hub.worker.create_sb(subtask_id)

            self.wait()
            self.hub.worker.set_scan_to_scanning(scan_id)

        scanning_args = self.hub.worker.get_scanning_args(profile)
        add_args = scanning_args.get('csmock_args', '')
        koji_profile = scanning_args.get('koji_profile', 'koji')

        with CsmockRunner() as runner:
            results, retcode = runner.koji_analyze(scanning_args['analyzers'],
                                                   build,
                                                   profile=mock_config,
                                                   additional_arguments=add_args,
                                                   koji_profile=koji_profile,
                                                   su_user=su_user)
            print('Retcode:', retcode)
            if results is None:
                print("Task did not produce any results", file=sys.stderr)
                self.hub.worker.fail_scan(scan_id, 'Empty task results')
                self.fail()

            try:
                base_results = os.path.basename(results)
                with open(results, 'rb') as f:
                    self.hub.upload_task_log(f, self.task_id, base_results)
            except OSError as e:
                print("Reading task logs failed:", e, file=sys.stderr)
                self.hub.worker.fail_scan(scan_id, f'Reading tak logs failed: {e}')
                self.fail()

        if retcode > 0:
            print(f"Scanning has not completed successfully ({retcode})",
                  file=sys.stderr)
            self.hub.worker.fail_scan(scan_id, f'csmock return code: {retcode}')
            self.fail()

        self.hub.worker.finish_scan(scan_id, base_results)

    @classmethod
    def notification(cls, hub, conf, task_info):
        hub.worker.email_scan_notification(task_info['args']['scan_id'])
