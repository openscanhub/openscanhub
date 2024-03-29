# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

from django.core.exceptions import ObjectDoesNotExist

from osh.hub.scan.models import MockConfig

# DO NOT REMOVE!  The __all__ list contains all publicly exported XML-RPC
# methods from this module.
__all__ = [
    "all",
    "get",
]


def all(request):
    """
    Return list of mockconfigs:
        [("mock_config_name", "is_enabled?"), ...]
    """
    return list(MockConfig.objects.all().values("name", "enabled"))


def get(request, name):
    """
    get(name) -> { "name": <name>, "enable": <True|False> }

    Return info about mockconfig specified by its name.
    """
    try:
        return MockConfig.objects.get(name=name).export()
    except ObjectDoesNotExist:
        return None
