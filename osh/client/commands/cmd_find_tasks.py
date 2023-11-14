# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

import sys

from kobo.client.constants import TASK_STATES

import osh.client


class Find_Tasks(osh.client.OshCommand):
    """find tasks by provided query string"""
    enabled = True
    admin = False  # admin type account required

    def options(self):
        # specify command usage
        # normalized name contains a lower-case class name with underscores
        # converted to dashes
        self.parser.usage = f"%prog {self.normalized_name} [options] <query_string>"
        self.parser.epilog = "without '-l' option, newest task is at the \
beginning of a list, unfinished tasks are at the end; you should pick one of \
these options: --regex, --package, --nvr"
        self.parser.add_option(
            "-l",
            "--latest",
            default=False,
            action="store_true",
            help="display only latest task",
        )
        self.parser.add_option(
            "-r",
            "--regex",
            default=False,
            action="store_true",
            help="query by regular expression (python, module: re)",
        )
        self.parser.add_option(
            "-p",
            "--package",
            default=False,
            action="store_true",
            help="query by package name",
        )
        self.parser.add_option(
            "-n",
            "--nvr",
            default=False,
            action="store_true",
            help="query by NVR (default one)"
        )
        self.parser.add_option(
            "-s",
            "--states",
            action="append",
            type="string",
            nargs=1,
            help=(f"query by task state. This option is used in conjunction with -r, -p, or -n. "
                  f"Specify multiple states by using it multiple times, like '-s failed -s closed'. "
                  f"Valid choices include {', '.join([s.lower() for s in TASK_STATES])}.")
        )

    def run(self, *args, **kwargs):
        regex = kwargs.pop("regex")
        package_name = kwargs.pop("package")
        states = kwargs.get("states")

        latest = kwargs.pop("latest")

        if len(args) != 1:
            self.parser.error("please specify exactly one query string \
(in case of regex, enclose it in quotes please)")

        query_string = args[0]

        # login to the hub
        self.connect_to_hub(kwargs)

        query = {}
        if regex:
            query['regex'] = query_string
        elif package_name:
            query['package_name'] = query_string
        else:
            # nvr is default one, so we don't care if it's specified
            query['nvr'] = query_string
        if states:
            query['states'] = [TASK_STATES[state.upper()] for state in states]
        task_ids = self.hub.scan.find_tasks(query)

        if not task_ids:
            print("No tasks found for the given query.", file=sys.stderr)
            sys.exit(1)

        if latest:
            print(task_ids[0])
            return

        for task_id in task_ids:
            print(task_id)
