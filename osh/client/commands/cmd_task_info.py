import sys

import osh.client


class Task_Info(osh.client.OshCommand):
    """display info about provided task"""
    enabled = True
    admin = False  # admin type account required

    def options(self):
        # specify command usage
        # normalized name contains a lower-case class name with underscores
        # converted to dashes
        self.parser.usage = f"%prog {self.normalized_name} <task_id>"
        self.parser.epilog = "exit status is set to 1, if the task is not \
found"

    def run(self, *args, **kwargs):
        username = kwargs.pop("username", None)
        password = kwargs.pop("password", None)

        if len(args) != 1:
            self.parser.error("please specify exactly one task ID")

        task_id = args[0]
        if not task_id.isdigit():
            self.parser.error(f"'{task_id}' is not a number")

        # login to the hub
        self.set_hub(username, password)

        task_info = self.hub.scan.get_task_info(task_id)
        if not task_info:
            print("There is no info about the task.", file=sys.stderr)
            sys.exit(1)

        for key, value in task_info.items():
            if key == 'args':
                print('args:')
                for a_k, a_v in value.items():
                    print(f"    {a_k} = {a_v}")
            else:
                print(f"{key} = {value}")
