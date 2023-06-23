from osh.client import OshCommand


class Base_Build(OshCommand):
    """Base class for build tasks that is not meant to be used on its own"""
    enabled = False

    def options(self):
        pass

    def run(self, *args, **kwargs):
        pass

    def submit_task(self, options):
        raise NotImplementedError
