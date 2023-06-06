# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.
"""
A set of mixins used to set up test data.

In Django, every test starts with a fresh empty database so it is up to a user
to populate database with data before running the test. This module provides a
set of mixins that can help with this task.
"""

import datetime

from kobo.client.constants import TASK_STATES
from kobo.django.auth.models import User
from kobo.hub.models import Arch, Channel, Task, Worker
from kobo.rpmlib import parse_nvr

from osh.hub.scan.models import (SCAN_STATES, SCAN_TYPES, Analyzer,
                                 AnalyzerVersion, MockConfig, Package, Scan,
                                 ScanBinding, SystemRelease, Tag)
from osh.hub.waiving.models import Result


class TestDataMixin:
    """
    A mixin that populates the database with test data.

    Add this mixin to the list of super classes of your test suite to unlock
    its features. Example::

        class MyTestSuite(TestCase, TestDataMixin):

            @classmethod
            def setUpTestData(cls):
                super().setUpTestData()
                # super() not used here as this method can be overridden
                # further in code
                cls.create_scans()

    :meth:`~.TestDataMixin.setUpTestData` populates the database with test
    data. See :meth:`~django.test.TestCase.setUpTestData` at Django
    documentation for detailed description. Note that if ``setUpTestData`` is
    not defined in a sub class Django *will not* look after it in super
    classes. Therefore ``setUpTestData`` should be defined every time
    :class:`.TestDataMixin` is used.

    Notable methods provided by this mixin:

    * :meth:`~.TestDataMixin.setUpTestData` populates the database with base
      data (users, arches, channels, workers, system releases, mock
      configurations, tags, packages, analyzers, and analyzer versions).
    * :meth:`~.TestDataMixin.create_scans` adds scans into the database. The
      number of scans added is chosen to bring pagination in action.
    """

    #: The number of users created by :meth:`~.TestDataMixin.create_users`.
    NUMBER_OF_USERS = 3
    #: When true, :meth:`~.TestDataMixin.create_users` makes ``user0`` a super
    #: user.
    CREATE_SUPERUSER = True
    #: The date and time of the very first scan and the initial value of
    #: :cvar:`~.TestDataMixin._now`. The date is set to past so scans that are
    #: added with :cvar:`~.TestDataMixin.SCAN_DURATION` interval between them
    #: will not end in future.
    SCAN_START_DATE = datetime.datetime(2023, 5, 3, 14, 34, 21)
    #: The duration of one scan and the increment of
    #: :cvar:`~.TestDataMixin._now`.
    SCAN_DURATION = datetime.timedelta(minutes=5)

    @classmethod
    def setUpTestData(cls):
        """Populate the database with test data."""
        #: Keep the *now* time stamp. *Now* is intentionally set to past.
        cls._now = cls.SCAN_START_DATE
        cls.create_base_data()

    @classmethod
    def create_base_data(cls):
        """
        Create base data.

        Create several users, one arch (``noarch``), one channel (``default``),
        one worker (``worker``), system releases, mock configurations, tags,
        packages, analyzers, and analyzer versions. These are the base level of
        data used to create more complex data objects like scans, waivers, ET
        mappings, etc.
        """
        cls.create_users()

        #: Architecture data object.
        cls.arch = Arch.objects.create(name="noarch", pretty_name="noarch")
        #: Channel data object.
        cls.channel = Channel.objects.create(name="default")

        #: Worker data object.
        cls.worker = Worker.objects.create(worker_key="worker", name="Worker")
        cls.worker.arches.add(cls.arch)
        cls.worker.channels.add(cls.channel)
        cls.worker.save()

        cls.create_system_releases()
        cls.create_mock_configs()
        cls.create_tags()
        cls.create_packages()

        pylint = Analyzer.objects.create(name="pylint")
        #: ``pylint`` analyzer version data object.
        cls.pylint = AnalyzerVersion.objects.create(
            version="2.17.4", analyzer=pylint, date_created=cls._now
        )
        flake8 = Analyzer.objects.create(name="flake8")
        #: ``flake8`` analyzer version data object.
        cls.flake8 = AnalyzerVersion.objects.create(
            version="6.0.0", analyzer=flake8, date_created=cls._now
        )
        cppcheck = Analyzer.objects.create(name="cppcheck")
        #: ``cppcheck`` analyzer version data object.
        cls.cppcheck = AnalyzerVersion.objects.create(
            version="2.9", analyzer=cppcheck, date_created=cls._now
        )
        cls.cppcheck.mocks.add(
            MockConfig.objects.get(name="rhel-8-x86_64"),
            MockConfig.objects.get(name="rhel-9-x86_64"),
        )
        cls.cppcheck.save()

    @classmethod
    def create_users(cls):
        """
        Create users.

        A user has a username ``userN``, an email ``userN@osh.net``, a password
        ``pwdN``, a first name ``NameN``, and a last name ``SurnameN``, where
        ``N`` is a number from 0 to :cvar:`~.TestDataMixin.NUMBER_OF_USERS`,
        exclusive.
        """
        for user_number in range(0, cls.NUMBER_OF_USERS):
            args = [
                f"user{user_number}",          # username
                f"user{user_number}@osh.net",  # email
                f"pwd{user_number}",           # password
            ]
            extra = {
                "first_name": f"Name{user_number}",
                "last_name": f"Surname{user_number}",
            }
            if user_number == 0 and cls.CREATE_SUPERUSER:
                User.objects.create_superuser(*args, **extra)
            else:
                User.objects.create_user(*args, **extra)

    @staticmethod
    def create_rhel_system_releases(major, minor_start, minor_end, active):
        """
        Create RHEL system releases.

        :param major: The major version number of RHEL
        :param minor_start: The initial minor number
        :param minor_end: The final minor number
        :param active: The truth value telling whether the product line is
            active or the list of minor numbers of active releases

        Create the sequence of releases from ``rhel-{major}.{minor_start}`` to
        ``rhel-{major}.{minor_end}``, inclusive. Negative ``minor_start`` means
        that the release is beta, e.g. ``rhel-{major}-beta``.
        """
        parent = None
        tag_prefix = f"rhel-{major}"
        product = f"Red Hat Enterprise Linux {major}"
        for minor in range(minor_start, minor_end + 1):
            tag_suffix = "-beta" if minor < 0 else f".{minor}"
            is_active = active if isinstance(active, bool) else minor in active
            parent = SystemRelease.objects.create(
                tag=f"{tag_prefix}{tag_suffix}",
                product=product,
                release=minor,
                active=is_active,
                parent=parent,
            )

    @classmethod
    def create_system_releases(cls):
        """Create system releases."""
        cls.create_rhel_system_releases(5, 0, 13, False)
        cls.create_rhel_system_releases(6, 0, 13, False)
        cls.create_rhel_system_releases(7, 0, 13, [2])
        cls.create_rhel_system_releases(8, 0, 8, True)
        cls.create_rhel_system_releases(9, -1, 2, True)
        SystemRelease.objects.create(
            tag="rhose",
            product="Red Hat OpenShift Enterprise",
            release=0,
            active=True,
            parent=None,
        )

    @staticmethod
    def create_mock_configs():
        """Create mock configurations."""
        MockConfig.objects.create(name="fedora-rawhide-x86_64", enabled=True)
        MockConfig.objects.create(name="eln-x86_64", enabled=True)
        MockConfig.objects.create(name="rhel-5-x86_64", enabled=True)
        MockConfig.objects.create(name="rhel-6-x86_64", enabled=True)
        MockConfig.objects.create(name="rhel-7-x86_64", enabled=True)
        MockConfig.objects.create(name="rhel-8-x86_64", enabled=True)
        MockConfig.objects.create(name="rhel-9-x86_64", enabled=True)
        MockConfig.objects.create(name="epel-4-x86_64", enabled=False)
        MockConfig.objects.create(name="epel-5-x86_64", enabled=False)
        MockConfig.objects.create(name="epel-6-x86_64", enabled=False)

    @staticmethod
    def create_rhel_tags(major, minor_start, minor_end):
        """
        Create RHEL tags.

        :param major: The major version of RHEL
        :param minor_start: The initial minor version
        :param minor_end: The final minor version

        Create the sequence of tags from ``RHEL-{major}.{minor_start}`` to
        ``RHEL-{major}.{minor_end}``, inclusive.
        """
        for minor in range(minor_start, minor_end + 1):
            mock = MockConfig.objects.get(name=f"rhel-{major}-x86_64")
            release = SystemRelease.objects.get(tag=f"rhel-{major}.{minor}")
            Tag.objects.create(
                name=f"RHEL-{major}.{minor}", mock=mock, release=release
            )

    @classmethod
    def create_tags(cls):
        """Create tags."""
        cls.create_rhel_tags(8, 0, 8)
        cls.create_rhel_tags(9, 0, 2)

    @staticmethod
    def create_packages():
        """
        Create packages.

        Create the sequence of dummy packages from ``pkgA`` to ``pkgZ``,
        inclusive.
        """
        for offset in range(0, ord("Z") - ord("A") + 1):
            Package.objects.create(
                name=f'pkg{chr(ord("A") + offset)}',
                blocked=False,
                priority_offset=0,
            )

    @classmethod
    def mock_submit_scan(cls, **opts):
        """
        Mock the submit scan operation.

        :param opts: The submit scan operation options, see below
        :return: the scan binding

        Options to this method are the same as
        :meth:`~.TestDataMixin.create_scan` options plus the option ``state``
        that denotes the outcome of the scanning (default is ``PASSED``).

        This method emulates database operations when a scan is submitted,
        started, and finished.
        """
        # Start scanning
        scan_binding = cls.mock_start_scan(**opts)

        # Increase the timer
        cls._now += cls.SCAN_DURATION

        # Finish scanning
        cls.mock_finish_scan(scan_binding, opts.get("state", "PASSED"))
        return scan_binding

    @classmethod
    def mock_resubmit_scan(cls, scan_binding, release, state="PASSED"):
        """
        Mock the resubmit scan operation.

        :param scan_binding: The scan binding of the child scan
        :param release: The release part of the new build's NVR
        :param state: The scanning outcome, see
            :data:`~osh.hub.scan.models.SCAN_TYPES`
        :return: the scan binding of the resubmitted scan

        This methods emulates database operations when a scan is resubmitted,
        started, and finished. In greater detail:

        #. From ``scan_binding``, determine child scan.
        #. From child scan, determine old build's NVR.
        #. Set release part of old build's NVR to ``release`` to get the NVR of
           the new build (for simplicity it is assumed that user only bumps
           the release part of NVR when resubmitting scan).
        #. Start the scanning of the new build. The new scan becomes the parent
           of the child (old) scan. Scan type, tag, username, and base of the
           new scan are inherited from its child.
        #. Increase the timer about scan duration.
        #. Finish the new scan.
        """
        child_scan = scan_binding.scan
        child_nvr_parts = parse_nvr(child_scan.nvr)

        new_scan_binding = cls.mock_start_scan(
            scan_type=child_scan.scan_type,
            nvr=(
                f'{child_nvr_parts["name"]}-{child_nvr_parts["version"]}'
                f"-{release}"
            ),
            tag=child_scan.tag,
            username=child_scan.username,
            base=child_scan.base,
        )
        child_scan.parent = new_scan_binding.scan
        child_scan.save()

        cls._now += cls.SCAN_DURATION

        cls.mock_finish_scan(new_scan_binding, state)
        return new_scan_binding

    @classmethod
    def mock_start_scan(cls, **opts):
        """
        Mock the start scan operation.

        :param opts: Options, see :meth:`~.TestDataMixin.create_scan`
        :return: the scan binding

        Emulates database operations when a scan is started.
        """
        scan = cls.create_scan(**opts)
        task = Task.objects.create(
            owner=scan.username,
            worker=cls.worker,
            state=TASK_STATES["OPEN"],
            label=opts["nvr"],
            method="DummyMethod",
            arch=cls.arch,
            channel=cls.channel,
            dt_created=scan.date_submitted,
            dt_started=scan.date_submitted,
        )
        cls.worker.save()
        scan_binding = ScanBinding.objects.create(task=task, scan=scan)
        return scan_binding

    @classmethod
    def mock_finish_scan(cls, scan_binding, state="PASSED"):
        """
        Mock the finish scan operation.

        :param scan_binding: The scan binding
        :param state: The scanning outcome, see
            :data:`~osh.hub.scan.models.SCAN_TYPES`

        Emulates database operations when the scan is finished.
        """
        scan = scan_binding.scan
        task = scan_binding.task

        # Create the result
        result = Result()
        result.lines = 1024
        result.scanning_time = cls.SCAN_DURATION.seconds
        result.date_submitted = cls._now
        result.save()
        result.analyzers.add(cls.pylint, cls.flake8, cls.cppcheck)
        result.save()

        # Finish the task and inform the worker
        task.state = TASK_STATES["CLOSED"]
        task.dt_finished = cls._now
        task.save()
        cls.worker.save()

        # Finish the scan
        scan.state = SCAN_STATES[state]
        scan.last_access = cls._now
        scan.save()

        # Update the scan binding with the result
        scan_binding.result = result
        scan_binding.save()

    @classmethod
    def create_scan(cls, **opts):
        """
        Create a scan data object.

        :param opts: Options, see below
        :return: the scan data object

        Options to this method are:

        * ``nvr`` (mandatory) -- the name-version-release of the build
        * ``scan_type`` (optional) -- the scan type (default ``ERRATA``)
        * ``base`` (optional) -- the base scan (default none)
        * ``tag`` (mandatory) -- the tag
        * ``username`` (mandatory) -- the username
        * ``enabled`` (optional) -- is the scan enabled? (default true)

        If ``scan_type``, ``base``, ``tag``, and ``username`` are :class:`str`
        objects, they are converted to proper data objects as follows:

        * ``scan_type`` is converted to the integer using the
          :data:`~osh.hub.scan.models.SCAN_TYPES` mapping
        * ``base`` is searched for under the ``nvr`` key in the
          :class:`~osh.hub.scan.models.Scan` database table
        * ``tag`` is searched for under the ``name`` key in the
          :class:`~osh.hub.scan.models.Tag` database table
        * ``username`` is searched for under the ``username`` key in the
          :class:`~kobo.django.auth.models.User` database table
        """
        scan_type = opts.get("scan_type", "ERRATA")
        if isinstance(scan_type, str):
            scan_type = SCAN_TYPES[scan_type]
        base = opts.get("base")
        if isinstance(base, str):
            base = Scan.objects.get(nvr=base)
        tag = opts["tag"]
        if isinstance(tag, str):
            tag = Tag.objects.get(name=tag)
        username = opts["username"]
        if isinstance(username, str):
            username = User.objects.get(username=username)

        return Scan.objects.create(
            nvr=opts["nvr"],
            scan_type=scan_type,
            state=SCAN_STATES["INIT"],
            base=base,
            tag=tag,
            username=username,
            last_access=cls._now,
            date_submitted=cls._now,
            enabled=opts.get("enabled", True),
            package=Package.objects.get(name=parse_nvr(opts["nvr"])["name"]),
            parent=None,
        )

    @classmethod
    def create_scans(cls):
        """
        Create several scans.

        Scans created by this method are::

            pkgQ-1.0.0-1.el9 RHEL-9.1 user1 (PASSED)
            ...
            pkgQ-1.0.0-20.el9 RHEL-9.1 user1 (PASSED)

            pkgP-1.1.1-1 None user1 (INIT)

            pkgA-1.2-1.el8 RHEL-8.6 user1 (PASSED)

            pkgA-1.2-2.el8 RHEL-8.6 user1 (PASSED)  Base: pkgA-1.2-1.el8
             |
             +-- pkgA-1.2-3.el8 RHEL-8.6 user1 (PASSED)
                  |
                  +-- pkgA-1.2-4.el8 RHEL-8.6 user1 (NEEDS_INSPECTION)

            pkgA-1.2-5.el8 RHEL-8.6 user1 (PASSED)  Base: pkgA-1.2-4.el8
             |
             +-- pkgA-1.2-6.el8 RHEL-8.6 user1 (NEEDS_INSPECTION)
        """
        # Add some "filling" to bring pagination into effect
        for i in range(0, 20):
            cls.mock_submit_scan(
                nvr=f"pkgQ-1.0.0-{i+1}.el9", tag="RHEL-9.1", username="user1"
            )

        # Add a dummy scan with no parent, base, tag, and scan binding
        cls.create_scan(nvr="pkgP-1.1.1-1", tag=None, username="user1")

        # Create a base scan
        cls.mock_submit_scan(
            nvr="pkgA-1.2-1.el8", tag="RHEL-8.6", username="user1"
        )

        # Create a chain of scans with pkgA-1.2-1.el8 as the base
        scan_binding = cls.mock_submit_scan(
            nvr="pkgA-1.2-2.el8",
            tag="RHEL-8.6",
            username="user1",
            base="pkgA-1.2-1.el8",
        )
        scan_binding = cls.mock_resubmit_scan(scan_binding, "3.el8")
        scan_binding = cls.mock_resubmit_scan(
            scan_binding, "4.el8", "NEEDS_INSPECTION"
        )

        # Create an another chain of scans with pkgA-1.2-4.el8 as the base
        scan_binding = cls.mock_submit_scan(
            nvr="pkgA-1.2-5.el8",
            tag="RHEL-8.6",
            username="user1",
            base=scan_binding.scan,
        )
        cls.mock_resubmit_scan(scan_binding, "6.el8", "NEEDS_INSPECTION")
