# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

from osh.client.commands.cmd_build import Base_Build
from osh.client.commands.common import add_tarball_option


class Version_Diff_Build(Base_Build):
    """analyze 2 SRPMs (base and target) and diff results"""
    enabled = True
    admin = False  # admin type account required

    def options(self):
        super().options()

        self.parser.add_option(
            "--base-config",
            help="specify mock config name for base package"
        )

        self.parser.add_option(
            "--base-nvr",
            help="use a Koji build for base (specified by NVR) instead of a local file"
        )

        self.parser.add_option(
            "--base-srpm",
            help="path to sources used as base"
        )

        self.parser.add_option(
            "--srpm",
            help="path to sources used as target"
        )

        add_tarball_option(self.parser)
        self.parser.add_option(
            "--base-tarball-build-script",
            help="With this option osh-cli accepts path to tarball specified via first argument and "
                 "then the tarball will be scanned. "
                 "This option sets command which should build the base package, usually this should be just "
                 "\"make\", in case of packages which doesn't need to be built, just pass \"true\".",
        )

        # Deprecated aliases:
        self.parser.add_option("--base-brew-build", dest="base_nvr",
                               help="DEPRECATED alias for --base-nvr")

    def prepare_task_options(self, args, kwargs):
        base_config = kwargs.get("base_config")
        base_nvr = kwargs.get("base_nvr")
        base_srpm = kwargs.get("base_srpm")
        config = kwargs.get("config")
        nvr = kwargs.get("nvr")
        srpm = kwargs.get("srpm")

        # both bases are specified
        if base_nvr and base_srpm:
            self.parser.error("Choose exactly one option (--base-nvr, --base-srpm), not both of them.")

        # both nvr/targets are specified
        if nvr and srpm:
            self.parser.error("Choose exactly one option (--nvr, --srpm), not both of them.")

        # no package option specified
        if (not base_nvr and not nvr and not srpm and not base_srpm):
            self.parser.error("Please specify both builds or SRPMs.")

        # no base specified
        if not base_nvr and not base_srpm:
            self.parser.error("You haven't specified base.")

        # no nvr/target specified
        if not nvr and not srpm:
            self.parser.error("You haven't specified target.")

        if not base_config and config:
            kwargs["base_config"] = config
        if base_config and not config:
            kwargs["config"] = base_config

        # prepare task options
        options = super().prepare_task_options(args, kwargs)
        options.update(self.check_build(args, kwargs, prefix="base_"))

        return options

    def submit_task(self, options):
        return self.hub.scan.create_user_diff_task(options, {})
