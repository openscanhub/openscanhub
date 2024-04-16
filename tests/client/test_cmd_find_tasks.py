import copy
import unittest
from io import StringIO
from optparse import OptionParser
from unittest.mock import MagicMock, patch

from osh.client.commands.cmd_find_tasks import Find_Tasks


class TestFindTasksCommand(unittest.TestCase):
    def setUp(self):
        # Mocking the parser and its methods
        parser = OptionParser()
        parser.add_option = MagicMock()
        parser.add_option("-r", "--regex", action="store_true", default=False)

        self.command = Find_Tasks(parser=parser)
        self.command.hub = MagicMock()  # Mocking the hub connection
        self.command.container = MagicMock()
        self.command.normalized_name = "find-tasks"
        # Populate default keyword arguments based on options in `Find_Tasks`
        self.default_kwargs = {
            "nvr": False,
            "regex": False,
            "package": False,
            "comment": False,
            "latest": False,
            "states": None
        }

    def test_options(self):
        self.command.options()
        assert self.command.parser.usage == f"%prog {self.command.normalized_name} [options] <query_string>"
        assert self.command.parser.epilog == (
            "without '-l' option, newest task is at the "
            "beginning of a list, unfinished tasks are at the end; you should pick one of "
            "these options: --regex, --package, --comment, --nvr"
        )

    def get_updated_kwargs(self, kwargs):
        # We use deepcopy here because `states` field is mutable
        data = copy.deepcopy(self.default_kwargs)
        data.update(kwargs)
        return data

    def test_basic_query(self):
        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.command.hub.scan.find_tasks.return_value = [3, 2, 1]
            self.command.run(("query_string"), **self.default_kwargs)
            retval = list(filter(None, fake_out.getvalue().split("\n")))
            self.assertEqual(["3", "2", "1"], retval)

    def test_basic_query_latest(self):
        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.command.hub.scan.find_tasks.return_value = [3, 2, 1]
            kwargs = self.get_updated_kwargs({"latest": True})
            self.command.run(("query_string"), **kwargs)
            retval = fake_out.getvalue().strip()
            self.assertEqual("3", retval)

    def test_query_by_regex(self):
        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.command.hub.scan.find_tasks.return_value = [3, 2, 1]
            kwargs = self.get_updated_kwargs({"regex": True})
            self.command.run(("query_string"), **kwargs)
            retval = list(filter(None, fake_out.getvalue().split("\n")))
            self.assertEqual(["3", "2", "1"], retval)

    def test_query_by_package(self):
        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.command.hub.scan.find_tasks.return_value = [3, 2, 1]
            kwargs = self.get_updated_kwargs({"package": True})
            self.command.run(("query_string"), **kwargs)
            retval = list(filter(None, fake_out.getvalue().split("\n")))
            self.assertEqual(["3", "2", "1"], retval)

    def test_query_by_comment(self):
        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.command.hub.scan.find_tasks.return_value = [2, 1]
            kwargs = self.get_updated_kwargs({"comment": True})
            self.command.run(("query_string"), **kwargs)
            retval = list(filter(None, fake_out.getvalue().split("\n")))
            self.assertEqual(["2", "1"], retval)

    def test_query_by_states(self):
        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.command.hub.scan.find_tasks.return_value = [2, 1]
            kwargs = self.get_updated_kwargs({"states": ["FAILED", "CLOSED"]})
            self.command.run(("query_string"), **kwargs)
            retval = list(filter(None, fake_out.getvalue().split("\n")))
            self.assertEqual(["2", "1"], retval)

    def test_query_by_invalid_states(self):
        with patch.object(self.command.parser, 'error') as mock_error:
            # Simulate the behavior of parser.error
            mock_error.side_effect = SystemExit(1)
            kwargs = self.get_updated_kwargs({"states": ["FOO", "BAR", "CLOSED"]})
            with self.assertRaises(SystemExit) as cm:
                self.command.run(("query_string"), **kwargs)
            self.assertEqual(cm.exception.code, 1)
            mock_error.assert_called_once()
            error_message = mock_error.call_args[0][0]
            # Expected output should be that the invalid states are being printed
            self.assertEqual("Invalid state(s) specified: FOO, BAR.", error_message)

    def test_no_tasks_found(self):
        with patch('sys.stderr', new=StringIO()) as fake_err:
            self.command.hub.scan.find_tasks.return_value = []
            with self.assertRaises(SystemExit) as cm:
                self.command.run(("query_string"), **self.default_kwargs)
            self.assertEqual(cm.exception.code, 1)
            self.assertEqual("No tasks found for the given query.", fake_err.getvalue().strip())

    def test_raises_error_with_no_query_string(self):
        with patch('sys.stderr', new=StringIO()) as fake_err:
            with self.assertRaises(SystemExit) as cm:
                self.command.run(**self.default_kwargs)
            self.assertEqual(cm.exception.code, 2)
            error_message = fake_err.getvalue()
            self.assertIn("Usage:", error_message)
            self.assertIn("error: please specify exactly one query string", error_message)
