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
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings


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
    for group, checkers in data.iteritems():
        try:
            ch = CheckerGroup.objects.get(name=group)
        except ObjectDoesNotExist:
            ch = CheckerGroup()
            ch.name = group
            ch.enabled = True
            ch.save()
        for checker in checkers:
            che, created = Checker.objects.get_or_create(name=checker)
            che.group = ch
            che.save()


def configure_hub():
    c = Channel()
    c.name = "Default"
    c.save()

    a = Arch()
    a.name = 'noarch'
    a.pretty_name = 'noarch'
    a.save()

    print "Don't forget to set up worker!\nYou have to use hostname as a name \
for the worker.\n"
    print "Don't forget to set up mock configs and tags!"


def main():
    print 'You are running covscanhub configure script.\nThis may take a \
of couple of seconds, please be patient.'
    #configure_hub()
    set_checker_groups()

if __name__ == '__main__':
    main()
    sys.exit(0)