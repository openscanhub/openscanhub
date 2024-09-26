import io
import unittest
from unittest.mock import patch

from osh.client.commands.cmd_list_mock_configs import List_Mock_Configs
from osh.tests.client import OSHCLITestBase


class TestListMockConfigs(OSHCLITestBase, unittest.TestCase):
    def setUp(self):
        self.setup_cmd(List_Mock_Configs)

        self.command.hub.mock_config.all.return_value = [
            {"name": "rhel-6-x86_64", "enabled": False},
            {"name": "rhel-7-x86_64", "enabled": True},
            {"name": "rhel-8-x86_64", "enabled": True},
        ]

    def test_list_mock_configs(self):
        with patch('sys.stdout', new=io.StringIO()) as fake_out, \
             patch('sys.stderr', new=io.StringIO()) as fake_err:
            self.command.run()

        expected_output = ["rhel-7-x86_64", "rhel-8-x86_64"]
        actual_output = fake_out.getvalue().strip().split('\n')

        # All enabled mock configs should be listed
        self.assertEqual(actual_output, expected_output)

        err_output = fake_err.getvalue().strip()
        self.assertEqual("NAME", err_output)
