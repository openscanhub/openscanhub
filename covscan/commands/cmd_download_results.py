# -*- coding: utf-8 -*-

import os, sys
import urllib
import covscan


class Download_Results(covscan.CovScanCommand):
    """analyze a SRPM without and with patches, return diff"""
    enabled = True
    admin = False  # admin type account required

    def options(self):
        # specify command usage
        # normalized name contains a lower-case class name with underscores
        # converted to dashes
        self.parser.usage = "%%prog %s [options] task_id [task_id...]" % \
            self.normalized_name

        self.parser.add_option(
            "-d",
            "--dir",
            help="path to store results",
        )

    def fetch_results(self, task_url, nvr):
        tarball = nvr + '.tar.xz'
        # get absolute path
        if self.dir:
            local_path = os.path.join(self.dir,
                                      tarball)
        else:
            local_path = os.path.join(os.path.abspath(os.curdir),
                                      tarball)
        # task_url is url to task with trailing '/'
        url = "%slog/%s?format=raw" % (task_url, tarball)
        urllib.urlretrieve(url, local_path)

    def run(self, *args, **kwargs):
        #local_conf = get_conf(self.conf)

        username = kwargs.pop("username", None)
        password = kwargs.pop("password", None)

        if len(args) == 0:
            self.parser.error("no task ID specified")
        tasks = args

        self.dir = kwargs.pop("dir", None)

        if self.dir:
            if not os.path.isdir(self.dir):
                self.parser.error("provided directory does not exist")
            else:
                self.dir = os.path.abspath(self.dir)

        # login to the hub
        self.set_hub(username, password)

        failed = False

        for task_id in tasks:
            try:
                task_url = self.hub.client.task_url(task_id)
                nvr = self.hub.client.task_info(task_id)['args']['srpm_name'].\
                    replace('.src.rpm', '')
                self.fetch_results(task_url, nvr)
            except Exception, ex:
                failed = True
                print ex

        if failed:
            sys.exit(1)
