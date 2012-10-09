# -*- coding: utf-8 -*-


import django.contrib.admin as admin

from models import Result, Event, Defect

class ResultAdmin(admin.ModelAdmin):
    list_display = ("scanner", "scanner_version", "scan")
class EventAdmin(admin.ModelAdmin):
    list_display = ("file_name", "line", "event", "message", "defect")
class DefectAdmin(admin.ModelAdmin):
    list_display = ("checker", "annotation", "key_event", "result")


admin.site.register(Result, ResultAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Defect, DefectAdmin)