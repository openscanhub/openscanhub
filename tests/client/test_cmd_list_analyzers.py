import io
import optparse
import unittest
from unittest.mock import MagicMock, patch

from osh.client.commands.cmd_list_analyzers import List_Analyzers


class TestListAnalyzers(unittest.TestCase):
    def setUp(self):
        self.mock_option_parser = MagicMock(spec=optparse.OptionParser)
        self.mock_hub = MagicMock()
        self.mock_hub.scan = MagicMock()
        # Initialize list of analyzers based on output from the OpenScanHub API
        self.list_analyzers_response = [
            {"analyzer__name": "clang", "version": "1.0", "cli_long_command": "clang"},
            {"analyzer__name": "cppcheck", "version": "2.0", "cli_long_command": "cppcheck"}
        ]
        self.mock_hub.scan.list_analyzers.return_value = self.list_analyzers_response

        self.command = List_Analyzers(parser=self.mock_option_parser)
        self.command.connect_to_hub = MagicMock()
        self.command.hub = self.mock_hub
        # crucial attribute to avoid a RecursionError raised from kobo.client.ClientCommand
        self.command.container = MagicMock()
        self.command.normalized_name = "list-analyzers"

    def test_options(self):
        self.command.options()
        assert self.command.parser.usage == "%prog list-analyzers [options] <args>"
        assert self.command.parser.epilog == (
            "list all available static analyzers, some of them in various versions; "
            "list contains command line arguments how to enable particular analyzer "
            "(e.g. '--analyzer clang' for clang)"
        )

    def test_list_analyzers_empty_response(self):
        self.command.hub.scan.list_analyzers.return_value = []

        with patch('sys.stdout', new=io.StringIO()) as stdout:
            self.command.stdout = stdout
            self.command.run()

        expected_output = [
            "NAME                 VERSION              ANALYZER_ID",
            "Example of usage: '--analyzer=clang,cppcheck'"
        ]
        actual_output = self.command.stdout.getvalue().strip()
        for line in expected_output:
            self.assertIn(line, actual_output)

    def test_list_analyzers(self):
        output = io.StringIO()
        self.command.stdout = output

        with patch('sys.stdout', new=io.StringIO()) as stdout:
            self.command.stdout = stdout
            self.command.run()

        expected_output = [
            "NAME                 VERSION              ANALYZER_ID",
            "clang                1.0                  clang",
            "cppcheck             2.0                  cppcheck",
            "Example of usage: '--analyzer=clang,cppcheck'"
        ]
        actual_output = self.command.stdout.getvalue().strip()
        for line in expected_output:
            self.assertIn(line, actual_output)
