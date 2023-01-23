#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

from __future__ import print_function

import datetime
import os
import re
import sys
from optparse import OptionParser
from pathlib import Path

import six
import six.moves.cPickle as pickle
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from kobo.hub.models import Arch, Channel
from six.moves import range

from osh.common.constants import DEFAULT_CHECKER_GROUP
from osh.hub.scan.models import (AppSettings, MockConfig, ReleaseMapping,
                                 SystemRelease, Tag)
from osh.hub.stats.models import StatType
from osh.hub.stats.service import get_mapping
from osh.hub.waiving.models import Checker, CheckerGroup

PROJECT_DIR = Path(__file__).parents[2]

if PROJECT_DIR not in sys.path:
    sys.path.append(PROJECT_DIR)


os.environ['DJANGO_SETTINGS_MODULE'] = 'osh.hub.settings'


def set_options():
    parser = OptionParser()
    parser.add_option("-H", "--hub", help="configure hub",
                      action="store_true", dest="hub", default=False)
    parser.add_option("-c", "--checkergroups",
                      action="store_true", dest="cgroups", default=False,
                      help="fill database with checker groups specified in \
'file checker_groups.txt'")
    parser.add_option("-s", "--statistics",
                      action="store_true", dest="stats", default=False,
                      help="write statistics definition into database",)
    parser.add_option("-m", "--mock", help="configure mock config",
                      action="store_true", dest="mock", default=False)
    parser.add_option("-r", "--release", help="configure release hierarchy",
                      action="store_true", dest="release", default=False)
    parser.add_option("-S", "--default-settings",
                      help="set hub's default settings",
                      action="store_true", dest="settings", default=False)
    (options, args) = parser.parse_args()

    return parser, options, args


def set_checker_groups():
    chgrp_file = open(os.path.join(settings.PROJECT_DIR,
                                   'scripts',
                                   'checker_groups.txt'), 'r')

    lines = chgrp_file.readlines()

    checker_pattern = re.compile(r'\d+\s+(?P<checker>[\w\.]+)')
    separator_pattern = re.compile(r'\-+')
    ch_grp_pattern = re.compile(r'(?P<group>[\w\+ ]+)')

    data = {}

    ch_grp = None

    with open(os.path.join(settings.PROJECT_DIR,
                           'scripts',
                           'checker_groups.txt'), 'r') as chgrp_file:
        lines = chgrp_file.readlines()
    for line in lines:
        if line == '\n':
            continue
        match = re.match(checker_pattern, line)
        if match:
            if ch_grp is None:
                raise RuntimeError(('Detected checker before any checker'
                                    'group, invalid file.'))
            else:
                data[ch_grp].append(match.group('checker'))
        else:
            match = re.match(ch_grp_pattern, line)
            if match:
                ch_grp = match.group('group')
                data[ch_grp] = []
            else:
                match = re.match(separator_pattern, line)
                if not match:
                    raise RuntimeError(('Line wasn\'t matched. You have'
                                        'provided an invalid file.'))
    CheckerGroup.objects.get_or_create(name=DEFAULT_CHECKER_GROUP)
    for group, checkers in six.iteritems(data):
        ch, created = CheckerGroup.objects.get_or_create(name=group,
                                                         enabled=True)
        for checker in checkers:
            che, created = Checker.objects.get_or_create(name=checker,
                                                         group=ch)


def configure_hub():
    c, _ = Channel.objects.get_or_create(name="default")
    c.save()

    a, _ = Arch.objects.get_or_create(name="noarch", pretty_name="noarch")
    a.save()

    print("Don't forget to set up worker!\nYou have to use hostname as a name \
for the worker.\n")


def download_mock_configs():
    # TODO: download configs (hardcore magic to find out latest build tag for
    #  product -- (rhel|RHEL)-(?P<x>\d+).(?P<y>\d+)(\.[zZ]){0,1}-build
    x_list = [5, 6, 7]
    for x in x_list:
        m, _ = MockConfig.objects.get_or_create(name="rhel-%d-x86_64")
        m.enabled = False
        m.save()


def release_tree():
    # release parsing
    r = ReleaseMapping()
    r.template = "RHEL-%s.%s"
    r.priority = 1
    r.release_tag = r"^RHEL-(\d+)\.(\d+)\.0$"
    r.save()

    r = ReleaseMapping()
    r.template = "RHEL-%s.%s"
    r.priority = 2
    r.release_tag = r"^FAST(\d+)\.(\d+)$"
    r.save()

    x_list = [5, 6, 7]
    y_list = range(12)

    # tags and system releases
    for x in x_list:
        previous = None
        mock, created = MockConfig.objects.get_or_create(name="rhel-%d-x86_64" % x)
        product = "Red Hat Enterprise Linux %d" % x
        for y in y_list:
            sr = SystemRelease()
            sr.active = False
            sr.parent = previous
            sr.tag = 'rhel-%d.%d' % (x, y)
            sr.product = product
            sr.release = y
            sr.save()

            previous = sr

            tag = Tag()
            tag.name = "RHEL-%d.%d" % (x, y)
            tag.mock = mock
            tag.release = sr
            tag.save()


def db_set_default(key, value):
    s, created = AppSettings.objects.get_or_create(key=key)
    if created:
        s.value = value
        s.save()


def set_default_settings():
    """If object exists in DB, DO NOT TOUCH IT"""
    db_set_default("SEND_MAIL", "N")
    db_set_default("SEND_BUS_MESSAGE", "N")
    db_set_default("CHECK_USER_CAN_SUBMIT_SCAN", "N")

    # run is overdue -- default
    db_set_default("WAIVER_IS_OVERDUE",
                   pickle.dumps(datetime.timedelta(days=-7)))

    db_set_default("ACTUAL_SCANNER",
                   pickle.dumps(('csmock', '3.3.4')))

    # release specific, structure: tuple('short_tag', timedelta)
    bindings = (
        ('rhel-6.4', datetime.timedelta(days=-13)),
    )
    # structure: tuple(model_object, 'short_tag', timedelta
    overdue_relspec = (
        (o, pickle.loads(str(o.value))[0], pickle.loads(str(o.value))[1])
        for o in AppSettings.objects.filter(key="WAIVER_IS_OVERDUE_RELSPEC")
    )
    # if it exists, update it, if not, create it
    for b in bindings:
        updated = False
        for spec in overdue_relspec:
            if b[0] == spec[1]:
                if b[1] != spec[2]:
                    spec[0].value = pickle.dumps(b)
                    spec[0].save()
                updated = True
                continue
        if not updated:
            AppSettings.objects.get_or_create(key="WAIVER_IS_OVERDUE_RELSPEC",
                                              value=pickle.dumps(b))


def set_statistics():
    # function = (key, description)
    for desc in six.itervalues(get_mapping()):
        try:
            s = StatType.objects.get(key=desc[0])
        except ObjectDoesNotExist:
            # tag, short_comment, comment, group, order
            s, created = StatType.objects.get_or_create(
                key=desc[0], short_comment=desc[1], comment=desc[2],
                group=desc[3], order=desc[4], is_release_specific=(
                    'RELEASE' in desc[0]))
        else:
            StatType.objects.filter(id=s.id).update(
                key=desc[0], short_comment=desc[1], comment=desc[2],
                group=desc[3], order=desc[4], is_release_specific=(
                    'RELEASE' in desc[0]))


def main():
    parser, options, args = set_options()
    print('You are running covscanhub configuration script.\nThis may take a \
couple of seconds, please be patient.')
    if options.hub:
        configure_hub()
    if options.cgroups:
        set_checker_groups()
    if options.stats:
        set_statistics()
    if options.release:
        release_tree()
    if options.settings:
        set_default_settings()
    if options.mock:
        download_mock_configs()


if __name__ == '__main__':
    main()
    sys.exit(0)
