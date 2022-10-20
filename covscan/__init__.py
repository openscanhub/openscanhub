# -*- coding: utf-8 -*-


from __future__ import absolute_import

import kobo.client.commands


__all__ = (
    "CovScanCommand",
)


class CovScanCommand(kobo.client.ClientCommand):
    def write_task_id_file(self, task_id, filename=None):
        if filename is not None:
            with open(filename, "w") as f:
                f.write(f"{task_id}\n")
