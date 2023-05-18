# Solutions to some OSH problems

* Web page [http://127.0.0.1:8000/xmlrpc/kerbauth/](http://127.0.0.1:8000/xmlrpc/kerbauth/) is saying *Authorization Required*
    * We want to the easiest name/password authentication, so comment apache kerberos authentication - in */etc/httpd/conf.d/auth_kerb.conf*.

* OSH hub is running (using docker), but when the worker is started, it says "Permission denied".
    *  SELinux prevented starting container, run `# setenforce 0` and run again.

* Errata scan says: _Unable to submit the scan, error: Packages in this release are not being scanned_.
    * System release is missing, it was probably not imported into the database.

* When you create errata scan and get _TransactionManagementError: An error occurred in the current transaction. You can't execute queries until the end of the 'atomic' block_.
    * Probably it is a problem with the database, try to run it again.
    * If it does not work, run other kind of task (f.e. `MockBuild`, `DiffBuild`), it will run the more cleaner way, it simply cleans the mess.

* Mock build fails with `csmock error: unrecognized arguments: --security`
    * Csmock does not directly have `--security` parameter but it is used for `--cov-analyze-opts=` param.

* When you are trying to do something (usually with *manage.py* file) and get *ImportError: No module named osh.hub.settings*.
     * Set environment variable path to OSH, f.e.: *export PYTHONPATH='/home/<user>/osh/:/home/<user>/kobo/'*
     (`kobo` shouldn't be necessary)

* When do you want to cancel running task:
    * run `osh-cli cancel-tasks`
    * however, it leads to another problem:

* Csmock has lock: waiting till /tmp/.csmock-rhel-7-x86_64.lock (PID 9340) disappears...
    * check if `mock` is running and kill it
    * remove lock
