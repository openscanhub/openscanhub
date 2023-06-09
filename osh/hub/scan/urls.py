# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

from django.urls import path

from osh.hub.scan.views import (MockConfigListView, PackageDetailView,
                                PackageListView, scan_submission)

urlpatterns = [
    path("mock/", MockConfigListView.as_view(),
         name="mock_config/index"),

    # path("<int:id>/", "osh.hub.scan.views.scan_detail",
    #      name="scan/detail"),
    path("new/", scan_submission,
         name="scan/new"),

    path("packages/", PackageListView.as_view(),
         name="package/list"),
    path("packages/<int:pk>/detail/",
         PackageDetailView.as_view(),
         name="package/detail"),
]
