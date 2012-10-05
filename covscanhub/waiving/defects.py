# -*- coding: utf-8 -*-

#from covscanhub.scan.models import Scan
#from covscanhub.waiving.models import Defect

def update_fixed(scan, diff_json_dict):
    """
    Checks all defects in result and compares them against diff. The result is
    that all missing defects are actually fixed.
    """
    


def update_newly_added():
    """
    Checks all defects in result and compares them against "csdiff -x". 
    Matched defects are newly added
    """

def update_already_waived():
    """
    This one will be one hell of a magic if ever.
    """    