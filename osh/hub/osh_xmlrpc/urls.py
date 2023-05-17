# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

import kobo.django.upload.views
import kobo.django.xmlrpc.views
from django.urls import path

urlpatterns = [
    # customize the index XML-RPC page if needed:
    # path("/", "django.views.generic.simple.direct_to_template", kwargs={"template": "xmlrpc_help.html"}, name="help/xmlrpc"),
    path("upload/", kobo.django.upload.views.file_upload),
    path("client/", kobo.django.xmlrpc.views.client_handler,
         name="help/xmlrpc/client"),
    path("worker/", kobo.django.xmlrpc.views.worker_handler,
         name="help/xmlrpc/worker"),
    path("kerbauth/", kobo.django.xmlrpc.views.kerbauth_handler,
         name="help/xmlrpc/kerbauth"),
]
