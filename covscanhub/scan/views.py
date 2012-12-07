# -*- coding: utf-8 -*-


from django.views.generic.list_detail import object_detail
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from kobo.django.views.generic import object_list

from models import MockConfig, Scan, Package
from forms import ScanSubmissionForm
from covscanhub.xmlrpc.scan import *


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
        "queryset": Scan.objects.exclude(base__isnull=True).\
            order_by('-date_submitted'),
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


def scan_submission(request):
    context = {}
    if request.method == "POST":
        form = ScanSubmissionForm(request.POST)
        if form.is_valid():
            options = {}
            scan_type = form.cleaned_data['scan_type']
            if scan_type == 'VersionDiffBuild':
                options['base'] = form.cleaned_data['base']

            options["brew_build"] = form.cleaned_data['nvr']
            options["srpm_name"] = options["brew_build"]
            options['scan_type'] = form.cleaned_data['scan_type']
            mock_config = form.cleaned_data['mock']
            options['security'] = form.cleaned_data['security_checker']
            options['all_checker'] = form.cleaned_data['all_checker']
            comment = form.cleaned_data['comment']

            if scan_type == 'VersionDiffBuild':
                task_id = create_user_diff_task(request, options)
            elif scan_type == 'MockBuild':
                task_id = diff_build(request, mock_config, comment, options)
            elif scan_type == 'DiffBuild':
                task_id = mock_build(request, mock_config, comment, options)
            return HttpResponseRedirect(reverse('task/detail',
                                                args=(task_id,)))
        else:
            return render_to_response("scan/new.html",
                                      {'form': form},
                                      context_instance=RequestContext(request))
    else:
        context['form'] = ScanSubmissionForm()
    return render_to_response("scan/new.html",
                              context,
                              context_instance=RequestContext(request))
