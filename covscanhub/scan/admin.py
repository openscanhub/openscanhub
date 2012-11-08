# -*- coding: utf-8 -*-


from covscanhub.other.shortcuts import add_link_field

import django.contrib.admin as admin

from models import Tag, MockConfig, Scan, Package


@add_link_field('task', 'task', 'hub')
class ScanAdmin(admin.ModelAdmin):
    list_display = ("id", "nvr", "state", "scan_type", "base", "tag",
                    'username', 'package', 'link')


class PackageAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "blocked")


admin.site.register(MockConfig)
admin.site.register(Tag)
admin.site.register(Package, PackageAdmin)
admin.site.register(Scan, ScanAdmin)