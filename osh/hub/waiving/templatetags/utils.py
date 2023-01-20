# -*- coding: utf-8 -*-

from datetime import date, datetime

from django import template
from django.template import defaultfilters
from django.utils.safestring import mark_safe
from django.utils.translation import pgettext, ungettext, ugettext as _
#from django.utils.timezone import is_aware, utc

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


@register.filter
def naturaltime(value):
    """
    taken from django:master

    For date and time values shows how many seconds, minutes or hours ago
    compared to current timestamp returns representing string.

    This filter doesn't require expects_localtime=True because it deals properly
    with both naive and aware datetimes. Therefore avoid the cost of conversion.
    """
    if not isinstance(value, date):  # datetime is a subclass of date
        return value

    now = datetime.now()  # (utc if is_aware(value) else None)
    if value < now:
        delta = now - value
        if delta.days != 0:
            return pgettext(
                'naturaltime', '%(delta)s ago'
            ) % {'delta': defaultfilters.timesince(value, now)}
        elif delta.seconds == 0:
            return _('now')
        elif delta.seconds < 60:
            return ungettext(
                'a second ago', '%(count)s seconds ago', delta.seconds
            ) % {'count': delta.seconds}
        elif delta.seconds // 60 < 60:
            count = delta.seconds // 60
            return ungettext(
                'a minute ago', '%(count)s minutes ago', count
            ) % {'count': count}
        else:
            count = delta.seconds // 60 // 60
            return ungettext(
                'an hour ago', '%(count)s hours ago', count
            ) % {'count': count}
    else:
        delta = value - now
        if delta.days != 0:
            return pgettext(
                'naturaltime', '%(delta)s from now'
            ) % {'delta': defaultfilters.timeuntil(value, now)}
        elif delta.seconds == 0:
            return _('now')
        elif delta.seconds < 60:
            return ungettext(
                'a second from now', '%(count)s seconds from now',
                delta.seconds
            ) % {'count': delta.seconds}
        elif delta.seconds // 60 < 60:
            count = delta.seconds // 60
            return ungettext(
                'a minute from now', '%(count)s minutes from now', count
            ) % {'count': count}
        else:
            count = delta.seconds // 60 // 60
            return ungettext(
                'an hour from now', '%(count)s hours from now', count
            ) % {'count': count}
