# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

import os
import sys
from urllib.parse import urljoin

from kobo.worker import TaskBase

from osh.worker.csmock_runner import CsmockRunner


class Build:
    enabled = True

    arches = ["noarch"]     # list of supported architectures
    channels = ["default"]  # list of channels
    exclusive = False       # leave False here unless you really know what you're doing
    foreground = False      # if True the task is not forked and runs in the worker process (no matter you run worker without -f)
    priority = 10
    weight = 1.0

    def run(self):
        mock_config = self.args.pop("mock_config")
        build = self.args.pop("build", {})
        srpm_name = self.args.pop("srpm_name", None)
        csmock_args = self.args.pop("csmock_args", None)
        analyzers = self.args.pop('analyzers')
        base_task_args = self.args.pop('base_task_args', None)
        upload_id = self.args.pop('upload_id', None)  # only base may have this
        su_user = self.args.pop('su_user', None)
        custom_model_name = self.args.pop("custom_model_name", None)
        task_url = self.hub.client.task_url(self.task_id)
        result_filename = self.args.pop("result_filename", None)

        # scan base
        if base_task_args:
            subtask_id = self.spawn_subtask(*base_task_args)
            self.hub.worker.assign_task(subtask_id)
            self.wait()

        if upload_id:
            self.hub.worker.move_upload(self.task_id, upload_id)

        with CsmockRunner() as runner:
            if custom_model_name:
                model_url = urljoin(task_url, f'log/{custom_model_name}?format=raw')
                model_path = runner.download_csmock_model(model_url, custom_model_name)
                csmock_args += " --cov-custom-model " + model_path

            if build:
                results, retcode = runner.koji_analyze(
                    analyzers,
                    build['nvr'],
                    profile=mock_config,
                    additional_arguments=csmock_args,
                    koji_profile=build['koji_profile'],
                    su_user=su_user)
            elif srpm_name:
                url = urljoin(task_url, f'log/{srpm_name}?format=raw')
                results, retcode = runner.srpm_download_analyze(
                    analyzers,
                    srpm_name,
                    url,
                    profile=mock_config,
                    additional_arguments=csmock_args,
                    result_filename=result_filename,
                    su_user=su_user)
            else:
                print("No srpm specified", file=sys.stderr)
                self.fail()

            if results is None:
                print("Task did not produce any results", file=sys.stderr)
                self.fail()

            try:
                base_results = os.path.basename(results)
                with open(results, "rb") as f:
                    self.hub.upload_task_log(f, self.task_id, base_results)
            except OSError as e:
                print("Reading task logs failed:", e, file=sys.stderr)
                self.fail()

        # first finish task, then fail if needed, so tarball gets unpacked
        self.hub.worker.finish_task(self.task_id)
        if retcode > 0:
            print(f"Scanning has not completed successfully ({retcode})",
                  file=sys.stderr)
            self.fail()

    @classmethod
    def notification(cls, hub, conf, task_info):
        hub.worker.email_task_notification(task_info["id"])


class DiffBuild(Build, TaskBase):
    def __init__(self, *args, **kwargs):
        Build.__init__(self)
        TaskBase.__init__(self, *args, **kwargs)


class MockBuild(Build, TaskBase):
    def __init__(self, *args, **kwargs):
        Build.__init__(self)
        TaskBase.__init__(self, *args, **kwargs)


class VersionDiffBuild(Build, TaskBase):
    def __init__(self, *args, **kwargs):
        Build.__init__(self)
        TaskBase.__init__(self, *args, **kwargs)
