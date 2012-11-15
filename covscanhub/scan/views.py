# -*- coding: utf-8 -*-


from django.views.generic.list_detail import object_detail

from kobo.django.views.generic import object_list

from models import MockConfig, Scan, Package, SCAN_TYPES


def mock_config_list(request):

    args = {
        "queryset": MockConfig.objects.all(),
        "allow_empty": True,
        "paginate_by": 50,
        "template_name": "mock_config/list.html",
        "template_object_name": "mock_config",
        "extra_context": {
            "title": "List mock configs",
        }
    }

    return object_list(request, **args)


def scan_list(request):

    args = {
        "queryset": Scan.objects.all().exclude(base__isnull=True),
#        "queryset": Scan.objects.exclude(base__isnull=True).
#            exclude(base__exact=''),
        "allow_empty": True,
        "paginate_by": 50,
        "template_name": "scan/list.html",
        "template_object_name": "scan",
        "extra_context": {
            "title": "List errata scans",
        }
    }

    return object_list(request, **args)


def scan_detail(request, id):

    args = {
        "queryset": Scan.objects.select_related(),
        "object_id": id,
        "template_object_name": "scan",
        "template_name": "scan/detail.html",
        "extra_context": {
            "title": "Scan detail",
        },
    }

    return object_detail(request, **args)


def package_list(request):
    args = {
        "queryset": Package.objects.all(),
        "allow_empty": True,
        "paginate_by": 50,
        "template_name": "scan/package_list.html",
        "template_object_name": "package",
        "extra_context": {
            "title": "Package list",
        }
    }

    return object_list(request, **args)


def package_detail(request, id):
    args = {
        "queryset": Package.objects.select_related(),
        "object_id": id,
        "template_name": "scan/package_detail.html",
        "template_object_name": "package",
        "extra_context": {
            "title": "Detail of package %s" % Package.objects.get(id=id).name,
        }
    }

    return object_detail(request, **args)
