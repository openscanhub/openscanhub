# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

"""
Functions related to checking provided data
"""

import logging
import os

import koji
from django.core.exceptions import ObjectDoesNotExist
from kobo.django.upload.models import FileUpload
from kobo.rpmlib import parse_nvr

from osh.hub.other.exceptions import PackageBlockedException
from osh.hub.scan.models import ClientAnalyzer, ScanBinding
from osh.hub.scan.xmlrpc_helper import cancel_scan

logger = logging.getLogger(__name__)


def check_nvr(nvr):
    try:
        return parse_nvr(nvr)
    except ValueError:
        logger.error('%s is not a correct N-V-R', nvr)
        raise RuntimeError('%s is not a correct N-V-R' % nvr)


def check_package_is_blocked(package, release):
    if package.is_blocked(release):
        raise PackageBlockedException(f'Package {package.name} is blocked.')


def check_obsolete_scan(package, release):
    bindings = ScanBinding.targets.by_package(package).by_release(release)
    for binding in bindings:
        if binding.scan.is_in_progress():
            cancel_scan(binding)


def check_build(nvr):
    configs = ['brew', 'koji']

    for config in configs:
        try:
            server = koji.read_config(config)['server']
        except koji.ConfigurationError as e:
            logger.debug('koji: %s', e)
            continue
        build = koji.ClientSession(server).getBuild(nvr)
        if build is None:
            continue

        if build['extra'] is not None and 'typeinfo' in build['extra'] and \
                'module' in build['extra']['typeinfo']:
            raise PackageBlockedException(
                'Module metadata builds are not eligible for scanning.')

        return {'type': 'build', 'nvr': nvr, 'koji_profile': config}

    raise RuntimeError(f"Build '{nvr}' does not exist")


def check_analyzers(analyzers_chain):
    if analyzers_chain:
        a_list = ClientAnalyzer.chain_to_list(analyzers_chain)
    else:
        a_list = []
    logger.debug("Analyzers specified by client: %s", a_list)
    return ClientAnalyzer.objects.verify_in_bulk(a_list)


def check_upload(upload_id, task_user, is_tarball=False):
    """
    srpm was uploaded via FileUpload, lets fetch it and check it

    return (nvr, filename, path to srpm)
    """
    try:
        upload = FileUpload.objects.get(id=upload_id)
    except:  # noqa: B901, E722
        raise ObjectDoesNotExist("Can't find uploaded file with id: %s" % upload_id)

    if upload.owner.username != task_user:
        raise RuntimeError("Can't process a file uploaded by a different user")

    srpm_path = os.path.join(upload.target_dir, upload.name)
    srpm_name = upload.name
    nvr = ''
    if not is_tarball:
        nvr = srpm_name.replace('.src.rpm', '')
    return nvr, srpm_name, srpm_path


def check_srpm(upload_id, build_nvr, task_user, is_tarball=False):
    if build_nvr:
        return check_build(build_nvr)

    if upload_id:
        cu_response = check_upload(upload_id, task_user, is_tarball)
        response = {
            'type': 'upload',
            'nvr': cu_response[0],
            'srpm_name': cu_response[1],
            'srpm_path': cu_response[2],
        }
    else:
        raise RuntimeError('No source RPM specified.')
    return response
