# Development environment

As simple as possible development setup for all three major parts of OpenScanHub (OSH) pipeline. We want to make it compatible with Python 3.6 (the main Python in RHEL 8, supported for its whole lifetime) so we use that specific version inside and outside of the container.

## Kobo

Because we need to fix issues in Kobo as well as in OpenScanHub, we should use it directly as cloned repository - this allows us to make changes in its code, test them and create a PR from them as quicky as possible.

* Switch to the main covscan folder (where covscan, covscand, and covscanhub are).
* Clone Kobo project: `git clone git@github.com:release-engineering/kobo.git`

## Using scripts

You can use `containers/scripts/init-db.sh` for deploying a basic containerized environment, which can either have a `--minimal` working database or `--restore` production state (this can take a while).
By default, this script will deploy a `postgresql` instance, the worker and the hub, but it can also generate a containerized version of the client with the `--full-dev` option.

You can skip deployment and basic settings if you use the script.

## OSH worker

Worker depends on some system packages not available from PyPI, needs to run under root user and has kinda complex setup which are all the reasons to run it in a container.

Build the container via: `podman build -f containers/worker.Dockerfile -t osh-worker .`.

Update `HUB_URL` and possibly other values in `osh/worker/worker-local.conf`.

## OSH hub

Because some of the dependencies of OSH hub are also not available on PyPI, we have to use containerized environment with all the important packages.

## OSH client

In case the dependencies of OSH client are not available on your system, you can use containerized environment for the osh-client, too.

### Prepare container images

Just run `podman build -f containers/hub/Dockerfile -t osh-hub .` and after a while, you'll have container image ready. You can do the same in case you need the client image with `podman build -f containers/client.Dockerfile -t osh-client .`.
Also, pull container image for the database layer: `podman pull registry-proxy.engineering.redhat.com/rh-osbs/rhel8-postgresql-12`.

### Prepare the cluster

Note: podman-compose 1.0.0 and newer does not support DNS resolution between containers out of the box so make sure that you have also its dnsname plugin installed (provided by podman-plugins RPM package in Fedora).

Run `podman-compose up --no-start` - this commands prepares all the services and a network for them but doesn't start them.

### Start the db first

Run the following command in the separated terminal window so you can follow its outputs later: `podman start -a db` and wait until it's ready for connections.

#### Restore the database from backup, if you want

If you want to, you can restore a database backup from the production server. If not, you can skip these steps and osh-hub will create an empty database for you.

* Download database backup from https://covscan-stage.lab.eng.brq2.redhat.com/covscanhub.db.gz
* Import the database into the running container: `gzip -cd covscanhub.db.gz | podman exec -i db psql -h localhost -U covscanhub`

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

After the first-time setup, all you need is `podman-compose stop` and `podman-compose start`. If, for any reason, you need to start from scratch, `podman-compose down` stops and destroys all the containers and `podman-compose up` starts their fresh copies. The last two commands work also for specific services so you can destroy also only the osh-hub instance and keep the db.

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

OSH client depends on six and koji Python modules. You should install them system-wide `dnf install python3-six python3-koji`.  You can also install them into a virtual environment `pip install six koji` but in that case, the packages like requests and urllib3 will ignore system-wide certificate authorities. In that case, setting `REQUESTS_CA_BUNDLE` env variable to something like `/etc/ssl/certs/ca-bundle.crt` might help.

As pointed above, all of these dependencies are automatically set up in the client container, so you can use that.

* OSH client should now be able to connect to the hub and send it tasks. You can test it by these commands:

  ```bash
  OSH_CLIENT_CONFIG_FILE=osh/client/client-local.conf PYTHONPATH=.:kobo python3 osh/client/osh-cli list-mock-configs
  OSH_CLIENT_CONFIG_FILE=osh/client/client-local.conf PYTHONPATH=.:kobo python3 osh/client/osh-cli mock-build --config=fedora-36-x86_64 --brew-build units-2.21-4.fc36 --nowait
  OSH_CLIENT_CONFIG_FILE=osh/client/client-local.conf PYTHONPATH=.:kobo python3 osh/client/osh-cli watch-log 1 #Replace 1 with task id
  ```

  Note: You can also set these variables permanently to your bashrc.

* Or, in the container (which already has the needed variables exported):

  ```bash
  podman exec -i osh-client python3 osh/client/osh-cli list-mock-configs
  podman exec -i osh-client python3 osh/client/osh-cli mock-build --config=fedora-36-x86_64 --brew-build units-2.21-4.fc36
  ```

## XML-RPC interface used by Errata Tool

* create Errata Scan using password authentication - new pkg:
```sh
covscan/osh/hub/scripts/osh-xmlrpc-client.py \
    --hub http://covscanhub/xmlrpc/kerbauth/ \
    --username=kdudka --password=xxxxxx \
    create-scan -t curl-7.29.0-25.el7 \
    --et-scan-id 1234 --advisory-id 4567 \
    --owner kdudka --release RHEL-7.7.0 \
    --base NEW_PACKAGE
```

* create Errata Scan using password authentication - update:
```sh
covscan/osh/hub/scripts/osh-xmlrpc-client.py \
    --hub http://covscanhub/xmlrpc/kerbauth/ \
    --username=kdudka --password=xxxxxx \
    create-scan -t curl-7.29.0-55.el7 \
    --et-scan-id 1234 --advisory-id 4567 \
    --owner kdudka --release RHEL-7.7.0 \
    --base curl-7.29.0-25.el7
```

* create Errata Scan using Kerberos authentication:
```sh
covscan/osh/hub/scripts/osh-xmlrpc-client.py \
    --hub https://covscan.lab.eng.brq2.redhat.com/covscanhub/xmlrpc/kerbauth/ \
    create-scan -t curl-7.29.0-55.el7 \
    --et-scan-id 1234 --advisory-id 4567 \
    --owner kdudka --release RHEL-7.7.0 \
    --base curl-7.29.0-25.el7
```

# Developing covscan

## Code path when submitting user scan

 1. Code execution starts in client, for a specific command, e.g. [diff-build](https://gitlab.cee.redhat.com/covscan/covscan/blob/master/covscan/commands/cmd_diff_build.py#L192).
   * Files are uploaded to server via [`upload_file` XML-RPC call](https://gitlab.cee.redhat.com/covscan/covscan/blob/master/covscan/commands/shortcuts.py#L88).
   * The XML-RPC call itself [is defined](https://gitlab.cee.redhat.com/covscan/covscan/blob/master/osh/hub/settings.py#L161) [in kobo](https://github.com/release-engineering/kobo/blob/master/kobo/django/upload/xmlrpc.py#L19).
 2. Server code path starts in XML-RPC API at specific method for particular scan type, e.g. for [mock builds](https://gitlab.cee.redhat.com/covscan/covscan/blob/master/osh/hub/xmlrpc/scan.py#L50).
 3. There is a hierarchical structure for configuring data for scan in `hub/errata/scanner.py`, for client scans this is [ClientScanScheduler](https://gitlab.cee.redhat.com/covscan/covscan/blob/master/osh/hub/errata/scanner.py#L321).
   * These classes have multiple methods:
     * `validate_options` — checks whether input data is valid.
     * `prepare_args` — initiates data for scan itself and for task.
     * `store` — saves data into database.
     * `spawn` — creates task(s).
   * Uploads are being processed [via kobo's API](https://gitlab.cee.redhat.com/covscan/covscan/blob/master/osh/hub/errata/check.py#L98).
 4. Once everything is set up, covscan creates task(s) and [puts files](https://gitlab.cee.redhat.com/covscan/covscan/blob/master/osh/hub/errata/scanner.py#L420) into task's directory.
 5. Command arguments for `csmock` may be pretty complex. These are specified via [CsmockRunner class](https://gitlab.cee.redhat.com/covscan/covscan/blob/master/osh/hub/service/csmock_parser.py#L183).


## XML-RPC API client

There is a client for connecting to hub's XML-RPC API located in

osh/hub/scripts/osh-xmlrpc-client.py

For more info, please check docstring of the script.

# Testing OSH

## Test Coverage

GitLab CI contains latest test coverage report of `master` branch for [Django unit tests](https://gitlab.cee.redhat.com/covscan/covscan/-/jobs/artifacts/master/file/htmlcov/index.html?job=django-unit-tests) and [integration tests](https://gitlab.cee.redhat.com/covscan/covscan/-/jobs/artifacts/master/file/htmlcov/index.html?job=integration-tests).

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
     (see [Writing and running tests](https://docs.djangoproject.com/en/2.2/topics/testing/overview/#module-django.test) for more info)
2. ensure containers are running or create and run them by `podman-compose up -d db osh-hub`
   command
3. run unit tests by `podman-compose exec osh-hub python3 osh/hub/manage.py test`
   command
4. after you are done with unit testing, you can tear down the whole container
   stack by `podman-compose down`

# Gitlab CI

GitLab CI is configured to trigger Copr builds on each update on [Copr](https://copr.devel.redhat.com/coprs/openscanhub-team/gitlab-ci-build-on-copr/builds/). If you want to use `rhcopr` locally, you can install it from [this repository](https://copr.devel.redhat.com/coprs/rhcopr-project/toolset/). If you are making merge requests from your own fork, you need to fork [this project](https://copr.devel.redhat.com/coprs/openscanhub-team/gitlab-ci-build-on-copr/) in your namespace. For example https://copr.devel.redhat.com/coprs/svashish/gitlab-ci-build-on-copr/

## How to set up required variables:
- Login to your Copr account and note Copr CLI Configurations from [this url](https://copr.devel.redhat.com/api/).

- On GitLab CI, go to `Project page` -> `Settings` -> `CI/CD` and select `Variables`.

- Add masked variables as `base64` encoded values for these variables:
```
COPR_CLI_USERNAME
COPR_CLI_TOKEN
COPR_CLI_LOGIN
COPR_CLI_COPR_URL
```

These variables are stored separately due to character limit imposed by GitLab and they are required to be stored in base64 form.

## How does GitLab CI build on Copr:

- Decode base64 encoded masked variables from GitLab CI.
- Store decoded variables in `~/.config/rhcopr` configuration file.
- Trigger a Copr build through `rhcopr` and wait for it's result.

## GitLab CI for Copr

Steps to set up GitLab CI runner for Copr:
- Go to [internal OpenStack](https://rhos-d.infra.prod.upshift.rdu2.redhat.com/dashboard/project/instances/) and login to `redhat.com` domain with your kerberos username and password. You have to be in [this](https://rover.redhat.com/groups/group/core-ser) rover group to access it. Contact @hhorak if you are not in this group.
- Click on Launch Instance.
- Set up instance name to `$USER-gitlab-ci-build-on-copr`. `$USER` is used to identify who is running the virtual machine.
- In the `Source` tab, select `IMAGE` as Boot Source,  Choose `RHEL-8.6.0-x86_64-released`.
- Go to `Flavor` section and select `m1.large`.
- Go to `Network` section and select `provider_net_cci_5`.
- Go to `Key Pair` section and verify that you have selected correct keypair.
- Click on `Launch Instance` and wait for instance to appear.
- Go to instances, click on instance name and select IP Address of the instance.
- SSH to the machine through `ssh -i ~/.ssh/id_rsa   cloud-user@IP_ADDRESS`.
- Switch to `root` user.
- Run `subscription-manager register` as `root` user.
- Next steps are taken from https://docs.gitlab.com/runner/install/linux-repository.html and https://docs.gitlab.com/runner/register/index.html
- Run `curl -L "https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.rpm.sh" | sudo bash` to set up gitlab runner repository.
- `dnf install -y gitlab-runner`.
- Modify `/etc/systemd/system/gitlab-runner.service` to run `gitlab-runner` as `root`:
 `ExecStart=/usr/bin/gitlab-runner "run" "--working-directory" "/home/gitlab-runner" "--config" "/etc/gitlab-runner/config.toml" "--service" "gitlab-runner" "--user" "gitlab-runner"`
- Run `cd /etc/pki/ca-trust/source/anchors/ && curl -O https://password.corp.redhat.com/RH-IT-Root-CA.crt && update-ca-trust`
- Go to Project page -> `Settings` -> `CI/CD` and select `Runners`. Note url and token for setting up new runner. `gitlab-ci-build-on-copr` is the tag for runner.
- Execute `gitlab-runner register` and register a runner with details from previous step. Add `shell` as the executor.

## Custom Gitlab CI runner

Because we need to run containers in our CI, we cannot use the standard shared Gitlab CI runners.
Therefore, we have our own private Gitlab CI runner on OpenStack.

Steps to set up Covscan CI runner for containers:
- Follow same steps from `Gitlab CI for Copr` section. Set up instance name to `$USER-covscan-ci-runner`.
- Run `dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm`.
- Run `dnf install -y podman podman-compose make git-core python3-pip`
- Run `python3 -m pip install`
