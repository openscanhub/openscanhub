# -*- coding: utf-8 -*-

import os
import json
import tempfile
import unittest
from covscanhub.service.loading import load_defects_from_file, get_defect_stats


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


class TestLoading(unittest.TestCase):
    def test_load_defects_from_file(self):
        fd, tmp_filename = tempfile.mkstemp()
        try:
            os.write(fd, DEFECTS_JSON)
            os.close(fd)
            defects = load_defects_from_file(tmp_filename)
            self.assertEqual(len(defects), 3)
            self.assertTrue('events' in defects[0])
        finally:
            os.remove(tmp_filename)

    def test_get_defect_stats(self):
        defects = json.loads(DEFECTS_JSON)
        stats = get_defect_stats(defects['defects'])
        self.assertEqual(stats['CHECKER1'], 2)
        self.assertEqual(stats['CHECKER2'], 1)