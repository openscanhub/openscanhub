# -*- coding: utf-8 -*-

from django import forms
from django.db.models import Q

from covscanhub.waiving.models import WAIVER_TYPES


class WaiverForm(forms.Form):
    waiver_type = forms.ChoiceField(
        choices=(
            (w, WAIVER_TYPES.get_item_help_text(w)) for w in WAIVER_TYPES
        )
    )
    message = forms.CharField(widget=forms.widgets.Textarea(),
                              initial="This defect is not a bug because...")


class ScanListSearchForm(forms.Form):
    search = forms.CharField(required=False)
    my = forms.BooleanField(required=False)

    def get_query(self, request):
        self.is_valid()
        search = self.cleaned_data["search"]
        my = self.cleaned_data["my"]

        query = Q()

        if search:
            try:
                id_query = int(search)
            except ValueError:
                pass
            else:
                query |= Q(id=id_query)
            query |= Q(scan__nvr__icontains=search)
            query |= Q(scan__base__nvr__icontains=search)
            query |= Q(scan__username__username__icontains=search)

        if my and request.user.is_authenticated():
            query &= Q(owner=request.user)

        return query
