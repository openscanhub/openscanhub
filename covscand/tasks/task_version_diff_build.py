# -*- coding: utf-8 -*-

import tempfile
import os
import pipes
import sys
import grp
import shutil
import urllib
import urlparse

from kobo.rpmlib import get_rpm_header
from kobo.worker import TaskBase
from kobo.shortcuts import run

import kobo.tback

from common import downloadSRPM
from covscanhub.service.csmock_parser import CsmockRunner


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

        # scan base
        if base_task_args:
            subtask_id = self.spawn_subtask(*tuple(base_task_args))
            self.hub.worker.assign_task(subtask_id)
            self.wait()

        if upload_id:
            self.hub.worker.move_upload(self.task_id, upload_id)

        with CsmockRunner() as runner:
            if build:
                results, retcode = runner.koji_analyze(
                    analyzers,
                    build['nvr'],
                    profile=mock_config,
                    additional_arguments=csmock_args,
                    koji_bin=build['koji_bin'],
                    su_user=su_user)
            elif srpm_name:
                task_url = self.hub.client.task_url(self.task_id)
                url = urlparse.urljoin(task_url, 'log/%s?format=raw' % srpm_name)
                results, retcode = runner.srpm_download_analyze(
                    analyzers,
                    srpm_name,
                    url,
                    profile=mock_config,
                    additional_arguments=csmock_args,
                    su_user=su_user)
            else:
                print >> sys.stderr, "No srpm specified"
                self.fail()
            base_results = os.path.basename(results)
            self.hub.upload_task_log(open(results, "r"),
                                     self.task_id, base_results)
        self.hub.worker.finish_task(self.task_id)
        if retcode > 0:
            print >> sys.stderr, "Scanning have not completed successfully (%d)" % retcode
            self.fail()

    @classmethod
    def cleanup(cls, hub, conf, task_info):
        pass
        # remove temp files, etc.

    @classmethod
    def notification(cls, hub, conf, task_info):
        hub.worker.email_task_notification(task_info["id"])
