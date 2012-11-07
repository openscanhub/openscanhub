# -*- coding: utf-8 -*-


import django.contrib.admin as admin

from models import Tag, MockConfig, Scan, Package


class ScanAdmin(admin.ModelAdmin):
    list_display = ("id", "nvr", "state", "scan_type", "base", "tag", "task",
                    'username', 'package')


class PackageAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "blocked")


admin.site.register(MockConfig)
admin.site.register(Tag)
admin.site.register(Package, PackageAdmin)
admin.site.register(Scan, ScanAdmin)