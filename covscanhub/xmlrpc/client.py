# -*- coding: utf-8 -*-


import os
import simplejson

from django.core.exceptions import ObjectDoesNotExist
#from django.core.urlresolvers import reverse

from kobo.hub.models import Task, TASK_STATES
from kobo.django.upload.models import FileUpload
from kobo.django.xmlrpc.decorators import login_required

from covscanhub.scan.models import MockConfig


__all__ = (
    "diff_build",
)


@login_required
def diff_build(request, mock_config, upload_id, comment=None, options=None):
    comment = comment or ""
    options = options or {}

    priority = options.pop("priority", 10)
    if priority is not None:
        max_prio = 20
        if int(priority) >= max_prio and not request.user.is_superuser:
            raise RuntimeError("Setting high task priority (>=%s) requires admin privileges." % max_prio)

    try:
        conf = MockConfig.objects.get(name=mock_config)
    except:
        raise ObjectDoesNotExist("Unknown mock config: %s" % mock_config)

    if not conf.enabled:
        raise RuntimeError("Mock config is disabled: %s" % mock_config)

    try:
        upload = FileUpload.objects.get(id=upload_id)
    except:
        raise ObjectDoesNotExist("Can't find uploaded file with id: %s" % upload_id)

    if upload.owner.username != request.user.username:
        raise RuntimeError("Can't process a file uploaded by a different user")

    srpm_path = os.path.join(upload.target_dir, upload.name)
    options["mock_config"] = mock_config
    options["srpm_name"] = upload.name


    task_id = Task.create_task(request.user.username, "", "DiffBuild", options, comment=comment, state=TASK_STATES["CREATED"], priority=priority)
    task_dir = Task.get_task_dir(task_id)
    import shutil

    if not os.path.isdir(task_dir):
        try:
            os.makedirs(task_dir, mode=0755)
        except OSError, ex:
            if ex.errno != 17:
                raise

    # move file to task dir, remove upload record and make the task available
    shutil.move(srpm_path, os.path.join(task_dir, os.path.basename(srpm_path)))
    upload.delete()
    Task.objects.get(id=task_id).free_task()
    return task_id
