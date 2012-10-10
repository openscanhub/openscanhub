# -*- coding: utf-8 -*-

"""
    compilation of functions that provide functionality for waiving and fill
    database with defects from scan
"""

import django.utils.simplejson as json
from models import DEFECT_STATES, Defect, Event, Result, Checker, CheckerGroup
import os
from kobo.hub.models import Task
from django.core.exceptions import ObjectDoesNotExist


def load_defects_from_json(json_dict, result, 
                        defect_state=DEFECT_STATES['UNKNOWN']):
    """
    this function loads defects from provided json dictionary and writes them
    into provided result model object
    """
    if 'defects' in json_dict:
        for defect in json_dict['defects']:
            d = Defect()
            json_checker_name = defect['checker']
            try:
                checker = Checker.objects.get(name=json_checker_name)
            except ObjectDoesNotExist:
                print "%s does not exist, so I'll create it" % \
                    json_checker_name
                checker = Checker()
                checker.name = json_checker_name
                checker.group = CheckerGroup.objects.get(name='Default')
                checker.save
            print "defect's checker is %s" % checker
            d.checker = checker
            d.annotation = defect['annotation']
            d.result = result
            d.state = defect_state
            d.save() 
            # we have to aquire id for 'd' so it is correctly linked to events
            key_event = defect['key_event_idx']

            if 'events' in defect:
                e_id = None
                for event in defect['events']:
                    e = Event()
                    e.file_name = event['file_name']
                    e.line = event['line']
                    e.event = event['event']
                    e.message = event['message']
                    e.defect = d
                    e.save()
                    if e_id is None:
                        if key_event == 0:
                            e_id = e
                        else:
                            key_event -= 1
                #e_id could be None
                d.key_event = e_id
            d.save()
            
def update_analyzer(result, json_dict):
    """
    fills object result with information about which analyzer performed scan
    """
    if 'scan' in json_dict:
        if 'analyzer' in json_dict['scan']:
            result.scanner = json_dict['scan']['analyzer']
        if 'analyzer-version' in json_dict['scan']:
            result.scanner_version = json_dict['scan']['analyzer-version']
    result.save()

def create_results(scan):
    """
    Task finished, so this method should update results
    """

    task_dir = Task.get_task_dir(scan.task.id)

    #json's path is <TASK_DIR>/<NVR>/run1/<NVR>.js
    defects_path = os.path.join(task_dir, scan.nvr, 'run1', scan.nvr + '.js')
    fixed_file_path = os.path.join(task_dir, 'csdiff_fixed.out')
    diff_file_path = os.path.join(task_dir, 'csdiff.out')
    
    try:
        f = open(defects_path, 'r')
    except IOError:
        print 'Unable to open file %s' % defects_path
        return
    json_dict = json.load(f)

    r = Result()

    update_analyzer(r, json_dict)
    
    r.scan = scan
    r.save()
    
    f.close()    
    
    try:
        fixed_file = open(fixed_file_path, 'r')
    except IOError:
        print 'Unable to open file %s' % fixed_file_path
        return
    fixed_json_dict = json.load(fixed_file)
    load_defects_from_json(fixed_json_dict, r, DEFECT_STATES['FIXED'])
    
    try:
        diff_file = open(diff_file_path, 'r')
    except IOError:
        print 'Unable to open file %s' % diff_file_path
        return
    diff_json_dict = json.load(diff_file)
    load_defects_from_json(diff_json_dict, r, DEFECT_STATES['NEW'])
    