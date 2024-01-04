#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

import os
import platform

os.environ['DJANGO_SETTINGS_MODULE'] = 'osh.hub.settings'


def main():
    from kobo.hub.models import Arch, Worker  # noqa: E402

    # get/create the native arch
    machine = platform.uname().machine
    arch = Arch.objects.get_or_create(name=machine, pretty_name=machine)[0]

    # assign the arch to worker
    worker = Worker.objects.get(name='localhost')
    worker.arches.add(arch)
    worker.save()


if __name__ == '__main__':
    import django
    django.setup()

    main()
