# Copyright (c) 2016 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import unittest

from gluster import utils
from gluster.exceptions import VolumeNotMounted


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
