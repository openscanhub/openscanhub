# -*- coding: utf-8 -*-

#from models import DEFECT_STATES

from covscanhub.other.admin import register_admin_module

#defect_states = lambda self, instance: \
#    DEFECT_STATES.get_value(instance.defect_type)
#defect_states.short_description = 'Defects state'

register_admin_module('covscanhub.waiving.models')  # new_fields={
#    'ResultGroup': ('defect_type_text', defect_states),
#})
