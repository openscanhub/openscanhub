# -*- coding: utf-8 -*-

import os
import sys
import urlparse

from covscanhub.service.csmock_parser import CsmockRunner

from kobo.worker import TaskBase


class MockBuild(TaskBase):
    enabled = True

    arches = ["noarch"]    # list of supported architectures
    channels = ["default"] # list of channels
    exclusive = False      # leave False here unless you really know what you're doing
    foreground = False     # if True the task is not forked and runs in the worker process (no matter you run worker without -f)
    priority = 19
    weight = 1.0

    def run(self):
        mock_config = self.args.pop("mock_config")
        build = self.args.pop("build", {})
        srpm_name = self.args.pop("srpm_name", None)
        csmock_args = self.args.pop("csmock_args", None)
        analyzers = self.args.pop('analyzers')
        su_user = self.args.pop('su_user', None)

        cim = self.hub.worker.get_cim_arg(self.task_id)
        if cim:
            if csmock_args:
                csmock_args += " %s" % cim
            else:
                csmock_args = cim

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
        if retcode > 0:
            print >> sys.stderr, "Scanning have not completed successfully (%d)" % retcode
            self.fail()

        self.hub.worker.finish_task(self.task_id)
