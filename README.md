# OpenScanHub

OpenScanHub is a service for static and dynamic analysis. You can find the
latest source code at:

    https://github.com/openscanhub/openscanhub

OpenScanHub is licensed under GPLv3+, see LICENSE for details. Please
report bugs and feature requests on GitHub using the above URL.

## Dependencies

### hub:
- `csdiff`
- `gzip`
- `httpd`
- `koji`
- `mod_auth_gssapi`
- `mod_ssl`
- `python3-bugzilla`
- `python3-csdiff`
- `python3-django >= 3.2.0`
- `python3-jira`
- `python3-kobo-client`
- `python3-kobo-django`
- `python3-kobo-hub`
- `python3-kobo-rpmlib`
- `python3-mod_wsgi`
- `python3-psycopg2`
- `python3-qpid-proton`
- `xz`

### worker:
- `csmock`
- `file`
- `koji`
- `python3-kobo-client`
- `python3-kobo-rpmlib`
- `python3-kobo-worker`

### client:
- `koji`
- `python3-kobo-client`

## Development Guide

See [development docs](docs/development.md) for instructions.

## RPM-based Installation

TODO

## Documentation

TODO
