# -*- coding: utf-8 -*-

import os
import urllib
import covscan

from xmlrpclib import Fault
from kobo.shortcuts import random_string
from covscan.commands.shortcuts import verify_brew_koji_build, verify_mock, upload_file, \
    handle_perm_denied
from covscan.commands.common import *
from covscan.utils.conf import get_conf
from covscan.utils.cim import extract_cim_data


class Diff_Build(covscan.CovScanCommand):
    """analyze a SRPM without and with patches, return diff"""
    enabled = True
    admin = False  # admin type account required

    def options(self):
        # specify command usage
        # normalized name contains a lower-case class name with underscores
        # converted to dashes
        self.parser.usage = "%%prog %s [options] <args>" % self.normalized_name
        self.parser.epilog = "User configuration file is located at: \
~/.config/covscan/covscan.conf"

        self.parser.add_option(
            "--config",
            help="specify mock config name (use default one from config files \
if not specified)"
        )

        add_cppcheck_option(self.parser)
        add_aggressive_option(self.parser)
        add_concurrency_option(self.parser)
        add_download_results_option(self.parser)

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
            "-m",
            dest="commit_string",
            metavar="user:passwd@host:port/stream",
            help="""Commit the results to Integrity Manager. You can specify \
the target host/stream as an optional argument using the
following format: "user:passwd@host:port/stream". User and password might be \
stored in user configuration file."""
        )

    def validate_results_store_file(self):
        if self.results_store_file:
            if isinstance(self.results_store_file, basestring):
                if not os.path.isdir(self.results_store_file):
                    self.parser.error("Path (%s) for storing results doesn't \
exist." % self.results_store_file)
            else:
                self.parser.error("Invalid path to store results.")

    def fetch_results(self, task_url):
        # we need nvr + '.tar.xz'
        if not self.srpm.endswith('.src.rpm'):
            tarball = self.srpm + '.tar.xz'
        else:
            tarball = self.srpm.replace('.src.rpm', '.tar.xz')
        # get absolute path
        if self.results_store_file:
            local_path = os.path.join(os.path.abspath(self.results_store_file),
                                      tarball)
        else:
            local_path = os.path.join(os.path.abspath(os.curdir),
                                      tarball)
        # task_url is url to task with trailing '/'
        url = "%slog/%s?format=raw" % (task_url, tarball)
        urllib.urlretrieve(url, local_path)

    def run(self, *args, **kwargs):
        local_conf = get_conf(self.conf)

        # optparser output is passed via *args (args) and **kwargs (opts)
        username = kwargs.pop("username", None)
        password = kwargs.pop("password", None)
        config = kwargs.pop("config", None)
        aggressive = kwargs.pop("aggressive", None)
        cppcheck = kwargs.pop("cppcheck", None)
        keep_covdata = kwargs.pop("keep_covdata", False)
        email_to = kwargs.pop("email_to", [])
        comment = kwargs.pop("comment")
        nowait = kwargs.pop("nowait")
        task_id_file = kwargs.pop("task_id_file")
        priority = kwargs.pop("priority")
        brew_build = kwargs.pop("brew_build")
        all_option = kwargs.pop("all")
        security = kwargs.pop("security")
        concurrency = kwargs.pop("concurrency")
        commit_string = kwargs.pop("commit_string", None)
        self.results_store_file = kwargs.pop("results_file", None)

        if len(args) != 1:
            self.parser.error("please specify exactly one SRPM")
        self.srpm = args[0]

        self.validate_results_store_file()

        if not brew_build and not self.srpm.endswith(".src.rpm"):
            self.parser.error("provided file doesn't appear to be a SRPM")

        if brew_build:
            result = verify_brew_koji_build(self.srpm, self.conf['BREW_URL'],
                                            self.conf['KOJI_URL'])
            if result is not None:
                self.parser.error(result)

        if not config:
            config = local_conf.get_default_mockconfig()
            if not config:
                self.parser.error("You haven't specified mock config, there \
is not even one in your user configuration file \
(~/.config/covscan/covscan.conf) nor in system configuration file \
(/etc/covscan/covscan.conf)")

        # login to the hub
        self.set_hub(username, password)

        result = verify_mock(config, self.hub)
        if result is not None:
            self.parser.error(result)

        # options setting

        options = {
            "keep_covdata": keep_covdata,
        }
        # check CIM string, it might be empty, so `if commit_string` is
        #  a bad idea
        if commit_string is not None:
            try:
                options['CIM'] = extract_cim_data(commit_string)
            except RuntimeError, ex:
                self.parser.error(ex.message)
        if email_to:
            options["email_to"] = email_to
        if priority is not None:
            options["priority"] = priority

        if aggressive:
            options["aggressive"] = aggressive
        if cppcheck:
            options["cppcheck"] = cppcheck
        if all_option:
            options["all"] = all_option
        if security:
            options["security"] = security
        if concurrency:
            options["concurrency"] = concurrency

        if brew_build:
            options["brew_build"] = self.srpm
            options["srpm_name"] = self.srpm
        else:
            target_dir = random_string(32)
            upload_id, err_code, err_msg = upload_file(self.hub, self.srpm,
                                                       target_dir, self.parser)
            options["upload_id"] = upload_id

        task_id = self.submit_task(config, comment, options)

        self.write_task_id_file(task_id, task_id_file)
        task_url = self.hub.client.task_url(task_id)
        print "Task info: %s" % task_url

        if not nowait:
            from kobo.client.task_watcher import TaskWatcher
            TaskWatcher.watch_tasks(self.hub, [task_id])

            # store results if user requested this
            if self.results_store_file is not None:
                self.fetch_results(task_url)

    def submit_task(self, config, comment, options):
        try:
            return self.hub.scan.diff_build(config, comment, options)
        except Fault, e:
            handle_perm_denied(e, self.parser)
