%define py_version %(python -c "import sys; v=sys.version_info[:2]; print '%%d.%%d'%%v" 2>/dev/null || echo PYTHON-NOT-FOUND)
%define py_prefix  %(python -c "import sys; print sys.prefix" 2>/dev/null || echo PYTHON-NOT-FOUND)
%define py_libdir  %{py_prefix}/lib/python%{py_version}
%define py_incdir  %{py_prefix}/include/python%{py_version}
%define py_sitedir %{py_libdir}/site-packages


Name:           covscan
Version:        0.4.0
Release:        1%{?dist}
License:        Commercial
Summary:        Coverity scan scheduler
Group:          Applications/Engineering
Source:         %{name}-%{version}.tar.bz2
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      noarch
BuildRequires:  python-devel >= 2.4
BuildRequires:  kobo-client >= 0.3.4


%description
CovScan is a Coverity scan scheduler.
It consists of central hub, workers and cli client.


%package client
Summary: CovScan CLI client
Group: Applications/Engineering
Requires: kobo-client >= 0.3.4
Requires: python-krbV
Requires: brewkoji

%description client
CovScan CLI client


%package worker
Summary: CovScan worker
Group: Applications/Engineering
# Requires: covscan-client = %{version}-%{release}
Requires: kobo-worker >= 0.3.4
Requires: kobo-rpmlib
Requires: cppcheck
%description worker
CovScan worker


%package hub
Summary: CovScan xml-rpc interface and web application
Group: Applications/Engineering
# Requires: covscan-client = %{version}-%{release}
Requires: kobo-hub >= 0.3.4
Requires: kobo-django >= 0.3.4
Requires: kobo-client
Requires: Django >= 1.2
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
Requires: brewkoji
# extract tarballs created by cov-mockbuild
Requires: xz
# auth for qpid
Requires: python-krbV
Requires: python-saslwrapper
Requires: cyrus-sasl-gssapi

Requires: csdiff
Requires: python-bugzilla
Requires: yum


%description hub
CovScan xml-rpc interface and web application


%prep
%setup -q


%build
echo OK


%install
rm -rf ${RPM_BUILD_ROOT}
python setup.py install --root=${RPM_BUILD_ROOT}

# tweak python paths in config files
sed -i 's@/lib/python2.[0-9]@/lib/python%{py_version}@g' ${RPM_BUILD_ROOT}/etc/httpd/conf.d/covscanhub-httpd.conf

# create symlink /etc/covscan/covscanhub.conf -> .../site-packages/covscanhub/settings.py
ln -s %{py_sitedir}/covscanhub/settings_local.py ${RPM_BUILD_ROOT}/etc/covscan/covscanhub.conf

# delete covscan-<version>-py2.5.egg-info file
egg_info=$RPM_BUILD_ROOT/%{py_sitedir}/%{name}-%{version}-py%{py_version}.egg-info
if [ -f $egg_info ]; then
  rm $egg_info
fi

# create /var/lib dirs
mkdir -p $RPM_BUILD_ROOT/var/lib/covscanhub/tasks
mkdir -p $RPM_BUILD_ROOT/var/lib/covscanhub/upload

# create log file
if [ ! -d $RPM_BUILD_ROOT/var/log ]
then
    mkdir $RPM_BUILD_ROOT/var/log
fi
touch $RPM_BUILD_ROOT/var/log/covscanhub.log

# copy checker_groups.txt
cp -R covscanhub/scripts/checker_groups.txt $RPM_BUILD_ROOT/%{py_sitedir}/covscanhub/scripts/


%clean
rm -rf $RPM_BUILD_ROOT


%files client
%defattr(644,root,root,755)
%{py_sitedir}/covscan
%attr(755,root,root) /usr/bin/covscan
%attr(644,root,root) %config(noreplace) /etc/covscan/covscan.conf
%{_sysconfdir}/bash_completion.d/


%files worker
%defattr(644,root,root,755)
%{py_sitedir}/covscand
%attr(640,root,root) %config(noreplace) /etc/covscan/covscand.conf
%attr(755,root,root) /etc/init.d/covscand
%attr(754,root,root) /usr/sbin/covscand


%files hub
%defattr(644,root,apache,755)
%{py_sitedir}/covscanhub
%attr(640,root,apache) %config(noreplace) %{py_sitedir}/covscanhub/settings.py
%attr(640,root,apache) %config(noreplace) %{py_sitedir}/covscanhub/settings_local.py
%attr(640,root,apache) %{py_sitedir}/covscanhub/settings.py[co]
%attr(640,root,apache) %{py_sitedir}/covscanhub/settings_local.py[co]
%attr(640,root,root) %config(noreplace) /etc/httpd/conf.d/covscanhub-httpd.conf
%config %ghost /var/log/covscanhub.log
%dir %attr(775,root,apache) /var/lib/covscanhub
%dir %attr(775,root,apache) /var/lib/covscanhub/tasks
%dir %attr(775,root,apache) /var/lib/covscanhub/upload
%{_sysconfdir}/covscan/covscanhub.conf


%changelog
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
