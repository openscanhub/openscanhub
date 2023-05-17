# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

import inspect

from kobo.client import ClientCommand


class OshCommand(ClientCommand):
    def connect_to_hub(self, opts):
        username = opts.pop("username", None)
        password = opts.pop("password", None)
        hub = opts.pop("hub", None)

        params = [username, password]

        # For compatibility with older kobo releases
        sig = inspect.signature(self.set_hub)
        if len(sig.parameters) == 4:
            params.append(hub)

        self.set_hub(*params)

    def write_task_id_file(self, task_id, filename=None):
        if filename is not None:
            with open(filename, "w") as f:
                print(task_id, file=f)
