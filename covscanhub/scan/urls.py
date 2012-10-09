# -*- coding: utf-8 -*-


from django.conf.urls.defaults import *


urlpatterns = patterns("",
    url(r"^$", "covscanhub.scan.views.mock_config_list", name="mock_config/index"),
    url(r"^$", "covscanhub.scan.views.errata_scan_list", name="errata/index"),
)
