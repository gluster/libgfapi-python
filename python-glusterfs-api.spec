# What's in a name ? :‑O
#
# * The source repo is named libgfapi-python
# * The python package is named gfapi
# * The RPM package is named python-glusterfs-api to be analogous to
#   glusterfs-api RPM which provides the libgfapi C library

%global python_package_name gfapi

Name:             python-glusterfs-api
Summary:          Python bindings for GlusterFS libgfapi
Version:          1.1
Release:          1%{?dist}
License:          GPLv2 or LGPLv3+
Group:            System Environment/Libraries
Vendor:           Gluster Community
URL:              https://github.com/gluster/libgfapi-python
Source0:          https://files.pythonhosted.org/packages/source/g/gfapi/%{python_package_name}-%{version}.tar.gz

BuildArch:        noarch
BuildRequires:    python-setuptools

# Provides libgfapi.so
Requires:         glusterfs-api >= 3.7.0
# Provides gluster/__init__.py
Requires:         python-gluster >= 3.7.0

%description
libgfapi is a library that allows applications to natively access GlusterFS
volumes. This package contains python bindings to libgfapi.

See http://libgfapi-python.rtfd.io/ for more details.

%prep
%setup -q -n %{python_package_name}-%{version}

%build
%{__python2} setup.py build

%install
rm -rf %{buildroot}
%{__python2} setup.py install --skip-build --root %{buildroot}

%files
%doc README.rst
%license COPYING-GPLV2 COPYING-LGPLV3
%{python2_sitelib}/*
# As weird as it may seem, excluding __init__.py[co] is intentional as
# it is provided by python-gluster package which is a dependency.
%exclude %{python2_sitelib}/gluster/__init__*

%changelog
* Tue Aug 9 2016 Prashanth Pai <ppai@redhat.com> - 1.1-1
- Update spec file

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
