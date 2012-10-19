# -*- coding: utf-8 -*-


from covscanhub.scan.models import MockConfig
from django.core.exceptions import ObjectDoesNotExist


__all__ = (
    "get",
    "all",
)


def all(request):
    return list(MockConfig.objects.all().values("name", "enabled"))


def get(request, name):
    try:
        return MockConfig.objects.get(name=name).export()
    except ObjectDoesNotExist:
        return None
