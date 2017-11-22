%define py_version %(python -c "import sys; v=sys.version_info[:2]; print '%%d.%%d'%%v" 2>/dev/null || echo PYTHON-NOT-FOUND)
%define py_prefix  %(python -c "import sys; print sys.prefix" 2>/dev/null || echo PYTHON-NOT-FOUND)
%define py_libdir  %{py_prefix}/lib/python%{py_version}
%define py_incdir  %{py_prefix}/include/python%{py_version}
%define py_sitedir %{py_libdir}/site-packages

%{!?hub_instance:%global hub_instance prod}

Name:           covscan
Version:        0.6.9
Release:        1%{?dist}
License:        Commercial
Summary:        Coverity scan scheduler
Source:         %{name}-%{version}.tar.bz2
BuildArch:      noarch
BuildRequires:  python-devel
BuildRequires:  python-six
BuildRequires:  kobo-client


%description
CovScan is a Coverity scan scheduler.
It consists of central hub, workers and cli client.


%package client
Summary: CovScan CLI client
Requires: kobo-client >= 0.6.0
Requires: python-krbV
Requires: koji

%description client
CovScan CLI client


%package worker-%{hub_instance}
Summary: CovScan worker
Requires: csmock
Requires: kobo-client
Requires: kobo-worker
Requires: kobo-rpmlib
Requires: koji

# FIXME: conf.py should be moved to covscan-common shared by both the packages
Requires: covscan-client

%description worker-%{hub_instance}
CovScan worker


%package hub-%{hub_instance}
Summary: CovScan xml-rpc interface and web application
Requires: kobo-hub
Requires: kobo-client
Requires: kobo-django
Requires: kobo-rpmlib
Requires: Django
%if 0%{?rhel} <= 6
# required by django 1.6
Requires: python-importlib
%endif
Requires: Django-south
Requires: httpd
Requires: mod_auth_kerb
Requires: mod_wsgi
# PostgreSQL adapter for python
Requires: python-psycopg2
Requires: gzip
# inform ET about progress using qpid broker
Requires: python-qpid
# hub is interacting with brew
Requires: koji
# extract tarballs created by cov-mockbuild
Requires: xz
# auth for qpid
Requires: python-krbV
Requires: python-saslwrapper
Requires: cyrus-sasl-gssapi

Requires: csdiff
Requires: python2-csdiff
Requires: python-bugzilla
Requires: yum
Requires: file

Requires: python-django-debug-toolbar > 1.0

# FIXME: should covscan-hub work even though covscan-worker is not installed?
Requires: covscan-worker-%{hub_instance}

%description hub-%{hub_instance}
CovScan xml-rpc interface and web application


%prep
%setup -q


%install
rm -rf ${RPM_BUILD_ROOT}
python setup.py install --root=${RPM_BUILD_ROOT}

mv $RPM_BUILD_ROOT/%{_sysconfdir}/httpd/conf.d/%{hub_instance}-covscanhub-httpd.conf \
   $RPM_BUILD_ROOT/%{_sysconfdir}/httpd/conf.d/covscanhub-httpd.conf
rm -f $RPM_BUILD_ROOT/%{_sysconfdir}/httpd/conf.d/devel-covscanhub-httpd.conf || :
rm -f $RPM_BUILD_ROOT/%{_sysconfdir}/httpd/conf.d/stage-covscanhub-httpd.conf || :
rm -f $RPM_BUILD_ROOT/%{_sysconfdir}/httpd/conf.d/prod-covscanhub-httpd.conf || :
# tweak python paths in config files
sed -i 's@/lib/python2.[0-9]@/lib/python%{py_version}@g' ${RPM_BUILD_ROOT}/etc/httpd/conf.d/covscanhub-httpd.conf

# create symlink /etc/covscan/covscanhub.conf -> .../site-packages/covscanhub/settings.py
# ln -s %{py_sitedir}/covscanhub/settings_local.py ${RPM_BUILD_ROOT}/etc/covscan/covscanhub.conf

mv $RPM_BUILD_ROOT/%{_sysconfdir}/covscan/%{hub_instance}_covscand.conf \
   $RPM_BUILD_ROOT/%{_sysconfdir}/covscan/covscand.conf
rm -f $RPM_BUILD_ROOT/%{_sysconfdir}/covscan/devel_covscand.conf || :
rm -f $RPM_BUILD_ROOT/%{_sysconfdir}/covscan/stage_covscand.conf || :
rm -f $RPM_BUILD_ROOT/%{_sysconfdir}/covscan/prod_covscand.conf || :

# use proper configuration, remove rest
mv $RPM_BUILD_ROOT/%{py_sitedir}/covscanhub/%{hub_instance}_settings_local.py \
   $RPM_BUILD_ROOT/%{py_sitedir}/covscanhub/settings_local.py
rm $RPM_BUILD_ROOT/%{py_sitedir}/covscanhub/prod_settings_local.py* || :
rm $RPM_BUILD_ROOT/%{py_sitedir}/covscanhub/stage_settings_local.py* || :
rm $RPM_BUILD_ROOT/%{py_sitedir}/covscanhub/devel_settings_local.py* || :

# delete covscan-<version>-py2.5.egg-info file
egg_info=$RPM_BUILD_ROOT/%{py_sitedir}/%{name}-%{version}-py%{py_version}.egg-info
if [ -f $egg_info ]; then
  rm $egg_info
fi

# create /var/lib dirs
mkdir -p $RPM_BUILD_ROOT/var/lib/covscanhub/tasks
mkdir -p $RPM_BUILD_ROOT/var/lib/covscanhub/upload

# create log file
mkdir -p $RPM_BUILD_ROOT/var/log
touch $RPM_BUILD_ROOT/var/log/covscanhub.log

# copy checker_groups.txt
cp -R covscanhub/scripts/checker_groups.txt $RPM_BUILD_ROOT/%{py_sitedir}/covscanhub/scripts/

# make manage.py executable
chmod 0755 $RPM_BUILD_ROOT%{py_sitedir}/covscanhub/manage.py

%clean
rm -rf $RPM_BUILD_ROOT


%files client
%defattr(644,root,root,755)
%{py_sitedir}/covscan
%attr(755,root,root) /usr/bin/covscan
%attr(644,root,root) %config(noreplace) /etc/covscan/covscan.conf
%{_sysconfdir}/bash_completion.d/


%files worker-%{hub_instance}
%defattr(644,root,root,755)
%{py_sitedir}/covscand
%attr(640,root,root) %config(noreplace) /etc/covscan/covscand.conf
%attr(755,root,root) /etc/init.d/covscand
%attr(754,root,root) /usr/sbin/covscand


%files hub-%{hub_instance}
%defattr(-,root,apache,-)
%{py_sitedir}/covscanhub
%attr(640,root,root) /etc/httpd/conf.d/covscanhub-httpd.conf
%ghost %attr(640,apache,apache) /var/log/covscanhub.log
%dir %attr(775,root,apache) /var/lib/covscanhub
%dir %attr(775,root,apache) /var/lib/covscanhub/tasks
%dir %attr(775,root,apache) /var/lib/covscanhub/upload


%changelog
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
