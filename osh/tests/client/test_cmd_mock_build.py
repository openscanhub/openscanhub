import io
import unittest
from unittest.mock import patch

from osh.client.commands.cmd_mock_build import Mock_Build
from osh.tests.client import OSHCLITestBase


class TestMockBuild(OSHCLITestBase, unittest.TestCase):
    def setUp(self):
        self.setup_cmd(Mock_Build)

    def test_submit_task(self):
        self.command.hub.scan.mock_build.return_value = 0
        options = {
            "mock_config": "rhel-7-x86_64",
            "comment": "my comment"
        }
        self.command.submit_task(options)
        self.command.hub.scan.mock_build.assert_called_once()

    @patch('osh.client.commands.cmd_build.Base_Build.prepare_task_options')
    def test_prepare_task_options_valid(self, mock_super_prepare_task_options):
        valid_cases = [
            (["/path/to/foo.src.rpm"], {}),
            ([], {"nvr": "foo-1.0.0-1.el8"}),
            ([], {"git_url": "https://example.com/repo.git"}),
        ]

        for args, kwargs in valid_cases:
            self.command.prepare_task_options(args, kwargs)

    @patch('osh.client.commands.cmd_build.Base_Build.prepare_task_options')
    def test_prepare_task_options_invalid(self, mock_super_prepare_task_options):
        # simulate args/kwargs that trigger a failure for
        # "exactly one of SRPM, NVR, or dist-git URL must be provided"
        invalid_cases = [
            ([], {"nvr": "foo-1.0.0-1.el8", "git_url": "https://example.com/repo.git"}),
            (["/path/to/foo.src.rpm"], {"nvr": "foo-1.0.0-1.el8"}),
            (["/path/to/foo.src.rpm"], {"git_url": "https://example.com/repo.git"}),
            ([], {}),
        ]

        for args, kwargs in invalid_cases:
            with self.assertRaises(SystemExit):
                with patch('sys.stderr', new=io.StringIO()) as fake_err:
                    self.command.prepare_task_options(args, kwargs)
                    output = fake_err.getvalue()
                    self.assertIn("error: please specify either SRPM or NVR or dist-git URL", output)
