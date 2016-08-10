# Copyright (c) 2016 Red Hat, Inc.
#
# This file is part of libgfapi-python project which is a
# subproject of GlusterFS ( www.gluster.org)
#
# This file is licensed to you under your choice of the GNU Lesser
# General Public License, version 3 or any later version (LGPLv3 or
# later), or the GNU General Public License, version 2 (GPLv2), in all
# cases as published by the Free Software Foundation.

import unittest

from gluster.gfapi import utils
from gluster.gfapi.exceptions import VolumeNotMounted


class TestUtils(unittest.TestCase):

    def test_validate_mount(self):

        class _FakeVol(object):

            def __init__(self):
                self.fs = None
                self._mounted = None
                self.volname = "vol1"

            @utils.validate_mount
            def test_method(self):
                return

        v = _FakeVol()
        try:
            v.test_method()
        except VolumeNotMounted as err:
            self.assertEqual(str(err), 'Volume "vol1" not mounted.')
        else:
            self.fail("Expected VolumeNotMounted exception.")

        v.fs = 12345
        v._mounted = True
        # Shouldn't raise exception.
        v.test_method()

    def test_validate_glfd(self):

        class _FakeFile(object):

            def __init__(self, fd, path=None):
                self.fd = fd

            @utils.validate_glfd
            def test_method(self):
                return

            def close(self):
                self.fd = None

        f = _FakeFile(1234)
        f.close()
        self.assertTrue(f.fd is None)
        self.assertRaises(OSError, f.test_method)

        f.fd = 1234
        # Shouldn't raise exception.
        f.test_method()
