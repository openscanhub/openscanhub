# -*- coding: utf-8 -*-
from covscanhub.scan.models import AppSettings

AppSettings.objects.create(
    key="DEFAULT_SCANNING_COMMAND",
    value="su - coverity -c 'cd %(tmp_dir)s ; cov-mockbuild -c %(mock_profile)s %(srpm_path)s --security --concurrency'"
)

