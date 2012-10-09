# -*- coding: utf-8 -*-


import django.contrib.admin as admin

from models import Tag, MockConfig, Scan

class ScanAdmin(admin.ModelAdmin):
    list_display = ("nvr", "scan_type", "base", "tag", "task", "state", 'username')


admin.site.register(MockConfig)
admin.site.register(Tag)
admin.site.register(Scan, ScanAdmin)