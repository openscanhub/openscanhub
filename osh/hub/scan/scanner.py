# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

"""
logic for spawning tasks

* common options are encapsulated in classes

"""

import logging
import os
import re
import shutil

from django.core.exceptions import ObjectDoesNotExist
from kobo.django.upload.models import FileUpload
from kobo.hub.models import TASK_STATES, Arch, Task

from osh.hub.other.exceptions import PackageBlockedException
from osh.hub.scan.check import (check_analyzers, check_build, check_nvr,
                                check_obsolete_scan, check_package_is_blocked,
                                check_srpm, check_task_metadata, check_upload,
                                is_container_build)
from osh.hub.scan.mock import generate_mock_configs
from osh.hub.scan.models import (REQUEST_STATES, SCAN_TYPES, AppSettings,
                                 ClientAnalyzer, ETMapping, MockConfig,
                                 Package, Profile, Scan, ScanBinding, Tag)
from osh.hub.scan.service import get_latest_binding
from osh.hub.scan.utils import get_or_fail, is_rebase
from osh.hub.service.processing import task_has_results

logger = logging.getLogger(__name__)


def dig_arch(mock_config):
    for arch in Arch.objects.all():
        if mock_config.endswith(arch.name):
            return arch.name
    return 'noarch'


# shutil.copytree on Python 3.6 demands that the target directory does not exist
# but there are issues with SELinux if it creates the target directory on its own.
#
# FIXME: simplify using shutil.copytree(..., ..., dirs_exist_ok=True) when
# Python 3.9 is the lowest supported version
def move_mock_configs(src, task_dir):
    dst = os.path.join(task_dir, 'mock')
    os.makedirs(dst)
    # os.listdir ignores `.` and `..`
    for f in os.listdir(src):
        shutil.copy(os.path.join(src, f), dst)
    shutil.rmtree(src)


class AbstractScheduler:
    """

    """
    def __init__(self, options, *args, **kwargs):
        """ """
        self.task_args = {}
        self.scan_args = {}

        # provided options
        self.options = options

        # {'name': 'foo', 'version':...}
        self.target_nvre_dict = {}

        # required for base & target
        self.package_owner = None
        self.package = None
        self.scan = None
        self.nvr = None
        self.tag = None
        self.priority_offset = 0

        # transaction management
        self.is_stored = False

    def validate_options(self):
        self.package_owner = get_or_fail('package_owner', self.options)
        self.nvr = get_or_fail('target', self.options)
        self.target_nvre_dict = check_nvr(self.nvr)
        self.koji_profile = check_build(self.nvr)['koji_profile']

    def prepare_args(self):
        """ prepare dicts -- arguments for task and scan """
        self.task_args['args'] = {}
        self.task_args['args']['build'] = self.nvr
        self.task_args['args']['profile'] = 'errata'
        self.task_args['args']['su_user'] = AppSettings.setting_get_su_user()
        self.scan_args['nvr'] = self.nvr
        self.scan_args['username'] = self.package_owner
        self.package = Package.objects.get_or_create_by_name(self.target_nvre_dict['name'])
        self.priority_offset = self.package.get_priority_offset()

    def store(self):
        """
        create and update database models from provided data
        """
        if self.is_stored:
            logger.warning("Trying to call store() second time.")
            return
        logger.debug("Creating scan with args %s", self.scan_args)
        self.scan = Scan.create_scan(**self.scan_args)
        self.task_args['args']['scan_id'] = self.scan.id

    def spawn(self):
        """ """
        raise NotImplementedError()


class BaseScheduler(AbstractScheduler):
    """
    base scans
    """
    def __init__(self, *args, **kwargs):
        """
        prepare base scan

        options = {
            'target': <nvr>
            'package_owner': ''
            'mock_config': '',
        }
        """
        super().__init__(*args, **kwargs)
        self.mock_config = ''
        self.method = ''
        self.parent_scan = None
        self.validate_options()

    def validate_options(self):
        super().validate_options()
        self.mock_config = get_or_fail('mock_config', self.options)
        self.package = get_or_fail('package', self.options)
        self.parent_scan = get_or_fail('parent_scan', self.options)
        self.method = get_or_fail('method', self.options)
        self.tag = get_or_fail('tag', self.options)

    def prepare_args(self):
        """ add scan type specific arguments to args dicts """
        super().prepare_args()
        self.scan_args['scan_type'] = SCAN_TYPES['ERRATA_BASE']
        self.scan_args['package'] = self.package
        self.scan_args['tag'] = self.tag
        self.scan_args['enabled'] = False

        self.task_args['arch_name'] = dig_arch(self.mock_config)
        self.task_args['label'] = self.nvr
        self.task_args['method'] = self.method

        # scan all 'auto' container builds using cspodman
        if self.mock_config == 'auto' and is_container_build(self.nvr, self.koji_profile):
            self.mock_config = 'cspodman'
        self.task_args['args']['mock_config'] = self.mock_config

    def store(self):
        """
        create and update database models from provided data
        """
        if self.is_stored:
            logger.warning("Trying to call store() second time.")
            return
        super().store()
        # update scan.models.Scan.base
        self.parent_scan.set_base(self.scan)
        self.is_stored = True

    def spawn(self):
        """
        """
        raise RuntimeError('Base scans are not meant to be scheduled directly, use TaskBase.spawn_subtask instead.')

    def get_spawn_subtask_args(self):
        """
            args for `spawn_subtask(method, args, label="")`
        """
        self.store()
        return self.task_args['method'], self.task_args['args'], self.task_args['label']


class AbstractTargetScheduler(AbstractScheduler):
    """
    abstract class for management of targets submitted by CI/release tool
    """

    def __init__(self, *args, **kwargs):
        """
        """
        super().__init__(*args, **kwargs)

        # required for target only
        self.base_nvr = None

        self.package_name = ""

        # transaction management
        self.is_spawned = False

        self.validate_options()

    def validate_options(self):
        """ Check if provided options are sane """
        super().validate_options()

        self.base_nvr = get_or_fail('base', self.options)
        get_or_fail('release', self.options)
        self.package_name = self.target_nvre_dict['name']

    def prepare_args(self):
        """ prepare dicts -- arguments for task and scan """
        super().prepare_args()
        self.task_args['args']['base_nvr'] = self.base_nvr
        self.task_args['owner_name'] = self.options['task_user']
        self.task_args['label'] = self.options['target']
        self.task_args['method'] = 'ErrataDiffBuild'
        self.task_args['comment'] = f'errata process scan of {self.options["target"]}'
        self.task_args['state'] = TASK_STATES['CREATED']
        self.task_args['priority'] = max(0, 10 + self.priority_offset)
        self.scan_args['enabled'] = True

    def store(self):
        """
        create and update database models from provided data
        """
        if self.is_stored:
            logger.warning("Trying to call store() second time.")
            return

        pkg_name = self.package.name

        # TODO: make this configurable
        if pkg_name.startswith("kpatch-patch"):
            raise PackageBlockedException('kpatch-patch is not eligible for scanning.')

        self.tag = Tag.objects.for_release_str(self.options['release'])
        mock_config = self.tag.mock.name

        if self.tag.name == 'ASYNC':
            self.tag = Tag.objects.for_release_str(self.options['rhel_version'])

        # scan all 'auto' container builds using cspodman
        is_container = is_container_build(self.nvr, self.koji_profile)
        if mock_config == 'auto' and is_container:
            mock_config = 'cspodman'

        self.task_args['arch_name'] = dig_arch(mock_config)
        self.task_args['args']['mock_config'] = mock_config
        if self.task_args['args']['mock_config'] == 'auto':
            self.mock_config_tmpdir = generate_mock_configs(self.nvr, self.koji_profile)

        self.scan_args['tag'] = self.tag
        self.scan_args['package'] = self.package

        if mock_config == "cspodman":
            # TODO: make this configurable
            self.task_args['priority'] = 8
        elif is_container:
            raise PackageBlockedException(f'Container {pkg_name} is not eligible for scanning.')

        check_package_is_blocked(self.package, self.tag.release)
        check_obsolete_scan(self.package, self.tag.release)

        super().store()

        self.is_stored = True

    def spawn(self):
        """ Spawn tasks """
        if self.is_spawned:
            logger.warning("Trying to call spawn() second time.")
            return
        self.prepare_args()
        self.store()
        task_id = Task.create_task(**self.task_args)
        task = Task.objects.get(id=task_id)
        task_dir = Task.get_task_dir(task_id, create=True)

        if self.task_args['args']['mock_config'] == 'auto':
            move_mock_configs(self.mock_config_tmpdir, task_dir)

        sb = ScanBinding.create_sb(task=task, scan=self.scan)
        task.free_task()

        child = ScanBinding.objects.latest_scan_of_package(self.package, self.tag.release)

        if child and child.scan:
            child_scan = child.scan
            child_scan.parent = self.scan
            child_scan.enabled = False
            child_scan.save()
        self.is_spawned = True
        return sb


class NewPkgScheduler(AbstractTargetScheduler):
    """

    """
    def prepare_args(self):
        """ add scan type specific arguments to args dicts """
        super().prepare_args()
        self.scan_args['scan_type'] = SCAN_TYPES['NEWPKG']


class RebaseScheduler(AbstractTargetScheduler):
    """

    """
    def prepare_args(self):
        """ add scan type specific arguments to args dicts """
        super().prepare_args()
        self.scan_args['scan_type'] = SCAN_TYPES['REBASE']


class ClassicScheduler(AbstractTargetScheduler):
    """

    """
    def prepare_args(self):
        """ add scan type specific arguments to args dicts """
        super().prepare_args()
        self.scan_args['scan_type'] = SCAN_TYPES['ERRATA']


class AbstractClientScanScheduler:
    def prepare_csmock_args(self, *additional_csmock_args):
        """ additional_csmock_args are additional arguments as string """
        def add_if(x, collection):
            if x:
                collection.append(x)
        csmock_args = {
            'warning_level': '-w%s',
            # --cov-custom-model='%s' is not here because we need to upload file
            'install_to_chroot': "--install='%s'",
            'tarball_build_script': "--shell-cmd='%s'",
        }
        # client args
        csmock_opts = []
        add_args = []
        # profile, analuzer args
        for a in additional_csmock_args:
            add_if(a, add_args)
        # args supplied to scheduler class
        add_if(self.additional_csmock_args, add_args)
        for opt in self.options:
            if opt in csmock_args:
                try:
                    csmock_opts.append(csmock_args[opt] % self.options[opt])
                except TypeError:
                    # value does not need to be converted
                    csmock_opts.append(csmock_args[opt])
        # client overrides via --csmock-args
        if self.client_csmock_args:
            csmock_opts.append(self.client_csmock_args)
        if csmock_opts:
            add_args.append(' '.join(csmock_opts))
        opts = " ".join(add_args)
        logger.info("Task opts are '%s'", opts)
        return opts

    @classmethod
    def determine_priority(cls, entered_priority, supposed_nvr, srpm_name,
                           is_tarball=False):
        """determine priority of scheduled task

        :param entered_priority: priority submitted by client
        :type entered_priority: int
        :param supposed_nvr: supposedly valid nvr
        :type supposed_nvr: str
        :param srpm_name: name of submitted srpm
        :type srpm_name: str
        :param is_tarball: determines whether we use a tarball build script
        :type is_tarball: bool
        :return: priority of scheduled task
        :rtype: int
        """
        if entered_priority is not None:
            return entered_priority

        priority_offset = 0
        name_candidates = []

        if srpm_name:
            if srpm_name.endswith('.src.rpm'):
                srpm_name = srpm_name[:-8]

            if is_tarball:
                srpm_name = re.sub(r'\.tar(\.[a-z0-9]+)?$', '', srpm_name)

        try:
            name_candidates.append(check_nvr(supposed_nvr or srpm_name)['name'])
        except RuntimeError:
            pass

        if srpm_name:
            # try also only NV and the whole filename
            name_candidates.append(re.sub('-[^-]*$', '', srpm_name))
            name_candidates.append(srpm_name)

        for name in name_candidates:
            try:
                priority_offset = Package.objects.get(name=name).get_priority_offset()
                break
            except (ObjectDoesNotExist, ValueError):
                pass

        # the priority must be non-negative
        return max(0, 10 + priority_offset)

    def determine_result_filename(self, nvr, filename, is_tarball, git_url=None):
        if nvr:
            return nvr

        if filename and filename.endswith(".src.rpm"):
            return os.path.basename(filename)[:-8]

        if is_tarball:
            f = os.path.basename(filename)
            return f.rsplit(".", 2 if ".tar." in f else 1)[0]
        # FIXME: resolve result_filename later
        if git_url is not None:
            return None

        raise RuntimeError("unknown input format of sources")


class ClientScanScheduler(AbstractClientScanScheduler):
    """
    scheduler for tasks submitted from client -- users
    """
    def __init__(self, options, method='MockBuild', additional_csmock_args=''):
        """ """
        self.task_args = {}

        # provided options
        self.options = options
        self.method = method
        self.additional_csmock_args = additional_csmock_args

        self.validate_options()

    def validate_options(self):
        self.username = get_or_fail('task_user', self.options)
        self.user = get_or_fail('user', self.options)
        self.upload_model_id = self.options.get('upload_model_id', None)

        self.model_name = None
        if self.upload_model_id:
            unused_nvr, self.model_name, self.model_path = check_upload(self.upload_model_id, self.username)

        # srpm
        self.build_nvr = self.options.get('brew_build', None)
        self.dist_git_url = self.options.get('dist_git_url')
        self.upload_id = self.options.get('upload_id', None)
        self.srpm_name = None
        self.srpm_path = None
        self.is_tarball = bool(self.options.get("tarball_build_script", None))
        if any((self.build_nvr, self.upload_id)):
            check_srpm_response = check_srpm(self.upload_id, self.build_nvr, self.username, self.is_tarball)
            if check_srpm_response['type'] == 'build':
                self.build_koji_profile = check_srpm_response['koji_profile']
            elif check_srpm_response['type'] == 'upload':
                self.srpm_path = check_srpm_response['srpm_path']
                self.srpm_name = check_srpm_response['srpm_name']
        elif self.dist_git_url is None:
            raise RuntimeError('No source RPM or tarball or dist-git URL specified.')

        # analyzers
        self.analyzers = self.options.get('analyzers', '')
        self.profile = self.options.get('profile', 'default')
        self.analyzer_models = check_analyzers(self.analyzers)
        self.profile_analyzers, self.profile_args = Profile.objects.get_analyzers_and_args_for_profile(self.profile)

        # mock profile
        self.mock_config = get_or_fail('mock_config', self.options)
        if self.mock_config == 'auto' and not self.build_nvr:
            raise RuntimeError("'auto' mock config is only compatible with '--nvr'")
        if self.mock_config == 'auto' and is_container_build(self.build_nvr, self.build_koji_profile):
            self.mock_config = 'cspodman'
        MockConfig.objects.verify_by_name(self.mock_config)

        self.comment = self.options.get('comment', '')

        self.priority = self.options.get('priority', None)
        if self.priority:
            self.priority = int(self.priority)
            if self.priority >= 20 and not self.user.is_staff:
                raise RuntimeError("Only admin is able to set higher priority than 20!")

        self.client_csmock_args = self.options.get('csmock_args', None)

        self.metadata = self.options.get('metadata')
        if self.metadata:
            self.metadata = check_task_metadata(self.metadata)

        self.email_to = self.options.get("email_to", None)

    def prepare_args(self):
        """ prepare dicts -- arguments for task and scan """
        self.task_args['arch_name'] = dig_arch(self.mock_config)
        self.task_args['owner_name'] = self.username
        input_pkg = self.build_nvr or self.srpm_name
        self.task_args['label'] = input_pkg
        self.task_args['method'] = self.method
        self.task_args['comment'] = self.comment
        self.task_args['priority'] = AbstractClientScanScheduler.determine_priority(
            self.priority, self.build_nvr, self.srpm_name, self.is_tarball)
        self.task_args['state'] = TASK_STATES['CREATED']
        self.task_args['args'] = {}
        if self.build_nvr:
            self.task_args['args']['build'] = {
                'nvr': self.build_nvr,
                'koji_profile': self.build_koji_profile,
            }
        elif self.dist_git_url is not None:
            self.task_args['args']['dist_git_url'] = self.dist_git_url
            # FIXME: parse the dist_git_url and populate self.task_args['label']
        else:
            self.task_args['args']['srpm_name'] = self.srpm_name

        self.task_args['args']['result_filename'] = self.determine_result_filename(
            self.build_nvr, input_pkg, self.is_tarball, self.dist_git_url)
        # FIXME: ideally rewrite the code to stuff all input-related info to "source" (e.g. builds,
        #        nvrs, srpm filenames etc.)
        if self.is_tarball:
            self.task_args['args']['source'] = {
                "type": "tar",
            }
        analyzer_opts = ClientAnalyzer.objects.get_opts(self.analyzer_models)
        analyzers_set = set(analyzer_opts['analyzers'] + self.profile_analyzers)
        analyzer_chain = ','.join(analyzers_set)
        self.task_args['args']['analyzers'] = analyzer_chain
        self.task_args['args']['mock_config'] = self.mock_config
        self.task_args['args']['profile'] = self.profile
        # profile args < analyzer args < client opts
        csmock_args = self.prepare_csmock_args(self.profile_args, *tuple(analyzer_opts['args']))
        self.task_args['args']['csmock_args'] = csmock_args
        self.task_args['args']['custom_model_name'] = self.model_name
        self.task_args['args']['su_user'] = AppSettings.setting_get_su_user()

        if self.metadata:
            self.task_args['args']['metadata'] = self.metadata

        if self.email_to:
            self.task_args['args']['email_to'] = self.email_to

        if self.mock_config == 'auto':
            self.mock_config_tmpdir = generate_mock_configs(self.build_nvr, self.build_koji_profile)

    def spawn(self):
        task_id = Task.create_task(**self.task_args)
        task = Task.objects.get(id=task_id)
        task_dir = Task.get_task_dir(task_id, create=True)

        if self.upload_id:
            # move file to task dir, remove upload record and make the task
            # available
            shutil.move(self.srpm_path, os.path.join(task_dir, self.srpm_name))
            FileUpload.objects.get(id=self.upload_id).delete()

        if self.upload_model_id:
            shutil.move(self.model_path, os.path.join(task_dir, self.model_name))
            FileUpload.objects.get(id=self.upload_model_id).delete()

        if self.mock_config == 'auto':
            move_mock_configs(self.mock_config_tmpdir, task_dir)

        task.free_task()
        return task_id


class ClientDiffPatchesScanScheduler(ClientScanScheduler):
    """
    task for diff of patches
    """
    def __init__(self, options, method='DiffBuild', additional_csmock_args="--diff-patches", **kwargs):
        super().__init__(
            options, method=method,
            additional_csmock_args=additional_csmock_args,
            **kwargs
        )


class ClientDiffScanScheduler(ClientScanScheduler):
    """
    scheduler for diff tasks submitted from client -- users
    """
    def __init__(self, options, method='VersionDiffBuild',
                 additional_csmock_args=''):
        """ """
        super().__init__(options, method, additional_csmock_args)

    def validate_options(self):
        super().validate_options()

        # base srpm
        self.base_build_nvr = self.options.get('base_brew_build', None)
        self.base_upload_id = self.options.get('base_upload_id', None)
        self.base_is_tarball = 'base_tarball_build_script' in self.options
        if any((self.base_upload_id, self.base_build_nvr)):
            base_check_srpm_response = check_srpm(self.base_upload_id, self.base_build_nvr, self.username, self.base_is_tarball)
        else:
            raise RuntimeError("No source RPM or tarball specified.")
        if base_check_srpm_response['type'] == 'build':
            self.base_build_koji_profile = base_check_srpm_response['koji_profile']
        elif base_check_srpm_response['type'] == 'upload':
            self.base_srpm_path = base_check_srpm_response['srpm_path']
            self.base_srpm_name = base_check_srpm_response['srpm_name']

        # base mock profile
        try:
            self.base_mock_config = self.options['base_mock_config']
        except KeyError:
            self.base_mock_config = self.mock_config
        else:
            if self.base_mock_config == 'auto' and is_container_build(self.base_build_nvr, self.base_build_koji_profile):
                self.base_mock_config = 'cspodman'

            MockConfig.objects.verify_by_name(self.base_mock_config)

        if self.base_mock_config == 'auto' and not self.base_build_nvr:
            raise RuntimeError("'auto' base mock config is only compatible with '--base-nvr'")

    def prepare_args(self):
        super().prepare_args()

        # base task args has to be last!
        self.task_args['args']['base_task_args'] = self.prepare_basetask_args()

    def prepare_basetask_args(self):
        label = self.base_build_nvr or self.base_srpm_name
        args = {
            'mock_config': self.base_mock_config,
            'profile': self.task_args['args']['profile'],
            'analyzers': self.task_args['args']['analyzers'],
            'csmock_args': self.task_args['args']['csmock_args'],
            'su_user': self.task_args['args']['su_user'],
            'custom_model_name': self.task_args['args']['custom_model_name'],
            'result_filename': self.determine_result_filename(self.base_build_nvr, label, self.base_is_tarball)
        }
        if self.base_build_nvr:
            args['build'] = {
                'nvr': self.base_build_nvr,
                'koji_profile': self.base_build_koji_profile,
            }
        else:
            args['srpm_name'] = self.base_srpm_name
            args['upload_id'] = self.base_upload_id

        # FIXME: ideally rewrite the code to stuff all input-related info to "source" (e.g. builds,
        #        nvrs, srpm filenames etc.)
        if self.base_is_tarball:
            args['source'] = {"type": "tar"}

        return self.task_args['method'], args, label


def prepare_base_scan(options):
    """
    subtasks are meant to be created with kobo.worker.task.TaskBase.spawn_subtask
    """
    bs = BaseScheduler(options)
    bs.prepare_args()
    spawn_subtask_args = bs.get_spawn_subtask_args()
    return spawn_subtask_args


def obtain_base(base_nvr, mock_config):
    """
    @param base_nvr - nvr of base to fetch
    @param mock_config - name of mock config to check analyzer versions against

    returns none if no suitable scan is found
    """
    binding = get_latest_binding(base_nvr)
    logger.debug("Latest binding is '%s'", binding)
    if not binding:
        return None

    if binding.scan.is_in_progress() and binding.result is None:
        logger.debug("Scan is in progress")
        return binding.scan

    if binding.result is None:
        # safe handling: there should be result but it's not there actually -- reschedule
        logger.warning("Scan %s is not in progress and has no result.", binding)
        return None

    if not binding.is_actual(mock_config):
        # is it scanned with up-to-date analysers?
        logger.debug("Configuration of analysers changed, rescan base")
        return None

    if not task_has_results(binding.task):
        return None

    return binding.scan


def create_errata_scan(options, etm):
    if options['base'].lower() == 'new_package':
        sb = NewPkgScheduler(options).spawn()
    elif is_rebase(options['base'], options['target']):
        sb = RebaseScheduler(options).spawn()
    else:
        sb = ClassicScheduler(options).spawn()
    etm.set_latest_run(sb)
    sb.scan.set_state_queued()
    return etm


def handle_scan(kwargs):
    """
    Create ET diff scan, handle all possible failures, return dict with
    response, so it can be passed to ET
    """
    response = {}
    message = None

    etm = ETMapping()

    try:
        # ET internal id for the scan record in ET
        etm.et_scan_id = get_or_fail('id', kwargs)
        # ET internal id of the advisory that the build is part of
        etm.advisory_id = get_or_fail('errata_id', kwargs)
        etm.save()

        create_errata_scan(kwargs, etm)
    except PackageBlockedException as ex:
        status = 'INELIGIBLE'
        message = str(ex)
    except RuntimeError as ex:
        status = 'ERROR'
        message = 'Unable to submit the scan, error: %s' % ex
    except Exception as ex:  # noqa: B902
        status = 'ERROR'
        message = str(ex)
    else:
        status = 'OK'

    # set status in response dict + in DB
    response['status'] = status
    etm.state = REQUEST_STATES[status]
    etm.save()

    # if there were some error, add it to response & DB
    if message:
        response['message'] = message
        etm.comment = message
        etm.save()

    # this should evaluated as True _always_
    if etm.id:
        response['id'] = etm.id

    return response
