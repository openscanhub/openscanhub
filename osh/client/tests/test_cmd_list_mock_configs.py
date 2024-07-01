import io
import optparse
import unittest
from unittest.mock import MagicMock, patch

from osh.client.commands.cmd_list_mock_configs import List_Mock_Configs


class TestListMockConfigs(unittest.TestCase):
    def setUp(self):
        self.mock_option_parser = MagicMock(spec=optparse.OptionParser)
        self.mock_hub = MagicMock()
        self.command = List_Mock_Configs(parser=self.mock_option_parser)
        self.command.connect_to_hub = MagicMock()
        self.command.hub = self.mock_hub
        self.command.hub.mock_config.all.return_value = [
            {"name": "rhel-6-x86_64", "enabled": False},
            {"name": "rhel-7-x86_64", "enabled": True},
            {"name": "rhel-8-x86_64", "enabled": True},
        ]
        # crucial attribute to avoid a RecursionError raised from kobo.client.ClientCommand
        self.command.container = MagicMock()
        self.command.normalized_name = "list-mock-configs"

    def test_options(self):
        self.command.options()
        assert self.command.parser.usage == f"%prog {self.command.normalized_name} [options] <args>"

    def test_list_mock_configs(self):
        with patch('sys.stdout', new=io.StringIO()) as stdout, \
             patch('sys.stderr', new=io.StringIO()) as stderr:
            self.command.stdout = stdout
            self.command.stderr = stderr
            self.command.run()
        expected_output = ["rhel-7-x86_64", "rhel-8-x86_64"]
        actual_output = self.command.stdout.getvalue().strip()
        # All enabled mock configs should be listed
        for line in expected_output:
            self.assertIn(line, actual_output)
        # Disabled mock config is not listed
        self.assertNotIn("rhel-6-x86_64", actual_output)
        err_output = self.command.stderr.getvalue().strip()
        self.assertEqual("NAME", err_output)
