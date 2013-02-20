# -*- coding: utf-8 -*-

import yum


__all__ = (
    "depend_on",
)


def depend_on(package_name, dependency):
    """
    TODO: check dependency from other side: check what depends on glibc and
          find out if `package_name` is in there, because this might not work
          for parent meta packages etc.
    """
    yb = yum.YumBase()
    yb.preconf.debuglevel = 0
    yb.setCacheDir()
    pkgs = yb.pkgSack.returnNewestByNameArch(patterns=[package_name])
    for pkg in pkgs:
        # alternative: for req in pkg.requires:
        for req in pkg.returnPrco('requires'):
            if req[0].startswith(dependency):
                return True
    return False


if __name__ == '__main__':
    import sys
    print depend_on(sys.argv[1], sys.argv[2])
