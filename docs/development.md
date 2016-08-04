# Developing covscan


## Code path when submitting user scan

 1. Code execution starts in client, for a specific command, e.g. [diff-build](https://gitlab.cee.redhat.com/covscan/covscan/blob/master/covscan/commands/cmd_diff_build.py#L192).
   * Files are uploaded to server via [`upload_file` XML-RPC call](https://gitlab.cee.redhat.com/covscan/covscan/blob/master/covscan/commands/shortcuts.py#L88).
   * The XML-RPC call itself [is defined](https://gitlab.cee.redhat.com/covscan/covscan/blob/master/covscanhub/settings.py#L161) [in kobo](https://github.com/release-engineering/kobo/blob/master/kobo/django/upload/xmlrpc.py#L19).
 2. Server code path starts in XML-RPC API at specific method for particular scan type, e.g. for [mock builds](https://gitlab.cee.redhat.com/covscan/covscan/blob/master/covscanhub/xmlrpc/scan.py#L50).
 3. There is a hierarchical structure for configuring data for scan in `hub/errata/scanner.py`, for client scans this is [ClientScanScheduler](https://gitlab.cee.redhat.com/covscan/covscan/blob/master/covscanhub/errata/scanner.py#L321).
   * These classes have multiple methods:
     * `validate_options` — checks whether input data is valid.
     * `prepare_args` — initiates data for scan itself and for task.
     * `store` — saves data into database.
     * `spawn` — creates task(s).
   * Uploads are being processed [via kobo's API](https://gitlab.cee.redhat.com/covscan/covscan/blob/master/covscanhub/errata/check.py#L98).
 4. Once everything is set up, covscan creates task(s) and [puts files](https://gitlab.cee.redhat.com/covscan/covscan/blob/master/covscanhub/errata/scanner.py#L420) into task's directory.
 5. Command arguments for `csmock` may be pretty complex. These are specified via [CsmockRunner class](https://gitlab.cee.redhat.com/covscan/covscan/blob/master/covscanhub/service/csmock_parser.py#L183).


## XML-RPC API client

There is a client for connecting to hub's XML-RPC API located in

covscanhub/scripts/xmlrpc.py

For more info, please check docstring of the script.

