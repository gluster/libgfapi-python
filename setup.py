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

import os
import re
from setuptools import setup, find_packages


# Get version without importing.
gfapi_file_path = os.path.join(os.path.dirname(__file__),
                               'gluster/gfapi/__init__.py')
with open(gfapi_file_path) as f:
    for line in f:
        match = re.match(r"__version__.*'([0-9.]+)'", line)
        if match:
            version = match.group(1)
            break
    else:
        raise Exception("Couldn't find version in setup.py")


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='gfapi',
    version=version,
    description='Python bindings for GlusterFS libgfapi',
    long_description=read('README.rst'),
    license='GPLv2 or LGPLv3+',
    author='Red Hat, Inc.',
    author_email='gluster-devel@gluster.org',
    url='http://www.gluster.org',
    packages=find_packages(exclude=['test*']),
    test_suite='nose.collector',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',  # noqa
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: System :: Filesystems',
    ],
)
