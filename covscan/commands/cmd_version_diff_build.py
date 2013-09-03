# -*- coding: utf-8 -*-


import covscan
from kobo.shortcuts import random_string
from shortcuts import verify_brew_koji_build, verify_mock, upload_file, \
    handle_perm_denied
from common import *
from covscan.utils.conf import get_conf
from covscan.commands.analyzers import check_analyzers
from xmlrpclib import Fault


class Version_Diff_Build(covscan.CovScanCommand):
    """analyze 2 SRPMs (base and target) and diff results"""
    enabled = True
    admin = False  # admin type account required

    def options(self):
        # specify command usage
        # normalized name contains a lower-case class name with underscores
        #  converted to dashes
        self.parser.usage = "%%prog %s [options] <args>" % self.normalized_name
        self.parser.epilog = "User configuration file is located at: \
~/.config/covscan/covscan.conf"

        add_cppcheck_option(self.parser)
        add_aggressive_option(self.parser)
        add_concurrency_option(self.parser)
        add_clang_option(self.parser)
        add_no_cov_option(self.parser)
        add_comp_warnings_option(self.parser)
        add_analyzers_option(self.parser)

        self.parser.add_option(
            "--base-config",
            help="specify mock config name for base package"
        )

        self.parser.add_option(
            "--config",
            help="specify mock config name for target package"
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
            help="don't wait until task(s) finish",
        )

        self.parser.add_option(
            "--email-to",
            action="append",
            help="send output to this address"
        )

        self.parser.add_option(
            "--priority",
            type="int",
            help="task priority (20+ is admin only), default is 10"
        )

        self.parser.add_option(
            "--base-brew-build",
            help="use a brew build for base (specified by NVR) instead of a \
local file"
        )

        self.parser.add_option(
            "--brew-build",
            help="use a brew build for target (specified by NVR) instead of a \
local file"
        )

        self.parser.add_option(
            "--base-srpm",
            help="path to SRPM used as base"
        )

        self.parser.add_option(
            "--srpm",
            help="path to SRPM used as target"
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

    def run(self, *args, **kwargs):
        # optparser output is passed via *args (args) and **kwargs (opts)
        local_conf = get_conf(self.conf)

        # options required for hub
        options_consumed = {}
        # options which should be forwarded to worker -- no need to manage
        # them on hub
        options_forwarded = {}

        username = kwargs.pop("username", None)
        password = kwargs.pop("password", None)
        config = kwargs.pop("config", None)
        base_config = kwargs.pop("base_config", None)
        aggressive = kwargs.pop("aggressive", None)
        cppcheck = kwargs.pop("cppcheck", None)
        keep_covdata = kwargs.pop("keep_covdata", False)
        email_to = kwargs.pop("email_to", [])
        comment = kwargs.pop("comment")
        nowait = kwargs.pop("nowait")
        task_id_file = kwargs.pop("task_id_file")
        priority = kwargs.pop("priority")
        base_brew_build = kwargs.pop("base_brew_build", None)
        brew_build = kwargs.pop("brew_build", None)
        base_srpm = kwargs.pop("base_srpm", None)
        srpm = kwargs.pop("srpm", None)
        all_checker = kwargs.pop("all")
        security = kwargs.pop("security")
        concurrency = kwargs.pop("concurrency")
        clang = kwargs.pop('clang', False)
        no_cov = kwargs.pop('no_cov', False)
        warn_level = kwargs.pop('warn_level', '0')
        analyzers = kwargs.pop('analyzers', '')

        if comment:
            options_consumed['comment'] = comment

        #both bases are specified
        if base_brew_build and base_srpm:
            self.parser.error("Choose exactly one option (--base-brew-build, \
--base-srpm), not both of them.")

        #both nvr/targets are specified
        if brew_build and srpm:
            self.parser.error("Choose exactly one option (--nvr-brew-build, \
--nvr-srpm), not both of them.")

        #no package option specified
        if (not base_brew_build and not brew_build and
                not srpm and not base_srpm):
            self.parser.error("Please specify both builds or SRPMs.")

        #no base specified
        if not base_brew_build and not base_srpm:
            self.parser.error("You haven't specified base.")

        #no nvr/target specified
        if not brew_build and not srpm:
            self.parser.error("You haven't specified target.")

        if srpm and not srpm.endswith(".src.rpm"):
            self.parser.error("provided target file doesn't appear to be \
a SRPM")

        if base_srpm and not base_srpm.endswith(".src.rpm"):
            self.parser.error("provided base file doesn't appear to be a SRPM")

        if brew_build:
            result = verify_brew_koji_build(brew_build, self.conf['BREW_URL'],
                                            self.conf['KOJI_URL'])
            if result is not None:
                self.parser.error(result)

        if base_brew_build:
            result = verify_brew_koji_build(base_brew_build,
                                            self.conf['BREW_URL'],
                                            self.conf['KOJI_URL'])
            if result is not None:
                self.parser.error(result)

        if not base_config:
            base_config = local_conf.get_default_mockconfig()
            if not base_config:
                self.parser.error("You haven't specified mock config, there \
is not even one in your user configuration file \
(~/.config/covscan/covscan.conf) nor in system configuration file \
(/etc/covscan/covscan.conf)")
            print "Mock config for base not specified, using default one: %s" \
                % base_config

        if not config:
            config = local_conf.get_default_mockconfig()
            if not config:
                self.parser.error("You haven't specified mock config, there \
is not even one in your user configuration file \
(~/.config/covscan/covscan.conf) nor in system configuration file \
(/etc/covscan/covscan.conf)")
            print "Mock config for target not specified, using default: %s" \
                % config

        # login to the hub
        self.set_hub(username, password)

        verify_mock(base_config, self.hub)
        options_consumed['base_mock'] = base_config
        verify_mock(config, self.hub)
        options_consumed['nvr_mock'] = config

        # end of CLI options handling

        if keep_covdata:
            options_forwarded["keep_covdata"] = keep_covdata

        if email_to:
            options_forwarded["email_to"] = email_to
        if priority is not None:
            options_consumed["priority"] = priority

        if aggressive:
            options_forwarded["aggressive"] = aggressive
        if cppcheck:
            options_forwarded["cppcheck"] = cppcheck
        if clang:
            options_forwarded['clang'] = clang
        if no_cov:
            options_forwarded['no_coverity'] = no_cov
        if warn_level:
            options_forwarded['warning_level'] = warn_level
        if analyzers:
            try:
                check_analyzers(self.hub, analyzers)
            except RuntimeError as ex:
                self.parser.error(str(ex))
            options_consumed['analyzers'] = analyzers
        if all_checker:
            options_forwarded["all"] = all_checker
        if security:
            options_forwarded["security"] = security
        if concurrency:
            options_forwarded["concurrency"] = concurrency

        if brew_build:
            options_consumed["nvr_brew_build"] = brew_build
        else:
            target_dir = random_string(32)
            upload_id, err_code, err_msg = upload_file(self.hub, srpm,
                                                       target_dir, self.parser)
            options_consumed["nvr_upload_id"] = upload_id
            options_consumed['nvr_srpm'] = srpm

        if base_brew_build:
            options_consumed["base_brew_build"] = base_brew_build
        else:
            target_dir = random_string(32)
            upload_id, err_code, err_msg = upload_file(self.hub, base_srpm,
                                                       target_dir, self.parser)
            options_consumed["base_upload_id"] = upload_id
            options_consumed['base_srpm'] = base_srpm

        task_id = self.submit_task(options_consumed, options_forwarded)

        self.write_task_id_file(task_id, task_id_file)
        print "Task info: %s" % self.hub.client.task_url(task_id)

        if not nowait:
            from kobo.client.task_watcher import TaskWatcher
            TaskWatcher.watch_tasks(self.hub, [task_id])

    def submit_task(self, hub_opts, task_opts):
        """
        hub_opts -- options for creating Task (consumed on hub)
        task_opts -- options for task itself
        """
        try:
            return self.hub.scan.create_user_diff_task(hub_opts, task_opts)
        except Fault, e:
            handle_perm_denied(e, self.parser)
