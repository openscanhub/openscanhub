# -*- coding: utf-8 -*-

from __future__ import print_function
import os
import sys
import six.moves.urllib.parse

from kobo.worker import TaskBase
from covscancommon.csmock_parser import CsmockRunner


class VersionDiffBuild(TaskBase):
    """
        Execute diff scan between two versions/releases of a package
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

        # scan base
        if base_task_args:
            subtask_id = self.spawn_subtask(*tuple(base_task_args))
            self.hub.worker.assign_task(subtask_id)
            self.wait()

        if upload_id:
            self.hub.worker.move_upload(self.task_id, upload_id)

        with CsmockRunner() as runner:
            if custom_model_name:
                model_url = six.moves.urllib.parse.urljoin(task_url, 'log/%s?format=raw' % custom_model_name)
                model_path = runner.download_csmock_model(model_url, custom_model_name)
                csmock_args += " --cov-custom-model %s" % model_path

            if build:
                results, retcode = runner.koji_analyze(
                    analyzers,
                    build['nvr'],
                    profile=mock_config,
                    additional_arguments=csmock_args,
                    koji_bin=build['koji_bin'],
                    su_user=su_user)
            elif srpm_name:
                url = six.moves.urllib.parse.urljoin(task_url, 'log/%s?format=raw' % srpm_name)
                results, retcode = runner.srpm_download_analyze(
                    analyzers,
                    srpm_name,
                    url,
                    profile=mock_config,
                    additional_arguments=csmock_args,
                    su_user=su_user)
            else:
                print("No srpm specified", file=sys.stderr)
                self.fail()
            if results is None:
                print("No results available", file=sys.stderr)
                self.fail()
            base_results = os.path.basename(results)
            self.hub.upload_task_log(open(results, "rb"),
                                     self.task_id, base_results)
        self.hub.worker.finish_task(self.task_id)
        if retcode > 0:
            print("Scanning have not completed successfully (%d)" % retcode, file=sys.stderr)
            self.fail()

    @classmethod
    def cleanup(cls, hub, conf, task_info):
        pass
        # remove temp files, etc.

    @classmethod
    def notification(cls, hub, conf, task_info):
        hub.worker.email_task_notification(task_info["id"])
