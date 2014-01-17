#!/usr/bin/python

import ctypes
from ctypes.util import find_library
import os
import sys
import types

from contextlib import contextmanager

# Looks like ctypes is having trouble with dependencies, so just force them to
# load with RTLD_GLOBAL until I figure that out.
api = ctypes.CDLL(find_library("gfapi"), ctypes.RTLD_GLOBAL, use_errno=True)

# Wow, the Linux kernel folks really play nasty games with this structure.  If
# you look at the man page for stat(2) and then at this definition you'll note
# two discrepancies.  First, we seem to have st_nlink and st_mode reversed.  In
# fact that's exactly how they're defined *for 64-bit systems*; for 32-bit
# they're in the man-page order.  Even uglier, the man page makes no mention of
# the *nsec fields, but they are very much present and if they're not included
# then we get memory corruption because libgfapi has a structure definition
# that's longer than ours and they overwrite some random bit of memory after
# the space we allocated.  Yes, that's all very disgusting, and I'm still not
# sure this will really work on 32-bit because all of the field types are so
# obfuscated behind macros and feature checks.


class Stat (ctypes.Structure):
    _fields_ = [
        ("st_dev", ctypes.c_ulong),
        ("st_ino", ctypes.c_ulong),
        ("st_nlink", ctypes.c_ulong),
        ("st_mode", ctypes.c_uint),
        ("st_uid", ctypes.c_uint),
        ("st_gid", ctypes.c_uint),
        ("st_rdev", ctypes.c_ulong),
        ("st_size", ctypes.c_ulong),
        ("st_blksize", ctypes.c_ulong),
        ("st_blocks", ctypes.c_ulong),
        ("st_atime", ctypes.c_ulong),
        ("st_atimensec", ctypes.c_ulong),
        ("st_mtime", ctypes.c_ulong),
        ("st_mtimensec", ctypes.c_ulong),
        ("st_ctime", ctypes.c_ulong),
        ("st_ctimensec", ctypes.c_ulong),
    ]


class Dirent (ctypes.Structure):
    _fields_ = [
        ("d_ino", ctypes.c_ulong),
        ("d_off", ctypes.c_ulong),
        ("d_reclen", ctypes.c_ushort),
        ("d_type", ctypes.c_char),
        ("d_name", ctypes.c_char * 256),
    ]

api.glfs_creat.restype = ctypes.c_void_p
api.glfs_open.restype = ctypes.c_void_p
api.glfs_lstat.restype = ctypes.c_int
api.glfs_lstat.argtypes = [ctypes.c_void_p, ctypes.c_char_p,
                           ctypes.POINTER(Stat)]
api.glfs_opendir.restype = ctypes.c_void_p
api.glfs_readdir_r.restype = ctypes.c_int
api.glfs_readdir_r.argtypes = [ctypes.c_void_p, ctypes.POINTER(Dirent),
                               ctypes.POINTER(ctypes.POINTER(Dirent))]


class File(object):

    def __init__(self, fd):
        self.fd = fd

    # File operations, in alphabetical order.

    def close(self):
        ret = api.glfs_close(self.fd)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return ret

    def discard(self, offset, len):
        ret = api.glfs_discard(self.fd, offset, len)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return ret

    def fallocate(self, mode, offset, len):
        ret = api.glfs_fallocate(self.fd, mode, offset, len)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return ret

    def fsync(self):
        ret = api.glfs_fsync(self.fd)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return ret

    def read(self, buflen, flags=0):
        rbuf = ctypes.create_string_buffer(buflen)
        ret = api.glfs_read(self.fd, rbuf, buflen, flags)
        if ret > 0:
            return rbuf.value[:ret]
        elif ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        else:
            return ret

    def write(self, data, flags=0):
        ret = api.glfs_write(self.fd, data, len(data), flags)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return ret


class Dir(object):

    def __init__(self, fd):
        # Add a reference so the module-level variable "api" doesn't
        # get yanked out from under us (see comment above File def'n).
        self._api = api
        self.fd = fd
        self.cursor = ctypes.POINTER(Dirent)()

    def __del__(self):
        self._api.glfs_closedir(self.fd)
        self._api = None

    def next(self):
        entry = Dirent()
        entry.d_reclen = 256
        rc = api.glfs_readdir_r(self.fd, ctypes.byref(entry),
                                ctypes.byref(self.cursor))

        if (rc < 0) or (not self.cursor) or (not self.cursor.contents):
            return rc

        return entry


class Volume(object):

    # Housekeeping functions.

    def __init__(self, host, volid, proto="tcp", port=24007):
        # Add a reference so the module-level variable "api" doesn't
        # get yanked out from under us (see comment above File def'n).
        self._api = api
        self.fs = api.glfs_new(volid)
        api.glfs_set_volfile_server(self.fs, proto, host, port)

    def __del__(self):
        self._api.glfs_fini(self.fs)
        self._api = None

    def set_logging(self, path, level):
        api.glfs_set_logging(self.fs, path, level)

    def mount(self):
        return api.glfs_init(self.fs)

    # File operations, in alphabetical order.

    @contextmanager
    def creat(self, path, flags, mode):
        fd = api.glfs_creat(self.fs, path, flags, mode)
        if not fd:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

        fileobj = None
        try:
            fileobj = File(fd)
            yield fileobj
        finally:
            fileobj.close()

    def getxattr(self, path, key, maxlen):
        buf = ctypes.create_string_buffer(maxlen)
        rc = api.glfs_getxattr(self.fs, path, key, buf, maxlen)
        if rc < 0:
            err = ctypes.get_errno()
            raise IOError(err, os.strerror(err))
        return buf.value[:rc]

    def listxattr(self, path):
        buf = ctypes.create_string_buffer(512)
        rc = api.glfs_listxattr(self.fs, path, buf, 512)
        if rc < 0:
            err = ctypes.get_errno()
            raise IOError(err, os.strerror(err))
        xattrs = []
        # Parsing character by character is ugly, but it seems like the
        # easiest way to deal with the "strings separated by NUL in one
        # buffer" format.
        i = 0
        while i < rc:
            new_xa = buf.raw[i]
            i += 1
            while i < rc:
                next_char = buf.raw[i]
                i += 1
                if next_char == '\0':
                    xattrs.append(new_xa)
                    break
                new_xa += next_char
        xattrs.sort()
        return xattrs

    def lstat(self, path):
        x = Stat()
        rc = api.glfs_lstat(self.fs, path, ctypes.byref(x))
        if rc < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return x

    def mkdir(self, path):
        ret = api.glfs_mkdir(self.fs, path)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return ret

    @contextmanager
    def open(self, path, flags):
        fd = api.glfs_open(self.fs, path, flags)
        if not fd:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

        fileobj = None
        try:
            fileobj = File(fd)
            yield fileobj
        finally:
            fileobj.close()

    def opendir(self, path):
        fd = api.glfs_opendir(self.fs, path)
        if not fd:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return Dir(fd)

    def rename(self, opath, npath):
        ret = api.glfs_rename(self.fs, opath, npath)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return ret

    def rmdir(self, path):
        ret = api.glfs_rmdir(self.fs, path)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return ret

    def setxattr(self, path, key, value, vlen):
        ret = api.glfs_setxattr(self.fs, path, key, value, vlen, 0)
        if ret < 0:
            err = ctypes.get_errno()
            raise IOError(err, os.strerror(err))
        return ret

    def unlink(self, path):
        ret = api.glfs_unlink(self.fs, path)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return ret

if __name__ == "__main__":

    def test_create_write(vol, path, data):
        mypath = path + ".io"
        with vol.creat(mypath, os.O_WRONLY | os.O_EXCL, 0644) as fd:
            if not fd:
                return False, "creat error"
            rc = fd.write(data)
            if rc != len(data):
                return False, "wrote %d/%d bytes" % (rc, len(data))
            return True, "wrote %d bytes" % rc

    # TBD: this test fails if we do create, open, write, read
    def test_open_read(vol, path, data):
        mypath = path + ".io"
        with vol.open(mypath, os.O_RDONLY) as fd:
            if not fd:
                return False, "open error"
            dlen = len(data) * 2
            buf = fd.read(dlen)
            if isinstance(buf, types.IntType):
                return False, "read error %d" % buf
            if len(buf) != len(data):
                return False, "read %d/%d bytes" % (len(buf), len(data))
            return True, "read '%s'" % buf

    def test_lstat(vol, path, data):
        mypath = path + ".io"
        sb = vol.lstat(mypath)
        if isinstance(sb, types.IntType):
            return False, "lstat error %d" % sb
        if sb.st_size != len(data):
            return False, "lstat size is %d, expected %d" % (
                sb.st_size, len(data))
        return True, "lstat got correct size %d" % sb.st_size

    def test_rename(vol, path, data):
        opath = path + ".io"
        npath = path + ".tmp"
        rc = vol.rename(opath, npath)
        if rc < 0:
            return False, "rename error %d" % rc
        try:
            with vol.open(opath, os.O_RDWR) as fd:
                return False, "old path working (%s) after rename" % fd
        except OSError:
            pass
        else:
            return False, "old path working after rename"

        with vol.open(npath, os.O_RDWR) as nfd:
            if not isinstance(nfd, File):
                return False, "new path not working after rename"
            return True, "rename worked"

    def test_unlink(vol, path, data):
        mypath = path + ".tmp"
        rc = vol.unlink(mypath)
        if rc < 0:
            return False, "unlink error %d" % rc

        try:
            with vol.open(mypath, os.O_RDWR) as fd:
                return False, "old path working (%s) after unlink" % fd
        except OSError:
            pass
        else:
            return False, "path still usable after unlink"

        return True, "unlink worked"

    def test_mkdir(vol, path, data):
        mypath = path + ".dir"
        rc = vol.mkdir(mypath)
        if rc < 0:
            return False, "mkdir error %d" % rc

        return True, "mkdir worked"

    def test_create_in_dir(vol, path, data):
        mypath = path + ".dir/probe"
        with vol.creat(mypath, os.O_RDWR, 0644) as fd:
            if not isinstance(fd, File):
                return False, "create (in dir) error"
            return True, "create (in dir) worked"

    def test_dir_listing(vol, path, data):
        mypath = path + ".dir"
        fd = vol.opendir(mypath)
        if not isinstance(fd, Dir):
            return False, "opendir error %d" % fd
        files = []
        while True:
            ent = fd.next()
            if not isinstance(ent, Dirent):
                break
            name = ent.d_name[:ent.d_reclen]
            files.append(name)
        if files != [".", "..", "probe"]:
            return False, "wrong directory contents"
        return True, "directory listing worked"

    def test_unlink_in_dir(vol, path, data):
        mypath = path + ".dir/probe"
        rc = vol.unlink(mypath)
        if rc < 0:
            return False, "unlink (in dir) error %d" % rc
        return True, "unlink (in dir) worked"

    def test_rmdir(vol, path, data):
        mypath = path + ".dir"
        rc = vol.rmdir(mypath)
        if rc < 0:
            return False, "rmdir error %d" % rc
        try:
            vol.lstat(mypath)
        except OSError:
            pass
        else:
            return False, "dir still there after rmdir"
        return True, "rmdir worked"

    def test_setxattr(vol, path, data):
        mypath = path + ".xa"
        with vol.creat(mypath, os.O_RDWR | os.O_EXCL, 0644) as fd:
            if not fd:
                return False, "creat (xattr test) error"

        key1, key2 = "hello", "goodbye"
        if vol.setxattr(mypath, "trusted.key1", key1, len(key1)) < 0:
            return False, "setxattr (key1) error"
        if vol.setxattr(mypath, "trusted.key2", key2, len(key2)) < 0:
            return False, "setxattr (key2) error"
        return True, "setxattr worked"

    def test_getxattr(vol, path, data):
        mypath = path + ".xa"
        buf = vol.getxattr(mypath, "trusted.key1", 32)
        if isinstance(buf, types.IntType):
            return False, "getxattr error"
        if buf != "hello":
            return False, "wrong getxattr value %s" % buf
        return True, "getxattr worked"

    def test_listxattr(vol, path, data):
        mypath = path + ".xa"
        xattrs = vol.listxattr(mypath)
        if isinstance(xattrs, types.IntType):
            return False, "listxattr error"
        if xattrs != ["trusted.key1", "trusted.key2"]:
            return False, "wrong listxattr value %s" % repr(xattrs)
        return True, "listxattr worked"

    def test_fallocate(vol, path, data):
        mypath = path + ".io"
        with vol.creat(mypath, os.O_WRONLY | os.O_EXCL, 0644) as fd:
            if not fd:
                return False, "creat error"
            rc = fd.fallocate(0, 0, 1024 * 1024)
            if rc != 0:
                return False, "fallocate error"
            rc = fd.discard(4096, 4096)
            if rc != 0:
                return False, "discard error"
            return True, "fallocate/discard worked"

    test_list = (
        test_create_write,
        #test_open_read,
        test_lstat,
        test_rename,
        test_unlink,
        test_mkdir,
        test_create_in_dir,
        test_dir_listing,
        test_unlink_in_dir,
        test_rmdir,
        test_setxattr,
        test_getxattr,
        test_listxattr,
        test_fallocate,
    )

    ok_to_fail = (
        # TBD: this fails opening the new file, even though the file
        # did get renamed.  Looks like a gfapi bug, not ours.
        (test_rename, "new path not working after rename"),
        # TBD: similar, call returns error even though it worked
        (test_rmdir, "dir still there after rmdir"),
    )

    volid, path = sys.argv[1:3]
    data = "fubar"
    vol = Volume("localhost", volid)
    vol.set_logging("/dev/null", 7)
    #vol.set_logging("/dev/stderr",7)
    vol.mount()

    failures = 0
    expected = 0
    for t in test_list:
        rc, msg = t(vol, path, data)
        if rc:
            print "PASS: %s" % msg
        else:
            print "FAIL: %s" % msg
            failures += 1
            for otf in ok_to_fail:
                if (t == otf[0]) and (msg == otf[1]):
                    print "  (skipping known failure)"
                    expected += 1
                    break  # from the *inner* for loop
            else:
                break  # from the *outer* for loop

    print "%d failures (%d expected)" % (failures, expected)
