# Development environment

As simple as possible development setup for all three major parts of OpenScanHub (OSH) pipeline. We want to make it compatible with Python 3.6 (the main Python in RHEL 8, supported for its whole lifetime) so we use that specific version inside and outside of the container.

## Quick setup

Execute following commands to quickly try a local OpenScanHub deployment (through podman/docker compose):

```bash
git clone https://github.com/openscanhub/openscanhub.git
cd openscanhub
git clone https://github.com/release-engineering/kobo.git
containers/scripts/init-db.sh --full-dev --minimal
# Get arch name and remove trailing carriage return or new line
OSH_ARCH_UNAME=$(podman exec -it osh-client uname -m 2>/dev/null | tr -d '\n\r')
podman exec -it osh-client env OSH_CLIENT_CONFIG_FILE=osh/client/client-local.conf PYTHONPATH=.:kobo python3 osh/client/osh-cli mock-build --config="fedora-37-$OSH_ARCH_UNAME" --brew-build units-2.21-5.fc37 --nowait
```

If the last command is successful, there should be a task accessible at http://localhost:8000/task/1/.

Run `containers/scripts/deploy.sh --clean` from root directory of the repository to bring down the compose.

## Kobo

Because we need to fix issues in Kobo as well as in OpenScanHub, we should use it directly as cloned repository - this allows us to make changes in its code, test them and create a PR from them as quicky as possible.

* Switch to the root project folder (where `osh` is).
* Clone Kobo project: `git clone git@github.com:release-engineering/kobo.git`

## Using scripts

You can use `containers/scripts/init-db.sh` for deploying a basic containerized environment, which can either have a `--minimal` working database or `--restore` production state (this can take a while).
By default, this script will deploy a `postgresql` instance, the worker and the hub, but it can also generate a containerized version of the client with the `--full-dev` option.

You can skip deployment and basic settings if you use the script.

## OSH worker

Worker depends on some system packages not available from PyPI, needs to run under root user and has kinda complex setup which are all the reasons to run it in a container.

Build the container via: `podman build -f containers/worker.Dockerfile -t osh-worker .`

Update `HUB_URL` and possibly other values in `osh/worker/worker-local.conf`.

## OSH hub

Because some of the dependencies of OSH hub are also not available on PyPI, we have to use containerized environment with all the important packages.

## OSH client

In case the dependencies of OSH client are not available on your system, you can use containerized environment for the osh-client, too.

### Prepare container images

Just run `podman build -f containers/hub/Dockerfile -t osh-hub .` and after a while, you'll have container image ready. You can do the same in case you need the client image with `podman build -f containers/client.Dockerfile -t osh-client .`.
Also, pull container image for the database layer: `podman pull quay.io/sclorg/postgresql-12-c8s`.

### Prepare the cluster

Run `podman-compose -p osh up --no-start` - this commands prepares all the services and a network for them but doesn't start them.

### Start the db first

Run the following command in the separated terminal window so you can follow its outputs later: `podman start -a db` and wait until it's ready for connections.

#### Restore the database from backup, if you want

If you want to, you can restore a database backup from the production server. If not, you can skip these steps and osh-hub will create an empty database for you.

* Download database backup in gzip format.
* Import the database into the running container: `gzip -cd "openscanhub-database-dump-filename.gz" | podman exec -i db psql -h localhost -U openscanhub`

Note that you can also restore the full snapshot of the production database (without the `-limited` suffix) if you have enough disk space and time.  The only difference between those two snapshots is that the `waiving_defect` table is empty in the `-limited` variant.

### Start the OSH hub

Now, you can start the hub with: `podman start -a osh-hub`. The hub will try to apply known migrations to your database. If it fails, all the migrations will be faked. Make sure your database is either empty or in a consistent state.


#### OSH hub users

* Enter the interactive shell inside the running container: `podman exec -it osh-hub python3 osh/hub/manage.py shell`
* Create user and admin:

```py
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.create_user('user', 'user@redhat.com', 'xxxxxx')
User.objects.create_superuser('admin', 'user@redhat.com', 'xxxxxx')
```

or, if the users already exist, you can change admin pass like this:

```py
from django.contrib.auth import get_user_model
User = get_user_model()
u = User.objects.get(username='admin')
u.set_password('velryba')
u.save()
```

After the first-time setup, all you need is `podman stop` and `podman start`. If, for any reason, you need to start from scratch, `podman-compose -p osh down` stops and destroys all the containers and `podman-compose -p osh up` starts their fresh copies. The last two commands work also for specific services so you can destroy also only the osh-hub instance and keep the db.

This step also saves their configuration so you can start them individually then via `podman start -a db`. It's good idea to start them in separated terminal windows so their outputs are not combined.

#### Configuration of hub ← worker connection

Go to admin interface and add a new worker with noarch, default channel and worker key from its config file.

## OSH worker

You can use OSH client to submit builds, but a OSH worker must be started manually for the builds to be successful:

  ```bash
     podman start -a osh-worker
  ```

## OSH client

Update important settings in `osh/client/client-local.conf` - namely HUB_URL, USERNAME, PASSWORD.

OSH client depends on koji Python module. You should install it system-wide `dnf install python3-koji`.  You can also install it into a virtual environment `pip install koji` but in that case, the packages like requests and urllib3 will ignore system-wide certificate authorities. In that case, setting `REQUESTS_CA_BUNDLE` env variable to something like `/etc/ssl/certs/ca-bundle.crt` might help.

As pointed above, all of these dependencies are automatically set up in the client container, so you can use that.

* OSH client should now be able to connect to the hub and send it tasks. You can test it by these commands:

  ```bash
  OSH_CLIENT_CONFIG_FILE=osh/client/client-local.conf PYTHONPATH=.:kobo python3 osh/client/osh-cli list-mock-configs
  OSH_CLIENT_CONFIG_FILE=osh/client/client-local.conf PYTHONPATH=.:kobo python3 osh/client/osh-cli mock-build --config=fedora-37-x86_64 --brew-build units-2.21-5.fc37 --nowait
  OSH_CLIENT_CONFIG_FILE=osh/client/client-local.conf PYTHONPATH=.:kobo python3 osh/client/osh-cli watch-log 1 #Replace 1 with task id
  ```

  Note: You can also set these variables permanently to your bashrc.

* Or, in the container (which already has the needed variables exported):

  ```bash
  podman exec -i osh-client python3 osh/client/osh-cli list-mock-configs
  podman exec -i osh-client python3 osh/client/osh-cli mock-build --config=fedora-37-x86_64 --brew-build units-2.21-5.fc37
  ```

## XML-RPC interface used by Errata Tool

* create Errata Scan using password authentication - new pkg:
```sh
osh/hub/scripts/osh-xmlrpc-client.py \
    --hub http://osh-hub:8000/xmlrpc/kerbauth/ --username=user --password=xxxxxx \
    create-scan -b NEW_PACKAGE -t libssh2-1.10.0-7.fc38 --et-scan-id=1 \
    --release=Fedora-37 --owner=admin --advisory-id=1
```

* create Errata Scan using password authentication - update:
```sh
osh/hub/scripts/osh-xmlrpc-client.py \
    --hub http://osh-hub:8000/xmlrpc/kerbauth/ --username=user --password=xxxxxx \
    create-scan -b libssh2-1.10.0-5.fc37 -t libssh2-1.10.0-7.fc38 --et-scan-id=1 \
    --release=Fedora-37 --owner=admin --advisory-id=1
```

* create Errata Scan using Kerberos authentication (will not work in a local development environment):
```sh
osh/hub/scripts/osh-xmlrpc-client.py \
    --hub https://$HOSTNAME/osh/xmlrpc/kerbauth/ \
    create-scan -t curl-7.29.0-55.el7 \
    --et-scan-id 1234 --advisory-id 4567 \
    --owner kdudka --release RHEL-7.7.0 \
    --base curl-7.29.0-25.el7
```

# Developing OSH

## Code path when submitting user scan

 1. Code execution starts in client, for a specific command, e.g. [diff-build](https://github.com/openscanhub/openscanhub/blob/main/osh/client/commands/cmd_diff_build.py).
   * Files are uploaded to server via [`upload_file` XML-RPC call](https://github.com/openscanhub/openscanhub/blob/main/osh/client/commands/shortcuts.py).
   * The XML-RPC call itself [is defined](https://github.com/openscanhub/openscanhub/blob/main/osh/hub/settings.py) [in kobo](https://github.com/release-engineering/kobo/blob/master/kobo/django/upload/xmlrpc.py).
 2. Server code path starts in XML-RPC API at specific method for particular scan type, e.g. for [mock builds](https://github.com/openscanhub/openscanhub/blob/main/osh/hub/osh_xmlrpc/scan.py).
 3. There is a hierarchical structure for configuring data for scan in `osh/hub/errata/scanner.py`, for client scans this is [ClientScanScheduler](https://github.com/openscanhub/openscanhub/blob/main/osh/hub/errata/scanner.py).
   * These classes have multiple methods:
     * `validate_options` — checks whether input data is valid.
     * `prepare_args` — initiates data for scan itself and for task.
     * `store` — saves data into database.
     * `spawn` — creates task(s).
   * Uploads are being processed [via kobo's API](https://github.com/openscanhub/openscanhub/blob/main/osh/hub/errata/check.py).
 4. Once everything is set up, OSH creates task(s) and [puts files](https://github.com/openscanhub/openscanhub/blob/main/osh/hub/errata/scanner.py) into task's directory.
 5. Command arguments for `csmock` may be pretty complex. These are specified via [CsmockRunner class](https://github.com/openscanhub/openscanhub/blob/main/osh/worker/csmock_runner.py).


## XML-RPC API client

There is a client for connecting to hub's XML-RPC API located in
`osh/hub/scripts/osh-xmlrpc-client.py`.

For more info, please check docstring of the script.

# Testing OSH

## Test Coverage

Latest test coverage report can be seen in [Codecov](https://app.codecov.io/gh/openscanhub/openscanhub).

### Test Coverage and os.fork()

The Code coverage testing module for Python does not work well with programs that use `os.fork()`.  This prevents certain parts of OSH worker code from being included in the test coverage data.  To work around this limitation, one can enable the `RUN_TASKS_IN_FOREGROUND` option in `worker.conf` to execute tasks directly in the main OSH worker process.  An unwanted side effect of this option is that `VersionDiffBuild` and `ErrataDiffBuild` tasks always fail because they cannot create any subtask while the main task is running in foreground (thus blocking the main OSH worker process).

## Running unit tests

Unit tests in Django are executed by `manage.py test` command. Since unit tests
in OSH contain also tests for models, a running service with database is
needed.

To run unit tests
1. ensure container image for hub is prepared as described in
   [Development environment](#development-environment) section
   * there is no need for creating users or populating database with data,
     Django creates its own isolated database instance and things such
     credentials and user accounts are mocked by Django unit test framework
     (see [Writing and running tests](https://docs.djangoproject.com/en/3.2/topics/testing/overview/#module-django.test) for more info)
2. ensure containers are running or create and run them by `podman-compose -p osh up -d db osh-hub`
   command
3. run unit tests by `podman exec osh-hub python3 osh/hub/manage.py test`
   command
4. after you are done with unit testing, you can tear down the whole container
   stack by `podman-compose -p osh down`

## Testing reporting integrations

Staging secrets for `bugzilla` and `jira` should be placed in a corresponding `*_secret` file in the `.secrets` folder at the top-level of the application.
Notice that `/etc/osh/hub/secrets` should be used for production.
Endpoints at `osh/hub/settings_local.py` already point to the respective staging instances.
