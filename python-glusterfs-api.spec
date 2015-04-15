
# From https://fedoraproject.org/wiki/Packaging:Python#Macros
%if ( 0%{?rhel} && 0%{?rhel} <= 5 )
%{!?python_sitelib: %global python_sitelib %(python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python_sitearch: %global python_sitearch %(python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%endif

Name:             python-glusterfs-api
Summary:          python binding of Gluster libgfapi
Version:          1.0.0
Release:          1%{?dist}
License:          GPLv2 or LGPLv3+
BuildArch:        noarch
URL:              https://github.com/gluster/libgfapi-python
Vendor:           gluster.org
Source0:          %{name}-%{version}.tar.gz
BuildRoot:        %{_tmppath}/%{name}-%{version}-root
#at build time
BuildRequires:    python-setuptools
BuildRequires:    python2-devel
#at time of run
Requires:         python
Requires:         python-ctypes
Requires:         glusterfs-api >= 3.6.1
Requires:         python-gluster >= 3.7.0

%description
GlusterFS is a distributed file-system capable of scaling to several
petabytes. It aggregates various storage bricks over Infiniband RDMA
or TCP/IP interconnect into one large parallel network file
system. GlusterFS is one of the most sophisticated file systems in
terms of features and extensibility.  It borrows a powerful concept
called Translators from GNU Hurd kernel. Much of the code in GlusterFS
is in user space and easily manageable.

libgfapi is one of the access mechanism for GlusterFS volumes and this package
contains python bindings of libgfapi.

%prep
%setup -q


%build
%{__python} setup.py build


%install
rm -rf %{buildroot}
mkdir -p %{buildroot}/%{python2_sitelib}/gluster/gfapi/
%{__python2} setup.py install --skip-build --verbose --root %{buildroot}
mv %{buildroot}/%{python2_sitelib}/gluster/gfapi.py* %{buildroot}/%{python2_sitelib}/gluster/gfapi/
mv %{buildroot}/%{python2_sitelib}/gluster/api.py* %{buildroot}/%{python2_sitelib}/gluster/gfapi/
mv %{buildroot}/%{python2_sitelib}/gluster/__init__.py* %{buildroot}/%{python2_sitelib}/gluster/gfapi/



%files
%doc README.md
%{python2_sitelib}/gluster/gfapi/
# Don't expect a .egg-info file on EL5
%if ( ! ( 0%{?rhel} && 0%{?rhel} < 6 ) )
%{python_sitelib}/*.egg-info
%endif
# unit and functional test files are part of source, however we are not packaging it, so adding them in
# exclude.
%exclude %{buildroot}/test/
%exclude %{buildroot}/functional_tests.sh
%exclude %{buildroot}/test-requirements.txt
%exclude %{buildroot}/tox.ini
%exclude %{buildroot}/unittests.sh

%{!?_licensedir:%global license %%doc}

%license COPYING-GPLV2 COPYING-LGPLV3

%changelog
* Wed May 20 2015 Humble Chirammal <hchiramm@redhat.com> - 1.0.0-1
- Change Package name to python-glusterfs-api instead of python-gluster-gfapi.

* Mon May 18 2015 Humble Chirammal <hchiramm@redhat.com> - 1.0.0-0beta3
- Added license macro.

* Wed Apr 15 2015 Humble Chirammal <hchiramm@redhat.com> - 1.0.0-0beta2
- Added detailed description for this package.

* Tue Apr 14 2015 Humble Chirammal <hchiramm@redhat.com> - 1.0.0-0beta1
- Renamed glusterfs module to gluster

* Wed Feb 11 2015 Humble Chirammal <hchiramm@redhat.com> - 1.0.0-0
- Introducing spec file.
