Name:           fake-django
Version:        1.6.5
Release:        1%{?dist}
License:        BSD
Summary:        fake django provide
Group:          Applications/Engineering
BuildArch:      noarch
Provides:       Django = 1.6.5
Obsoletes:      Django < 1.6

%description
fake django provide

%install
mkdir -p %{buildroot}/%{python2_sitelib}/django

%files
%{python2_sitelib}/django/

%changelog
* Sun Aug 03 2014 Tomas Tomecek <ttomecek@redhat.com> - 1.6.5-1
- initial

