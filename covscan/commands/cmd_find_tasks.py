# -*- coding: utf-8 -*-

import sys
import covscan


class Find_Tasks(covscan.CovScanCommand):
    """find tasks by provided query string"""
    enabled = True
    admin = False  # admin type account required

    def options(self):
        # specify command usage
        # normalized name contains a lower-case class name with underscores
        # converted to dashes
        self.parser.usage = "%%prog %s [options] <query_string>" % \
            self.normalized_name
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

    def run(self, *args, **kwargs):
        #local_conf = get_conf(self.conf)

        username = kwargs.pop("username", None)
        password = kwargs.pop("password", None)

        regex = kwargs.pop("regex")
        package_name = kwargs.pop("package")

        latest = kwargs.pop("latest")

        if len(args) != 1:
            self.parser.error("please specify exactly one query string \
(in case of regex, enclose it in quotes please)")

        query_string = args[0]

        # login to the hub
        self.set_hub(username, password)

        query = {}
        if regex:
            query['regex'] = query_string
        elif package_name:
            query['package_name'] = query_string
        else:
            # nvr is default one, so we don't care if it's specified
            query['nvr'] = query_string
        task_ids = self.hub.scan.find_tasks(query)

        if task_ids:
            if latest:
                print task_ids[0]
            else:
                for task_id in task_ids:
                    print task_id
        else:
            sys.exit(1)
        sys.exit(0)
