# -*- coding: utf-8 -*-


import os
import brew

import covscan
from kobo.shortcuts import random_string
from kobo.client import HubProxy
from shortcuts import verify_brew_build, verify_mock


class Diff_Build(covscan.CovScanCommand):
    """analyze a SRPM without and with pathes, return diff"""
    enabled = True
    admin = False  # admin type account required

    def options(self):
        # specify command usage
        # normalized name contains a lower-case class name with underscores
        # converted to dashes
        self.parser.usage = "%%prog %s [options] <args>" % self.normalized_name

        self.parser.add_option(
            "--config",
            help="specify mock config name"
        )

        self.parser.add_option(
            "-i",
            "--keep-covdata",
            default=False,
            action="store_true",
            help="keep coverity data in final archive",
        )

        self.parser.add_option(
            "--comment",
            help="a task description",
        )

        self.parser.add_option(
            "--task-id-file",
            help="task id is written to this file",
        )

        self.parser.add_option(
            "--nowait",
            default=False,
            action="store_true",
            help="don't wait until tasks finish",
        )

        self.parser.add_option(
            "--email-to",
            action="append",
            help="send output to this address"
        )

        self.parser.add_option(
            "--priority",
            type="int",
            help="task priority (20+ is admin only)"
        )

        self.parser.add_option(
            "--brew-build",
            action="store_true",
            default=False,
            help="use a brew build (specified by NVR) instead of a local file"
        )

        self.parser.add_option(
            "--all",
            action="store_true",
            default=False,
            help="turn all checkers on"
        )

        self.parser.add_option(
            "--security",
            action="store_true",
            default=False,
            help="turn security checkers on"
        )

        self.parser.add_option(
            "--hub",
            help="URL of XML-RPC interface on hub; something like \
http://$hostname/covscan/xmlrpc"
        )

    def run(self, *args, **kwargs):
        # optparser output is passed via *args (args) and **kwargs (opts)
        username = kwargs.pop("username", None)
        password = kwargs.pop("password", None)
        config = kwargs.pop("config", None)
        keep_covdata = kwargs.pop("keep_covdata", False)
        email_to = kwargs.pop("email_to", [])
        comment = kwargs.pop("comment")
        nowait = kwargs.pop("nowait")
        task_id_file = kwargs.pop("task_id_file")
        priority = kwargs.pop("priority")
        brew_build = kwargs.pop("brew_build")
        all = kwargs.pop("all")
        security = kwargs.pop("security")
        #'http://uqtm.lab.eng.brq.redhat.com/covscan/xmlrpc'
        hub_url = kwargs.pop('hub', None)

        if len(args) != 1:
            self.parser.error("please specify exactly one SRPM")
        srpm = args[0]

        if not brew_build and not srpm.endswith(".src.rpm"):
            self.parser.error("provided file doesn't appear to be a SRPM")

        if brew_build:
            result = verify_brew_build(srpm, self.conf['BREW_URL'])
            if result is not None:
                self.parser.error(result)

        if not config:
            self.parser.error("please specify a mock config")

        # login to the hub
        if hub_url is None:
            self.set_hub(username, password)
        else:
            self.hub = HubProxy(conf=self.conf,
                                AUTH_METHOD='krbv',
                                HUB_URL=hub_url)

        result = verify_mock(config, self.hub)
        if result is not None:
            self.parser.error(result)

        # end of CLI options handling

        options = {
            "keep_covdata": keep_covdata,
        }
        if email_to:
            options["email_to"] = email_to
        if priority is not None:
            options["priority"] = priority

        if all:
            options["all"] = all
        if security:
            options["security"] = security

        if brew_build:
            options["brew_build"] = srpm
            options["srpm_name"] = srpm
        else:
            target_dir = random_string(32)
            upload_id, err_code, err_msg = self.hub.upload_file(srpm,
                                                                target_dir)
            options["upload_id"] = upload_id

        task_id = self.submit_task(config, comment, options)
        self.write_task_id_file(task_id, task_id_file)
        print "Task info: %s" % self.hub.client.task_url(task_id)

        if not nowait:
            from kobo.client.task_watcher import TaskWatcher
            TaskWatcher.watch_tasks(self.hub, [task_id])

    def submit_task(self, config, comment, options):
        #xmlrpc call
        return self.hub.scan.diff_build(config, comment, options)