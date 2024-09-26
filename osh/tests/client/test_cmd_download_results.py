import io
import unittest
from unittest.mock import MagicMock, patch

from osh.client.commands.cmd_download_results import Download_Results
from osh.tests.client import OSHCLITestBase


class TestDownloadResults(OSHCLITestBase, unittest.TestCase):
    def setUp(self):
        self.setup_cmd(Download_Results)

    def test_options(self):
        self.command.options()
        assert self.command.parser.usage == f"%prog {self.command.normalized_name} [options] task_id [task_id...]"

    def test_run_with_various_conditions(self):
        test_cases = [
            ([], "no task ID specified", {}),
            (['1', '2', 'n'], "'n' is not a number", {}),
            (['1', '2'], "provided directory does not exist", {"dir": "/path/to/non-exist-dir/"})
        ]

        for tasks, expected_output, kwargs in test_cases:
            with patch('sys.stderr', new=io.StringIO()) as fake_err:
                if not tasks:
                    with self.assertRaises(SystemExit) as cm:
                        self.command.run(*tasks)
                else:
                    with self.assertRaises(SystemExit) as cm:
                        self.command.run(*tasks, **kwargs)
                self.assertEqual(cm.exception.code, 2)
                output = fake_err.getvalue()
                self.assertIn(expected_output, output)

    @patch("os.path.isdir")
    def test_run_failed(self, fake_isdir):
        fake_isdir.return_value = True
        self.command.connect_to_hub = MagicMock()
        tasks = ['1', '2']
        kwargs = {"dir": "/path/to/non-existent-dir/"}

        with patch('sys.stderr', new=io.StringIO()) as fake_err:
            tasks = ['1', '2']
            kwargs = {"dir": "/path/to/non-existent-dir/"}
            self.command.hub.scan.get_task_info.return_value = False
            with self.assertRaises(SystemExit) as cm:
                self.command.run(*tasks, **kwargs)
            self.assertEqual(cm.exception.code, 1)
            output = fake_err.getvalue()
            for task_id in tasks:
                error_message = f"Task {task_id} does not exist!"
                self.assertIn(error_message, output)
