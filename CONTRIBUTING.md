# OpenScanHub Contribution Guidelines

This documentation contains contribution guidelines for OpenScanHub project.


## Commit Prefixes

Please prefix your commit messages with one of the below prefixes:

- ci
- client
- containers
- docs
- hub
- lint
- packaging
- worker

For example `hub: Fix a bug in hub component`.


## Pre-commit Hook

It is recommended to enable pre-commit hook in your local git repository:
```sh
$ sudo dnf install pre-commit
$ pre-commit install
```

This will cause all changes to be linted before you commit them.  The first run
of the pre-commit hook will take some time because it downloads content from
network.  The downloaded content is cached locally, so next runs are usually
much faster.  If pre-existing issues are identified by the linters, they should
be fixed in separate commits.  Issues in newly added code should be squashed so
that no fix-up commits unnecessarily end up in the `main` branch.
