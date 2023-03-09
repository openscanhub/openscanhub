import osh.client


class List_Analyzers(osh.client.OshCommand):
    """list available versions of static analyzers"""
    enabled = True
    admin = False  # admin type account required

    def options(self):
        self.parser.usage = f"%prog {self.normalized_name} [options] <args>"
        self.parser.epilog = "list all available static analyzers, some of them in various versions;" + " list contains command line arguments how to enable particular analyzer " + "(e.g. '--analyzer clang' for clang)"

    def run(self, *args, **kwargs):
        # login to the hub
        self.connect_to_hub(kwargs)

        format = "%-20s %-20s %-25s"
        columns = ("NAME", "VERSION", "ANALYZER_ID")
        print(format % columns)
        available_analyzers = self.hub.scan.list_analyzers()
        for i in available_analyzers:
            print(format % (i["analyzer__name"], i['version'], i["cli_long_command"]))

        print("\nExample of usage: '--analyzer=clang,cppcheck'")
