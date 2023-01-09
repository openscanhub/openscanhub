# -*- coding: utf-8 -*-

import random

from django.test import Client, TestCase


class BasicWebTestCase(TestCase):
    """
    GET to all basic pages
    """

    def setUp(self):
        self.client = Client()

    def test_scans_list(self):
        r = self.client.get('/waiving/')
        self.assertEqual(r.status_code, 200)

    def test_random_scans(self):
        scan_id = random.randint(20, 100)
        r = self.client.get('/waiving/%d/' % scan_id)
        self.assertTrue(r.status_code in [200, 404])

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

    def test_et_task_list(self):
        r = self.client.get('/task/et/')
        self.assertEqual(r.status_code, 200)

    def test_stats(self):
        r = self.client.get('/stats/')
        self.assertEqual(r.status_code, 200)

    def test_mockconfs_list(self):
        r = self.client.get('/scan/mock/')
        self.assertEqual(r.status_code, 200)
