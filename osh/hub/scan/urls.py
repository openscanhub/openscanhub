# -*- coding: utf-8 -*-


from django.conf.urls import *

from osh.hub.scan.views import *


urlpatterns = [
    url(r"^mock", MockConfigListView.as_view(),
        name="mock_config/index"),

    #url(r"^(?P<id>\d+)/$", "osh.hub.scan.views.scan_detail",
    #    name="scan/detail"),
    #url(r"^new/$", "osh.hub.scan.views.scan_submission",
    #    name="scan/new"),

    url(r"^packages/$", PackageListView.as_view(),
        name="package/list"),
    url(r"^packages/(?P<pk>\d+)/detail/$",
        PackageDetailView.as_view(),
        name="package/detail"),
    ]
