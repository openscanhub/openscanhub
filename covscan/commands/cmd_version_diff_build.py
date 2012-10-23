# -*- coding: utf-8 -*-


import os
import brew
import covscan
from kobo.shortcuts import random_string
from kobo.client import HubProxy

            
class Version_Diff_Build(covscan.CovScanCommand):
    """analyze 2 SRPMs and diff results"""
    enabled = True
    admin = False  # admin type account required

    def verify_brew_build(self, build):
        srpm = os.path.basename(build) # strip path if any
        if srpm.endswith(".src.rpm"):
            srpm = srpm[:-8]
        # XXX: hardcoded
        brew_proxy = brew.ClientSession("http://brewhub.devel.redhat.com/brewhub")
        try:
            build_info = brew_proxy.getBuild(srpm)
        except brew.GenericError:
            self.parser.error("Build does not exist in brew: %s" % srpm)
                    
    def verify_mock(self, mock):
        mock_conf = self.hub.mock_config.get(mock)
        if not mock_conf:
            self.parser.error("Unknown mock config: %s" % mock_conf)
        if not mock_conf["enabled"]:
            self.parser.error("Mock config is not enabled: %s" % mock_conf)

    def options(self):
        # specify command usage
        # normalized name contains a lower-case class name with underscores
        #  converted to dashes
        self.parser.usage = "%%prog %s [options] <args>" % self.normalized_name

        self.parser.add_option(
            "--base-config",
            help="specify mock config name for base package"
        )

        self.parser.add_option(
            "--nvr-config",
            help="specify mock config name for parent package"
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
            help="task priority (20+ is admin only)"
        )

        self.parser.add_option(
            "--base-brew-build",
            help="use a brew build for base (specified by NVR) instead of a \
local file"
        )

        self.parser.add_option(
            "--nvr-brew-build",
            help="use a brew build for target (specified by NVR) instead of a \
local file"
        )
        
        self.parser.add_option(
            "--base-srpm",
            help="local file used as base"
        )

        self.parser.add_option(
            "--nvr-srpm",
            help="local file used as target"
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

        print args
        print kwargs

        # optparser output is passed via *args (args) and **kwargs (opts)
        username = kwargs.pop("username", None)
        password = kwargs.pop("password", None)
        nvr_config = kwargs.pop("nvr_config", None)
        base_config = kwargs.pop("base_config", None)
        keep_covdata = kwargs.pop("keep_covdata", False)
        email_to = kwargs.pop("email_to", [])
        comment = kwargs.pop("comment")
        nowait = kwargs.pop("nowait")
        task_id_file = kwargs.pop("task_id_file")
        priority = kwargs.pop("priority")
        base_brew_build = kwargs.pop("base_brew_build", None)
        nvr_brew_build = kwargs.pop("nvr_brew_build", None)
        base_srpm = kwargs.pop("base_srpm", None)
        nvr_srpm = kwargs.pop("nvr_srpm", None)        
        all = kwargs.pop("all")
        security = kwargs.pop("security")

        #print "args = %s" % args
        #print "kwargs = %s" % kwargs

        #both bases are specified
        if base_brew_build and base_srpm:
            self.parser.error("Choose exactly one option (--base-brew-build, \
--base-srpm), not both of them.")

        #both nvr/targets are specified
        if nvr_brew_build and nvr_srpm:
            self.parser.error("Choose exactly one option (--nvr-brew-build, \
--nvr-srpm), not both of them.")

        #no package option specified
        if not base_brew_build and not nvr_brew_build and not nvr_srpm and \
not base_srpm:
            self.parser.error("Please specify both builds or SRPMs.")

        #no base specified
        if not base_brew_build and not base_srpm:
            self.parser.error("You haven't specified base.")
        
        #no nvr/target specified
        if not nvr_brew_build and not nvr_srpm:
            self.parser.error("You haven't specified target.")

        if nvr_srpm and not nvr_srpm.endswith(".src.rpm"):
            self.parser.error("provided target file doesn't appear to be a SRPM")

        if base_srpm and not base_srpm.endswith(".src.rpm"):
            self.parser.error("provided base file doesn't appear to be a SRPM")

        if nvr_brew_build:
            self.verify_brew_build(nvr_brew_build)
                
        if base_brew_build:
            self.verify_brew_build(nvr_brew_build)

        if not base_config:
            self.parser.error("please specify a mock config for base")

        if not nvr_config:
            self.parser.error("please specify a mock config for target")
            
        # login to the hub
        if hub_url is None:
            self.set_hub(username, password)
        else:
            self.hub = HubProxy(conf=self.conf, 
                                AUTH_METHOD='krbv', 
                                HUB_URL=hub_url)

        self.verify_mock(base_mock_conf)
        self.verify_mock(nvr_mock_conf)

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
        """
        if nvr_brew_build:
            options["nvr_brew_build"] = nvr_brew_build
        else:
            target_dir = random_string(32)
            upload_id, err_code, err_msg = self.hub.upload_file(nvr_srpm, target_dir)
            options["nvr_upload_id"] = upload_id
            
        if base_brew_build:
            options["base_brew_build"] = base_brew_build
        else:
            target_dir = random_string(32)
            upload_id, err_code, err_msg = self.hub.upload_file(base_srpm, target_dir)
            options["base_upload_id"] = upload_id

        task_id = self.submit_task(config, comment, options)
        self.write_task_id_file(task_id, task_id_file)
        print "Task info: %s" % self.hub.client.task_url(task_id)

        if not nowait:
            from kobo.client.task_watcher import TaskWatcher
            TaskWatcher.watch_tasks(self.hub, [task_id])

        
    def submit_task(self, config, comment, options):
        #xmlrpc call
        return self.hub.scan.diff_build(config, comment, options)
        """

