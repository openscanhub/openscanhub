# -*- coding: utf-8 -*-

import kobo.django.upload.views
import kobo.django.xmlrpc.views
from django.conf.urls import url

urlpatterns = [
    # customize the index XML-RPC page if needed:
    # url(r"^$", "django.views.generic.simple.direct_to_template", kwargs={"template": "xmlrpc_help.html"}, name="help/xmlrpc"),
    url(r"^upload/", kobo.django.upload.views.file_upload),
    url(r"^client/", kobo.django.xmlrpc.views.client_handler,
        name="help/xmlrpc/client"),
    url(r"^worker/", kobo.django.xmlrpc.views.worker_handler,
        name="help/xmlrpc/worker"),
    url(r"^kerbauth/", kobo.django.xmlrpc.views.kerbauth_handler,
        name="help/xmlrpc/kerbauth"),
]
