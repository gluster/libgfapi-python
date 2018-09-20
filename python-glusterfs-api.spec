# What's in a name ? :‑O
#
# * The source repo is named libgfapi-python
# * The python package is named gfapi
# * The RPM package is named python-glusterfs-api to be analogous to
#   glusterfs-api RPM which provides the libgfapi C library

%global src_repo_name libgfapi-python
%global python_pkg_name gfapi
%global pkg_name glusterfs-api

%if ( 0%{?fedora} && 0%{?fedora} > 26 ) || ( 0%{?rhel} && 0%{?rhel} > 7 )
%global with_python3 1
%endif

%global _description \
libgfapi is a library that allows applications to natively access \
GlusterFS volumes. This package contains python bindings to libgfapi. \
See https://libgfapi-python.rtfd.io/ for more details.

Name:             python-%{pkg_name}
Summary:          Python bindings for GlusterFS libgfapi
Version:          1.2
Release:          1%{?dist}
License:          GPLv2 or LGPLv3+
Group:            System Environment/Libraries
Vendor:           Gluster Community
URL:              https://github.com/gluster/%{src_repo_name}
Source0:          %pypi_source %{python_pkg_name} %{version}
BuildArch:        noarch

%description %{_description}

# BEGIN python2 package section
%package -n python2-%{pkg_name}

Summary:          %{summary}
BuildRequires:    python2-setuptools
Requires:         glusterfs-api >= 3.12.0
Requires:         python2-gluster >= 3.12.0
%{?python_provide:%python_provide python2-%{pkg_name}}

%description -n python2-%{pkg_name} %{_description}
# END python2 package section

# BEGIN python3 package section
%if 0%{?with_python3}
%package -n python3-%{pkg_name}

Summary:          %{summary}
BuildRequires:    python3-setuptools
Requires:         glusterfs-api >= 3.12.0
Requires:         python3-gluster >= 3.12.0
%{?python_provide:%python_provide python3-%{pkg_name}}


%description -n python3-%{pkg_name} %{_description}
%endif
# END python3 package section

%prep
%autosetup -n %{python_pkg_name}-%{version} -S git

%build
%py2_build
%if 0%{?with_python3}
%py3_build
%endif

%install
%py2_install
%if 0%{?with_python3}
%py3_install
%endif

%files -n python2-%{pkg_name}
%doc README.rst
%license COPYING-GPLV2 COPYING-LGPLV3
%{python2_sitelib}/*
# As weird as it may seem, excluding __init__.py[co] is intentional as
# it is provided by python-gluster package which is a dependency.
%exclude %{python2_sitelib}/gluster/__init__*

%if 0%{?with_python3}
%files -n python3-%{pkg_name}
%doc README.rst
%license COPYING-GPLV2 COPYING-LGPLV3
%{python3_sitelib}/*
# As weird as it may seem, excluding __init__.py[co] is intentional as
# it is provided by python-gluster package which is a dependency.
%exclude %{python3_sitelib}/gluster/__init__*
%endif

%changelog
* Wed Sep 19 2018 Prashanth Pai <ppai@redhat.com> - 1.2-0
- Add Python 3.x support
- Add mknod() and get_volume_id() APIs
- Support setting multiple hosts (volfile servers)
- Support mounting over unix domain socket
- Disable client logging by default

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
