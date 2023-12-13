[![Copr build status](https://copr.fedorainfracloud.org/coprs/g/openscanhub/devel/package/osh/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/g/openscanhub/devel/)

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
- `python3-kobo-django >= 0.35.0`
- `python3-kobo-hub >= 0.33.0`
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
- `python3-kobo-worker >= 0.32.0`

### client:
- `koji`
- `python3-kobo-client`

## Development Guide

See [development docs](docs/development.md) for instructions.

## RPM-based Installation

Latest development RPM packages can be found in [Copr](https://copr.fedorainfracloud.org/coprs/g/openscanhub/devel/).

## Documentation

TODO
