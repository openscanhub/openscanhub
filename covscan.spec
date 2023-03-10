Name:           covscan
Version:        %{version}
Release:        2%{?dist}
License:        Commercial
Summary:        Coverity scan scheduler
Source:         %{name}-%{version}.tar.bz2
BuildArch:      noarch

BuildRequires:  koji
BuildRequires:  python3-csdiff
BuildRequires:  python3-devel
BuildRequires:  python3-django
BuildRequires:  python3-django-debug-toolbar
BuildRequires:  python3-kobo-client
BuildRequires:  python3-kobo-django
BuildRequires:  python3-kobo-hub
BuildRequires:  python3-kobo-rpmlib
BuildRequires:  python3-psycopg2
BuildRequires:  python3-qpid-proton
BuildRequires:  python3-setuptools
BuildRequires:  python3-six
BuildRequires:  systemd-rpm-macros

%description
CovScan is a Coverity scan scheduler.
It consists of central hub, workers and cli client.


%package client
Summary: CovScan CLI client
Requires: koji
Requires: python3-kobo-client >= 0.15.1-100
Requires: %{name}-common = %{version}-%{release}
Obsoletes: python3-%{name}-client < %{version}-%{release}

%description client
CovScan CLI client


%package common
Summary: CovScan shared files for client, hub and worker

%description common
CovScan shared files for client, hub and worker.


%package worker
Summary: CovScan worker
Requires: csmock
Requires: koji
Requires: python3-kobo-client
Requires: python3-kobo-rpmlib
Requires: python3-kobo-worker
Requires: %{name}-common = %{version}-%{release}
Requires: %{name}-worker-conf = %{version}-%{release}
Obsoletes: covscan-worker-prod < %{version}-%{release}
Obsoletes: covscan-worker-stage < %{version}-%{release}
Obsoletes: python3-%{name}-worker < %{version}-%{release}
Obsoletes: python3-covscan-worker-prod < %{version}-%{release}
Obsoletes: python3-covscan-worker-stage < %{version}-%{release}

%description worker
CovScan worker

%package hub
Summary: CovScan xml-rpc interface and web application
Requires: boost-python3
Requires: httpd
Requires: mod_auth_gssapi
Requires: mod_ssl
Requires: python3-django
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
Requires: file
Requires: python3-bugzilla
Requires: python3-csdiff

Requires: python3-django-debug-toolbar

Requires(post): /usr/bin/pg_isready

Requires: %{name}-common = %{version}-%{release}
Requires: %{name}-hub-conf = %{version}-%{release}
Obsoletes: covscan-hub-prod < %{version}-%{release}
Obsoletes: covscan-hub-stage < %{version}-%{release}
Obsoletes: python3-covscan-hub-prod < %{version}-%{release}
Obsoletes: python3-covscan-hub-stage < %{version}-%{release}
Obsoletes: python3-%{name}-hub < %{version}-%{release}

%description hub
CovScan xml-rpc interface and web application

# define covscan-{worker,hub}-conf-{devel,stage,prod} subpackages
%(for sub in worker hub; do
for alt in devel stage prod; do
cat << EOF
%package ${sub}-conf-${alt}
Summary: Covscan ${sub} ${alt} configuration
Provides: covscan-${sub}-conf = %{version}-%{release}
Conflicts: covscan-${sub}-conf
RemovePathPostfixes: .${alt}
%description ${sub}-conf-${alt}
Covscan ${sub} ${alt} configuration
EOF
done;done)

%prep
%setup -q

%build

# collect static files from Django itself
PYTHONPATH=. osh/hub/manage.py collectstatic --noinput

%py3_build


%install
%py3_install

# avoid transforming /usr/bin/env -S ... to /usr/bin/-S
%global __brp_mangle_shebangs_exclude_from %{_bindir}/osh-cli

# Temporarily provide /usr/bin/covscan for backward compatibility
ln -s osh-cli %{buildroot}%{_bindir}/covscan

# rename settings_local.{stage,prod}.* -> settings_local.*.{stage,prod}
for i in stage prod; do (
    cd %{buildroot}%{python3_sitelib}/osh/hub
    eval mv -v settings_local.{${i}.py,py.${i}}

    cd __pycache__
    for j in settings_local.${i}.*; do
        eval mv -v $j "settings_local\\${j#settings_local.${i}}.${i}"
    done
) done

# create /etc/osh/hub directory
mkdir -p %{buildroot}%{_sysconfdir}/osh/hub

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
%{_sysconfdir}/bash_completion.d/
%{python3_sitelib}/osh/client
%{python3_sitelib}/covscan-*-py%{python3_version}.egg-info

%files common
%defattr(644,root,root,755)
%dir %{_sysconfdir}/osh
%{python3_sitelib}/osh/common
%dir %{python3_sitelib}/osh
%dir /var/lib/osh

%files worker
%defattr(644,root,root,755)
%{python3_sitelib}/osh/worker
%{_unitdir}/covscand.service
%attr(754,root,root) /usr/sbin/covscand

%post client
if test -f /etc/covscan/covscan.conf; then
    mv /etc/covscan/covscan.conf /etc/osh/client.conf
fi

%post worker
%systemd_post covscand.service

%preun worker
%systemd_preun covscand.service

%postun worker
%systemd_postun_with_restart covscand.service

%files worker-conf-devel
%attr(640,root,root) %config(noreplace) /etc/osh/worker.conf

%files worker-conf-stage
%attr(640,root,root) %config(noreplace) /etc/osh/worker.conf.stage

%files worker-conf-prod
%attr(640,root,root) %config(noreplace) /etc/osh/worker.conf.prod

%(for alt in devel stage prod; do
cat << EOF
%post worker-conf-${alt}
if test -f /etc/covscan/covscand.conf; then
    mv /etc/covscan/covscand.conf /etc/osh/worker.conf
fi
EOF
done)

%files hub
%defattr(-,root,apache,-)
%{_sysconfdir}/osh/hub
%{python3_sitelib}/osh/hub
%exclude %{python3_sitelib}/osh/hub/settings_local.py*
%exclude %{python3_sitelib}/osh/hub/__pycache__/settings_local.*
%dir %attr(775,root,apache) /var/log/osh/hub
%ghost %attr(640,apache,apache) /var/log/osh/hub/hub.log
%attr(775,root,apache) /var/lib/osh/hub
%ghost %attr(640,root,apache) /var/lib/osh/hub/secret_key

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

# define covscan-hub-conf-{devel,stage,prod} `post` tasks
%(for alt in devel stage prod; do
cat << EOF
%post hub-conf-${alt}
# Handle 'covscanhub' to 'osh/hub' transition
# https://gitlab.cee.redhat.com/covscan/covscan/-/issues/154
if test -f %{python3_sitelib}/covscanhub/settings_local.py; then
    mv %{python3_sitelib}/{covscanhub,osh/hub}/settings_local.py
fi
EOF
done)

%files hub-conf-devel
%attr(640,root,apache) %config(noreplace) %{python3_sitelib}/osh/hub/settings_local.py
%attr(640,root,apache) %config(noreplace) %{python3_sitelib}/osh/hub/__pycache__/settings_local*.pyc

%files hub-conf-stage
%attr(640,root,apache) %config(noreplace) %{python3_sitelib}/osh/hub/settings_local.py.stage
%attr(640,root,apache) %config(noreplace) %{python3_sitelib}/osh/hub/__pycache__/settings_local*.pyc.stage
%attr(640,root,root) %config(noreplace) /etc/httpd/conf.d/osh-hub-httpd.conf.stage

%files hub-conf-prod
%attr(640,root,apache) %config(noreplace) %{python3_sitelib}/osh/hub/settings_local.py.prod
%attr(640,root,apache) %config(noreplace) %{python3_sitelib}/osh/hub/__pycache__/settings_local*.pyc.prod
%attr(640,root,root) %config(noreplace) /etc/httpd/conf.d/osh-hub-httpd.conf.prod


%changelog
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
