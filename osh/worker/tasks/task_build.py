# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

import os
import platform
import sys
from urllib.parse import urljoin

from kobo.worker import TaskBase

from osh.worker.csmock_runner import CsmockRunner


class OSHTaskBase(TaskBase):
    """
    Default task settings
    """
    # each final class should set this to true
    enabled = False

    # list of supported architectures
    arches = ["noarch", "aarch64", "x86_64"]

    # list of channels
    channels = ["default"]

    # exclusive tasks have the highest possible priority
    # leave False unless you really know what you're doing
    exclusive = False

    # if True the task is not forked and runs in the worker process
    # (no matter you run worker without -f)
    foreground = False

    # determines how many resources is used when processing the task
    weight = 1.0


class Build(OSHTaskBase):
    def run(self):
        mock_config = self.args.pop("mock_config")
        build = self.args.pop("build", {})
        srpm_name = self.args.pop("srpm_name", None)
        dist_git_url = self.args.pop("dist_git_url", None)
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
            self.spawn_subtask(*base_task_args, inherit_worker=True)
            self.wait()

        # download custom mock config from the hub
        mock_config_url = None
        if mock_config == 'auto':
            self.hub.worker.create_mock_configs(self.task_id)
            arch = platform.uname().machine
            mock_config_url = urljoin(task_url, f'log/mock/mock-{arch}.cfg?format=raw')

        if upload_id:
            self.hub.worker.move_upload(self.task_id, upload_id)

        with CsmockRunner() as runner:
            if custom_model_name:
                model_url = urljoin(task_url, f'log/{custom_model_name}?format=raw')
                model_path = runner.download_file(model_url, custom_model_name)
                csmock_args += " --cov-custom-model " + model_path

            if build:
                results, retcode = runner.koji_analyze(
                    analyzers,
                    build['nvr'],
                    profile=mock_config,
                    profile_url=mock_config_url,
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
                    profile_url=mock_config_url,
                    additional_arguments=csmock_args,
                    result_filename=result_filename,
                    su_user=su_user)
            elif dist_git_url:
                results, retcode = runner.dist_git_url_analyze(
                    analyzers,
                    dist_git_url,
                    profile=mock_config,
                    su_user=su_user,
                    result_filename=result_filename,
                    additional_arguments=csmock_args)
            else:
                print("No srpm or dist-git URL specified", file=sys.stderr)
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


class DiffBuild(Build):
    enabled = True


class MockBuild(Build):
    enabled = True


class VersionDiffBuild(Build):
    enabled = True
