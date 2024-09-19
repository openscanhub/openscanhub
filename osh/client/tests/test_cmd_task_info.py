import io
import json
import unittest
from unittest.mock import patch

from osh.client.commands.cmd_task_info import Task_Info
from osh.client.tests import OSHCLITestBase


class TestTaskInfoCommand(OSHCLITestBase, unittest.TestCase):
    def setUp(self):
        self.setup_cmd(Task_Info)

    def test_options(self):
        self.command.options()
        self.assertEqual(self.command.parser.usage, f"%prog {self.command.normalized_name} <task_id>")
        self.assertEqual(self.command.parser.epilog, "exit status is set to 1, if the task is not found")

    # runs successfully with valid task ID
    def test_runs_successfully_with_valid_task_id_and_no_json_flag(self):
        args = ['123']
        kwargs = {}
        self.command.hub.scan.get_task_info.return_value = {
            "id": 123456, "owner": "admin", "state": 1,
            "args": {"build": {"nvr": "foo-1.0.0-1.el8", "koji_profile": "brew"}}
        }

        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            self.command.run(*args, **kwargs)
            expected_output = (
                "id = 123456\n"
                "owner = admin\n"
                "state = 1\n"
                "args:\n"
                "    build = {'nvr': 'foo-1.0.0-1.el8', 'koji_profile': 'brew'}\n"
            )
            output = fake_out.getvalue()
            self.assertEqual(expected_output, output)
            # verify that args are being unpacked
            self.assertNotIn("args: {", output)

    # runs successfully with valid task ID and json flag
    def test_runs_successfully_with_valid_task_id_and_json(self):
        args = ['123']
        kwargs = {"json": True}
        self.command.hub.scan.get_task_info.return_value = {
            "id": 123456, "owner": "admin", "state": 1,
            "args": {"build": {"nvr": "foo-1.0.0-1.el8", "koji_profile": "brew"}}
        }

        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            self.command.run(*args, **kwargs)
            output = fake_out.getvalue()
            try:
                json.loads(output)
            except json.JSONDecodeError as e:
                self.fail(f"Unexpected json output found: {e}")

    def test_no_task_info_found(self):
        args = ["123456"]
        self.command.hub.scan.get_task_info.return_value = None
        with patch('sys.stderr', new=io.StringIO()) as fake_err:
            with self.assertRaises(SystemExit) as cm:
                self.command.run(*args)
            # an explicit exit code specified in `cmd_task_info`
            self.assertEqual(cm.exception.code, 1)
            output = fake_err.getvalue()
            self.assertIn("There is no info about the task.", output)

    def test_raises_error_with_invalid_number_of_arguments(self):
        with patch('sys.stderr', new=io.StringIO()) as fake_err:
            with self.assertRaises(SystemExit) as cm:
                self.command.run()
            self.assertEqual(cm.exception.code, 2)
            error_message = fake_err.getvalue()
            self.assertIn("Usage:", error_message)
            self.assertIn("error: please specify exactly one task ID", error_message)

    def test_raise_error_with_invalid_task_id(self):
        with patch('sys.stderr', new=io.StringIO()) as fake_err:
            with self.assertRaises(SystemExit) as cm:
                self.command.run("invalid-task-id")
            self.assertEqual(cm.exception.code, 2)
            error_message = fake_err.getvalue()
            self.assertIn("error: 'invalid-task-id' is not a number", error_message)
