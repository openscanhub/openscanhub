# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

import sys

import osh.client


class List_Mock_Configs(osh.client.OshCommand):
    """list available mock configs present on hub"""
    enabled = True
    admin = False  # admin type account required

    def options(self):
        # specify command usage
        # normalized name contains a lower-case class name with underscores converted to dashes
        self.parser.usage = f"%prog {self.normalized_name} [options] <args>"

    def run(self, *args, **kwargs):
        # login to the hub
        self.connect_to_hub(kwargs)

        print("NAME", file=sys.stderr)
        for i in self.hub.mock_config.all():
            if i["enabled"]:
                print(i["name"])
