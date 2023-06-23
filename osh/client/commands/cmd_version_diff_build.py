# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

from osh.client.commands.cmd_build import Base_Build


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
            "--base-brew-build",
            help="use a brew build for base (specified by NVR) instead of a \
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

    def prepare_task_options(self, args, kwargs):
        base_brew_build = kwargs.get("base_brew_build")
        base_config = kwargs.get("base_config")
        base_srpm = kwargs.get("base_srpm")
        brew_build = kwargs.get("brew_build")
        config = kwargs.get("config")
        srpm = kwargs.get("srpm")

        # both bases are specified
        if base_brew_build and base_srpm:
            self.parser.error("Choose exactly one option (--base-brew-build, \
--base-srpm), not both of them.")

        # both nvr/targets are specified
        if brew_build and srpm:
            self.parser.error("Choose exactly one option (--brew-build, \
--srpm), not both of them.")

        # no package option specified
        if (not base_brew_build and not brew_build and not srpm and not
                base_srpm):
            self.parser.error("Please specify both builds or SRPMs.")

        # no base specified
        if not base_brew_build and not base_srpm:
            self.parser.error("You haven't specified base.")

        # no nvr/target specified
        if not brew_build and not srpm:
            self.parser.error("You haven't specified target.")

        if srpm and not srpm.endswith(".src.rpm"):
            self.parser.error("provided target file doesn't appear to be \
a SRPM")

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
