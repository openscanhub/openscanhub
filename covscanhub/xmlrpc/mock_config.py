# -*- coding: utf-8 -*-


from covscanhub.scan.models import MockConfig


__all__ = (
    "get",
    "all",
)


def all(request):
    return list(MockConfig.objects.all().values("name", "enabled"))


def get(request, name):
    return MockConfig.objects.get(name=name).export()
