# -*- coding: utf-8 -*-


import django.contrib.admin as admin

from models import Result, Event, Defect, Checker, CheckerGroup, Waiver


class ResultAdmin(admin.ModelAdmin):
    list_display = ("scanner", "scanner_version", "scan")


class EventAdmin(admin.ModelAdmin):
    list_display = ("file_name", "line", "event", "message", "defect")


class DefectAdmin(admin.ModelAdmin):
    list_display = ("checker", "annotation", "key_event", "result_group",
                    'get_state_display')


class CheckerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "group")


class CheckerGroupAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "enabled")


class WaiverAdmin(admin.ModelAdmin):
    list_display = ("id", "state", 'date', 'user', 'message', 'result_group')

admin.site.register(Result, ResultAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Defect, DefectAdmin)
admin.site.register(Checker, CheckerAdmin)
admin.site.register(CheckerGroup, CheckerGroupAdmin)
admin.site.register(Waiver, WaiverAdmin)