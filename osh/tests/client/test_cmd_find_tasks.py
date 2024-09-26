import copy
import io
import unittest
from unittest.mock import patch

from osh.client.commands.cmd_find_tasks import Find_Tasks
from osh.tests.client import OSHCLITestBase


class TestFindTasksCommand(OSHCLITestBase, unittest.TestCase):
    def setUp(self):
        self.setup_cmd(Find_Tasks)
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

    def get_updated_kwargs(self, **kwargs):
        # We use deepcopy here because `states` field is mutable
        data = copy.deepcopy(self.default_kwargs)
        data.update(kwargs)
        return data

    def test_query_cases(self):
        test_cases = [
            ({"latest": False}, [3, 2, 1], ["3", "2", "1"]),
            ({"latest": True}, [3, 2, 1], ["3"]),
            ({"regex": True}, [3, 2, 1], ["3", "2", "1"]),
            ({"package": True}, [3, 2, 1], ["3", "2", "1"]),
            ({"comment": True}, [2, 1], ["2", "1"]),
            ({"states": ["FAILED", "CLOSED"]}, [2, 1], ["2", "1"]),
        ]

        for kwargs, return_value, expected in test_cases:
            with patch('sys.stdout', new=io.StringIO()) as fake_out:
                self.command.hub.scan.find_tasks.return_value = return_value
                self.command.run(("query_string"), **self.get_updated_kwargs(**kwargs))
                retval = list(filter(None, fake_out.getvalue().split("\n")))
                self.assertEqual(expected, retval)

    def test_query_invalid_states_or_no_tasks_found(self):
        with patch.object(self.command.parser, 'error') as mock_error, \
             patch('sys.stderr', new=io.StringIO()) as fake_err:

            # Test for invalid states
            mock_error.side_effect = SystemExit(1)
            kwargs = self.get_updated_kwargs(**{"states": ["FOO", "BAR", "CLOSED"]})
            with self.assertRaises(SystemExit) as cm:
                self.command.run(("query_string"), **kwargs)
            self.assertEqual(cm.exception.code, 1)
            mock_error.assert_called_once()
            error_message = mock_error.call_args[0][0]
            self.assertEqual("Invalid state(s) specified: FOO, BAR.", error_message)

            # Test for no tasks found
            self.command.hub.scan.find_tasks.return_value = []
            with self.assertRaises(SystemExit) as cm:
                self.command.run(("query_string"), **self.default_kwargs)
            self.assertEqual(cm.exception.code, 1)
            self.assertEqual("No tasks found for the given query.", fake_err.getvalue().strip())

    def test_raises_error_with_no_query_string(self):
        with patch('sys.stderr', new=io.StringIO()) as fake_err:
            with self.assertRaises(SystemExit) as cm:
                self.command.run(**self.default_kwargs)
            self.assertEqual(cm.exception.code, 2)
            error_message = fake_err.getvalue()
            self.assertIn("Usage:", error_message)
            self.assertIn("error: please specify exactly one query string", error_message)
