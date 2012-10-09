# -*- coding: utf-8 -*-


import django.contrib.admin as admin

from models import Result, Event, Defect


admin.site.register(Result)
admin.site.register(Event)
admin.site.register(Defect)