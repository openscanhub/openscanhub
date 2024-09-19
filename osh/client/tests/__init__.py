import optparse
from unittest.mock import MagicMock

from kobo.client import ClientCommandContainer


class OSHCLITestBase():
    def setup_cmd(self, PluginCls):
        container = ClientCommandContainer(conf={})
        name = container.register_plugin(PluginCls)
        self.command = container[name](parser=optparse.OptionParser())

        self.command.hub = MagicMock()
        self.command.set_hub = MagicMock()

    def test_options(self):
        self.command.options()
        self.assertEqual(self.command.parser.usage,
                         f"%prog {self.command.normalized_name} [options] <args>")
