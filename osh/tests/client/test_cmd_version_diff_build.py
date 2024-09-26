import io
import unittest
from unittest.mock import MagicMock, patch

from osh.client.commands.cmd_version_diff_build import Version_Diff_Build
from osh.tests.client import OSHCLITestBase


class VersionDiffBuild(OSHCLITestBase, unittest.TestCase):
    def setUp(self):
        self.setup_cmd(Version_Diff_Build)

    def test_prepare_task_options_invalid_cases(self):
        test_cases = [
            ([], {}, "Please specify both builds or SRPMs."),
            ((), {"base_nvr": "base_nvr", "base_srpm": "base_srpm"}, "Choose exactly one option (--base-nvr, --base-srpm), not both of them."),
            ((), {"nvr": "nvr"}, "You haven't specified base."),
            ((), {"base_nvr": "base_nvr"}, "You haven't specified target."),
            ((), {"nvr": "nvr", "srpm": "srpm"}, "Choose exactly one option (--nvr, --srpm), not both of them."),
        ]

        for args, kwargs, error_message in test_cases:
            with patch('sys.stderr', new=io.StringIO()) as fake_err:
                with self.assertRaises(SystemExit) as cm:
                    self.command.prepare_task_options(args, kwargs)
                self.assertEqual(cm.exception.code, 2)
                output = fake_err.getvalue()
                self.assertIn(error_message, output)

    @patch('osh.client.commands.cmd_build.Base_Build.prepare_task_options')
    def test_prepare_task_options_with_no_package(self, mock_super_prepare_task_options):
        self.command.check_build = MagicMock()
        self.command.check_build.return_value = {}
        kwargs = {"config": "myconfig", "nvr": "nvr", "base_nvr": "base_nvr"}
        self.command.prepare_task_options((), kwargs)
        mock_super_prepare_task_options.assert_called_once()

    def test_submit_task(self):
        self.command.hub.scan.create_user_diff_task.return_value = 0
        options = {
            "mock_config": "rhel-7-x86_64",
            "comment": "my comment"
        }
        self.command.submit_task(options)
        self.command.hub.scan.create_user_diff_task.assert_called_once()
