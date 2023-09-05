%global min_required_version_django 3.2

Name:           osh
Version:        %{version}
Release:        1%{?dist}
License:        GPL-3.0-or-later
Summary:        Static and Dynamic Analysis as a Service
Source:         %{name}-%{version}.tar.gz
BuildArch:      noarch

BuildRequires:  koji
BuildRequires:  python3-csdiff
BuildRequires:  python3-devel
BuildRequires:  python3-django >= %{min_required_version_django}
BuildRequires:  python3-kobo-client
BuildRequires:  python3-kobo-django
BuildRequires:  python3-kobo-hub
BuildRequires:  python3-kobo-rpmlib
BuildRequires:  python3-psycopg2
BuildRequires:  python3-qpid-proton
BuildRequires:  python3-setuptools
BuildRequires:  systemd-rpm-macros

# make sure that shell completion dir macros are defined in the buildroot
%{!?bash_completions_dir: %global bash_completions_dir %{_datadir}/bash-completion/completions}
%{!?zsh_completions_dir: %global zsh_completions_dir %{_datadir}/zsh/site-functions}


%description
OpenScanHub is a service for static and dynamic analysis.
It consists of central hub, workers and cli client.


%package client
Summary: OpenScanHub CLI client
Requires: koji
Requires: python3-kobo-client >= 0.15.1-100
Requires: %{name}-common = %{version}-%{release}
Obsoletes: python3-%{name}-client < %{version}-%{release}
# This is kept here for backward compatibility with old package name
Provides: covscan-client = %{version}
Obsoletes: covscan-client < %{version}
Conflicts: covscan-client < %{version}

%description client
OpenScanHub CLI client


%package common
Summary: OpenScanHub shared files for client, hub and worker
Obsoletes: covscan-common < %{version}

%description common
OpenScanHub shared files for client, hub and worker.


%package worker
Summary: OpenScanHub worker
Requires: csmock
Requires: file
Requires: koji
Requires: python3-kobo-client
Requires: python3-kobo-rpmlib
Requires: python3-kobo-worker >= 0.24.0
Requires: %{name}-common = %{version}-%{release}
Requires: osh-worker-conf

Obsoletes: covscan-worker < %{version}

%description worker
OpenScanHub worker

%package hub
Summary: OpenScanHub xml-rpc interface and web application
Requires: httpd
Requires: mod_auth_gssapi
Requires: mod_ssl
Requires: python3-django >= %{min_required_version_django}
Requires: python3-kobo-client
Requires: python3-kobo-django
Requires: python3-kobo-hub
Requires: python3-kobo-rpmlib
Requires: python3-mod_wsgi
# PostgreSQL adapter for python
Requires: python3-psycopg2
Requires: gzip
# inform ET about progress using UMB (Unified Message Bus)
Requires: python3-qpid-proton
# hub is interacting with brew
Requires: koji
# extract tarballs created by csmock
Requires: xz

Requires: csdiff
Requires: python3-bugzilla
Requires: python3-csdiff
Requires: python3-jira

Requires(post): /usr/bin/pg_isready

Requires: %{name}-common = %{version}-%{release}
Requires: osh-hub-conf

Obsoletes: covscan-hub < %{version}

%description hub
OpenScanHub xml-rpc interface and web application

# define osh-{worker,hub}-conf-devel subpackages
%(for sub in worker hub; do
cat << EOF
%package ${sub}-conf-devel
Summary: OpenScanHub ${sub} devel configuration
Provides: osh-${sub}-conf = %{version}-%{release}
Conflicts: osh-${sub}-conf
%description ${sub}-conf-devel
OpenScanHub ${sub} devel configuration
EOF
done)

%prep
%setup -q

%build

# Add -s to the shebang in osh/client/osh-cli:
# https://docs.fedoraproject.org/en-US/packaging-guidelines/Python/#_shebang_macros
# TODO: Remove this when we migrate to newer Python packaging macros which
# do this automatically.
%py3_shebang_fix osh/client/osh-cli

# collect static files from Django itself
PYTHONPATH=. osh/hub/manage.py collectstatic --noinput

%py3_build


%install
%py3_install

# install the files collected by `manage.py collectstatic`
cp -a {,%{buildroot}%{python3_sitelib}/}osh/hub/static/

# Temporarily provide /usr/bin/covscan for backward compatibility
ln -s osh-cli %{buildroot}%{_bindir}/covscan

# create /etc/osh/hub/secrets directory
mkdir -p %{buildroot}%{_sysconfdir}/osh/hub/secrets

# create /var/lib dirs
mkdir -p %{buildroot}/var/lib/osh/hub/{tasks,upload,worker}

# create log file
mkdir -p %{buildroot}/var/log/osh/hub
touch %{buildroot}/var/log/osh/hub/hub.log

# copy checker_groups.txt
cp -R osh/hub/scripts/checker_groups.txt %{buildroot}%{python3_sitelib}/osh/hub/scripts/

# make manage.py executable
chmod 0755 %{buildroot}%{python3_sitelib}/osh/hub/manage.py

# scripts are needed for setup.py, no longer needed
rm -rf %{buildroot}%{python3_sitelib}/scripts

%files client
%defattr(644,root,root,755)
%attr(755,root,root) %{_bindir}/osh-cli
%{_bindir}/covscan
%attr(644,root,root) %config(noreplace) /etc/osh/client.conf
%{bash_completions_dir}
%{zsh_completions_dir}
%{python3_sitelib}/osh/client
%{python3_sitelib}/osh-*-py%{python3_version}.egg-info

%files common
%defattr(644,root,root,755)
%dir %{_sysconfdir}/osh
%{python3_sitelib}/osh/common
%{python3_sitelib}/osh/__init__.py*
%{python3_sitelib}/osh/__pycache__
%dir %{python3_sitelib}/osh
%dir /var/lib/osh

%files worker
%defattr(644,root,root,755)
%{python3_sitelib}/osh/worker
%{_unitdir}/osh-worker.service
%attr(754,root,root) /usr/sbin/osh-worker
%dir %attr(775,root,root) /var/log/osh

%post client
if test -f /etc/covscan/covscan.conf; then
    mv /etc/covscan/covscan.conf /etc/osh/client.conf
fi

%post worker
%systemd_post osh-worker.service

%preun worker
%systemd_preun osh-worker.service

%postun worker
%systemd_postun_with_restart osh-worker.service

%files worker-conf-devel
%attr(640,root,root) %config(noreplace) /etc/osh/worker.conf

%files hub
%defattr(-,root,apache,-)
%{_sbindir}/osh-stats
%{_sysconfdir}/osh/hub
%{python3_sitelib}/osh/hub
%{_unitdir}/osh-stats.*
%exclude %{python3_sitelib}/osh/hub/settings_local.py*
%exclude %{python3_sitelib}/osh/hub/__pycache__/settings_local.*
%dir %attr(775,root,root) /var/log/osh
%dir %attr(775,root,apache) /var/log/osh/hub
%ghost %attr(640,apache,apache) /var/log/osh/hub/hub.log
%attr(775,root,apache) /var/lib/osh/hub
%ghost %attr(640,root,apache) /var/lib/osh/hub/secret_key
%dir %attr(775,root,apache) %{_sysconfdir}/osh/hub/secrets
%ghost %attr(640,root,apache) %{_sysconfdir}/osh/hub/secrets/jira_secret
%ghost %attr(640,root,apache) %{_sysconfdir}/osh/hub/secrets/bugzilla_secret

%post hub
exec &>> /var/log/osh/hub/post-install-%{name}-%{version}-%{release}.log

# record timestamp
echo -n '>>> '
date -R

set -x
umask 0026

if ! test -e /var/lib/osh/hub/secret_key; then
    # generate Django secret key for a fresh installation
    %{__python3} -c "from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())" > /var/lib/osh/hub/secret_key
    chgrp apache /var/lib/osh/hub/secret_key
fi

# this only takes an effect if PostgreSQL is running and the database exists
pg_isready -h localhost && %{python3_sitelib}/osh/hub/manage.py migrate

%systemd_post osh-stats.service osh-stats.timer

%preun hub
%systemd_preun osh-stats.service osh-stats.timer

%postun hub
%systemd_postun_with_restart osh-stats.service osh-stats.timer

%files hub-conf-devel
%attr(640,root,apache) %config(noreplace) %{python3_sitelib}/osh/hub/settings_local.py
%attr(640,root,apache) %config(noreplace) %{python3_sitelib}/osh/hub/__pycache__/settings_local*.pyc


%changelog
* Tue Sep 05 2023 Kamil Dudka <kdudka@redhat.com> - 0.9.4-1
- stabilize a new version of osh-client

* Wed May 17 2023 Kamil Dudka <kdudka@redhat.com> - 0.9.3-1
- rename covscan-* packages to osh-*

* Tue Apr 25 2023 Lukáš Zaoral <lzaoral@redhat.com> - 0.9.2-1
- revert osh-cli to use an absolute path to python3

* Fri Apr 14 2023 Kamil Dudka <kdudka@redhat.com> - 0.9.1-1
- let osh-cli use hub URL with the new /osh prefix

* Thu Mar 16 2023 Kamil Dudka <kdudka@redhat.com> - 0.9.0-1
- stabilize the refactored version of covscan-client

* Thu Sep 01 2022 Siteshwar Vashisht <svashisht@redhat.com> - 0.8.2-2
- Add mod_ssl as runtime dependency

* Wed Aug 24 2022 Kamil Dudka <kdudka@redhat.com> - 0.8.2-1
- update production hub URL in default configuration of covscan-client

* Fri Jun 17 2022 Kamil Dudka <kdudka@redhat.com> - 0.8.1-1
- bump version to make upgrades to git snapshots work again

* Thu Apr 07 2022 Lumír Balhar <lbalhar@redhat.com> - 0.8.0-3
- Reorganize specfile and add covscan-common

* Mon Mar 14 2022 Kamil Dudka <kdudka@redhat.com> - 0.8.0-2
- add obsoletes to ease upgrade

* Thu Jan 20 2022 Kamil Dudka <kdudka@redhat.com> - 0.8.0-1
- drop support for python 2.x and django 1.x
- new major release

* Thu Nov 04 2021 Kamil Dudka <kdudka@redhat.com> - 0.7.2-1
- new release

* Thu Mar 25 2021 Kamil Dudka <kdudka@redhat.com> - 0.7.1-1
- new release

* Tue Dec 22 2020 Kamil Dudka <kdudka@redhat.com> - 0.7.0-1
- new release

* Thu Oct 24 2019 Matej Mužila <mmuzila@redhat.com> - 0.6.12-3
- spec changes to build python3 covscan

* Thu Sep 19 2019 Kamil Dudka <kdudka@redhat.com> - 0.6.12-2
- explicitly require python2-* build dependencies

* Tue Sep 03 2019 Kamil Dudka <kdudka@redhat.com> - 0.6.12-1
- new release

* Fri Oct 19 2018 Kamil Dudka <kdudka@redhat.com> - 0.6.11-1
- new release

* Mon Aug 13 2018 Kamil Dudka <kdudka@redhat.com> - 0.6.10-1
- new release

* Fri Oct 20 2017 Kamil Dudka <kdudka@redhat.com> - 0.6.9-1
- new release

* Mon Jun 26 2017 Kamil Dudka <kdudka@redhat.com> - 0.6.8-1
- new release

* Tue Apr 12 2016 Kamil Dudka <kdudka@redhat.com> - 0.6.7-2
- bump release to force update if stale covscan-testing packages are installed

* Thu Aug 20 2015 Kamil Dudka <kdudka@redhat.com> - 0.6.7-1
- 0.6.7 bugfix release

* Wed Aug 12 2015 Kamil Dudka <kdudka@redhat.com> - 0.6.6-1
- 0.6.6 bugfix release
- update the list of dependencies
- create empty /var/log/covscanhub.log unless it exists already

* Thu Feb 19 2015 Tomas Tomecek <ttomecek@redhat.com> - 0.6.5-1
- 0.6.5 bugfix release

* Wed Dec 10 2014 Tomas Tomecek <ttomecek@redhat.com> - 0.6.4-1
- update CLI docs (--help) and homepage
- workaround a race on server when running multiple tasks

* Tue Nov 04 2014 Tomas Tomecek <ttomecek@redhat.com> - 0.6.3-1
- enable passing args to csmock from client
- fix several TBs

* Mon Oct 20 2014 Tomas Tomecek <ttomecek@redhat.com> - 0.6.2-1
- enable submitting prio from cli
- pass cmock args to version task

* Mon Oct 13 2014 Tomas Tomecek <ttomecek@redhat.com> - 0.6.1-1
- bugfix update: fix version-diff-build

* Sat Oct 11 2014 Tomas Tomecek <ttomecek@redhat.com> - 0.6.0-1
- 0.6.0 release
- add profiles

* Thu Sep 25 2014 Tomas Tomecek <ttomecek@redhat.com> - 0.6.0-1.a
- 0.6.0a alpha release

* Mon Aug 04 2014 Tomas Tomecek <ttomecek@redhat.com> - 0.5.2-1
- add DB fixtures to package

* Mon Aug 04 2014 Tomas Tomecek <ttomecek@redhat.com> - 0.5.1-1
- fixes for reworked scheduler

* Wed Jan 8 2014 Tomas Tomecek <ttomecek@redhat.com> - 0.4.4-1
- remove brewkoji dependency

* Sun Nov 17 2013 Tomas Tomecek <ttomecek@redhat.com> - 0.4.3-1
- hub update (django and kobo rebase)

* Fri Oct 18 2013 Tomas Tomecek <ttomecek@redhat.com> - 0.4.2-2
- update kobo dependency (0.4.1 should be fine)
- add scriptlets for handling issues with kobo-0.4.0

* Mon Sep 30 2013 Tomas Tomecek <ttomecek@redhat.com> - 0.4.1-2
- make dependency to kobo 0.3.8 (0.4 is broken currently)

* Fri Sep 13 2013 Tomas Tomecek <ttomecek@redhat.com> - 0.4.1-1
- improve stats
- bugfixes

* Wed Sep 11 2013 Tomas Tomecek <ttomecek@redhat.com> - 0.4.0-1
- new version of hub and client

* Mon Jun 03 2013 Tomas Tomecek <ttomecek@redhat.com> - 0.3.2-3
- store provider requests in DB (hub)

* Thu May 23 2013 Tomas Tomecek <ttomecek@redhat.com> - 0.3.2-2
- New release of hub, bugfixes and RFEs
- Getting ready for 6.5 scanning

* Thu May 23 2013 Tomas Tomecek <ttomecek@redhat.com> - 0.3.2-1
- Update to version 0.3.2

* Wed Apr 24 2013 Tomas Tomecek <ttomecek@redhat.com> - 0.3.1-1
- Update to version 0.3.1

* Fri Apr 5 2013 Tomas Tomecek <ttomecek@redhat.com> - 0.3.0-1
- Update for hub and worker
- ET pilot

* Fri Mar 15 2013 Tomas Tomecek <ttomecek@redhat.com> - 0.2.3-1
- Let client depend on brewkoji
- new version

* Thu Jan 24 2013 Tomas Tomecek <ttomecek@redhat.com> - 0.2.2-2
- Tarball extraction fix

* Wed Jan 09 2013 Tomas Tomecek <ttomecek@redhat.com> - 0.2.2-1
- Added support for multiple new options (CLI)

* Tue Nov 06 2012 Tomas Tomecek <ttomecek@redhat.com> - 0.2.1-2
- Updated requirements for hub and worker

* Thu Nov 1 2012 Tomas Tomecek <ttomecek@redhat.com> - 0.2.1-1
- Added version-diff-build (CLI, HUB, worker)
- Improved WebUI (scans, waiver) (HUB)
- Implemented functionality for ET scans (HUB, worker)
- Fixed several bugs on worker (worker)
- Tarball on hub is now automatically extracted (worker, HUB)
- You may browse more types of log files (.out, .html, etc.) (HUB)

* Thu Dec  8 2011 Daniel Mach <dmach@redhat.com> - 0.2.0-1
- Implement a mock-build command and brew build support. (Daniel Mach)
- Minor tweaks to hub settings and client configuration. (Daniel Mach)
- Add a --timeout option to the diff-build command. (Daniel Mach)

* Tue Jun 14 2011 Daniel Mach <dmach@redhat.com> - 0.1.0-1
- Initial build.
