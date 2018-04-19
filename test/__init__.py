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
try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser


def get_test_config():
    """
    Reads test.conf config file which contains configurable options
    to run functional tests.

    :returns: ConfigParser instance if test.conf found, None otherwise.
    """
    dirname = os.path.dirname(__file__)
    conf_file = dirname + "/test.conf"
    if os.path.exists(conf_file):
        config = ConfigParser()
        config.read(conf_file)
        return config
    return None
