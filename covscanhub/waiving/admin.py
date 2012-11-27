# -*- coding: utf-8 -*-

from covscanhub.other.shortcuts import add_link_field

import django.contrib.admin as admin

from models import Result, Defect, Checker, CheckerGroup, Waiver,\
    ResultGroup


@add_link_field('scan','scan', 'scan')
class ResultAdmin(admin.ModelAdmin):
    list_display = ("id", "scanner", "scanner_version", "link")


@add_link_field('checkergroup','checker_group',field_name='link2')
@add_link_field('result','result')
class ResultGroupAdmin(admin.ModelAdmin):
    list_display = ("id", "state_display", 'new_defects', 'fixed_defects', 'link', 'link2')
    
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


@add_link_field('resultgroup','result_group')
class WaiverAdmin(admin.ModelAdmin):
    list_display = ("id", "state", 'date', 'user', 'message', 'link')


admin.site.register(Result, ResultAdmin)
admin.site.register(Defect, DefectAdmin)
admin.site.register(Checker, CheckerAdmin)
admin.site.register(CheckerGroup, CheckerGroupAdmin)
admin.site.register(Waiver, WaiverAdmin)
admin.site.register(ResultGroup, ResultGroupAdmin)