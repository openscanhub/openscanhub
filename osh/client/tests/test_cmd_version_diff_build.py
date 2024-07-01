import optparse
import unittest
from io import StringIO
from unittest.mock import MagicMock, patch

from osh.client.commands.cmd_version_diff_build import Version_Diff_Build


class VersionDiffBuild(unittest.TestCase):
    def setUp(self):
        parser = optparse.OptionParser()
        parser.add_option = MagicMock()
        self.command = Version_Diff_Build(parser=parser)
        self.command.hub = MagicMock()
        self.command.container = MagicMock()
        self.command.normalized_name = "version-diff-build"

    @patch('osh.client.commands.cmd_build.Base_Build.options')
    def test_options(self, mock_super_options):
        self.command.options()
        mock_super_options.assert_called_once()
        self.assertEqual(self.command.parser.usage, "%prog [options]")

    def test_prepare_task_options_with_empty_kwargs(self):
        with patch('sys.stderr', new=StringIO()) as fake_err:
            with self.assertRaises(SystemExit) as cm:
                self.command.prepare_task_options([], {})
            self.assertEqual(cm.exception.code, 2)
            output = fake_err.getvalue()
            error_message = "Please specify both builds or SRPMs."
            self.assertIn(error_message, output)

    def test_prepare_task_options_with_both_bases(self):
        with patch('sys.stderr', new=StringIO()) as fake_err:
            args = []
            kwargs = {"base_nvr": "base_nvr", "base_srpm": "base_srpm"}
            with self.assertRaises(SystemExit) as cm:
                self.command.prepare_task_options(args, kwargs)
            self.assertEqual(cm.exception.code, 2)
            output = fake_err.getvalue()
            error_message = "Choose exactly one option (--base-nvr, --base-srpm), not both of them."
            self.assertIn(error_message, output)

    def test_prepare_task_options_with_no_base(self):
        kwargs = {"nvr": "nvr"}
        with patch('sys.stderr', new=StringIO()) as fake_err:
            with self.assertRaises(SystemExit) as cm:
                self.command.prepare_task_options((), kwargs)
            self.assertEqual(cm.exception.code, 2)
            output = fake_err.getvalue()
            error_message = "You haven't specified base."
            self.assertIn(error_message, output)

    def test_prepare_task_options_with_no_target(self):
        kwargs = {"base_nvr": "base_nvr"}
        with patch('sys.stderr', new=StringIO()) as fake_err:
            with self.assertRaises(SystemExit) as cm:
                self.command.prepare_task_options((), kwargs)
            self.assertEqual(cm.exception.code, 2)
            output = fake_err.getvalue()
            error_message = "You haven't specified target."
            self.assertIn(error_message, output)

    def test_prepare_task_options_with_both_nvr_and_srpm(self):
        with patch('sys.stderr', new=StringIO()) as fake_err:
            kwargs = {"nvr": "nvr", "srpm": "srpm"}
            with self.assertRaises(SystemExit) as cm:
                self.command.prepare_task_options((), kwargs)
            self.assertEqual(cm.exception.code, 2)
            output = fake_err.getvalue()
            error_message = "Choose exactly one option (--nvr, --srpm), not both of them."
            self.assertIn(error_message, output)

    @patch('osh.client.commands.cmd_build.Base_Build.prepare_task_options')
    def test_prepare_task_options_with_no_package(self, mock_super_prepare_task_options):
        mock_super_prepare_task_options.return_value = {}
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
