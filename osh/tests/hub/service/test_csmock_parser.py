# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

import unittest

from osh.hub.service.csmock_parser import parse_elapsed_time


class TestParseElapsedTime(unittest.TestCase):
    def test_normal_time(self):
        self.assertEqual(parse_elapsed_time("01:30:00"), 5400)

    def test_zero(self):
        self.assertEqual(parse_elapsed_time("00:00:00"), 0)

    def test_over_24_hours(self):
        self.assertEqual(parse_elapsed_time("30:45:44"), 110744)

    def test_exactly_24_hours(self):
        self.assertEqual(parse_elapsed_time("24:00:00"), 86400)

    def test_large_hours(self):
        self.assertEqual(parse_elapsed_time("100:00:00"), 360000)
