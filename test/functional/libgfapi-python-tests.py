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
import os
import types
import errno
import threading

from gluster.gfapi import File, Volume
from gluster.exceptions import LibgfapiException
from test import get_test_config
from ConfigParser import NoSectionError, NoOptionError
from uuid import uuid4

config = get_test_config()
if config:
    try:
        HOST = config.get('func_test', 'gfs_host')
    except (NoSectionError, NoOptionError):
        HOST = 'localhost'
    try:
        VOLNAME = config.get('func_test', 'gfs_volname')
    except (NoSectionError, NoOptionError):
        VOLNAME = 'test'
else:
    HOST = 'localhost'
    VOLNAME = 'test'


class BinFileOpsTest(unittest.TestCase):

    vol = None
    path = None
    data = None

    @classmethod
    def setUpClass(cls):
        cls.vol = Volume(HOST, VOLNAME)
        ret = cls.vol.mount()
        if ret == 0:
            # Cleanup volume
            cls.vol.rmtree("/", ignore_errors=True)

    @classmethod
    def tearDownClass(cls):
        cls.vol.rmtree("/", ignore_errors=True)
        cls.vol = None

    def test_bin_open_and_read(self):
        # Write binary data
        data = "Gluster is so awesome"
        payload = bytearray(data, "ascii")
        path = self._testMethodName + ".io"
        with File(self.vol.open(path,
                  os.O_CREAT | os.O_WRONLY | os.O_EXCL, 0644)) as f:
            f.write(payload)
        # Read binary data
        with File(self.vol.open(path, os.O_RDONLY)) as f:
            buf = f.read()
            self.assertEqual(bytearray(buf), payload)
            self.assertEqual(buf.decode("ascii"), data)


class FileOpsTest(unittest.TestCase):

    vol = None
    path = None
    data = None

    @classmethod
    def setUpClass(cls):
        cls.vol = Volume(HOST, VOLNAME)
        ret = cls.vol.mount()
        if ret == 0:
            # Cleanup volume
            cls.vol.rmtree("/", ignore_errors=True)

    @classmethod
    def tearDownClass(cls):
        cls.vol.rmtree("/", ignore_errors=True)
        cls.vol = None

    def setUp(self):
        self.data = "gluster is awesome"
        self.path = self._testMethodName + ".io"
        with File(self.vol.open(self.path,
                  os.O_CREAT | os.O_WRONLY | os.O_EXCL, 0644),
                  path=self.path) as f:
            rc = f.write(self.data)
            self.assertEqual(rc, len(self.data))
            f.fsync()
            self.assertEqual(f.originalpath, self.path)

    def tearDown(self):
        self.path = None
        self.data = None

    def test_open_and_read(self):
        with File(self.vol.open(self.path, os.O_RDONLY)) as f:
            self.assertTrue(isinstance(f, File))
            buf = f.read(len(self.data))
            self.assertFalse(isinstance(buf, types.IntType))
            self.assertEqual(buf, self.data)

    def test_open_file_not_exist(self):
        try:
            f = File(self.vol.open("filenotexist", os.O_WRONLY))
        except OSError as e:
            self.assertEqual(e.errno, errno.ENOENT)
        else:
            f.close()
            self.fail("Expected a OSError with errno.ENOENT")

    def test_open_err(self):
        # flags not int
        self.assertRaises(TypeError, self.vol.open, "file", 'w')
        # invalid flags
        self.assertRaises(OSError, self.vol.open, "file",
                          12345)

    def test_fopen_err(self):
        # mode not string
        self.assertRaises(TypeError, self.vol.fopen, "file", os.O_WRONLY)
        # invalid mode
        self.assertRaises(ValueError, self.vol.fopen, "file", 'x+')
        # file does not exist
        self.assertRaises(OSError, self.vol.fopen, "file", 'r')

    def test_fopen(self):
        # Default permission should be 0666
        name = uuid4().hex
        data = "Gluster is so awesome"
        with self.vol.fopen(name, 'w') as f:
            f.write(data)
        perms = self.vol.stat(name).st_mode & 0777
        self.assertEqual(perms, int(0666))

        # 'r': Open file for reading.
        # If not specified, mode should default to 'r'
        with self.vol.fopen(name) as f:
            self.assertEqual('r', f.mode)
            self.assertEqual(f.lseek(0, os.SEEK_CUR), 0)
            self.assertEqual(f.read(), data)

        # 'r+': Open for reading and writing.
        with self.vol.fopen(name, 'r+') as f:
            self.assertEqual(f.lseek(0, os.SEEK_CUR), 0)
            self.assertEqual('r+', f.mode)
            # ftruncate doesn't (and shouldn't) change offset
            f.ftruncate(0)
            # writes should pass
            f.write(data)
            f.lseek(0, os.SEEK_SET)
            self.assertEqual(f.read(), data)

        # 'w': Truncate file to zero length or create text file for writing.
        self.assertEqual(self.vol.getsize(name), len(data))
        with self.vol.fopen(name, 'w') as f:
            self.assertEqual('w', f.mode)
            f.fsync()
            self.assertEqual(self.vol.getsize(name), 0)
            f.write(data)

        # 'w+': Open for reading and writing.  The file is created if it does
        # not exist, otherwise it is truncated.
        with self.vol.fopen(name, 'w+') as f:
            self.assertEqual('w+', f.mode)
            f.fsync()
            self.assertEqual(self.vol.getsize(name), 0)
            f.write(data)
            f.lseek(0, os.SEEK_SET)
            self.assertEqual(f.read(), data)

        # 'a': Open for appending (writing at end of file).  The file is
        # created if it does not exist.
        with self.vol.fopen(name, 'a') as f:
            self.assertEqual('a', f.mode)
            # This should be appended at the end
            f.write("hello")
        with self.vol.fopen(name) as f:
            self.assertEqual(f.read(), data + "hello")

        # 'a+': Open for reading and appending (writing at end of file)
        with self.vol.fopen(name, 'a+') as f:
            self.assertEqual('a+', f.mode)
            # This should be appended at the end
            f.write(" world")
            f.fsync()
            f.lseek(0, os.SEEK_SET)
            self.assertEqual(f.read(), data + "hello world")

    def test_fopen_in_thread(self):
        def gluster_fopen():
            name = uuid4().hex
            with self.vol.fopen(name, 'w') as f:
                f.write('hello world')

        # the following caused segfault before the fix
        thread = threading.Thread(target=gluster_fopen)
        thread.start()
        thread.join()

    def test_create_file_already_exists(self):
        try:
            f = File(self.vol.open("newfile", os.O_CREAT))
            f.close()
            g = File(self.vol.open("newfile", os.O_CREAT | os.O_EXCL))
        except OSError as e:
            self.assertEqual(e.errno, errno.EEXIST)
        else:
            g.close()
            self.fail("Expected a OSError with errno.EEXIST")

    def test_write_file_dup_lseek_read(self):
        try:
            f = File(self.vol.open("dune", os.O_CREAT | os.O_EXCL | os.O_RDWR))
            f.write("I must not fear. Fear is the mind-killer.")
            fdup = f.dup()
            self.assertTrue(isinstance(fdup, File))
            f.close()
            ret = fdup.lseek(0, os.SEEK_SET)
            self.assertEqual(ret, 0)

            buf = fdup.read(15)
            self.assertEqual(buf, "I must not fear")

            ret = fdup.lseek(29, os.SEEK_SET)
            self.assertEqual(ret, 29)

            buf = fdup.read(11)
            self.assertEqual(buf, "mind-killer")

            fdup.close()
        except OSError as e:
            self.fail(e.message)

    def test_chmod(self):
        stat = self.vol.stat(self.path)
        orig_mode = oct(stat.st_mode & 0777)
        self.assertEqual(orig_mode, '0644L')
        self.vol.chmod(self.path, 0600)
        stat = self.vol.stat(self.path)
        new_mode = oct(stat.st_mode & 0777)
        self.assertEqual(new_mode, '0600L')

    def test_exists(self):
        e = self.vol.exists(self.path)
        self.assertTrue(e)

    def test_exists_false(self):
        e = self.vol.exists("filedoesnotexist")
        self.assertFalse(e)

    def test_getsize(self):
        size = self.vol.getsize(self.path)
        self.assertEqual(size, len(self.data))

    def test_isfile(self):
        isfile = self.vol.isfile(self.path)
        self.assertTrue(isfile)

    def test_isdir_false(self):
        isdir = self.vol.isdir(self.path)
        self.assertFalse(isdir)

    def test_symlink(self):
        link = self._testMethodName + ".link"
        self.vol.symlink(self.path, link)
        islink = self.vol.islink(link)
        self.assertTrue(islink)

    def test_islink_false(self):
        islink = self.vol.islink(self.path)
        self.assertFalse(islink)

    def test_lstat(self):
        sb = self.vol.lstat(self.path)
        self.assertFalse(isinstance(sb, types.IntType))
        self.assertEqual(sb.st_size, len(self.data))

    def test_rename(self):
        newpath = self.path + ".rename"
        self.vol.rename(self.path, newpath)
        self.assertRaises(OSError, self.vol.lstat, self.path)

    def test_stat(self):
        sb = self.vol.stat(self.path)
        self.assertFalse(isinstance(sb, types.IntType))
        self.assertEqual(sb.st_size, len(self.data))

    def test_unlink(self):
        self.vol.unlink(self.path)
        self.assertRaises(OSError, self.vol.lstat, self.path)

    def test_setxattr(self):
        value = "hello world"
        self.vol.setxattr(self.path, "trusted.key1", value)
        self.assertEqual(self.vol.getxattr(self.path, "trusted.key1"),
                         value)

        # flag = 1 behavior: fail if xattr exists
        self.assertRaises(OSError, self.vol.setxattr, self.path,
                          "trusted.key1", "whatever", flags=1)
        # flag = 1 behavior: pass if xattr does not exist
        self.vol.setxattr(self.path, "trusted.key2", "awesome", flags=1)
        self.assertEqual(self.vol.getxattr(self.path, "trusted.key2"),
                         "awesome")

        # flag = 2 behavior: fail if xattr does not exist
        self.assertRaises(OSError, self.vol.setxattr, self.path,
                          "trusted.key3", "whatever", flags=2)
        # flag = 2 behavior: pass if xattr exists
        self.vol.setxattr(self.path, "trusted.key2",
                          "more awesome", flags=2)
        self.assertEqual(self.vol.getxattr(self.path, "trusted.key2"),
                         "more awesome")

    def test_getxattr(self):
        self.vol.setxattr(self.path, "user.gluster", "awesome")
        # user does not know the size of value beforehand
        self.assertEqual(self.vol.getxattr(self.path, "user.gluster"),
                         "awesome")
        # user knows the size of value beforehand
        self.assertEqual(self.vol.getxattr(self.path, "user.gluster", size=7),
                         "awesome")
        # size is larger
        self.assertEqual(self.vol.getxattr(self.path, "user.gluster", size=20),
                         "awesome")
        # size is smaller
        self.assertRaises(OSError, self.vol.getxattr, self.path,
                          "user.gluster", size=1)
        # size is negative
        self.assertRaises(ValueError, self.vol.getxattr, self.path,
                          "user.gluster", size=-7)

    def test_listxattr(self):
        self.vol.setxattr(self.path, "user.gluster", "awesome")
        self.vol.setxattr(self.path, "user.gluster2", "awesome2")
        xattrs = self.vol.listxattr(self.path)
        self.assertTrue("user.gluster" in xattrs)
        self.assertTrue("user.gluster2" in xattrs)
        # Test passing of size
        # larger size - should pass
        xattrs = self.vol.listxattr(self.path, size=512)
        self.assertTrue("user.gluster" in xattrs)
        self.assertTrue("user.gluster2" in xattrs)
        # smaller size - should fail
        self.assertRaises(OSError, self.vol.listxattr, self.path, size=1)
        # invalid size - should fail
        self.assertRaises(ValueError, self.vol.listxattr, self.path, size=-1)

    def test_removexattr(self):
        self.vol.setxattr(self.path, "user.gluster", "awesome")
        self.vol.removexattr(self.path, "user.gluster")
        # The xattr now shouldn't exist
        self.assertRaises(OSError, self.vol.getxattr,
                          self.path, "user.gluster")
        # Removing an xattr that does not exist
        self.assertRaises(OSError, self.vol.removexattr,
                          self.path, "user.gluster")

    def test_fsetxattr(self):
        name = uuid4().hex
        with File(self.vol.open(name, os.O_WRONLY | os.O_CREAT)) as f:
            f.fsetxattr("user.gluster", "awesome")
            self.assertEqual(f.fgetxattr("user.gluster"), "awesome")
            # flag = 1 behavior: fail if xattr exists
            self.assertRaises(OSError, f.fsetxattr, "user.gluster",
                              "more awesome", flags=1)
            # flag = 1 behavior: pass if xattr does not exist
            f.fsetxattr("user.gluster2", "awesome2", flags=1)
            self.assertEqual(f.fgetxattr("user.gluster2"), "awesome2")
            # flag = 2 behavior: fail if xattr does not exist
            self.assertRaises(OSError, f.fsetxattr, "user.whatever",
                              "awesome", flags=2)
            # flag = 2 behavior: pass if xattr exists
            f.fsetxattr("user.gluster", "more awesome", flags=2)
            self.assertEqual(f.fgetxattr("user.gluster"), "more awesome")

    def test_fremovexattr(self):
        name = uuid4().hex
        with File(self.vol.open(name, os.O_WRONLY | os.O_CREAT)) as f:
            f.fsetxattr("user.gluster", "awesome")
            f.fremovexattr("user.gluster")
            # The xattr now shouldn't exist
            self.assertRaises(OSError, f.fgetxattr, "user.gluster")
            # Removing an xattr that does not exist
            self.assertRaises(OSError, f.fremovexattr, "user.gluster")

    def test_fgetxattr(self):
        name = uuid4().hex
        with File(self.vol.open(name, os.O_WRONLY | os.O_CREAT)) as f:
            f.fsetxattr("user.gluster", "awesome")
            # user does not know the size of value beforehand
            self.assertEqual(f.fgetxattr("user.gluster"), "awesome")
            # user knows the size of value beforehand
            self.assertEqual(f.fgetxattr("user.gluster", 7), "awesome")
            # size is larger
            self.assertEqual(f.fgetxattr("user.gluster", 70), "awesome")
            # size is smaller
            self.assertRaises(OSError, f.fgetxattr,
                              "user.gluster", size=1)
            # size is negative
            self.assertRaises(ValueError, f.fgetxattr,
                              "user.gluster", size=-7)

    def test_ftruncate(self):
        name = uuid4().hex
        with File(self.vol.open(name, os.O_WRONLY | os.O_CREAT)) as f:
            f.write("123456789")
            f.ftruncate(5)
            f.fsync()
        with File(self.vol.open(name, os.O_RDONLY)) as f:
            # The size should be reduced
            self.assertEqual(f.fgetsize(), 5)
            # So should be the content.
            self.assertEqual(f.read(), "12345")

    def test_flistxattr(self):
        name = uuid4().hex
        with File(self.vol.open(name, os.O_RDWR | os.O_CREAT)) as f:
            f.fsetxattr("user.gluster", "awesome")
            f.fsetxattr("user.gluster2", "awesome2")
            xattrs = f.flistxattr()
            self.assertTrue("user.gluster" in xattrs)
            self.assertTrue("user.gluster2" in xattrs)
            # Test passing of size
            # larger size - should pass
            xattrs = f.flistxattr(size=512)
            self.assertTrue("user.gluster" in xattrs)
            self.assertTrue("user.gluster2" in xattrs)
            # smaller size - should fail
            self.assertRaises(OSError, f.flistxattr, size=1)
            # invalid size - should fail
            self.assertRaises(ValueError, f.flistxattr, size=-1)

    def test_access(self):
        file_name = uuid4().hex
        with File(self.vol.open(file_name, os.O_WRONLY | os.O_CREAT)) as f:
            f.write("I'm whatever Gotham needs me to be")
            f.fsync()
        # Check that file exists
        self.assertTrue(self.vol.access(file_name, os.F_OK))
        # Check that file does not exist
        self.assertFalse(self.vol.access("nonexistentfile", os.F_OK))
        dir_name = uuid4().hex
        self.vol.mkdir(dir_name)
        # Check that directory exists
        self.assertTrue(self.vol.access(dir_name, os.F_OK))
        # Check if there is execute and write permission
        self.assertTrue(self.vol.access(file_name, os.W_OK | os.X_OK))

    def test_getcwd_and_chdir(self):
        # CWD should be root at first
        self.assertEqual(self.vol.getcwd(), '/')
        dir_structure = "/%s/%s" % (uuid4().hex, uuid4().hex)
        self.vol.makedirs(dir_structure)
        # Change directory
        self.vol.chdir(dir_structure)
        # The changed directory should now be CWD
        self.assertEqual(self.vol.getcwd(), dir_structure)
        self.vol.chdir("../..")
        self.assertEqual(self.vol.getcwd(), '/')

    def test_readlink(self):
        file_name = uuid4().hex
        with File(self.vol.open(file_name, os.O_WRONLY | os.O_CREAT)) as f:
            f.write("It's not who I am underneath,"
                    "but what I do that defines me.")
            f.fsync()
        # Create a symlink
        link_name = uuid4().hex
        self.vol.symlink(file_name, link_name)
        self.assertEqual(self.vol.readlink(link_name), file_name)


class DirOpsTest(unittest.TestCase):

    data = None
    dir_path = None
    testfile = None

    @classmethod
    def setUpClass(cls):
        cls.vol = Volume(HOST, VOLNAME)
        ret = cls.vol.mount()
        if ret == 0:
            # Cleanup volume
            cls.vol.rmtree("/", ignore_errors=True)
        cls.testfile = "testfile"

    @classmethod
    def tearDownClass(cls):
        cls.vol.rmtree("/", ignore_errors=True)
        cls.vol = None
        cls.testfile = None

    def setUp(self):
        self.data = "gluster is awesome"
        self.dir_path = self._testMethodName + "_dir"
        self.vol.mkdir(self.dir_path, 0755)
        for x in range(0, 3):
            f = os.path.join(self.dir_path, self.testfile + str(x))
            with File(self.vol.open(f, os.O_CREAT | os.O_WRONLY | os.O_EXCL,
                      0644)) as f:
                rc = f.write(self.data)
                self.assertEqual(rc, len(self.data))
                f.fdatasync()

    def tearDown(self):
        self.dir_path = None
        self.data = None

    def test_isdir(self):
        isdir = self.vol.isdir(self.dir_path)
        self.assertTrue(isdir)

    def test_isfile_false(self):
        isfile = self.vol.isfile(self.dir_path)
        self.assertFalse(isfile)

    def test_listdir(self):
        dir_list = self.vol.listdir(self.dir_path)
        dir_list.sort()
        self.assertEqual(dir_list, ["testfile0", "testfile1", "testfile2"])

    def test_makedirs(self):
        name = self.dir_path + "/subd1/subd2/subd3"
        self.vol.makedirs(name, 0755)
        self.assertTrue(self.vol.isdir(name))

    def test_statvfs(self):
        sb = self.vol.statvfs("/")
        self.assertFalse(isinstance(sb, types.IntType))
        self.assertEqual(sb.f_namemax, 255L)
        # creating a dir, checking Total number of free inodes
        # is reduced
        self.vol.makedirs("statvfs_dir1", 0755)
        sb2 = self.vol.statvfs("/")
        self.assertTrue(sb2.f_ffree < sb.f_ffree)

    def test_rmtree(self):
        """
        by testing rmtree, we are also testing unlink and rmdir
        """
        f = os.path.join(self.dir_path, self.testfile + "1")
        self.vol.rmtree(self.dir_path, True)
        self.assertRaises(OSError, self.vol.lstat, f)
        self.assertRaises(OSError, self.vol.lstat, self.dir_path)


class TestVolumeInit(unittest.TestCase):

    def test_mount_umount_default(self):
        # Create volume object instance
        vol = Volume(HOST, VOLNAME)
        # Check attribute init
        self.assertEqual(vol.log_file, None)
        self.assertEqual(vol.log_level, 7)
        self.assertEqual(vol.host, HOST)
        self.assertEqual(vol.volname, VOLNAME)
        self.assertEqual(vol.port, 24007)
        self.assertFalse(vol.mounted)
        # Mount the volume
        vol.mount()
        # Check mounted property
        self.assertTrue(vol.mounted)
        # Unmount the volume
        vol.umount()
        # Check mounted property again
        self.assertFalse(vol.mounted)
        # Do a double umount - should not crash or raise exception
        vol.umount()
        self.assertFalse(vol.mounted)
        # Do a double mount - should not crash or raise exception
        vol.mount()
        vol.mount()
        self.assertTrue(vol.mounted)
        # Unmount the volume
        vol.umount()
        self.assertFalse(vol.mounted)

    def test_mount_err(self):
        # Volume does not exist
        fake_volname = str(uuid4().hex)[:10]
        vol = Volume(HOST, fake_volname)
        self.assertRaises(LibgfapiException, vol.mount)
        self.assertFalse(vol.mounted)

        # Invalid host - glfs_set_volfile_server will fail
        fake_hostname = str(uuid4().hex)[:10]
        vol = Volume(fake_hostname, VOLNAME)
        self.assertRaises(LibgfapiException, vol.mount)
        self.assertFalse(vol.mounted)

    def test_set_logging(self):
        # Create volume object instance
        vol = Volume(HOST, VOLNAME)
        # Call set_logging before mount()
        log_file = "/tmp/%s" % (uuid4().hex)
        vol.set_logging(log_file, 7)
        # Mount the volume
        vol.mount()
        self.assertTrue(vol.mounted)
        self.assertEqual(vol.log_file, log_file)
        self.assertEqual(vol.log_level, 7)
        # Check that log has been created and exists
        self.assertTrue(os.path.exists(log_file))
        # Change the logging after mounting
        log_file2 = "/tmp/%s" % (uuid4().hex)
        vol.set_logging(log_file2, 7)
        self.assertEqual(vol.log_file, log_file2)
        # Unmount the volume
        vol.umount()
        self.assertFalse(vol.mounted)
