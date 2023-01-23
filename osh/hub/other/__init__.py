# -*- coding: utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist


def get_or_none(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except ObjectDoesNotExist:
        return None
