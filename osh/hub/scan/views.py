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
        context = super().get_context_data(**kwargs)
        context['title'] = "Detail of package %s" % kwargs['object'].name
        return context
