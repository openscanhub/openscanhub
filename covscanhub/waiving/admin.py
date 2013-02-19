# -*- coding: utf-8 -*-

from covscanhub.other.shortcuts import add_link_field

import django.contrib.admin as admin

from models import *


@add_link_field('scanbinding','scanbinding','scan',
                field_name='scanbinding_link',
                field_label="Binding")
class ResultAdmin(admin.ModelAdmin):
    list_display = ("id", "scanner", "scanner_version", 'date_submitted',
                    'scanbinding_link')


@add_link_field('checkergroup','checker_group',field_name='link2')
@add_link_field('result','result')
class ResultGroupAdmin(admin.ModelAdmin):
    list_display = ("id", "state_display", 'defects_count',
                    'defects_state_display', 'link', 'link2')

    def defects_state_display(self, instance):
        return DEFECT_STATES.get_value(instance.defect_type)
    defects_state_display.short_description = 'Defects state'

    def state_display(self, instance):
        return instance.get_state_display()
    state_display.short_description = 'State'


@add_link_field('resultgroup','result_group')
class DefectAdmin(admin.ModelAdmin):
    list_display = ("id", "checker", "annotation", "key_event", "link",
                    'state_display')

    def state_display(self, instance):
        return instance.get_state_display()
    state_display.short_description = 'State'


@add_link_field('resultgroup','group')
class CheckerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "link")


class CheckerGroupAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "enabled")


@add_link_field('bugzilla', 'bz', field_name="bz_link")
@add_link_field('resultgroup','result_group')
class WaiverAdmin(admin.ModelAdmin):
    list_display = ("id", "state", 'is_deleted', 'date', 'user', 'message',
                    'link', 'bz_link')


@add_link_field('package', 'package', 'scan', field_name='package_link',
                field_label="Package")
@add_link_field('systemrelease', 'release', 'scan', field_name='release_link',
                field_label="Release")
class BugzillaAdmin(admin.ModelAdmin):
    list_display = ("id", "release_link", "package_link", "number")


@add_link_field('waiver', 'waiver', field_name='waiver_link',
                field_label="Waiver")
class WaivingLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'user', 'state_display', 'waiver_link')

    def state_display(self, instance):
        return instance.get_state_display()
    state_display.short_description = 'State'


admin.site.register(Bugzilla, BugzillaAdmin)
admin.site.register(Result, ResultAdmin)
admin.site.register(Defect, DefectAdmin)
admin.site.register(Checker, CheckerAdmin)
admin.site.register(CheckerGroup, CheckerGroupAdmin)
admin.site.register(Waiver, WaiverAdmin)
admin.site.register(ResultGroup, ResultGroupAdmin)
admin.site.register(WaivingLog, WaivingLogAdmin)