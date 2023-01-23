# -*- coding: utf-8 -*-


from django.core.exceptions import ObjectDoesNotExist

from osh.hub.scan.models import MockConfig

__all__ = (
    "get",
    "all",
)


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
