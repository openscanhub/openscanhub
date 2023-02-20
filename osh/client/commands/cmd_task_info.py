import sys

import osh.client


class Task_Info(osh.client.CovScanCommand):
    """display info about provided task"""
    enabled = True
    admin = False  # admin type account required

    def options(self):
        # specify command usage
        # normalized name contains a lower-case class name with underscores
        # converted to dashes
        self.parser.usage = "%%prog %s <task_id>" % \
            self.normalized_name
        self.parser.epilog = "exit status is set to 1, if the task is not \
found"

    def run(self, *args, **kwargs):
        # local_conf = get_conf(self.conf)

        username = kwargs.pop("username", None)
        password = kwargs.pop("password", None)

        if len(args) != 1:
            self.parser.error("please specify exactly one task ID")
        task_id = args[0]

        # login to the hub
        self.set_hub(username, password)

        task_info = self.hub.scan.get_task_info(task_id)

        if task_info:
            for key, value in task_info.items():
                if key == 'args':
                    print('args:')
                    for a_k, a_v in value.items():
                        print("%s%s = %s" % (' ' * 4, a_k, a_v))
                else:
                    print("%s = %s" % (key, value))
        else:
            print("There is no info about the task. It doesn't exist most \
likely.")
            sys.exit(1)
        sys.exit(0)
