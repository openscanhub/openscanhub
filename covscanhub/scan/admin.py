# -*- coding: utf-8 -*-


import django.contrib.admin as admin

from models import *

import kobo.django.forms


admin.site.register(MockConfig)
admin.site.register(Tag)
admin.site.register(Scan)
