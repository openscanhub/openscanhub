# -*- coding: utf-8 -*-


from django.conf.urls.defaults import patterns, url


urlpatterns = patterns("",
    url(r"^$", "covscanhub.waiving.views.results_list", name="waiving/list"),

    url(r"^(?P<result_id>\d+)/(?P<result_group_id>\d+)/$",
        "covscanhub.waiving.views.waiver", name="waiving/waiver"),

    url(r"^(?P<result_id>\d+)/(?P<result_group_id>\d+)/fixed/$",
        "covscanhub.waiving.views.fixed_defects",
        name="waiving/fixed_defects"),

    url(r"^(?P<result_id>\d+)/$",
        "covscanhub.waiving.views.result", name="waiving/result"),
    url(r"^(?P<package_name>.+)/(?P<release_tag>.+)/newest/$",
        "covscanhub.waiving.views.newest_result",
        name="waiving/result/newest"),
    url(r"^(?P<package_id>\d+)/(?P<release_id>\d+)/newbz/$",
        "covscanhub.waiving.views.new_bz",
        name="waiving/new_bz"),
    url(r"^(?P<package_id>\d+)/(?P<release_id>\d+)/updatebz/$",
        "covscanhub.waiving.views.update_bz",
        name="waiving/update_bz"),
)