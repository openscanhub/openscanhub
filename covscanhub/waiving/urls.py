# -*- coding: utf-8 -*-


from __future__ import absolute_import
from django.conf.urls import url

from covscanhub.waiving.views import *


urlpatterns = [
    url(r"^$", ResultsListView.as_view(), name="waiving/list"),

    url(r"^(?P<sb_id>\d+)/(?P<result_group_id>\d+)/$",
        "covscanhub.waiving.views.waiver", name="waiving/waiver"),
    url(r"^(?P<sb_id>\d+)/(?P<result_group_id>\d+)/fixed/$",
        "covscanhub.waiving.views.fixed_defects",
        name="waiving/fixed_defects"),
    url(r"^(?P<sb_id>\d+)/(?P<result_group_id>\d+)/waived/$",
        "covscanhub.waiving.views.previously_waived",
        name="waiving/previously_waived"),

    url(r"^(?P<waiver_id>\d+)/remove$",
        "covscanhub.waiving.views.remove_waiver",
        name="waiving/waiver/remove"),

    url(r"^(?P<sb_id>\d+)/$",
        "covscanhub.waiving.views.result", name="waiving/result"),
    url(r"^(?P<package_name>.+)/(?P<release_tag>.+)/newest/$",
        "covscanhub.waiving.views.newest_result",
        name="waiving/result/newest"),
    url(r"^et/(?P<et_id>.+)/$",
        "covscanhub.waiving.views.et_latest",
        name="waiving/et_id"),
    url(r"^et_mapping/(?P<etmapping_id>\d+)/$",
        "covscanhub.waiving.views.etmapping_latest",
        name="waiving/etmapping_id"),

    #BZ stuff
    url(r"^(?P<package_id>\d+)/(?P<release_id>\d+)/newbz/$",
        "covscanhub.waiving.views.new_bz",
        name="waiving/new_bz"),
    url(r"^(?P<package_id>\d+)/(?P<release_id>\d+)/updatebz/$",
        "covscanhub.waiving.views.update_bz",
        name="waiving/update_bz"),
    ]
