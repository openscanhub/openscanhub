import io
import unittest
from unittest.mock import patch

from osh.client.commands.cmd_list_analyzers import List_Analyzers
from osh.client.tests import OSHCLITestBase


class TestListAnalyzers(OSHCLITestBase, unittest.TestCase):
    def setUp(self):
        self.setup_cmd(List_Analyzers)
        # Initialize list of analyzers based on output from the OpenScanHub API
        self.list_analyzers_response = [
            {"analyzer__name": "clang", "version": "1.0", "cli_long_command": "clang"},
            {"analyzer__name": "cppcheck", "version": "2.0", "cli_long_command": "cppcheck"}
        ]
        self.command.hub.scan.list_analyzers.return_value = self.list_analyzers_response

    def test_list_analyzers_empty_response(self):
        self.command.hub.scan.list_analyzers.return_value = []

        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            self.command.run()

        expected_output = [
            "NAME                 VERSION              ANALYZER_ID",
            "Example of usage: '--analyzer=clang,cppcheck'"
        ]
        actual_output = fake_out.getvalue().strip()
        for line in expected_output:
            self.assertIn(line, actual_output)

    def test_list_analyzers(self):
        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            self.command.run()

        expected_output = [
            "NAME                 VERSION              ANALYZER_ID",
            "clang                1.0                  clang",
            "cppcheck             2.0                  cppcheck",
            "Example of usage: '--analyzer=clang,cppcheck'"
        ]
        actual_output = fake_out.getvalue().strip()
        for line in expected_output:
            self.assertIn(line, actual_output)
