# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

import pathlib

from django.core.management import call_command
from django.test import Client, TestCase


class BasicWebTestCase(TestCase):
    """
    GET to all basic pages
    """

    def setUp(self):
        fixture_path = pathlib.Path(__file__).parent.absolute() / 'fixtures/initial_test_data.json'
        call_command('loaddata', fixture_path, verbosity=0)
        self.client = Client()

    def test_scans_list(self):
        r = self.client.get('/waiving/')
        self.assertEqual(r.status_code, 200)

    def test_existent_scan(self):
        r = self.client.get('/waiving/1/')
        self.assertEqual(r.status_code, 200)

    def test_non_existent_scan(self):
        r = self.client.get('/waiving/2/')
        self.assertEqual(r.status_code, 404)

    def test_home(self):
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)

    def test_task_list(self):
        r = self.client.get('/task/')
        self.assertEqual(r.status_code, 200)

    def test_running_task_list(self):
        r = self.client.get('/task/running/')
        self.assertEqual(r.status_code, 200)

    def test_finished_task_list(self):
        r = self.client.get('/task/finished/')
        self.assertEqual(r.status_code, 200)

    def test_stats(self):
        r = self.client.get('/stats/')
        self.assertEqual(r.status_code, 200)

    def test_mockconfs_list(self):
        r = self.client.get('/scan/mock/')
        self.assertEqual(r.status_code, 200)
