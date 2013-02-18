# -*- coding: utf-8 -*-

import yum


__all__ = (
    "depend_on",
)


def depend_on(package_name, dependency):
    yb = yum.YumBase()
    yb.preconf.debuglevel = 0
    yb.setCacheDir()
    pkgs = yb.pkgSack.returnNewestByNameArch(patterns=[package_name])
    for pkg in pkgs:
        for req in pkg.requires:
            if req[0].startswith(dependency):
                return True
    return False
