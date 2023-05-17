# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

from django.urls import path

from osh.hub.waiving.views import (ResultsListView, et_latest,
                                   etmapping_latest, fixed_defects, new_bz,
                                   new_jira, newest_result, previously_waived,
                                   remove_waiver, result, update_bz,
                                   update_jira, waiver)

urlpatterns = [
    path("", ResultsListView.as_view(), name="waiving/list"),

    path("<int:sb_id>/<int:result_group_id>/",
         waiver, name="waiving/waiver"),
    path("<int:sb_id>/<int:result_group_id>/fixed/",
         fixed_defects,
         name="waiving/fixed_defects"),
    path("<int:sb_id>/<int:result_group_id>/waived/",
         previously_waived,
         name="waiving/previously_waived"),

    path("<int:waiver_id>/remove",
         remove_waiver,
         name="waiving/waiver/remove"),

    path("<int:sb_id>/",
         result, name="waiving/result"),
    path("<str:package_name>/<str:release_tag>/newest/",
         newest_result,
         name="waiving/result/newest"),
    path("et/<str:et_id>/",
         et_latest,
         name="waiving/et_id"),
    path("et_mapping/<int:etmapping_id>/",
         etmapping_latest,
         name="waiving/etmapping_id"),

    # BZ stuff
    path("<int:package_id>/<int:release_id>/newbz/",
         new_bz,
         name="waiving/new_bz"),
    path("<int:package_id>/<int:release_id>/updatebz/",
         update_bz,
         name="waiving/update_bz"),

    # Jira stuff
    path("<int:package_id>/<int:release_id>/newjira/",
         new_jira,
         name="waiving/new_jira"),
    path("<int:package_id>/<int:release_id>/updatejira/",
         update_jira,
         name="waiving/update_jira"),
]
