# Development environment

As simple as possible development setup for all three major parts of Covscan pipeline. We want to make it compatible with Python 3.6 (the main Python in RHEL 8, supported for its whole lifetime) so we use that specific version inside and outside of the container.

## Kobo

Because we need to fix issues in Kobo as well as in Covscan, we should use it directly as cloned repository - this allows us to make changes in its code, test them and create a PR from them as quicky as possible.

* Switch to the main covscan folder (where covscan, covscand, and covscanhub are).
* Clone Kobo project: `git clone git@github.com:release-engineering/kobo.git`

## Covscan worker

Worker depends on some system packages not available from PyPI, needs to run under root user and has kinda complex setup which are all the reasons to run it in a container.

Build the container via: `podman build -f containers/Dockerfile.worker -t covscanworker .`.

Update `HUB_URL` and possibly other values in `covscand/covscand-local.conf`.

## Covscan hub

Because some of the dependencies of covscan hub are also not available on PyPI, we have to use containerized environment with all the important packages.

## Covscan client

In case the dependencies of covscan client are not available on your system, you can use containerized environment for the covscan client, too.

### Prepare container images

Just run `podman build -f containers/Dockerfile.hub -t covscanhub .` and after a while, you'll have container image ready. You can do the same in case you need the client image with `podman build -f containers/Dockerfile.client -t covscanclient .`.
Also, pull container image for the database layer: `podman pull registry-proxy.engineering.redhat.com/rh-osbs/rhel8-postgresql-12`.

### Prepare the cluster

Note: podman-compose 1.0.0 and newer does not support DNS resolution between containers out of the box so make sure that you have also its dnsname plugin installed (provided by podman-plugins RPM package in Fedora).

Run `podman-compose up --no-start` - this commands prepares all the services and a network for them but doesn't start them.

### Start the db first

Run the following command in the separated terminal window so you can follow its outputs later: `podman start -a db` and wait until it's ready for connections.

#### Restore the database from backup, if you want

If you want to, you can restore a database backup from the production server. If not, you can skip these steps and covscanhub will create an empty database for you.

* Download database backup from https://covscan-stage.lab.eng.brq2.redhat.com/covscanhub.db.gz
* Import the database into the running container: `gzip -cd covscanhub.db.gz | podman exec -i db psql -h localhost -U covscanhub`
* Run the migration SQL script: `cat production_to_dev_database.sql | podman exec -i db psql -h localhost -U covscanhub`

### Start the hub

Now, you can start the hub with: `podman start -a covscanhub`. The hub will try to apply known migrations to your database. If it fails, all the migrations will be faked. Make sure your database is either empty or in a consistent state.

You can start the worker container in the same way, but not now as the hub is not yet ready for it.

#### Covscan hub users

* Enter the interactive shell inside the running container: `podman exec -it covscanhub python3 covscanhub/manage.py shell`
* Create user and admin:

  ```py
  from django.contrib.auth import get_user_model
  User = get_user_model()
  User.objects.create_user('username', 'user@redhat.com', 'xxxxxx')
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

After the first-time setup, all you need is `podman-compose stop` and `podman-compose start`. If, for any reason, you need to start from scratch, `podman-compose down` stops and destroys all the containers and `podman-compose up` starts their fresh copies. The last two commands work also for specific services so you can destroy also only the covscanhub instance and keep the db.

This step also saves their configuration so you can start them individually then via `podman start -a db`. It's good idea to start them in separated terminal windows so their outputs are not combined.

#### Configuration of hub ← worker connection

Go to admin interface and add a new worker with noarch, default channel and worker key from its config file.

## Covscan client

Update important settings in `covscan/covscan-local.conf` - namely HUB_URL, USERNAME, PASSWORD.

Covscan client depends on six and koji Python modules. You should install them system-wide `dnf install python3-six python3-koji`.  You can also install them into a virtual environment `pip install six koji` but in that case, the packages like requests and urllib3 will ignore system-wide certificate authorities. In that case, setting `REQUESTS_CA_BUNDLE` env variable to something like `/etc/ssl/certs/ca-bundle.crt` might help.

As pointed above, all of these dependencies are automatically set up in the client container, so you can use that.

* Covscan client should now be able to connect to the hub and send it tasks. You can test it by these commands:

  ```bash
  COVSCAN_CONFIG_FILE=covscan/covscan-local.conf PYTHONPATH=.:kobo python3 covscan/covscan list-mock-configs
  COVSCAN_CONFIG_FILE=covscan/covscan-local.conf PYTHONPATH=.:kobo python3 covscan/covscan mock-build --config=fedora-35-x86_64 --brew-build curl-7.79.1-1.fc35
  ```

  Note: You can also set these variables permanently to your bashrc.

* Or, in the container (which already has the needed variables exported):

  ```bash
  docker exec -i covscanclient python3 covscan/covscan list-mock-configs
  docker exec -i covscanclient python3 covscan/covscan mock-build --config=fedora-35-x86_64 --brew-build curl-7.79.1-1.fc35
  ```

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

covscanhub/scripts/covscan-xmlrpc-client.py

For more info, please check docstring of the script.

# Testing covscan

## Running unit tests

Unit tests in Django are executed by `manage.py test` command. Since unit tests
in covscan contain also tests for models, a running service with database is
needed.

To run unit tests
1. ensure container image for hub is prepared as described in
   [Development environment](#development-environment) section
   * there is no need for creating users or populating database with data,
     Django creates its own isolated database instance and things such
     credentials and user accounts are mocked by Django unit test framework
     (see [Writing and running tests](https://docs.djangoproject.com/en/2.2/topics/testing/overview/#module-django.test) for more info)
2. ensure containers are running or create and run them by `podman-compose up -d db covscanhub`
   command
3. run unit tests by `podman-compose exec covscanhub python3 covscanhub/manage.py test`
   command
4. after you are done with unit testing, you can tear down the whole container
   stack by `podman-compose down`


## Custom Gitlab CI runner

Because we need to run containers in our CI, we cannot use the standard shared Gitlab CI runners.
Therefore, we have our own private Gitlab CI runner on OpenStack.

### Details

* Maintainer: Lumír Balhar (lbalhar@redhat.com)
* Virtual machine runs on rhos-d.infra.prod.upshift.rdu2.redhat.com
* OS: Fedora-Cloud-Base-35
* IP address: 10.0.151.181
* Main system user: `fedora`

### Installation steps

If we'd ever need to deploy a new runner, those are the steps to do that:

1. You need a running server in Red Hat internal network so it can communicate with Gitlab.
2. As first step, install Red Hat internal CA certificates.
3. The installation instructions for Gitlab runner can be found in the project in Settings → CI/CD → Runners.
4. Download, install, and start the runner.
5. Use the registration token to register the runner with your project.
6. Use `covscan-ci-runner` as a tag. Tags specify which runners take what jobs.
7. Install additional packages for our CI jobs: podman, podman-compose, make, git-core
8. Profit ;)
