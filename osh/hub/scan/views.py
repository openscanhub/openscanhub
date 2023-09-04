# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic.detail import DetailView
from kobo.django.views.generic import ExtraListView, SearchView
from kobo.django.xmlrpc.decorators import login_required

from osh.hub.osh_xmlrpc.scan import (create_user_diff_task, diff_build,
                                     mock_build)
from osh.hub.scan.forms import PackageSearchForm, ScanSubmissionForm

from .models import MockConfig, Package


class MockConfigListView(ExtraListView):
    template_name = "mock_config/list.html"
    context_object_name = "mock_config"
    title = "Mock config list"
    paginate_by = 50
    allow_empty = True

    def get_queryset(self):
        return MockConfig.objects.all()


class PackageListView(SearchView):
    template_name = "scan/package_list.html"
    form_class = PackageSearchForm
    context_object_name = "package"
    title = "Package list"
    paginate_by = 50
    allow_empty = True


class PackageDetailView(DetailView):
    model = Package
    template_name = "scan/package_detail.html"
    context_object_name = "package"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Detail of package %s" % kwargs['object'].name
        return context


@login_required
def scan_submission(request):
    title = "Create new scan"

    if request.method != "POST":
        return render(request, "scan/new.html", {'form': ScanSubmissionForm(), 'title': title})

    form = ScanSubmissionForm(request.POST)
    if not form.is_valid():
        return render(request, "scan/new.html", {'form': form, 'title': title})

    # XXX: only for compatibility with old API
    mock_config = form.cleaned_data['mock']
    comment = form.cleaned_data['comment']

    options = {
        "brew_build": form.cleaned_data['nvr'],
        "comment": comment,
        "mock_config": mock_config,
        "scan_type": form.cleaned_data['scan_type'],
    }

    scan_type = form.cleaned_data['scan_type']
    if scan_type == 'VersionDiffBuild':
        options['base_brew_build'] = form.cleaned_data['base']
        task_id = create_user_diff_task(request, options, {})
    elif scan_type == 'MockBuild':
        task_id = mock_build(request, mock_config, comment, options)
    elif scan_type == 'DiffBuild':
        task_id = diff_build(request, mock_config, comment, options)
    else:
        raise RuntimeError("Unknown scan type: " + scan_type)

    return HttpResponseRedirect(reverse('task/detail', args=(task_id,)))
