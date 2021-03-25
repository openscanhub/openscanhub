%{!?hub_instance:%global hub_instance prod}

%if 0%{?fedora} || 0%{?rhel} > 7
%bcond_without python3
%else
%bcond_with python3
%endif

%if 0%{?rhel} > 7 || 0%{?fedora} > 30
# Disable python2 build by default
%bcond_with python2
%else
%bcond_without python2
%endif

Name:           covscan
Version:        0.7.1
Release:        1%{?dist}
License:        Commercial
Summary:        Coverity scan scheduler
Source:         %{name}-%{version}.tar.bz2
BuildArch:      noarch

%if %{with python2}
BuildRequires:  python2-devel
BuildRequires:  python2-six
BuildRequires:  kobo-client
%endif

%if %{with python3}
BuildRequires:  python3-devel
BuildRequires:  python3-six
BuildRequires:  python3-kobo-client
%endif

%{?!git_version: %global git_version %{version}}

%description
CovScan is a Coverity scan scheduler.
It consists of central hub, workers and cli client.


%package client
Summary: CovScan CLI client
%if %{with python3}
Requires: python3-%{name}-client = %{git_version}-%{release}
%else
Requires: python2-%{name}-client = %{git_version}-%{release}
%endif

%description client
CovScan CLI client

%package worker-%{hub_instance}
Summary: CovScan worker
%if %{with python3}
Requires: python3-%{name}-worker-%{hub_instance} = %{git_version}-%{release}
%else
Requires: python2-%{name}-worker-%{hub_instance} = %{git_version}-%{release}
%endif

%description worker-%{hub_instance}
CovScan worker

%package hub-%{hub_instance}
Summary: CovScan xml-rpc interface and web application
%if %{with python3}
Requires: python3-%{name}-hub-%{hub_instance} = %{git_version}-%{release}
%else
Requires: python2-%{name}-hub-%{hub_instance} = %{git_version}-%{release}
%endif

%description hub-%{hub_instance}
CovScan xml-rpc interface and web application



%if %{with python2}
%package -n python2-%{name}-client
Summary: CovScan CLI client python2 library
Requires: kobo-client >= 0.8.0
Requires: koji
Requires: python-krbV
Requires: python2-koji
Requires: python2-requests

%description -n python2-%{name}-client
CovScan CLI client python2 library


%package -n python2-%{name}-worker-%{hub_instance}
Summary: CovScan worker python2 library
Requires: csmock
Requires: kobo-client
Requires: kobo-worker
Requires: kobo-rpmlib
Requires: koji
Requires: python2-koji

# FIXME: conf.py should be moved to covscan-common shared by both the packages
Requires: python2-%{name}-client

%description -n python2-%{name}-worker-%{hub_instance}
CovScan worker python2 library


%package -n python2-%{name}-hub-%{hub_instance}
Summary: CovScan xml-rpc interface and web application python2 library
Requires: %{name}-hub-%{hub_instance}
Requires: kobo-hub
Requires: kobo-client
Requires: kobo-django
Requires: kobo-rpmlib
Requires: boost-python
Requires: Django
%if 0%{?rhel} <= 6
# required by django 1.6
Requires: python-importlib
%endif
Requires: httpd
%if 0%{?rhel} <= 7
Requires: mod_auth_kerb
%else
Requires: mod_auth_gssapi
%endif
Requires: mod_wsgi
# PostgreSQL adapter for python
Requires: python-psycopg2
Requires: gzip
# inform ET about progress using UMB (Unified Message Bus)
Requires: python2-qpid-proton
# hub is interacting with brew
Requires: koji
Requires: python2-koji
# extract tarballs created by cov-mockbuild
Requires: xz

Requires: csdiff
Requires: python2-csdiff
Requires: python-bugzilla
Requires: yum
Requires: file

Requires: python-django-debug-toolbar > 1.0

# FIXME: should covscan-hub work even though covscan-worker is not installed?
Requires: covscan-worker-%{hub_instance}

%description -n python2-%{name}-hub-%{hub_instance}
CovScan xml-rpc interface and web application python2 library

%endif

%if %{with python3}
%package -n python3-%{name}-client
Summary: CovScan CLI client python3 library
Requires: python3-kobo-client >= 0.15.1-100
Requires: koji
Requires: python3-koji

%description -n python3-%{name}-client
CovScan CLI client python3 library


%package -n python3-%{name}-worker-%{hub_instance}
Summary: CovScan worker python3 library
Requires: csmock
Requires: python3-kobo-client
Requires: python3-kobo-worker
Requires: python3-kobo-rpmlib
Requires: koji
Requires: python3-koji

# FIXME: conf.py should be moved to covscan-common shared by both the packages
Requires: python3-%{name}-client

%description -n python3-%{name}-worker-%{hub_instance}
CovScan worker python3 library


%package -n python3-%{name}-hub-%{hub_instance}
Summary: CovScan xml-rpc interface and web application python3 library
Requires: %{name}-hub-%{hub_instance}
Requires: python3-kobo-hub
Requires: python3-kobo-client
Requires: python3-kobo-django
Requires: python3-kobo-rpmlib
Requires: python3-django
Requires: boost-python3
%if 0%{?rhel} <= 6
# required by django 1.6
Requires: python-importlib
%endif
Requires: httpd
%if 0%{?rhel} <= 7
Requires: mod_auth_kerb
%else
Requires: mod_auth_gssapi
%endif
Requires: python3-mod_wsgi
# PostgreSQL adapter for python
Requires: python3-psycopg2
Requires: gzip
# inform ET about progress using UMB (Unified Message Bus)
Requires: python3-qpid-proton
# hub is interacting with brew
Requires: koji
Requires: python3-koji
# extract tarballs created by cov-mockbuild
Requires: xz
# auth for qpid
#Requires: python3-saslwrapper
#Requires: cyrus-sasl-gssapi

Requires: csdiff
Requires: python3-csdiff
Requires: python3-bugzilla
Requires: yum
Requires: file

Requires: python3-django-debug-toolbar > 1.0

# FIXME: should covscan-hub work even though covscan-worker is not installed?
Requires: python3-%{name}-worker-%{hub_instance}

%description -n python3-%{name}-hub-%{hub_instance}
CovScan xml-rpc interface and web application python3 library

%endif


%prep
%setup -q

%build
%if %{with python2}
%py2_build
%endif

%if %{with python3}
%py3_build
%endif


%install
rm -rf ${RPM_BUILD_ROOT}
#%{__python2} setup.py install --root=${RPM_BUILD_ROOT}

%if %{with python2}
%py2_install
%endif

%if %{with python3}
%py3_install
%endif


mv $RPM_BUILD_ROOT/%{_sysconfdir}/httpd/conf.d/%{hub_instance}-covscanhub-httpd.conf \
   $RPM_BUILD_ROOT/%{_sysconfdir}/httpd/conf.d/covscanhub-httpd.conf
rm -f $RPM_BUILD_ROOT/%{_sysconfdir}/httpd/conf.d/devel-covscanhub-httpd.conf || :
rm -f $RPM_BUILD_ROOT/%{_sysconfdir}/httpd/conf.d/stage-covscanhub-httpd.conf || :
rm -f $RPM_BUILD_ROOT/%{_sysconfdir}/httpd/conf.d/prod-covscanhub-httpd.conf || :
# tweak python paths in config files

# TODO
%if %{with python3}
sed -i 's@/lib/python2.[0-9]@/lib/python%{python3_version}@g' ${RPM_BUILD_ROOT}/etc/httpd/conf.d/covscanhub-httpd.conf
%else
sed -i 's@/lib/python2.[0-9]@/lib/python%{python2_version}@g' ${RPM_BUILD_ROOT}/etc/httpd/conf.d/covscanhub-httpd.conf
%endif

# create symlink /etc/covscan/covscanhub.conf -> .../site-packages/covscanhub/settings.py
# ln -s %{python2_sitelib}/covscanhub/settings_local.py ${RPM_BUILD_ROOT}/etc/covscan/covscanhub.conf

mv $RPM_BUILD_ROOT/%{_sysconfdir}/covscan/%{hub_instance}_covscand.conf \
   $RPM_BUILD_ROOT/%{_sysconfdir}/covscan/covscand.conf
rm -f $RPM_BUILD_ROOT/%{_sysconfdir}/covscan/devel_covscand.conf || :
rm -f $RPM_BUILD_ROOT/%{_sysconfdir}/covscan/stage_covscand.conf || :
rm -f $RPM_BUILD_ROOT/%{_sysconfdir}/covscan/prod_covscand.conf || :

# use proper configuration, remove rest

%if %{with python2}
mv $RPM_BUILD_ROOT/%{python2_sitelib}/covscanhub/%{hub_instance}_settings_local.py \
   $RPM_BUILD_ROOT/%{python2_sitelib}/covscanhub/settings_local.py
rm $RPM_BUILD_ROOT/%{python2_sitelib}/covscanhub/prod_settings_local.py* || :
rm $RPM_BUILD_ROOT/%{python2_sitelib}/covscanhub/stage_settings_local.py* || :
rm $RPM_BUILD_ROOT/%{python2_sitelib}/covscanhub/devel_settings_local.py* || :
%endif

%if %{with python3}
mv $RPM_BUILD_ROOT/%{python3_sitelib}/covscanhub/%{hub_instance}_settings_local.py \
   $RPM_BUILD_ROOT/%{python3_sitelib}/covscanhub/settings_local.py
rm $RPM_BUILD_ROOT/%{python3_sitelib}/covscanhub/prod_settings_local.py* || :
rm $RPM_BUILD_ROOT/%{python3_sitelib}/covscanhub/stage_settings_local.py* || :
rm $RPM_BUILD_ROOT/%{python3_sitelib}/covscanhub/devel_settings_local.py* || :
sed -r -i 's|(#!/usr/bin/python)2|\13|' $RPM_BUILD_ROOT/%{_bindir}/covscan
%endif

# create /var/lib dirs
mkdir -p $RPM_BUILD_ROOT/var/lib/covscanhub/tasks
mkdir -p $RPM_BUILD_ROOT/var/lib/covscanhub/upload

# create log file
mkdir -p $RPM_BUILD_ROOT/var/log/covscanhub
touch $RPM_BUILD_ROOT/var/log/covscanhub/covscanhub.log

# copy checker_groups.txt
%if %{with python2}
cp -R covscanhub/scripts/checker_groups.txt $RPM_BUILD_ROOT/%{python2_sitelib}/covscanhub/scripts/
%endif

%if %{with python3}
cp -R covscanhub/scripts/checker_groups.txt $RPM_BUILD_ROOT/%{python3_sitelib}/covscanhub/scripts/
%endif

# make manage.py executable
%if %{with python2}
chmod 0755 $RPM_BUILD_ROOT%{python2_sitelib}/covscanhub/manage.py
%endif

%if %{with python3}
chmod 0755 $RPM_BUILD_ROOT%{python3_sitelib}/covscanhub/manage.py
%endif

%files client
%defattr(644,root,root,755)
%attr(755,root,root) /usr/bin/covscan
%attr(644,root,root) %config(noreplace) /etc/covscan/covscan.conf
%{_sysconfdir}/bash_completion.d/

%files worker-%{hub_instance}
%defattr(644,root,root,755)
%attr(640,root,root) %config(noreplace) /etc/covscan/covscand.conf
%attr(755,root,root) /etc/init.d/covscand
%attr(754,root,root) /usr/sbin/covscand

%files hub-%{hub_instance}
%defattr(-,root,apache,-)
%attr(640,root,root) %config(noreplace) /etc/httpd/conf.d/covscanhub-httpd.conf
%dir %attr(775,root,apache) /var/log/covscanhub
%ghost %attr(640,apache,apache) /var/log/covscanhub/covscanhub.log
%dir %attr(775,root,apache) /var/lib/covscanhub
%dir %attr(775,root,apache) /var/lib/covscanhub/tasks
%dir %attr(775,root,apache) /var/lib/covscanhub/upload

%if %{with python2}
%files -n python2-%{name}-client
%defattr(644,root,root,755)
%{python2_sitelib}/covscan
%{python2_sitelib}/covscan-%{version}-py%{python2_version}.egg-info


%files -n python2-%{name}-worker-%{hub_instance}
%defattr(644,root,root,755)
%{python2_sitelib}/covscand


%files -n python2-%{name}-hub-%{hub_instance}
%defattr(-,root,apache,-)
%{python2_sitelib}/covscanhub

%endif

%if %{with python3}
%files -n python3-%{name}-client
%defattr(644,root,root,755)
%{python3_sitelib}/covscan
%{python3_sitelib}/covscan-%{version}-py%{python3_version}.egg-info


%files -n python3-%{name}-worker-%{hub_instance}
%defattr(644,root,root,755)
%{python3_sitelib}/covscand


%files -n python3-%{name}-hub-%{hub_instance}
%defattr(-,root,apache,-)
%{python3_sitelib}/covscanhub

%endif


%changelog
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
