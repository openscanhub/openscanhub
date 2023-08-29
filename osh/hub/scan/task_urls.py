# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

"""custom task urls"""

from django.urls import path
from kobo.hub.urls.task import urlpatterns
from kobo.hub.views import TaskListView

urlpatterns.append(
    path("et/",
         TaskListView.as_view(title="Errata Tool Tasks"),
         # FIXME: `kobo` ignores the kwargs argumentdue to a bug
         kwargs={'method': "ErrataDiffBuild"},
         name="task/et")
)
