#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

import sys
import os
import re
import inspect

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname
    (os.path.abspath(__file__))))   

if PROJECT_DIR not in sys.path:
    print '%s is not on sys.path' % PROJECT_DIR 
    sys.path.append(PROJECT_DIR)

os.environ['DJANGO_SETTINGS_MODULE'] = 'covscanhub.settings'

from kobo.hub.models import Arch, Channel

from covscanhub.waiving.models import Checker, CheckerGroup
from covscanhub.stats.models import StatType
from covscanhub.stats.service import get_mapping
from covscanhub.other.constants import DEFAULT_CHECKER_GROUP

from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from optparse import OptionParser


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
    
    (options, args) = parser.parse_args()
    
    return parser, options, args


def set_checker_groups():
    chgrp_file = open('checker_groups.txt', 'r')

    lines = chgrp_file.readlines()

    checker_pattern = re.compile('\d+\s+(?P<checker>[\w\.]+)')
    separator_pattern = re.compile('\-+')
    ch_grp_pattern = re.compile('(?P<group>[\w\+ ]+)')

    data = {}

    ch_grp = None

    for line in lines:
        if line == '\n':
            continue
        match = re.match(checker_pattern, line)
        if match:
            if ch_grp is None:
                raise RuntimeError('Detected checker before any checker group\
, invalid file.')
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
                    raise RuntimeError("Line wasn't matched. You have \
provided invalid file.")
    chgrp_file.close()
    CheckerGroup.objects.get_or_create(name=DEFAULT_CHECKER_GROUP)
    for group, checkers in data.iteritems():
        ch, created = CheckerGroup.objects.get_or_create(name=group,
                                                         enabled=True)
        for checker in checkers:
            che, created = Checker.objects.get_or_create(name=checker,
                                                         group=ch)


def configure_hub():
    c = Channel()
    c.name = "default"
    c.save()

    a = Arch()
    a.name = 'noarch'
    a.pretty_name = 'noarch'
    a.save()

    print "Don't forget to set up worker!\nYou have to use hostname as a name \
for the worker.\n"
    print "Don't forget to set up mock configs and tags!"


def set_statistics():
    # function = (key, description)
    for desc in get_mapping().itervalues():
        #tag, short_comment, comment, group, order
        s, created = StatType.objects.get_or_create(
            key=desc[0], short_comment=desc[1], comment=desc[2],
            group=desc[3], order=desc[4], is_release_specific=(
                'RELEASE' in desc[0]))
        if created:
            s.save()


def main():
    parser, options, args = set_options()
    print 'You are running covscanhub configuration script.\nThis may take a \
couple of seconds, please be patient.'
    if options.hub:
        configure_hub()
    elif options.cgroups:
        set_checker_groups()
    elif options.stats:
        set_statistics()

if __name__ == '__main__':
    main()
    sys.exit(0)
    