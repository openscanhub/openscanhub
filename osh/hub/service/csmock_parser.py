# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

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
import json
import logging
import os
import subprocess
import tempfile

RESULT_FILE_JSON = 'scan-results.js'
RESULT_FILE_ERR = 'scan-results.err'
RESULT_FILE_HTML = 'scan-results.html'


logger = logging.getLogger(__name__)


class ResultsExtractor:
    """

    """

    def __init__(self, path, output_dir=None, unpack_in_temp=True):
        """
        path is either path to tarball or to a dir with results
        """
        self.path = path
        if output_dir:
            self.output_dir = output_dir
        elif unpack_in_temp:
            self.output_dir = tempfile.mkdtemp(prefix='csmock-')
        else:
            self.output_dir = os.path.dirname(os.path.expanduser(path))
        self._json_path = None

    @property
    def json_path(self):
        if self._json_path is None:
            self.process()
        if not os.path.exists(self._json_path):
            raise RuntimeError('json results do not exist: ' + self._json_path)
        return self._json_path

    def extract_tarball(self, exclude_patterns=None):
        """

        """
        exclude_patterns = exclude_patterns or []
        exclude_patterns.append("*debug")  # do not unpack debug dir
        # python 2 does not support lzma
        command = [
            'tar', '-xf', self.path,
            '-C', self.output_dir,
            '--wildcards',
            '--wildcards-match-slash',
        ]
        if exclude_patterns:
            # do NOT quote pattern! it won't work
            command += ['--exclude=' + p for p in exclude_patterns]
        logger.debug('Running command %s', command)
        subprocess.check_call(command)

    def get_json_result_path(self):
        return self.json_path

    def process(self):
        """ untar results if needed """
        if os.path.isdir(self.path):
            self._json_path = os.path.join(self.path, RESULT_FILE_JSON)
        else:
            self.extract_tarball()
            try:
                self._json_path = glob.glob(os.path.join(self.output_dir, '*', RESULT_FILE_JSON))[0]
            except IndexError:
                logger.error("no results (%s) in dir %s", RESULT_FILE_JSON, self.output_dir)
                self._json_path = ''


class CsmockAPI:
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
            with open(self.json_results_path) as fp:
                self._json_result = json.load(fp)
        return self._json_result

    def get_defects(self):
        """
        return list of defects: csmock's output is used directly
        """
        return self.json_result['defects']

    def get_scan_metadata(self):
        return self.json_result.get('scan', {})

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
        for key, value in scan.items():
            if key.startswith('analyzer-version-'):
                # analyzer-version-[gcc]
                analyzer = {'name': key[17:], 'version': value}
                analyzers.append(analyzer)
        return analyzers


def unpack_and_return_api(tb_path, in_dir=""):
    """ convenience shortcut """
    in_dir = in_dir or os.path.dirname(tb_path)
    rex = ResultsExtractor(tb_path, output_dir=in_dir, unpack_in_temp=False)
    try:
        return CsmockAPI(rex.json_path)
    except RuntimeError as ex:
        logger.error('Error while creating csmock api: %s', ex)
        return None
