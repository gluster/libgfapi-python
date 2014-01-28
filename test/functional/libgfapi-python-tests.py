import unittest
import os
import types
import loremipsum

from nose import SkipTest
from gluster import gfapi


class FileOpsTest(unittest.TestCase):

    vol = None
    path = None
    data = None

    @classmethod
    def setUpClass(cls):
        cls.vol = gfapi.Volume("gfshost", "test")
        cls.vol.set_logging("/dev/null", 7)
        cls.vol.mount()

    @classmethod
    def tearDownClass(cls):
        cls.vol = None

    def setUp(self):
        self.data = loremipsum.get_sentence()
        self.path = self._testMethodName + ".io"
        with self.vol.creat(self.path, os.O_WRONLY | os.O_EXCL, 0644) as fd:
            rc = fd.write(self.data)

    def tearDown(self):
        self.path = None
        self.data = None

    def test_open_and_read(self):
        with self.vol.open(self.path, os.O_RDONLY) as fd:
            self.assertTrue(isinstance(fd, gfapi.File))
            buf = fd.read(len(self.data))
            self.assertFalse(isinstance(buf, types.IntType))
            self.assertEqual(buf, self.data)

    def test_lstat(self):
        sb = self.vol.lstat(self.path)
        self.assertFalse(isinstance(sb, types.IntType))
        self.assertEqual(sb.st_size, len(self.data))

    def test_rename(self):
        newpath = self.path + ".rename"
        ret = self.vol.rename(self.path, newpath)
        self.assertEqual(ret, 0)
        self.assertRaises(OSError, self.vol.lstat, self.path)

    def test_unlink(self):
        ret = self.vol.unlink(self.path)
        self.assertEqual(ret, 0)
        self.assertRaises(OSError, self.vol.lstat, self.path)

    def test_xattr(self):
        key1, key2 = "hello", "world"
        ret1 = self.vol.setxattr(self.path, "trusted.key1", key1, len(key1))
        self.assertEqual(0, ret1)
        ret2 = self.vol.setxattr(self.path, "trusted.key2", key2, len(key2))
        self.assertEqual(0, ret2)

        xattrs = self.vol.listxattr(self.path)
        self.assertFalse(isinstance(xattrs, types.IntType))
        self.assertEqual(xattrs, ["trusted.key1", "trusted.key2"])

        buf = self.vol.getxattr(self.path, "trusted.key1", 32)
        self.assertFalse(isinstance(buf, types.IntType))
        self.assertEqual(buf, "hello")


class DirOpsTest(unittest.TestCase):

    data = None
    dir_path = None
    file_path = None
    testfile = None

    @classmethod
    def setUpClass(cls):
        cls.vol = gfapi.Volume("gfshost", "test")
        cls.vol.set_logging("/dev/null", 7)
        cls.vol.mount()
        cls.testfile = "testfile.io"

    @classmethod
    def tearDownClass(cls):
        cls.vol = None
        cls.testfile = None

    def setUp(self):
        self.data = loremipsum.get_sentence()
        self.dir_path = self._testMethodName + "_dir"
        self.vol.mkdir(self.dir_path, 0755)
        self.file_path = self.dir_path + "/" + self.testfile
        with self.vol.creat(
                self.file_path, os.O_WRONLY | os.O_EXCL, 0644) as fd:
            rc = fd.write(self.data)

    def tearDown(self):
        self.dir_path = None
        self.file_path = None
        self.data = None

    def test_dir_listing(self):
        fd = self.vol.opendir(self.dir_path)
        self.assertTrue(isinstance(fd, gfapi.Dir))
        files = []
        while True:
            ent = fd.next()
            if not isinstance(ent, gfapi.Dirent):
                break
            name = ent.d_name[:ent.d_reclen]
            files.append(name)
        self.assertEqual(files, [".", "..", self.testfile])

    def test_delete_file_and_dir(self):
        ret = self.vol.unlink(self.file_path)
        self.assertEqual(ret, 0)
        self.assertRaises(OSError, self.vol.lstat, self.file_path)

        ret = self.vol.rmdir(self.dir_path)
        self.assertEqual(ret, 0)
        self.assertRaises(OSError, self.vol.lstat, self.dir_path)
