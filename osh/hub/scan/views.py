# -*- coding: utf-8 -*-

from __future__ import absolute_import

from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from .models import MockConfig, Package


class MockConfigListView(ListView):
    template_name = "mock_config/list.html"
    context_object_name = "mock_config"
    title = "List mock configs"
    paginate_by = 50
    allow_empty = True

    def get_queryset(self):
        return MockConfig.objects.all()


class PackageListView(ListView):
    template_name = "scan/package_list.html"
    context_object_name = "package"
    title = "Package list"
    paginate_by = 50
    allow_empty = True

    def get_queryset(self):
        return Package.objects.all()


class PackageDetailView(DetailView):
    model = Package
    template_name = "scan/package_detail.html"
    context_object_name = "package"

    def get_context_data(self, **kwargs):
        context = super(PackageDetailView, self).get_context_data(**kwargs)
        context['title'] = "Detail of package %s" % kwargs['object'].name
        return context


# def scan_submission(request):
#    context = {}
#    if request.method == "POST":
#        form = ScanSubmissionForm(request.POST)
#        if form.is_valid():
#            options = {}
#            scan_type = form.cleaned_data['scan_type']
#            if scan_type == 'VersionDiffBuild':
#                options['base'] = form.cleaned_data['base']
#
#            options["brew_build"] = form.cleaned_data['nvr']
#            options["srpm_name"] = options["brew_build"]
#            options['scan_type'] = form.cleaned_data['scan_type']
#            mock_config = form.cleaned_data['mock']
#            options['security'] = form.cleaned_data['security_checker']
#            options['all_checker'] = form.cleaned_data['all_checker']
#            comment = form.cleaned_data['comment']
#
#            if scan_type == 'VersionDiffBuild':
#                task_id = create_user_diff_task(request, options)
#            elif scan_type == 'MockBuild':
#                task_id = diff_build(request, mock_config, comment, options)
#            elif scan_type == 'DiffBuild':
#                task_id = mock_build(request, mock_config, comment, options)
#            return HttpResponseRedirect(reverse('task/detail',
#                                                args=(task_id,)))
#        else:
#            return render_to_response("scan/new.html",
#                                      {'form': form},
#                                      context_instance=RequestContext(request))
#    else:
#        context['form'] = ScanSubmissionForm()
#    return render_to_response("scan/new.html",
#                              context,
#                              context_instance=RequestContext(request))
