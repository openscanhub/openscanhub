"""
Service functions for views

not in use yet
"""

from covscanhub.waiving.models import Waiver, WaivingLog

# WAIVING


def submit_waiver_to_group(**kwargs):
    """
    submit new waiver to provided result group, kwargs:
    user - user who sent request
    result_group - result group to attach waiver to
    """
    user = kwargs['user']
    rg = kwargs['result_group']
    wl = WaivingLog()
    wl.user = user
    if rg.has_waiver():
        wl.state = WAIVER_LOG_ACTIONS['REWAIVE']
    else:
        wl.state = WAIVER_LOG_ACTIONS['NEW']

    latest_waiver = result_group_object.latest_waiver()

    if latest_waiver:
        latest_waiver.is_active = False
        latest_waiver.save()

    w = Waiver()
    w.message = form.cleaned_data['message']
    w.result_group = result_group_object
    w.user = request.user
    w.is_active = True
    w.state = WAIVER_TYPES[form.cleaned_data['waiver_type']]
    w.save()

    wl.waiver = w
    wl.save()

    s = sb.scan

    if result_group_object.is_previously_waived():
        result_group_object.defect_type = DEFECT_STATES['NEW']
        result_group_object.save()

    # set RG as waived when condition is met
    # set run as waived if everything is okay
    if waiver_condition(result_group_object):
        result_group_object.state = RESULT_GROUP_STATES['WAIVED']
        result_group_object.save()

        if not get_unwaived_rgs(sb.result) and not s.is_waived():
            s.set_state(SCAN_STATES['WAIVED'])
    s.last_access = datetime.datetime.now()
    s.save()


def submit_comment_to_group(**kwargs):
    """
    Add comment to group of defects
    kwargs contains these texts:

    text - comment text
    result_group - result group to attach comment to
    user - user who posted the comment
    """
    rg = kwargs['result_group']
    text = kwargs['text']
    user = kwargs['user']

    w = Waiver.new_comment(message=text, result_group=rg, user=user)
    w.save()
    wl = WaivingLog.new_log(user=user, waiver=w)
    wl.save()
