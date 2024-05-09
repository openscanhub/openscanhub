import optparse
import unittest
from unittest.mock import MagicMock, patch

from osh.client.commands.cmd_mock_build import Mock_Build


class TestMockBuild(unittest.TestCase):
    def setUp(self):
        parser = optparse.OptionParser()
        parser.add_option = MagicMock()

        self.command = Mock_Build(parser=parser)
        self.command.hub = MagicMock()
        self.command.container = MagicMock()
        self.command.normalized_name = "mock-build"

    @patch('osh.client.commands.cmd_diff_build.Diff_Build.options')
    def test_options_method(self, mock_super_options):
        self.command.options()
        # Assert that the superclass method was called
        mock_super_options.assert_called_once()

    def test_submit_task(self):
        self.command.hub.scan.mock_build.return_value = 0
        options = {
            "mock_config": "rhel-7-x86_64",
            "comment": "my comment"
        }
        self.command.submit_task(options)
        self.command.hub.scan.mock_build.assert_called_once()
