# -*- coding: utf-8 -*-


import kobo.client.commands


__all__ = (
    "CovScanCommand",
)


class CovScanCommand(kobo.client.ClientCommand):
    def write_task_id_file(self, task_id, filename=None):
        if filename is not None:
            f = open(filename, "w")
            f.write("%s\n" % task_id)
            f.close()
