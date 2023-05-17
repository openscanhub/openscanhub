# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

# -*- coding: utf-8 -*-


import os
import pwd

from osh.common.csmock_parser import CsmockAPI, CsmockRunner, ResultsExtractor

DEFECTS_JSON = """
{
    "scan":
    {
        "analyzer": "clang",
        "analyzer-version": "1",
        "host": "localhost",
        "mock-config": "fedora-rawhide",
        "project-name": "package-1",
        "tool": "cov-mockbuild"
    },
    "defects":
    [
        {
            "checker": "CHECKER1",
            "key_event_idx": 2,
            "events":
            [
                {
                    "file_name": "file.c",
                    "line": 76,
                    "event": "a",
                    "message": "Something went wrong."
                },
                {
                    "file_name": "file2.c",
                    "line": 102,
                    "event": "b",
                    "message": "It failed here."
                }
            ]
        },
        {
            "checker": "CHECKER1",
            "key_event_idx": 1,
            "events":
            [
                {
                    "file_name": "file3.c",
                    "line": 436,
                    "event": "c",
                    "message": "Something went wrong."
                }
            ]
        },
        {
            "checker": "CHECKER2",
            "key_event_idx": 3,
            "events":
            [
                {
                    "file_name": "source.c",
                    "line": 436,
                    "event": "e",
                    "message": "Executing that."
                },
                {
                    "file_name": "source.c",
                    "line": 436,
                    "event": "f",
                    "message": "Triggering this."
                },
                {
                    "file_name": "source2.c",
                    "line": 440,
                    "event": "g",
                    "message": "Variable is not initialized."
                }
            ]
        }
    ]
}
"""


# SRPM = os.path.join(os.getcwd(), 'isync-1.1.1-3.fc22.src.rpm')
#
# @pytest.fixture
# def simple_scan():
#     runner = CsmockRunner(create_tmpdir=True)
#     return runner.analyze('cppcheck,clang', SRPM)


class TestCsmockAPI:
    """ intergration tests for csmock api """

    def test_run(self):
        runner = CsmockRunner()
        runner.do('--help')

    def test_get_analyzers(self):
        with CsmockRunner() as runner:
            tb_path, err_code = runner.no_scan('cppcheck,clang',
                                               profile='fedora-rawhide-x86_64')
            api = CsmockAPI(ResultsExtractor(tb_path, output_dir=runner.tmpdir, unpack_in_temp=False).json_path)
            analyzers = api.get_analyzers()
            print(analyzers)
        assert isinstance(analyzers, list)

    def test_do_with_su(self):
        with CsmockRunner() as runner:
            user = 'asd'
            path = os.path.join(runner.tmpdir, 'output.tar.xz')
            output_path, err_code = runner.do('-t clang,cppcheck --no-scan',
                                              output_path=path, su_user=user)
            assert pwd.getpwuid(os.stat(output_path).st_uid).pw_name == user

    def test_koji_analyze(self):
        with CsmockRunner() as runner:
            nvr = 'notmuch-0.18.1-4.fc21'
            tb_path, err_code = runner.koji_analyze('clang,cppcheck', nvr, profile='fedora-rawhide-x86_64')
            assert os.path.exists(tb_path)
            api = CsmockAPI(ResultsExtractor(tb_path, output_dir=runner.tmpdir, unpack_in_temp=False).json_path)
            defects = api.get_defects()
            assert isinstance(defects, list)
