# -*- coding: utf-8 -*-


from django.conf.urls import *

from covscanhub.scan.views import *


urlpatterns = patterns("",
    url(r"^mock", MockConfigListView.as_view(),
        name="mock_config/index"),

    #url(r"^(?P<id>\d+)/$", "covscanhub.scan.views.scan_detail",
    #    name="scan/detail"),
    #url(r"^new/$", "covscanhub.scan.views.scan_submission",
    #    name="scan/new"),

    url(r"^packages/$", PackageListView.as_view(),
        name="package/list"),
    url(r"^packages/(?P<id>\d+)/detail/$",
        PackageDetailView.as_view(),
        name="package/detail"),
)
