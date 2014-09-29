#!/usr/bin/python -tt
#-*- coding: utf-8 -*-

"""

csmock python api

{
    "scan":
    {
        "analyzer-version-clang": "3.4",
        "analyzer-version-cppcheck": "1.66",
        "analyzer-version-gcc": "4.9.1",
        "exit-code": 0,
        "host": "quahog",
        "mock-config": "fedora-21-x86_64",
        "store-results-to": "/tmp/asd",
        "time-created": "2014-09-01 18:30:19",
        "time-finished": "2014-09-01 18:38:15",
        "tool": "csmock",
        "tool-args": "'/bin/csmock' '-t' 'cppcheck,gcc,clang' '--no-scan' '-r' 'fedora-21-x86_64' '-o' 'asd' '--force'",
        "tool-version": "csmock-1.3.2.20140829.165742.ge16c941-1.fc21"
    },
    "defects": ""
}
"""
import glob
import os
import json
import pipes
import shutil
import subprocess
import tempfile
import logging
import urllib


__all__ = ('CsmockAPI', 'CsmockRunner', 'ResultsExtractor')


RESULT_FILE_JSON = 'scan-results.js'
RESULT_FILE_ERR = 'scan-results.err'
RESULT_FILE_HTML = 'scan-results.html'


logger = logging.getLogger(__name__)


class Results(object):
    """
    output from run

    it is represented as tarball -- needs to be extracted and data from
    json file has to be imported
    """

    def __init__(self, json_results_path):
        self.json_results_path = json_results_path


class ResultsExtractor(object):
    """

    """

    def __init__(self, path, output_dir=None, unpack_in_temp=True):
        """
        path is either path to tarball or to a dir with results
        """
        self.path = path
        self.output_dir = output_dir
        if unpack_in_temp:
            self.output_dir = tempfile.mkdtemp(prefix='csmock-')
        self._json_path = None

    @property
    def json_path(self):
        if self._json_path is None:
            self.process()
        return self._json_path

    def extract_tarball(self, exclude_patterns=None):
        """

        """
        exclude_patterns = exclude_patterns or []
        exclude_patterns.append("*debug")  # do not unpack debug dir
        # python 2 does not support lzma
        command = [
            'tar', '-xf', pipes.quote(self.path),
            '-C', pipes.quote(self.output_dir),
            '--wildcards',
            '--wildcards-match-slash',
        ]
        if exclude_patterns:
            # do NOT quote pattern! it won't work
            command += ['--exclude=%s' % p for p in exclude_patterns]
        logger.debug('Running command %s' % command)
        subprocess.check_call(command)

    def get_json_result_path(self):
        return self.json_path

    def process(self):
        """ untar results if needed """
        if os.path.isdir(self.path):
            self._json_path = os.path.join(self.path, RESULT_FILE_JSON)
        else:
            self.extract_tarball()
            self._json_path = glob.glob(os.path.join(self.output_dir, '*', RESULT_FILE_JSON))[0]


class CsmockAPI(object):
    """

    """

    def __init__(self, json_results_path):
        """
        path -- path to results in JSON format
        """
        self.json_results_path = json_results_path
        self._json_result = None

    @property
    def json_result(self):
        if self._json_result is None:
            with open(self.json_results_path, 'r') as fp:
                self._json_result = json.load(fp)
        return self._json_result

    def get_defects(self):
        """
        return list of defects: csmock's output is used directly
        """
        return self.json_result['defects']

    def get_scan_metadata(self):
        return self.json_result['scan']

    def json(self):
        """
        return result report from csmock as json
        """
        return self.json_result

    def get_analyzers(self):
        """
        return analyzers used for scan, format:

        [{
            'name': 'analyzer1',
            'version': '1.2.3'
        },... ]
        """
        scan = self.get_scan_metadata()
        analyzers = []
        for key, value in scan.iteritems():
            if key.startswith('analyzer-version-'):
                analyzer = {}
                # analyzer-version-[gcc]
                analyzer['name'] = key[17:]
                analyzer['version'] = value
                analyzers.append(analyzer)
        return analyzers


class CsmockRunner(object):
    """
    context manager class which executes csmock in current process
    """

    def __init__(self, tmpdir=None, create_tmpdir=False):
        if create_tmpdir:
            self.tmpdir = tempfile.mkdtemp()
            self.our_temp_dir = True
        else:
            self.tmpdir = tmpdir
            self.our_temp_dir = False

    def __enter__(self):
        self.tmpdir = tempfile.mkdtemp()
        self.our_temp_dir = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.our_temp_dir:
            try:
                shutil.rmtree(self.tmpdir)
            except OSError:
                # dangling temp dir
                # could be erased with sudo rm -rf self.tmpdir
                pass

    def _run(self, args):
        """
        run csmock with provided arguments
        """
        if not args:
            logger.error("no args for csmock specified!")
            raise RuntimeError("no args for csmock specified!")

        command = "csmock " + args

        subprocess.check_call(command, shell=True, stdout=subprocess.STDOUT, stderr=subprocess.STDOUT)

    def do(self, args, output_path=None, su_user=None):
        """ we are expecting that csmock will produce and output """
        if not args:
            logger.error("no args for csmock specified!")
            raise RuntimeError("no args for csmock specified!")

        command = "csmock " + args
        if output_path:
            command += ' -o ' + output_path

        if self.tmpdir:
            if not os.path.isdir(self.tmpdir):
                logger.error('temp dir does not exists!')
                raise RuntimeError('temp dir does not exists!')
            command = 'cd %s && ' % pipes.quote(self.tmpdir) + command

        if su_user:
            if self.our_temp_dir:
                subprocess.check_call(['sudo', '--',
                                       'chown', '%s:%s' % (su_user, su_user), self.tmpdir])
                subprocess.check_call(['sudo', '-u', pipes.quote(su_user), '--',
                                       'chmod', 'go+rx', self.tmpdir])
            command = 'sudo su - %s -c "%s"' % (pipes.quote(su_user), command)
        retcode = subprocess.call(command, shell=True)
        if output_path:
            return output_path, retcode
        if self.tmpdir:
            return glob.glob(os.path.join(self.tmpdir, '*.tar.xz'))[0], retcode
        else:
            return glob.glob('./*.tar.xz')[0], retcode

    def analyze(self, analyzers, srpm_path, profile=None, su_user=None, additional_arguments=None, **kwargs):
        if not srpm_path.endswith('.src.rpm'):
            raise RuntimeError("'srpm' path has to end with '.src.rpm'")
        base_srpm = os.path.basename(srpm_path)[:-8]
        if self.tmpdir:
            output_path = os.path.join(self.tmpdir, base_srpm + '.tar.xz')
        else:
            output_path = os.path.join(os.getcwd(), base_srpm + '.tar.xz')
        cmd = '-t %s -o %s' % (pipes.quote(analyzers), pipes.quote(output_path))
        if profile:
            cmd += ' -r %s' % pipes.quote(profile)
        if additional_arguments:
            cmd += ' ' + additional_arguments
        cmd += ' ' + srpm_path
        return self.do(cmd, su_user=su_user)

    def srpm_download_analyze(self, analyzers, srpm_name, srpm_url, profile=None,
                              su_user=None, additional_arguments=None, **kwargs):
        """ download srpm from remote location and analyze it"""
        if self.tmpdir:
            srpm_path = os.path.join(self.tmpdir, srpm_name)
        else:
            srpm_path = os.path.join(os.getcwd(), srpm_name)
        urllib.urlretrieve(srpm_url, srpm_path)
        return self.analyze(analyzers, srpm_path, profile, su_user, additional_arguments, **kwargs)

    def koji_analyze(self, analyzers, nvr, profile=None, su_user=None,
                     additional_arguments=None, koji_bin="koji", **kwargs):
        download_cmd = [koji_bin, "download-build", "--quiet", "--arch=src", nvr]
        if self.tmpdir:
            subprocess.check_call(download_cmd, cwd=self.tmpdir)
            srpm_path = os.path.join(self.tmpdir, '%s.src.rpm' % nvr)
        else:
            subprocess.check_call(download_cmd)
            srpm_path = os.path.join(os.getcwd(), '%s.src.rpm' % nvr)
        return self.analyze(analyzers, srpm_path, profile, su_user, additional_arguments, **kwargs)

    def no_scan(self, analyzers, profile=None, su_user=None, additional_arguments=None, **kwargs):
        """
        execute csmock command for listing analyzers and versions
        returns path to dir with results
        """
        if self.tmpdir:
            output_path = os.path.join(self.tmpdir, 'output.tar.xz')
        else:
            output_path = os.path.join(os.getcwd(), 'csmock-output')
        cmd = '-t ' + pipes.quote(analyzers)
        if profile:
            cmd += ' -r %s' % pipes.quote(profile)
        cmd += ' --no-scan'
        if additional_arguments:
            cmd += ' ' + additional_arguments
        self.do(cmd, output_path=output_path, su_user=su_user)
        return output_path


def unpack_and_return_api(tb_path, in_dir=""):
    """ convenience shortcut """
    in_dir = in_dir or os.path.dirname(tb_path)
    rex = ResultsExtractor(tb_path, output_dir=in_dir, unpack_in_temp=False)
    return CsmockAPI(rex.json_path)
