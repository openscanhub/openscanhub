from kobo.client import ClientCommand


class OshCommand(ClientCommand):
    def write_task_id_file(self, task_id, filename=None):
        if filename is not None:
            with open(filename, "w") as f:
                f.write(f"{task_id}\n")
