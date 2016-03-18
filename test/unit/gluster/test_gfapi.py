#  Copyright (c) 2012-2015 Red Hat, Inc.
#  This file is part of libgfapi-python project
#  (http://review.gluster.org/#/q/project:libgfapi-python)
#  which is a subproject of GlusterFS ( www.gluster.org)
#
#  This file is licensed to you under your choice of the GNU Lesser
#  General Public License, version 3 or any later version (LGPLv3 or
#  later), or the GNU General Public License, version 2 (GPLv2), in all
#  cases as published by the Free Software Foundation.


import unittest
import gluster
import os
import stat
import errno

from gluster.gfapi import File, Dir, Volume
from gluster import api
from gluster.exceptions import LibgfapiException
from nose import SkipTest
from mock import Mock, patch
from contextlib import nested


def _mock_glfs_close(fd):
    return 0


def _mock_glfs_closedir(fd):
    return


def _mock_glfs_new(volid):
    return 12345


def _mock_glfs_init(fs):
    return 0


def _mock_glfs_set_volfile_server(fs, proto, host, port):
    return 0


def _mock_glfs_fini(fs):
    return 0


def _mock_glfs_set_logging(fs, log_file, log_level):
    return 0


class TestFile(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.fd = File(2, 'fakefile')

    @classmethod
    def tearDownClass(cls):
        cls.fd = None

    def setUp(self):
        self._saved_glfs_close = gluster.gfapi.api.glfs_close
        gluster.gfapi.api.glfs_close = _mock_glfs_close

    def tearDown(self):
        gluster.gfapi.api.glfs_close = self._saved_glfs_close

    def test_fchmod_success(self):
        mock_glfs_fchmod = Mock()
        mock_glfs_fchmod.return_value = 0

        with patch("gluster.gfapi.api.glfs_fchmod", mock_glfs_fchmod):
            self.fd.fchmod(0600)

    def test_fchmod_fail_exception(self):
        mock_glfs_fchmod = Mock()
        mock_glfs_fchmod.return_value = -1

        with patch("gluster.gfapi.api.glfs_fchmod", mock_glfs_fchmod):
            self.assertRaises(OSError, self.fd.fchmod, 0600)

    def test_fchown_success(self):
        mock_glfs_fchown = Mock()
        mock_glfs_fchown.return_value = 0

        with patch("gluster.gfapi.api.glfs_fchown", mock_glfs_fchown):
            self.fd.fchown(9, 11)

    def test_fchown_fail_exception(self):
        mock_glfs_fchown = Mock()
        mock_glfs_fchown.return_value = -1

        with patch("gluster.gfapi.api.glfs_fchown", mock_glfs_fchown):
            self.assertRaises(OSError, self.fd.fchown, 9, 11)

    def test_dup(self):
        mock_glfs_dup = Mock()
        mock_glfs_dup.return_value = 2

        with patch("gluster.gfapi.api.glfs_dup", mock_glfs_dup):
            f = self.fd.dup()
            self.assertTrue(isinstance(f, File))
            self.assertEqual(f.originalpath, "fakefile")
            self.assertEqual(f.fd, 2)

    def test_fdatasync_success(self):
        mock_glfs_fdatasync = Mock()
        mock_glfs_fdatasync.return_value = 4

        with patch("gluster.gfapi.api.glfs_fdatasync", mock_glfs_fdatasync):
            self.fd.fdatasync()

    def test_fdatasync_fail_exception(self):
        mock_glfs_fdatasync = Mock()
        mock_glfs_fdatasync.return_value = -1

        with patch("gluster.gfapi.api.glfs_fdatasync", mock_glfs_fdatasync):
            self.assertRaises(OSError, self.fd.fdatasync)

    def test_fstat_success(self):
        mock_glfs_fstat = Mock()
        mock_glfs_fstat.return_value = 0

        with patch("gluster.gfapi.api.glfs_fstat", mock_glfs_fstat):
            s = self.fd.fstat()
            self.assertTrue(isinstance(s, api.Stat))

    def test_fstat_fail_exception(self):
        mock_glfs_fstat = Mock()
        mock_glfs_fstat.return_value = -1

        with patch("gluster.gfapi.api.glfs_fstat", mock_glfs_fstat):
            self.assertRaises(OSError, self.fd.fstat)

    def test_fsync_success(self):
        mock_glfs_fsync = Mock()

        with patch("gluster.gfapi.api.glfs_fsync", mock_glfs_fsync):
            self.fd.fsync()

    def test_fsync_fail_exception(self):
        mock_glfs_fsync = Mock()
        mock_glfs_fsync.return_value = -1

        with patch("gluster.gfapi.api.glfs_fsync", mock_glfs_fsync):
            self.assertRaises(OSError, self.fd.fsync)

    def test_lseek_success(self):
        mock_glfs_lseek = Mock()
        mock_glfs_lseek.return_value = 20

        with patch("gluster.gfapi.api.glfs_lseek", mock_glfs_lseek):
            o = self.fd.lseek(20, os.SEEK_SET)
            self.assertEqual(o, 20)

    def test_read_success(self):
        def _mock_glfs_read(fd, rbuf, buflen, flags):
            rbuf.value = "hello"
            return 5

        with patch("gluster.gfapi.api.glfs_read", _mock_glfs_read):
            b = self.fd.read(5)
            self.assertEqual(b, "hello")

    def test_read_fail_exception(self):
        mock_glfs_read = Mock()
        mock_glfs_read.return_value = -1

        with patch("gluster.gfapi.api.glfs_read", mock_glfs_read):
            self.assertRaises(OSError, self.fd.read, 5)

    def test_read_fail_empty_buffer(self):
        mock_glfs_read = Mock()
        mock_glfs_read.return_value = 0

        with patch("gluster.gfapi.api.glfs_read", mock_glfs_read):
            self.fd.read(5)

    def test_read_buflen_negative(self):
        _mock_fgetsize = Mock(return_value=12345)

        def _mock_glfs_read(fd, rbuf, buflen, flags):
            self.assertEqual(buflen, 12345)
            return buflen

        for buflen in (-1, -2, -999):
            with patch("gluster.gfapi.api.glfs_read", _mock_glfs_read):
                with patch("gluster.gfapi.File.fgetsize", _mock_fgetsize):
                    self.fd.read(buflen)

    def test_readinto(self):
        mock_glfs_read = Mock()
        mock_glfs_read.return_value = 5

        with patch("gluster.gfapi.api.glfs_read", mock_glfs_read):
            buf = bytearray(10)
            ret = self.fd.readinto(buf)
            self.assertEqual(ret, 5)

        self.assertRaises(TypeError, self.fd.readinto, str("hello"))

    def test_write_success(self):
        mock_glfs_write = Mock()
        mock_glfs_write.return_value = 5

        with patch("gluster.gfapi.api.glfs_write", mock_glfs_write):
            ret = self.fd.write("hello")
            self.assertEqual(ret, 5)

    def test_write_binary_success(self):
        mock_glfs_write = Mock()
        mock_glfs_write.return_value = 3

        with patch("gluster.gfapi.api.glfs_write", mock_glfs_write):
            b = bytearray(3)
            ret = self.fd.write(b)
            self.assertEqual(ret, 3)

    def test_write_fail_exception(self):
        mock_glfs_write = Mock()
        mock_glfs_write.return_value = -1

        with patch("gluster.gfapi.api.glfs_write", mock_glfs_write):
            self.assertRaises(OSError, self.fd.write, "hello")

    def test_fallocate_success(self):
        raise SkipTest("need to solve issue with dependency on gluster.so")
        mock_glfs_fallocate = Mock()
        mock_glfs_fallocate.return_value = 0

        with patch("gluster.gfapi.api.glfs_fallocate", mock_glfs_fallocate):
            ret = self.fd.fallocate(0, 0, 1024)
            self.assertEqual(ret, 0)

    def test_fallocate_fail_exception(self):
        raise SkipTest("need to solve issue with dependency on gluster.so")
        mock_glfs_fallocate = Mock()
        mock_glfs_fallocate.return_value = -1

        with patch("gluster.gfapi.api.glfs_fallocate", mock_glfs_fallocate):
            self.assertRaises(OSError, self.fd.fallocate, 0, 0, 1024)

    def test_discard_success(self):
        raise SkipTest("need to solve issue with dependency on gluster.so")
        mock_glfs_discard = Mock()
        mock_glfs_discard.return_value = 0

        with patch("gluster.gfapi.api.glfs_discard", mock_glfs_discard):
            ret = self.fd.discard(1024, 1024)
            self.assertEqual(ret, 0)

    def test_discard_fail_exception(self):
        raise SkipTest("need to solve issue with dependency on gluster.so")
        mock_glfs_discard = Mock()
        mock_glfs_discard.return_value = -1

        with patch("gluster.gfapi.api.glfs_discard", mock_glfs_discard):
            self.assertRaises(OSError, self.fd.discard, 1024, 1024)


class TestDir(unittest.TestCase):

    def setUp(self):
        self._saved_glfs_closedir = gluster.gfapi.api.glfs_closedir
        gluster.gfapi.api.glfs_closedir = _mock_glfs_closedir

    def tearDown(self):
        gluster.gfapi.api.glfs_closedir = self._saved_glfs_closedir

    def test_next_success(self):
        raise SkipTest("need to solve issue with dependency on gluster.so")

        def mock_glfs_readdir_r(fd, ent, cursor):
            cursor.contents = "bla"
            return 0

        with patch("gluster.gfapi.api.glfs_readdir_r", mock_glfs_readdir_r):
            fd = Dir(2)
            ent = fd.next()
            self.assertTrue(isinstance(ent, api.Dirent))


class TestVolume(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._saved_glfs_new = gluster.gfapi.api.glfs_new
        gluster.gfapi.api.glfs_new = _mock_glfs_new

        cls._saved_glfs_set_volfile_server = \
            gluster.gfapi.api.glfs_set_volfile_server
        gluster.gfapi.api.glfs_set_volfile_server = \
            _mock_glfs_set_volfile_server

        cls._saved_glfs_init = gluster.gfapi.api.glfs_init
        gluster.gfapi.api.glfs_init = _mock_glfs_init

        cls._saved_glfs_fini = gluster.gfapi.api.glfs_fini
        gluster.gfapi.api.glfs_fini = _mock_glfs_fini

        cls._saved_glfs_close = gluster.gfapi.api.glfs_close
        gluster.gfapi.api.glfs_close = _mock_glfs_close

        cls._saved_glfs_closedir = gluster.gfapi.api.glfs_closedir
        gluster.gfapi.api.glfs_closedir = _mock_glfs_closedir

        cls._saved_glfs_set_logging = gluster.gfapi.api.glfs_set_logging
        gluster.gfapi.api.glfs_set_logging = _mock_glfs_set_logging

        cls.vol = Volume("mockhost", "test")
        cls.vol.fs = 12345
        cls.vol._mounted = True

    @classmethod
    def tearDownClass(cls):
        cls.vol = None
        gluster.gfapi.api.glfs_new = cls._saved_glfs_new
        gluster.gfapi.api.glfs_set_volfile_server = \
            cls._saved_glfs_set_volfile_server
        gluster.gfapi.api.glfs_fini = cls._saved_glfs_fini
        gluster.gfapi.api.glfs_close = cls._saved_glfs_close
        gluster.gfapi.api.glfs_closedir = cls._saved_glfs_closedir

    def test_initialization_error(self):
        self.assertRaises(LibgfapiException, Volume, "host", None)
        self.assertRaises(LibgfapiException, Volume, None, "vol")
        self.assertRaises(LibgfapiException, Volume, None, None)
        self.assertRaises(LibgfapiException, Volume, "host", "vol", "ZZ")
        self.assertRaises(LibgfapiException, Volume, "host", "vol",
                          "tcp", "invalid_port")

    def test_initialization_success(self):
        v = Volume("host", "vol", "tcp", 9876)
        self.assertEqual(v.host, "host")
        self.assertEqual(v.volname, "vol")
        self.assertEqual(v.protocol, "tcp")
        self.assertEqual(v.port, 9876)
        self.assertFalse(v.mounted)

    def test_mount_umount_success(self):
        v = Volume("host", "vol")
        v.mount()
        self.assertTrue(v.mounted)
        self.assertTrue(v.fs)
        v.umount()
        self.assertFalse(v.mounted)
        self.assertFalse(v.fs)

    def test_mount_multiple(self):
        _m_glfs_new = Mock()
        v = Volume("host", "vol")
        with patch("gluster.gfapi.api.glfs_new", _m_glfs_new):
            # Mounting for first time
            v.mount()
            _m_glfs_new.assert_called_once_with("vol")
            _m_glfs_new.reset_mock()
            for i in range(0, 5):
                v.mount()
                self.assertFalse(_m_glfs_new.called)
                self.assertTrue(v.mounted)

    def test_mount_error(self):
        # glfs_new() failed
        _m_glfs_new = Mock(return_value=None)
        v = Volume("host", "vol")
        with patch("gluster.gfapi.api.glfs_new", _m_glfs_new):
            self.assertRaises(LibgfapiException, v.mount)
            self.assertFalse(v.fs)
            self.assertFalse(v.mounted)
            _m_glfs_new.assert_called_once_with("vol")

        # glfs_set_volfile_server() failed
        _m_set_vol = Mock(return_value=-1)
        v = Volume("host", "vol")
        with patch("gluster.gfapi.api.glfs_set_volfile_server", _m_set_vol):
            self.assertRaises(LibgfapiException, v.mount)
            self.assertFalse(v.mounted)
            _m_glfs_new.assert_called_once_with("vol")
            _m_set_vol.assert_called_once_with(v.fs, v.protocol,
                                               v.host, v.port)

        # glfs_init() failed
        _m_glfs_init = Mock(return_value=-1)
        v = Volume("host", "vol")
        with patch("gluster.gfapi.api.glfs_init", _m_glfs_init):
            self.assertRaises(LibgfapiException, v.mount)
            self.assertFalse(v.mounted)
            _m_glfs_init.assert_called_once_with(v.fs)

    def test_umount_error(self):
        v = Volume("host", "vol")
        v.mount()
        _m_glfs_fini = Mock(return_value=-1)
        with patch("gluster.gfapi.api.glfs_fini", _m_glfs_fini):
            self.assertRaises(LibgfapiException, v.umount)
            _m_glfs_fini.assert_called_once_with(v.fs)
            # Should still be mounted as umount failed.
            self.assertTrue(v.mounted)

    def test_set_logging(self):
        _m_set_logging = Mock()

        # Called after mount()
        v = Volume("host", "vol")
        with patch("gluster.gfapi.api.glfs_set_logging", _m_set_logging):
            v.mount()
            v.set_logging("/path/whatever", 7)
            self.assertEqual(v.log_file, "/path/whatever")
            self.assertEqual(v.log_level, 7)

    def test_set_logging_err(self):
        v = Volume("host", "vol")
        v.fs = 12345
        _m_set_logging = Mock(return_value=-1)
        with patch("gluster.gfapi.api.glfs_set_logging", _m_set_logging):
            self.assertRaises(LibgfapiException, v.set_logging, "/dev/null", 7)
            _m_set_logging.assert_called_once_with(v.fs, None, 7)

    def test_chmod_success(self):
        mock_glfs_chmod = Mock()
        mock_glfs_chmod.return_value = 0

        with patch("gluster.gfapi.api.glfs_chmod", mock_glfs_chmod):
            self.vol.chmod("file.txt", 0600)

    def test_chmod_fail_exception(self):
        mock_glfs_chmod = Mock()
        mock_glfs_chmod.return_value = -1

        with patch("gluster.gfapi.api.glfs_chmod", mock_glfs_chmod):
            self.assertRaises(OSError, self.vol.chmod, "file.txt", 0600)

    def test_chown_success(self):
        mock_glfs_chown = Mock()
        mock_glfs_chown.return_value = 0

        with patch("gluster.gfapi.api.glfs_chown", mock_glfs_chown):
            self.vol.chown("file.txt", 9, 11)

    def test_chown_fail_exception(self):
        mock_glfs_chown = Mock()
        mock_glfs_chown.return_value = -1

        with patch("gluster.gfapi.api.glfs_chown", mock_glfs_chown):
            self.assertRaises(OSError, self.vol.chown, "file.txt", 9, 11)

    def test_creat_success(self):
        mock_glfs_creat = Mock()
        mock_glfs_creat.return_value = 2

        with patch("gluster.api.glfs_creat", mock_glfs_creat):
            with File(self.vol.open("file.txt", os.O_CREAT, 0644)) as f:
                self.assertTrue(isinstance(f, File))
                self.assertEqual(mock_glfs_creat.call_count, 1)
                mock_glfs_creat.assert_called_once_with(12345,
                                                        "file.txt",
                                                        os.O_CREAT, 0644)

    def test_exists_true(self):
        mock_glfs_stat = Mock()
        mock_glfs_stat.return_value = 0

        with patch("gluster.gfapi.api.glfs_stat", mock_glfs_stat):
            ret = self.vol.exists("file.txt")
            self.assertTrue(ret)

    def test_not_exists_false(self):
        mock_glfs_stat = Mock()
        mock_glfs_stat.return_value = -1

        with patch("gluster.gfapi.api.glfs_stat", mock_glfs_stat):
            ret = self.vol.exists("file.txt")
            self.assertFalse(ret)

    def test_isdir_true(self):
        mock_glfs_stat = Mock()
        s = api.Stat()
        s.st_mode = stat.S_IFDIR
        mock_glfs_stat.return_value = s

        with patch("gluster.gfapi.Volume.stat", mock_glfs_stat):
            ret = self.vol.isdir("dir")
            self.assertTrue(ret)

    def test_isdir_false(self):
        mock_glfs_stat = Mock()
        s = api.Stat()
        s.st_mode = stat.S_IFREG
        mock_glfs_stat.return_value = s

        with patch("gluster.gfapi.Volume.stat", mock_glfs_stat):
            ret = self.vol.isdir("file")
            self.assertFalse(ret)

    def test_isdir_false_nodir(self):
        mock_glfs_stat = Mock()
        mock_glfs_stat.return_value = -1

        with patch("gluster.gfapi.api.glfs_stat", mock_glfs_stat):
            ret = self.vol.isdir("dirdoesnotexist")
            self.assertFalse(ret)

    def test_isfile_true(self):
        mock_glfs_stat = Mock()
        s = api.Stat()
        s.st_mode = stat.S_IFREG
        mock_glfs_stat.return_value = s

        with patch("gluster.gfapi.Volume.stat", mock_glfs_stat):
            ret = self.vol.isfile("file")
            self.assertTrue(ret)

    def test_isfile_false(self):
        mock_glfs_stat = Mock()
        s = api.Stat()
        s.st_mode = stat.S_IFDIR
        mock_glfs_stat.return_value = s

        with patch("gluster.gfapi.Volume.stat", mock_glfs_stat):
            ret = self.vol.isfile("dir")
            self.assertFalse(ret)

    def test_isfile_false_nofile(self):
        mock_glfs_stat = Mock()
        mock_glfs_stat.return_value = -1

        with patch("gluster.gfapi.api.glfs_stat", mock_glfs_stat):
            ret = self.vol.isfile("filedoesnotexist")
            self.assertFalse(ret)

    def test_islink_true(self):
        mock_glfs_lstat = Mock()
        s = api.Stat()
        s.st_mode = stat.S_IFLNK
        mock_glfs_lstat.return_value = s

        with patch("gluster.gfapi.Volume.lstat", mock_glfs_lstat):
            ret = self.vol.islink("solnk")
            self.assertTrue(ret)

    def test_islink_false(self):
        mock_glfs_lstat = Mock()
        s = api.Stat()
        s.st_mode = stat.S_IFREG
        mock_glfs_lstat.return_value = s

        with patch("gluster.gfapi.Volume.lstat", mock_glfs_lstat):
            ret = self.vol.islink("file")
            self.assertFalse(ret)

    def test_islink_false_nolink(self):
        mock_glfs_lstat = Mock()
        mock_glfs_lstat.return_value = -1

        with patch("gluster.gfapi.api.glfs_lstat", mock_glfs_lstat):
            ret = self.vol.islink("linkdoesnotexist")
            self.assertFalse(ret)

    def test_getxattr_success(self):
        def mock_glfs_getxattr(fs, path, key, buf, maxlen):
            buf.value = "fake_xattr"
            return 10

        with patch("gluster.gfapi.api.glfs_getxattr", mock_glfs_getxattr):
            buf = self.vol.getxattr("file.txt", "key1", 32)
            self.assertEquals("fake_xattr", buf)

    def test_getxattr_fail_exception(self):
        mock_glfs_getxattr = Mock()
        mock_glfs_getxattr.return_value = -1

        with patch("gluster.gfapi.api.glfs_getxattr", mock_glfs_getxattr):
            self.assertRaises(OSError, self.vol.getxattr, "file.txt",
                              "key1", 32)

    def test_listdir_success(self):
        mock_glfs_opendir = Mock()
        mock_glfs_opendir.return_value = 2

        dirent1 = api.Dirent()
        dirent1.d_name = "mockfile"
        dirent1.d_reclen = 8
        dirent2 = api.Dirent()
        dirent2.d_name = "mockdir"
        dirent2.d_reclen = 7
        dirent3 = api.Dirent()
        dirent3.d_name = "."
        dirent3.d_reclen = 1
        mock_Dir_next = Mock()
        mock_Dir_next.side_effect = [dirent1, dirent2, dirent3, None]

        with nested(patch("gluster.gfapi.api.glfs_opendir",
                          mock_glfs_opendir),
                    patch("gluster.gfapi.Dir.next", mock_Dir_next)):
            d = self.vol.listdir("testdir")
            self.assertEqual(len(d), 2)
            self.assertEqual(d[0], 'mockfile')

    def test_listdir_fail_exception(self):
        mock_glfs_opendir = Mock()
        mock_glfs_opendir.return_value = None

        with patch("gluster.gfapi.api.glfs_opendir", mock_glfs_opendir):
            self.assertRaises(OSError, self.vol.listdir, "test.txt")

    def test_listxattr_success(self):
        def mock_glfs_listxattr(fs, path, buf, buflen):
            if buf:
                buf.raw = "key1\0key2\0"
            return 10

        with patch("gluster.gfapi.api.glfs_listxattr", mock_glfs_listxattr):
            xattrs = self.vol.listxattr("file.txt")
            self.assertTrue("key1" in xattrs)
            self.assertTrue("key2" in xattrs)

    def test_listxattr_fail_exception(self):
        mock_glfs_listxattr = Mock()
        mock_glfs_listxattr.return_value = -1

        with patch("gluster.gfapi.api.glfs_listxattr", mock_glfs_listxattr):
            self.assertRaises(OSError, self.vol.listxattr, "file.txt")

    def test_lstat_success(self):
        mock_glfs_lstat = Mock()
        mock_glfs_lstat.return_value = 0

        with patch("gluster.gfapi.api.glfs_lstat", mock_glfs_lstat):
            s = self.vol.lstat("file.txt")
            self.assertTrue(isinstance(s, api.Stat))

    def test_lstat_fail_exception(self):
        mock_glfs_lstat = Mock()
        mock_glfs_lstat.return_value = -1

        with patch("gluster.gfapi.api.glfs_lstat", mock_glfs_lstat):
            self.assertRaises(OSError, self.vol.lstat, "file.txt")

    def test_stat_success(self):
        mock_glfs_stat = Mock()
        mock_glfs_stat.return_value = 0

        with patch("gluster.gfapi.api.glfs_stat", mock_glfs_stat):
            s = self.vol.stat("file.txt")
            self.assertTrue(isinstance(s, api.Stat))

    def test_stat_fail_exception(self):
        mock_glfs_stat = Mock()
        mock_glfs_stat.return_value = -1

        with patch("gluster.gfapi.api.glfs_stat", mock_glfs_stat):
            self.assertRaises(OSError, self.vol.stat, "file.txt")

    def test_statvfs_success(self):
        mock_glfs_statvfs = Mock()
        mock_glfs_statvfs.return_value = 0

        with patch("gluster.gfapi.api.glfs_statvfs", mock_glfs_statvfs):
            s = self.vol.statvfs("/")
            self.assertTrue(isinstance(s, api.Statvfs))

    def test_statvfs_fail_exception(self):
        mock_glfs_statvfs = Mock()
        mock_glfs_statvfs.return_value = -1

        with patch("gluster.gfapi.api.glfs_statvfs", mock_glfs_statvfs):
            self.assertRaises(OSError, self.vol.statvfs, "/")

    def test_makedirs_success(self):
        mock_glfs_mkdir = Mock()
        mock_glfs_mkdir.side_effect = [0, 0]

        mock_exists = Mock()
        mock_exists.side_effect = (False, True, False)

        with nested(patch("gluster.gfapi.api.glfs_mkdir", mock_glfs_mkdir),
                    patch("gluster.gfapi.Volume.exists", mock_exists)):
            self.vol.makedirs("dir1/", 0775)
            self.assertEqual(mock_glfs_mkdir.call_count, 1)
            mock_glfs_mkdir.assert_any_call(self.vol.fs, "dir1/", 0775)

    def test_makedirs_success_EEXIST(self):
        err = errno.EEXIST
        mock_glfs_mkdir = Mock()
        mock_glfs_mkdir.side_effect = [OSError(err, os.strerror(err)), 0]

        mock_exists = Mock()
        mock_exists.side_effect = [False, True, False]

        with nested(patch("gluster.gfapi.api.glfs_mkdir", mock_glfs_mkdir),
                    patch("gluster.gfapi.Volume.exists", mock_exists)):
            self.vol.makedirs("./dir1/dir2", 0775)
            self.assertEqual(mock_glfs_mkdir.call_count, 2)
            mock_glfs_mkdir.assert_any_call(self.vol.fs, "./dir1", 0775)
            mock_glfs_mkdir.assert_called_with(self.vol.fs, "./dir1/dir2",
                                               0775)

    def test_makedirs_fail_exception(self):
        mock_glfs_mkdir = Mock()
        mock_glfs_mkdir.return_value = -1

        mock_exists = Mock()
        mock_exists.return_value = False

        with nested(patch("gluster.gfapi.api.glfs_mkdir", mock_glfs_mkdir),
                    patch("gluster.gfapi.Volume.exists", mock_exists)):
            self.assertRaises(OSError, self.vol.makedirs, "dir1/dir2", 0775)

    def test_mkdir_success(self):
        mock_glfs_mkdir = Mock()
        mock_glfs_mkdir.return_value = 0

        with patch("gluster.gfapi.api.glfs_mkdir", mock_glfs_mkdir):
            self.vol.mkdir("testdir", 0775)

    def test_mkdir_fail_exception(self):
        mock_glfs_mkdir = Mock()
        mock_glfs_mkdir.return_value = -1

        with patch("gluster.gfapi.api.glfs_mkdir", mock_glfs_mkdir):
            self.assertRaises(OSError, self.vol.mkdir, "testdir", 0775)

    def test_open_with_statement_success(self):
        mock_glfs_open = Mock()
        mock_glfs_open.return_value = 2

        with patch("gluster.api.glfs_open", mock_glfs_open):
            with File(self.vol.open("file.txt", os.O_WRONLY)) as f:
                self.assertTrue(isinstance(f, File))
                self.assertEqual(mock_glfs_open.call_count, 1)
                mock_glfs_open.assert_called_once_with(12345,
                                                       "file.txt", os.O_WRONLY)

    def test_open_with_statement_fail_exception(self):
        mock_glfs_open = Mock()
        mock_glfs_open.return_value = None

        def assert_open():
            with self.vol.open("file.txt", os.O_WRONLY) as fd:
                self.assertEqual(fd, None)

        with patch("gluster.api.glfs_open", mock_glfs_open):
            self.assertRaises(OSError, assert_open)

    def test_open_direct_success(self):
        mock_glfs_open = Mock()
        mock_glfs_open.return_value = 2

        with patch("gluster.api.glfs_open", mock_glfs_open):
            f = File(self.vol.open("file.txt", os.O_WRONLY))
            self.assertTrue(isinstance(f, File))
            self.assertEqual(mock_glfs_open.call_count, 1)
            mock_glfs_open.assert_called_once_with(12345, "file.txt",
                                                   os.O_WRONLY)

    def test_open_direct_fail_exception(self):
        mock_glfs_open = Mock()
        mock_glfs_open.return_value = None

        with patch("gluster.api.glfs_open", mock_glfs_open):
            self.assertRaises(OSError, self.vol.open, "file.txt", os.O_RDONLY)

    def test_opendir_success(self):
        mock_glfs_opendir = Mock()
        mock_glfs_opendir.return_value = 2

        with patch("gluster.gfapi.api.glfs_opendir", mock_glfs_opendir):
            d = self.vol.opendir("testdir")
            self.assertTrue(isinstance(d, Dir))

    def test_opendir_fail_exception(self):
        mock_glfs_opendir = Mock()
        mock_glfs_opendir.return_value = None

        with patch("gluster.gfapi.api.glfs_opendir", mock_glfs_opendir):
            self.assertRaises(OSError, self.vol.opendir, "testdir")

    def test_rename_success(self):
        mock_glfs_rename = Mock()
        mock_glfs_rename.return_value = 0

        with patch("gluster.gfapi.api.glfs_rename", mock_glfs_rename):
            self.vol.rename("file.txt", "newfile.txt")

    def test_rename_fail_exception(self):
        mock_glfs_rename = Mock()
        mock_glfs_rename.return_value = -1

        with patch("gluster.gfapi.api.glfs_rename", mock_glfs_rename):
            self.assertRaises(OSError, self.vol.rename,
                              "file.txt", "newfile.txt")

    def test_rmdir_success(self):
        mock_glfs_rmdir = Mock()
        mock_glfs_rmdir.return_value = 0

        with patch("gluster.gfapi.api.glfs_rmdir", mock_glfs_rmdir):
            self.vol.rmdir("testdir")

    def test_rmdir_fail_exception(self):
        mock_glfs_rmdir = Mock()
        mock_glfs_rmdir.return_value = -1

        with patch("gluster.gfapi.api.glfs_rmdir", mock_glfs_rmdir):
            self.assertRaises(OSError, self.vol.rmdir, "testdir")

    def test_unlink_success(self):
        mock_glfs_unlink = Mock()
        mock_glfs_unlink.return_value = 0

        with patch("gluster.gfapi.api.glfs_unlink", mock_glfs_unlink):
            self.vol.unlink("file.txt")

    def test_unlink_fail_exception(self):
        mock_glfs_unlink = Mock()
        mock_glfs_unlink.return_value = -1

        with patch("gluster.gfapi.api.glfs_unlink", mock_glfs_unlink):
            self.assertRaises(OSError, self.vol.unlink, "file.txt")

    def test_removexattr_success(self):
        mock_glfs_removexattr = Mock()
        mock_glfs_removexattr.return_value = 0

        with patch("gluster.gfapi.api.glfs_removexattr",
                   mock_glfs_removexattr):
            self.vol.removexattr("file.txt", "key1")

    def test_removexattr_fail_exception(self):
        mock_glfs_removexattr = Mock()
        mock_glfs_removexattr.return_value = -1

        with patch("gluster.gfapi.api.glfs_removexattr",
                   mock_glfs_removexattr):
            self.assertRaises(OSError, self.vol.removexattr, "file.txt",
                              "key1")

    def test_rmtree_success(self):
        dir1_list = ["dir2", "file"]
        empty_list = []
        mock_listdir = Mock()
        mock_listdir.side_effect = [dir1_list, empty_list]

        mock_isdir = Mock()
        mock_isdir.side_effect = [True, False]

        mock_unlink = Mock()
        mock_unlink.return_value = 0

        mock_rmdir = Mock()
        mock_rmdir.return_value = 0

        mock_islink = Mock()
        mock_islink.return_value = False

        with nested(patch("gluster.gfapi.Volume.listdir", mock_listdir),
                    patch("gluster.gfapi.Volume.isdir", mock_isdir),
                    patch("gluster.gfapi.Volume.islink", mock_islink),
                    patch("gluster.gfapi.Volume.unlink", mock_unlink),
                    patch("gluster.gfapi.Volume.rmdir", mock_rmdir)):
            self.vol.rmtree("dir1")
            mock_rmdir.assert_any_call("dir1/dir2")
            mock_unlink.assert_called_once_with("dir1/file")
            mock_rmdir.assert_called_with("dir1")

    def test_rmtree_listdir_exception(self):
        mock_listdir = Mock()
        mock_listdir.side_effect = [OSError]

        mock_islink = Mock()
        mock_islink.return_value = False

        with nested(patch("gluster.gfapi.Volume.listdir", mock_listdir),
                    patch("gluster.gfapi.Volume.islink", mock_islink)):
            self.assertRaises(OSError, self.vol.rmtree, "dir1")

    def test_rmtree_islink_exception(self):
        mock_islink = Mock()
        mock_islink.return_value = True

        with patch("gluster.gfapi.Volume.islink", mock_islink):
            self.assertRaises(OSError, self.vol.rmtree, "dir1")

    def test_rmtree_ignore_unlink_rmdir_exception(self):
        dir1_list = ["dir2", "file"]
        empty_list = []
        mock_listdir = Mock()
        mock_listdir.side_effect = [dir1_list, empty_list]

        mock_isdir = Mock()
        mock_isdir.side_effect = [True, False]

        mock_unlink = Mock()
        mock_unlink.side_effect = [OSError]

        mock_rmdir = Mock()
        mock_rmdir.side_effect = [0, OSError]

        mock_islink = Mock()
        mock_islink.return_value = False

        with nested(patch("gluster.gfapi.Volume.listdir", mock_listdir),
                    patch("gluster.gfapi.Volume.isdir", mock_isdir),
                    patch("gluster.gfapi.Volume.islink", mock_islink),
                    patch("gluster.gfapi.Volume.unlink", mock_unlink),
                    patch("gluster.gfapi.Volume.rmdir", mock_rmdir)):
            self.vol.rmtree("dir1", True)
            mock_rmdir.assert_any_call("dir1/dir2")
            mock_unlink.assert_called_once_with("dir1/file")
            mock_rmdir.assert_called_with("dir1")

    def test_setfsuid_success(self):
        mock_glfs_setfsuid = Mock()
        mock_glfs_setfsuid.return_value = 0

        with patch("gluster.gfapi.api.glfs_setfsuid", mock_glfs_setfsuid):
            self.vol.setfsuid(1000)

    def test_setfsuid_fail(self):
        mock_glfs_setfsuid = Mock()
        mock_glfs_setfsuid.return_value = -1

        with patch("gluster.gfapi.api.glfs_setfsuid", mock_glfs_setfsuid):
            self.assertRaises(OSError, self.vol.setfsuid, 1001)

    def test_setfsgid_success(self):
        mock_glfs_setfsgid = Mock()
        mock_glfs_setfsgid.return_value = 0

        with patch("gluster.gfapi.api.glfs_setfsgid", mock_glfs_setfsgid):
            self.vol.setfsgid(1000)

    def test_setfsgid_fail(self):
        mock_glfs_setfsgid = Mock()
        mock_glfs_setfsgid.return_value = -1

        with patch("gluster.gfapi.api.glfs_setfsgid", mock_glfs_setfsgid):
            self.assertRaises(OSError, self.vol.setfsgid, 1001)

    def test_setxattr_success(self):
        mock_glfs_setxattr = Mock()
        mock_glfs_setxattr.return_value = 0

        with patch("gluster.gfapi.api.glfs_setxattr", mock_glfs_setxattr):
            self.vol.setxattr("file.txt", "key1", "hello", 5)

    def test_setxattr_fail_exception(self):
        mock_glfs_setxattr = Mock()
        mock_glfs_setxattr.return_value = -1

        with patch("gluster.gfapi.api.glfs_setxattr", mock_glfs_setxattr):
            self.assertRaises(OSError, self.vol.setxattr, "file.txt",
                              "key1", "hello", 5)

    def test_symlink_success(self):
        mock_glfs_symlink = Mock()
        mock_glfs_symlink.return_value = 0

        with patch("gluster.gfapi.api.glfs_symlink", mock_glfs_symlink):
            self.vol.symlink("file.txt", "filelink")

    def test_symlink_fail_exception(self):
        mock_glfs_symlink = Mock()
        mock_glfs_symlink.return_value = -1

        with patch("gluster.gfapi.api.glfs_symlink", mock_glfs_symlink):
            self.assertRaises(OSError, self.vol.symlink, "file.txt",
                              "filelink")

    def test_walk_success(self):
        dir1_list = ["dir2", "file"]
        empty_list = []
        mock_listdir = Mock()
        mock_listdir.side_effect = [dir1_list, empty_list]

        mock_isdir = Mock()
        mock_isdir.side_effect = [True, False]

        with nested(patch("gluster.gfapi.Volume.listdir", mock_listdir),
                    patch("gluster.gfapi.Volume.isdir", mock_isdir)):
            for (path, dirs, files) in self.vol.walk("dir1"):
                self.assertEqual(dirs, ['dir2'])
                self.assertEqual(files, ['file'])
                break

    def test_walk_listdir_exception(self):
        mock_listdir = Mock()
        mock_listdir.side_effect = [OSError]

        def mock_onerror(err):
            self.assertTrue(isinstance(err, OSError))

        with patch("gluster.gfapi.Volume.listdir", mock_listdir):
            for (path, dirs, files) in self.vol.walk("dir1",
                                                     onerror=mock_onerror):
                pass
