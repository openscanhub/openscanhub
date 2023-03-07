import osh.client


class List_Profiles(osh.client.OshCommand):
    """list available scanning profiles"""
    enabled = True
    admin = False  # admin type account required

    def options(self):
        self.parser.usage = f"%prog {self.normalized_name}"
        self.parser.epilog = "List of predifned scanning profiles. " \
                             "These profiles serve as predefined scanning environments. " \
                             "One scanning profile could be for C, another for python, shell..."

    def run(self, *args, **kwargs):
        username = kwargs.pop("username", None)
        password = kwargs.pop("password", None)

        # login to the hub
        self.set_hub(username, password)

        format = "%-20s %s"
        columns = ("NAME", "DESCRIPTION")
        print(format % columns)
        available_profiles = self.hub.scan.list_profiles()
        for i in available_profiles:
            print(format % (i["name"], i['description']))
