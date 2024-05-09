import io
import optparse
import unittest
from unittest.mock import MagicMock, patch

from osh.client.commands.cmd_list_profiles import List_Profiles


class TestListProfilesCommand(unittest.TestCase):
    def setUp(self):
        # Mocking the parser and its methods
        parser = optparse.OptionParser()
        parser.add_option = MagicMock()
        parser.error = MagicMock()

        self.command = List_Profiles(parser=parser)
        self.command.hub = MagicMock()  # Mocking the hub connection
        self.command.container = MagicMock()
        self.command.normalized_name = "list-profiles"
        self.command.hub.scan.list_profiles.return_value = [
            {"name": "default", "description": "Default profile"},
            {"name": "custom", "description": "Custom profile"}
        ]

    def test_options(self):
        self.command.options()
        assert self.command.parser.usage == f"%prog {self.command.normalized_name}"
        assert self.command.parser.epilog == (
            "List of predifned scanning profiles. "
            "These profiles serve as predefined scanning environments. "
            "One scanning profile could be for C, another for python, shell..."
        )

    def test_list_profiles(self):
        with patch('sys.stdout', new=io.StringIO()) as fake_output:
            self.command.stdout = fake_output
            self.command.run()

        output_lines = fake_output.getvalue().split("\n")
        self.assertEqual(output_lines[0], "NAME                 DESCRIPTION")
        self.assertEqual(output_lines[1], "default              Default profile")
        self.assertEqual(output_lines[2], "custom               Custom profile")
