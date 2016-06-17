#!/usr/bin/python
#
# Copyright (c) 2016 Red Hat, Inc.
#
# This file is part of libgfapi-python project which is a
# subproject of GlusterFS ( www.gluster.org)
#
# This file is licensed to you under your choice of the GNU Lesser
# General Public License, version 3 or any later version (LGPLv3 or
# later), or the GNU General Public License, version 2 (GPLv2), in all
# cases as published by the Free Software Foundation.

from setuptools import setup

from gluster import __canonical_version__ as version


name = 'gfapi'


setup(
    name=name,
    version=version,
    description='Python bindings for GlusterFS libgfapi',
    license='GPLv2 or LGPLv3+',
    author='Red Hat, Inc.',
    author_email='gluster-devel@gluster.org',
    url='http://www.gluster.org',
    packages=['gluster', ],
    test_suite='nose.collector',
    classifiers=[
        'Development Status :: 5 - Production/Stable'
        'Intended Audience :: Developers'
        'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)'
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)'
        'Operating System :: POSIX :: Linux'
        'Programming Language :: Python'
        'Programming Language :: Python :: 2'
        'Programming Language :: Python :: 2.6'
        'Programming Language :: Python :: 2.7'
        'Topic :: System :: Filesystems'
    ],
    install_requires=[],
    scripts=[],
    entry_points={},
)
