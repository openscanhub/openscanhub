# -*- coding: utf-8 -*-

#import kobo.tback
#kobo.tback.set_except_hook()


import covscan
from kobo.shortcuts import random_string


class Diff_Build(covscan.CovScanCommand):
    """analyze a SRPM without and with pathes, return diff"""
    enabled = True
    admin = False # admin type account required

    def options(self):
        # specify command usage
        # normalized name contains a lower-case class name with underscores converted to dashes
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

        if len(args) != 1:
            self.parser.error("please specify exactly one SRPM")
        srpm = args[0]
        if not srpm.endswith(".src.rpm"):
            self.parser.error("provided file doesn't appear to be a SRPM")

        # login to the hub
        self.set_hub(username, password)

        if not config:
            self.parser.error("please specify a mock config")

        mock_conf = self.hub.mock_config.get(config)
        if not mock_conf["enabled"]:
            self.parser.error("Mock config is not enabled: %s" % config)

        # check if config is valid (rpc call) (move to call?)
        target_dir = random_string(32)
        upload_id, err_code, err_msg = self.hub.upload_file(srpm, target_dir)

        options = {
            "keep_covdata": keep_covdata,
        }
        if email_to:
            options["email_to"] = email_to

        task_id = self.hub.client.diff_build(config, upload_id, comment, options)
        self.write_task_id_file(task_id, task_id_file)
        print "Task info: %s" % self.hub.client.task_url(task_id)

        if not nowait:
            from kobo.client.task_watcher import TaskWatcher
            TaskWatcher.watch_tasks(self.hub, [task_id])
