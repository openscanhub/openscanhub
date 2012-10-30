# -*- coding: utf-8 -*-

from django import forms
from covscanhub.waiving.models import WAIVER_TYPES


class WaiverForm(forms.Form):
    waiver_type = forms.ChoiceField(choices=((w, \
        WAIVER_TYPES.get_item_help_text(w)) for w in WAIVER_TYPES))
    message = forms.CharField(widget=forms.widgets.Textarea(), 
                              initial="This defect is not a bug because...")        