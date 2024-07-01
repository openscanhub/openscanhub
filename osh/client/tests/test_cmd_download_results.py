import optparse
import unittest
from io import StringIO
from unittest.mock import MagicMock, patch

from osh.client.commands.cmd_download_results import Download_Results


class TestDownloadResults(unittest.TestCase):
    def setUp(self):
        parser = optparse.OptionParser()
        parser.add_option = MagicMock()

        self.command = Download_Results(parser=parser)
        self.command.hub = MagicMock()
        self.command.container = MagicMock()
        self.command.normalized_name = "download-results"

    def test_options(self):
        self.command.options()
        assert self.command.parser.usage == f"%prog {self.command.normalized_name} [options] task_id [task_id...]"

    def test_run_with_no_task_id(self):
        with patch('sys.stderr', new=StringIO()) as fake_err:
            tasks = []
            with self.assertRaises(SystemExit) as cm:
                self.command.run(*tasks)
            self.assertEqual(cm.exception.code, 2)
            output = fake_err.getvalue()
            self.assertIn("no task ID specified", output)

    def test_run_with_non_digit_task_id(self):
        with patch('sys.stderr', new=StringIO()) as fake_err:
            tasks = ['1', '2', 'n']
            with self.assertRaises(SystemExit) as cm:
                self.command.run(*tasks)
            self.assertEqual(cm.exception.code, 2)
            output = fake_err.getvalue()
            self.assertIn("'n' is not a number", output)

    def test_run_with_none_existent_dir(self):
        with patch('sys.stderr', new=StringIO()) as fake_err:
            tasks = ['1', '2']
            kwargs = {"dir": "/path/to/non-existent-dir/"}
            with self.assertRaises(SystemExit) as cm:
                self.command.run(*tasks, **kwargs)
            self.assertEqual(cm.exception.code, 2)
            output = fake_err.getvalue()
            self.assertIn("provided directory does not exist", output)

    @patch("os.path.isdir")
    def test_run_failed(self, fake_isdir):
        fake_isdir.return_value = True
        self.command.connect_to_hub = MagicMock()
        tasks = ['1', '2']
        kwargs = {"dir": "/path/to/non-existent-dir/"}

        with patch('sys.stderr', new=StringIO()) as fake_err:
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
