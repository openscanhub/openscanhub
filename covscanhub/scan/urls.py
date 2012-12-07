# -*- coding: utf-8 -*-


from django.conf.urls.defaults import *


urlpatterns = patterns("",
    url(r"^mock", "covscanhub.scan.views.mock_config_list",
        name="mock_config/index"),

    url(r"^$", "covscanhub.scan.views.scan_list", name="scan/list"),
    url(r"^(?P<id>\d+)/$", "covscanhub.scan.views.scan_detail",
        name="scan/detail"),
    url(r"^new/$", "covscanhub.scan.views.scan_submission",
        name="scan/new"),

    url(r"^packages/$", "covscanhub.scan.views.package_list",
        name="package/list"),
    url(r"^packages/(?P<id>\d+)/detail/$",
        "covscanhub.scan.views.package_detail",
        name="package/detail"),
)