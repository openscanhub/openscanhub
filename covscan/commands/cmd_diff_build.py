# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import

import six

import os
from six.moves import urllib
import covscan

from six.moves.xmlrpc_client import Fault
from kobo.shortcuts import random_string
from covscan.commands.shortcuts import verify_brew_koji_build, verify_mock, \
    upload_file, handle_perm_denied
from covscan.commands.common import *
from covscancommon.utils.conf import get_conf
from covscancommon.utils.cim import extract_cim_data
from covscan.commands.analyzers import check_analyzers


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

        add_config_option(self.parser)
        add_cppcheck_option(self.parser)
        add_aggressive_option(self.parser)
        add_concurrency_option(self.parser)
        add_download_results_option(self.parser)
        add_clang_option(self.parser)
        add_no_cov_option(self.parser)
        add_comp_warnings_option(self.parser)
        add_analyzers_option(self.parser)
        add_profile_option(self.parser)
        add_csmock_args_option(self.parser)

        add_keep_covdata_option(self.parser)
        add_comment_option(self.parser)
        add_task_id_file_option(self.parser)
        add_nowait_option(self.parser)
        add_email_to_option(self.parser)
        add_priority_option(self.parser)
        add_brew_build_option(self.parser)
        add_all_option(self.parser)
        add_security_option(self.parser)
        add_custom_model_option(self.parser)

        self.parser.add_option(
            "-m",
            dest="commit_string",
            metavar="user:passwd@host:port/stream",
            help="""Commit results to Integrity Manager. You can specify \
the target host/stream as an optional argument using the
following format: "user:passwd@host:port/stream". User and password might be \
stored in user configuration file."""
        )

        add_install_to_chroot_option(self.parser)

    def validate_results_store_file(self):
        if self.results_store_file:
            if isinstance(self.results_store_file, six.string_types):
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
        urllib.request.urlretrieve(url, local_path)

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
        self.results_store_file = kwargs.pop("results_dir", None)
        clang = kwargs.pop('clang', False)
        no_cov = kwargs.pop('no_cov', False)
        warn_level = kwargs.pop('warn_level', '0')
        analyzers = kwargs.pop('analyzers', '')
        profile = kwargs.pop('profile', None)
        csmock_args = kwargs.pop('csmock_args', None)
        cov_custom_model = kwargs.pop('cov_custom_model', None)
        tarball_build_script = kwargs.pop('tarball_build_script', None)
        packages_to_install = kwargs.pop('install_to_chroot', None)

        if len(args) != 1:
            self.parser.error("please specify exactly one SRPM")
        if brew_build:
            # self.srpm contains NVR if --brew-build is used!
            self.srpm = args[0]
        else:
            self.srpm = os.path.abspath(os.path.expanduser(args[0]))

        self.validate_results_store_file()

        if brew_build:
            # get build from koji
            result = verify_brew_koji_build(self.srpm, self.conf['BREW_URL'],
                                            self.conf['KOJI_URL'])
            if result is not None:
                self.parser.error(result)
        elif tarball_build_script:
            # we are analyzing tarball with build script
            if not os.path.exists(self.srpm):
                self.parser.error("Tarball does not exist.")

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

        options = {}
        # check CIM string, it might be empty, so `if commit_string` is
        #  a bad idea
        if commit_string is not None:
            try:
                options['CIM'] = extract_cim_data(commit_string)
            except RuntimeError as ex:
                self.parser.error(ex.message)
        if email_to:
            options["email_to"] = email_to
        if priority is not None:
            options["priority"] = priority

        if keep_covdata:
            options["keep_covdata"] = keep_covdata
        if aggressive:
            options["aggressive"] = aggressive
        if cppcheck:
            options["cppcheck"] = cppcheck
        if clang:
            options['clang'] = clang
        if no_cov:
            options['no_coverity'] = no_cov
        if warn_level:
            options['warning_level'] = warn_level
        if analyzers:
            try:
                check_analyzers(self.hub, analyzers)
            except RuntimeError as ex:
                self.parser.error(str(ex))
            options['analyzers'] = analyzers
        if profile:
            options['profile'] = profile
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

        if csmock_args:
            options['csmock_args'] = csmock_args
        if cov_custom_model:
            target_dir = random_string(32)
            upload_model_id, err_code, err_msg = upload_file(self.hub, cov_custom_model,
                                                       target_dir, self.parser)
            options["upload_model_id"] = upload_model_id

        if packages_to_install:
            options['install_to_chroot'] = packages_to_install
        if tarball_build_script:
            options['tarball_build_script'] = tarball_build_script

        task_id = self.submit_task(config, comment, options)

        self.write_task_id_file(task_id, task_id_file)
        task_url = self.hub.client.task_url(task_id)
        print("Task info: %s" % task_url)

        if not nowait:
            from kobo.client.task_watcher import TaskWatcher
            TaskWatcher.watch_tasks(self.hub, [task_id])

            # store results if user requested this
            if self.results_store_file is not None:
                self.fetch_results(task_url)

    def submit_task(self, config, comment, options):
        try:
            return self.hub.scan.diff_build(config, comment, options)
        except Fault as e:
            handle_perm_denied(e, self.parser)
