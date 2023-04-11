from django.conf.urls import url

from osh.hub.waiving.views import (ResultsListView, et_latest,
                                   etmapping_latest, fixed_defects, new_bz,
                                   newest_result, previously_waived,
                                   remove_waiver, result, update_bz, waiver)

urlpatterns = [
    url(r"^$", ResultsListView.as_view(), name="waiving/list"),

    url(r"^(?P<sb_id>\d+)/(?P<result_group_id>\d+)/$",
        waiver, name="waiving/waiver"),
    url(r"^(?P<sb_id>\d+)/(?P<result_group_id>\d+)/fixed/$",
        fixed_defects,
        name="waiving/fixed_defects"),
    url(r"^(?P<sb_id>\d+)/(?P<result_group_id>\d+)/waived/$",
        previously_waived,
        name="waiving/previously_waived"),

    url(r"^(?P<waiver_id>\d+)/remove$",
        remove_waiver,
        name="waiving/waiver/remove"),

    url(r"^(?P<sb_id>\d+)/$",
        result, name="waiving/result"),
    url(r"^(?P<package_name>.+)/(?P<release_tag>.+)/newest/$",
        newest_result,
        name="waiving/result/newest"),
    url(r"^et/(?P<et_id>.+)/$",
        et_latest,
        name="waiving/et_id"),
    url(r"^et_mapping/(?P<etmapping_id>\d+)/$",
        etmapping_latest,
        name="waiving/etmapping_id"),

    # BZ stuff
    url(r"^(?P<package_id>\d+)/(?P<release_id>\d+)/newbz/$",
        new_bz,
        name="waiving/new_bz"),
    url(r"^(?P<package_id>\d+)/(?P<release_id>\d+)/updatebz/$",
        update_bz,
        name="waiving/update_bz"),
]
