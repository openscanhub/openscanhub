import io
import unittest
from unittest.mock import patch

from osh.client.commands.cmd_list_profiles import List_Profiles
from osh.tests.client import OSHCLITestBase


class TestListProfilesCommand(OSHCLITestBase, unittest.TestCase):
    def setUp(self):
        self.setup_cmd(List_Profiles)

        self.command.hub.scan.list_profiles.return_value = [
            {"name": "default", "description": "Default profile"},
            {"name": "custom", "description": "Custom profile"}
        ]

    # overwrite since it's having slightly different usage/epilog
    def test_options(self):
        self.command.options()
        assert self.command.parser.usage == f"%prog {self.command.normalized_name}"
        assert self.command.parser.epilog == (
            "List of predifned scanning profiles. "
            "These profiles serve as predefined scanning environments. "
            "One scanning profile could be for C, another for python, shell..."
        )

    def test_list_profiles(self):
        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            self.command.stdout = fake_out
            self.command.run()

        output_lines = fake_out.getvalue().split("\n")
        self.assertEqual(output_lines[0], "NAME                 DESCRIPTION")
        self.assertEqual(output_lines[1], "default              Default profile")
        self.assertEqual(output_lines[2], "custom               Custom profile")
