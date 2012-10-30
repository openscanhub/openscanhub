# -*- coding: utf-8 -*-


from django.conf.urls.defaults import *


urlpatterns = patterns("",
    url(r"^$", "covscanhub.waiving.views.results_list", name="waiving/list"),
    url(r"^(?P<result_id>\d+)/(?P<checker_group_id>\d+)/$", 
        "covscanhub.waiving.views.waiver", name="waiving/waiver"),
    url(r"^(?P<result_id>\d+)/$", 
        "covscanhub.waiving.views.result", name="waiving/result"),
)