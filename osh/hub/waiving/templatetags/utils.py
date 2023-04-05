from django import template

register = template.Library()


@register.filter
def line_and_column(obj):
    response = ""
    if "line" in obj:
        response += str(obj['line'])
    if "column" in obj:
        response += ':' + str(obj['column'])
    return response
