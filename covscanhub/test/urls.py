# -*- coding: utf-8 -*-

from django.conf.urls.defaults import patterns, url


urlpatterns = patterns("",
    url(r"^notify/(<scan_id>\d+)/$", "covscanhub.test.views.notify",
        name="test/notify"),
)
