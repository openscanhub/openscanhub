# -*- coding: utf-8 -*-

import datetime
import os
import random

from covscanhub.other.test_enviroment import *
from covscanhub.scripts.db import set_checker_groups
from covscanhub.scan.models import *
from covscanhub.waiving.models import *
from covscanhub.waiving.service import *
from covscanhub.cs_xmlrpc.errata import create_errata_diff_scan

from unittest import TestCase
from django.test import Client
from django.conf import settings
import json
from django.db.models import Q

from kobo.hub.models import Task


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


class AssetsTestCase(TestCase):
    """
    GET to all static content
    """

    def setUp(self):
        self.client = Client()

    def test_css(self):
        self.assertTrue(self.client.get('/static/css/redhat.css').status_code is not 404)
        self.assertTrue(self.client.get('/static/kobo/css/screen.css').status_code is not 404)

    def test_js(self):
        self.assertTrue(self.client.get('/static/js/jquery-1.8.3.min.js').status_code is not 404)
