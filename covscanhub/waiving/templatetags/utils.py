# -*- coding: utf-8 -*-

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.tag(name='captureas')
def do_captureas(parser, token):
    try:
        tag_name, args = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError("'captureas' node requires a \
variable name.")
    nodelist = parser.parse(('endcaptureas',))
    parser.delete_first_token()
    return CaptureasNode(nodelist, args)


class CaptureasNode(template.Node):
    def __init__(self, nodelist, varname):
        self.nodelist = nodelist
        self.varname = varname

    def render(self, context):
        output = self.nodelist.render(context)
        context[self.varname] = output
        return ''


@register.filter
def result_group_display_new(obj):
    return mark_safe(obj.display_in_result('NEW', 'waiving/waiver'))


@register.filter
def result_group_display_fixed(obj):
    return mark_safe(obj.display_in_result('FIXED', 'waiving/fixed_defects'))


@register.filter
def line_and_column(obj):
    response = ""
    if "line" in obj:
        response += str(obj['line'])
    if "column" in obj:
        response += ':' + str(obj['column'])
    return response