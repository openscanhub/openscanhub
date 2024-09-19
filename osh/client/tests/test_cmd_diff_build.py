import io
import unittest
from unittest.mock import patch

from osh.client.commands.cmd_diff_build import Diff_Build
from osh.client.tests import OSHCLITestBase


class TestDiffBuild(OSHCLITestBase, unittest.TestCase):
    def setUp(self):
        self.setup_cmd(Diff_Build)

    @patch('osh.client.commands.cmd_diff_build.Base_Build.prepare_task_options')
    def test_prepare_task_options(self, mock_super_prepare_task_options):
        with patch('sys.stderr', new=io.StringIO()) as fake_err:
            # Error if no SRPM/NVR is specified
            args = []
            with self.assertRaises(SystemExit) as cm:
                self.command.prepare_task_options(args, {})
            self.assertEqual(cm.exception.code, 2)
            output = fake_err.getvalue()
            self.assertIn("please specify either SRPM or NVR", output)

            # Error if length of args is larger than 1
            args = ["srpm1", "srpm2"]
            with self.assertRaises(SystemExit) as cm:
                self.command.prepare_task_options(args, {})
            self.assertEqual(cm.exception.code, 2)
            output = fake_err.getvalue()
            self.assertIn("please specify exactly one SRPM", output)

        # valid args provided
        args = ["srpm1"]
        kwargs = {}
        self.command.prepare_task_options(args, kwargs)
        self.assertIn("srpm", kwargs)
        mock_super_prepare_task_options.assert_called_once()

    def test_submit_task(self):
        self.command.hub.scan.diff_build.return_value = 0
        options = {
            "mock_config": "rhel-7-x86_64",
            "comment": "my comment"
        }
        self.command.submit_task(options)
        self.command.hub.scan.diff_build.assert_called_once()
