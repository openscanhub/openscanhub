# -*- coding: utf-8 -*-


import os

from django.core.exceptions import ObjectDoesNotExist

import koji

from kobo.hub.models import Task, TASK_STATES
from kobo.django.upload.models import FileUpload
from kobo.django.xmlrpc.decorators import login_required

from covscanhub.scan.models import MockConfig, SCAN_TYPES
from covscanhub.scan.service import create_diff_scan


__all__ = (
    "diff_build",
    "mock_build",
    "create_user_diff_scan",
)


class DiffBuild(object):
    def __init__(self, koji_url):
        self.koji_url = koji_url
        self.koji_proxy = koji.ClientSession(self.koji_url)

    def get_task_class_name(self):
        return "DiffBuild"

    def __call__(self, request, mock_config, comment=None, options=None):
        """
            @param mock_config: mock config name
            @type  mock_config: str
            @param comment: scan description
            @type  comment: str
            @param options:
            @type  options: dict
        """
        comment = comment or ""
        options = options or {}

        upload_id = options.pop("upload_id", None)
        brew_build = options.pop("brew_build", None)

        if upload_id is None and brew_build is None:
            raise RuntimeError("Neither upload_id or brew_build specified.")
        if upload_id is not None and brew_build is not None:
            raise RuntimeError("Can't specify both upload_id and brew_build at the same time.")

        priority = options.pop("priority", 10)
        if priority is not None:
            max_prio = 20
            if int(priority) > max_prio and not request.user.is_superuser:
                raise RuntimeError("Setting high task priority (>%s) requires admin privileges." % max_prio)

        try:
            conf = MockConfig.objects.get(name=mock_config)
        except:
            raise ObjectDoesNotExist("Unknown mock config: %s" % mock_config)
        if not conf.enabled:
            raise RuntimeError("Mock config is disabled: %s" % mock_config)
        options["mock_config"] = mock_config

        if upload_id:
            try:
                upload = FileUpload.objects.get(id=upload_id)
            except:
                raise ObjectDoesNotExist("Can't find uploaded file with id: %s" % upload_id)

            if upload.owner.username != request.user.username:
                raise RuntimeError("Can't process a file uploaded by a different user")

            srpm_path = os.path.join(upload.target_dir, upload.name)
            options["srpm_name"] = upload.name
            task_label = options["srpm_name"]

        if brew_build:
            options["brew_build"] = brew_build
            task_label = options["brew_build"]

        task_id = Task.create_task(request.user.username, task_label, self.get_task_class_name(), options, comment=comment, state=TASK_STATES["CREATED"], priority=priority)
        task_dir = Task.get_task_dir(task_id)

        if not os.path.isdir(task_dir):
            try:
                os.makedirs(task_dir, mode=0755)
            except OSError, ex:
                if ex.errno != 17:
                    raise

        if upload_id:
            # move file to task dir, remove upload record and make the task available
            import shutil
            shutil.move(srpm_path, os.path.join(task_dir, os.path.basename(srpm_path)))
            upload.delete()

        # set the task state to FREE
        Task.objects.get(id=task_id).free_task()
        return task_id


class MockBuild(DiffBuild):
    def get_task_class_name(self):
        return "MockBuild"


diff_build_obj = DiffBuild("http://brewhub.devel.redhat.com/brewhub")
mock_build_obj = MockBuild("http://brewhub.devel.redhat.com/brewhub")


@login_required
def diff_build(*args, **kwargs):
    global diff_build_obj
    return diff_build_obj(*args, **kwargs)


@login_required
def mock_build(*args, **kwargs):
    global mock_build_obj
    return mock_build_obj(*args, **kwargs)


@login_required
def create_user_diff_scan(request, kwargs):
    """
        create scan of a package and perform diff on results against specified
        version

        kwargs:
         - username - name of user who is requesting scan
         - nvr - name, version, release of scanned package
         - base - nvr of previous version, the one to make diff against
         - nvr_mock - mock config
         - base_mock - mock config
    """
    kwargs['scan_type'] = SCAN_TYPES['USER']
    kwargs['task_user'] = request.user.username
    create_diff_scan(kwargs)