# -*- coding: utf-8 -*-

import tempfile
import os
import pipes
import sys
import grp
import shutil
import logging
import urllib

from kobo.rpmlib import get_rpm_header
from kobo.worker import TaskBase
from kobo.shortcuts import run

import kobo.tback


class VersionDiffBuild(TaskBase):
    """
        Execute diff scan between two versions/releases of a package
    """
    enabled = True

    # list of supported architectures
    arches = ["noarch"]
    # list of channels
    channels = ["default"]
    # leave False here unless you really know what you're doing
    exclusive = False
    # if True the task is not forked and runs in the worker process
    # (no matter you run worker without -f)
    foreground = False
    priority = 19
    weight = 1.0

    def run(self):
        DEBUG = False
        logging.basicConfig(
            format='%(asctime)s %(levelname)8s %(filename)s %(lineno)s \
%(message)s',
            filename='/tmp/covscand_task.log',
            level=logging.DEBUG
        )

        mock_config = self.args.pop("mock_config")
        keep_covdata = self.args.pop("keep_covdata", False)
        all_checks = self.args.pop("all", False)
        security_checks = self.args.pop("security", False)
        brew_build = self.args.pop("brew_build", None)
        srpm_name = self.args.pop("srpm_name", None)
        aggressive = self.args.pop("aggressive", None)
        cppcheck = self.args.pop("cppcheck", None)
        concurrency = self.args.pop("concurrency", None)

        # create a temp dir, make it writable by 'coverity' user
        tmp_dir = tempfile.mkdtemp(prefix="covscan_")
        os.chmod(tmp_dir, 0775)
        srpm_path = os.path.join(tmp_dir, "%s.src.rpm" % brew_build)

        if not DEBUG:
            #change atributes of temp dir
            coverity_gid = grp.getgrnam("coverity").gr_gid
            os.chown(tmp_dir, -1, coverity_gid)

            #download srpm from brew
            if brew_build is not None:
                logging.debug('I am about to download %s', brew_build)
                cmd = ["brew", "download-build", "--quiet",
                       "--arch=src", brew_build]
                run(cmd, workdir=tmp_dir)

                if not os.path.exists(srpm_path):
                    print >> sys.stderr, \
                        "Invalid path %s to SRPM file (%s): %s" % \
                        (srpm_path, brew_build, kobo.tback.get_exception())
                    self.fail()
            elif srpm_name is not None:
                # download SRPM
                task_url = self.hub.client.task_url(self.task_id).rstrip("/")
                srpm_path = os.path.join(tmp_dir, srpm_name)
                urllib.urlretrieve("%s/log/%s?format=raw" % (task_url,
                                                             srpm_name),
                                   srpm_path)

            #is srpm allright?
            try:
                get_rpm_header(srpm_path)
            except Exception:
                print >> sys.stderr, "Invalid RPM file(%s): %s" % \
                    (brew_build, kobo.tback.get_exception())
                self.fail()

        #execute mockbuild of this package
        cov_cmd = []
        cov_cmd.append("cd")
        cov_cmd.append(pipes.quote(tmp_dir))
        cov_cmd.append(";")

        # $program [-fit] MOCK_PROFILE my-package.src.rpm [COV_OPTS]
        cov_cmd.append('cov-mockbuild')
        if keep_covdata:
            cov_cmd.append("-i")
        if cppcheck:
            cov_cmd.append("-c")
        cov_cmd.append(pipes.quote(mock_config))
        cov_cmd.append(pipes.quote(srpm_path))
        if all_checks:
            cov_cmd.append("--all")
        if aggressive:
            cov_cmd.append("--aggressiveness-level high")
        if security_checks:
            cov_cmd.append("--security")
        if concurrency:
            cov_cmd.append("--concurrency")

        command = ["su", "-", "coverity", "-c", " ".join(cov_cmd)]

        if not DEBUG:
            retcode, output = run(command, can_fail=True, stdout=True)
        else:
            command_str = ' '.join(command)
            logging.info("In production I would run this command: %s",
                         command_str)
            retcode = 0

        # upload results back to hub

        if DEBUG:
            logging.debug('I am about to copy test tarball')
            shutil.copy2('/tmp/' + brew_build + '.tar.xz', tmp_dir)

        xz_path = srpm_path[:-8] + ".tar.xz"
        if not os.path.exists(xz_path):
            xz_path = srpm_path[:-8] + ".tar.lzma"
        self.hub.upload_task_log(open(xz_path, "r"),
                                 self.task_id, os.path.basename(xz_path))

        try:
            self.hub.worker.extract_tarball(self.task_id, '')
        except Exception, ex:
            logging.error("got exception %s, trace:\n%s", str(ex),
                          kobo.tback.get_exception())
            self.fail()

        # remove temp files
        shutil.rmtree(tmp_dir)

        if retcode:
            self.fail()

        self.hub.worker.finish_task(self.task_id)

    @classmethod
    def cleanup(cls, hub, conf, task_info):
        pass
        # remove temp files, etc.

    @classmethod
    def notification(cls, hub, conf, task_info):
        pass
        #hub.worker.email_task_notification(task_info["id"])