# Copyright (c) 2012-2014 Red Hat, Inc.
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

import ctypes
from ctypes.util import find_library
import os
import stat
import errno

# Disclaimer: many of the helper functions (e.g., exists, isdir) where copied
# from the python source code

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
api.glfs_stat.restype = ctypes.c_int
api.glfs_stat.argtypes = [ctypes.c_void_p, ctypes.c_char_p,
                          ctypes.POINTER(Stat)]
api.glfs_fstat.restype = ctypes.c_int
api.glfs_fstat.argtypes = [ctypes.c_void_p, ctypes.POINTER(Stat)]


class File(object):

    def __init__(self, fd):
        self.fd = fd

    def __enter__(self):
        if self.fd is None:
            # __enter__ should only be called within the context
            # of a 'with' statement when opening a file through
            # Volume.open()
            raise ValueError("I/O operation on closed file")
        return self

    def __exit__(self, type, value, tb):
        self.close()

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

    def fchown(self, uid, gid):
        """
        Change this file's owner and group id

        :param uid: new user id for file
        :param gid: new group id for file
        :returns: 0 if success, raises OSError if it fails
        """
        ret = api.glfs_fchown(self.fd, uid, gid)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return ret

    def fdatasync(self):
        """
        Force write of file

        :returns: 0 if success, raises OSError if it fails
        """
        ret = api.glfs_fdatasync(self.fd)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return ret

    def fstat(self):
        """
        Returns Stat object for this file.
        """
        s = Stat()
        rc = api.glfs_fstat(self.fd, ctypes.byref(s))
        if rc < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return s

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
            return rbuf
        elif ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        else:
            return ret

    def write(self, data):
        # creating a ctypes.c_ubyte buffer to handle converting bytearray
        # to the required C data type
        if type(data) is bytearray:
            buf = (ctypes.c_ubyte * len(data)).from_buffer(data)
        else:
            buf = data
        ret = api.glfs_write(self.fd, buf, len(buf))
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

    def chown(self, path, uid, gid):
        """
        Change owner and group id of path

        :param path: the item to be modified
        :param uid: new user id for item
        :param gid: new group id for item
        :returns: 0 if success, raises OSError if it fails
        """
        ret = api.glfs_chown(self.fs, path, uid, gid)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return ret

    def exists(self, path):
        """
        Test whether a path exists.
        Returns False for broken symbolic links.
        """
        try:
            self.stat(path)
        except OSError:
            return False
        return True

    def getsize(self, filename):
        """
        Return the size of a file, reported by stat()
        """
        return self.stat(filename).st_size

    def getxattr(self, path, key, maxlen):
        buf = ctypes.create_string_buffer(maxlen)
        rc = api.glfs_getxattr(self.fs, path, key, buf, maxlen)
        if rc < 0:
            err = ctypes.get_errno()
            raise IOError(err, os.strerror(err))
        return buf.value[:rc]

    def isdir(self, path):
        """
        Test whether a path is an existing directory
        """
        try:
            s = self.stat(path)
        except OSError:
            return False
        return stat.S_ISDIR(s.st_mode)

    def isfile(self, path):
        """
        Test whether a path is a regular file
        """
        try:
            s = self.stat(path)
        except OSError:
            return False
        return stat.S_ISREG(s.st_mode)

    def islink(self, path):
        """
        Test whether a path is a symbolic link
        """
        try:
            s = self.lstat(path)
        except OSError:
            return False
        return stat.S_ISLNK(s.st_mode)

    def listdir(self, path):
        """
        Return list of entries in a given directory 'path'.
        "." and ".." are not included, and the list is not sorted.
        """
        d = self.opendir(path)
        dir_list = []
        while True:
            ent = d.next()
            if not isinstance(ent, Dirent):
                break
            name = ent.d_name[:ent.d_reclen]
            if not name in [".", ".."]:
                dir_list.append(name)
        return dir_list

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
        s = Stat()
        rc = api.glfs_lstat(self.fs, path, ctypes.byref(s))
        if rc < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return s

    def makedirs(self, name, mode):
        """
        Create directories defined in 'name' recursively.
        """
        head, tail = os.path.split(name)
        if not tail:
            head, tail = os.path.split(head)
        if head and tail and not self.exists(head):
            try:
                self.makedirs(head, mode)
            except OSError as err:
                if err.errno != errno.EEXIST:
                    raise
            if tail == os.curdir:
                return
        self.mkdir(name, mode)

    def mkdir(self, path, mode):
        ret = api.glfs_mkdir(self.fs, path, mode)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return ret

    def open(self, path, flags, mode=0777):
        if (os.O_CREAT & flags) == os.O_CREAT:
            fd = api.glfs_creat(self.fs, path, flags, mode)
        else:
            fd = api.glfs_open(self.fs, path, flags)
        if not fd:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

        return File(fd)

    def opendir(self, path):
        fd = api.glfs_opendir(self.fs, path)
        if not fd:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return Dir(fd)

    def removexattr(self, path, key):
        ret = api.glfs_removexattr(self.fs, path, key)
        if ret < 0:
            err = ctypes.get_errno()
            raise IOError(err, os.strerror(err))
        return ret

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

    def rmtree(self, path, ignore_errors=False, onerror=None):
        """
        Delete a whole directory tree structure. Raises OSError
        if path is a symbolic link.

        :param path: Directory tree to remove
        :param ignore_errors: If True, errors are ignored
        :param onerror: If set, it is called to handle the error with arguments
                        (func, path, exc) where func is the function that
                        raised the error, path is the argument that caused it
                        to fail; and exc is the exception that was raised.
                        If ignore_errors is False and onerror is None, an
                        exception is raised
        """
        if ignore_errors:
            def onerror(*args):
                pass
        elif onerror is None:
            def onerror(*args):
                raise
        if self.islink(path):
            raise OSError("Cannot call rmtree on a symbolic link")
        names = []
        try:
            names = self.listdir(path)
        except OSError as e:
            onerror(self.listdir, path, e)
        for name in names:
            fullname = os.path.join(path, name)
            if self.isdir(fullname):
                self.rmtree(fullname, ignore_errors, onerror)
            else:
                try:
                    self.unlink(fullname)
                except OSError as e:
                    onerror(self.unlink, fullname, e)
        try:
            self.rmdir(path)
        except OSError as e:
            onerror(self.rmdir, path, e)

    def setxattr(self, path, key, value, vlen):
        ret = api.glfs_setxattr(self.fs, path, key, value, vlen, 0)
        if ret < 0:
            err = ctypes.get_errno()
            raise IOError(err, os.strerror(err))
        return ret

    def stat(self, path):
        s = Stat()
        rc = api.glfs_stat(self.fs, path, ctypes.byref(s))
        if rc < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return s

    def symlink(self, source, link_name):
        """
        Create a symbolic link 'link_name' which points to 'source'
        """
        ret = api.glfs_symlink(self.fs, source, link_name)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return ret

    def unlink(self, path):
        """
        Delete the file 'path'

        :param path: file to be deleted
        :returns: 0 if success, raises OSError if it fails
        """
        ret = api.glfs_unlink(self.fs, path)
        if ret < 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        return ret

    def walk(self, top, topdown=True, onerror=None, followlinks=False):
        """
        Directory tree generator. Yields a 3-tuple dirpath, dirnames, filenames

        dirpath is the path to the directory, dirnames is a list of the names
        of the subdirectories in dirpath. filenames is a list of the names of
        the non-directiry files in dirpath
        """
        try:
            names = self.listdir(top)
        except OSError as err:
            if onerror is not None:
                onerror(err)
            return

        dirs, nondirs = [], []
        for name in names:
            if self.isdir(os.path.join(top, name)):
                dirs.append(name)
            else:
                nondirs.append(name)

        if topdown:
            yield top, dirs, nondirs
        for name in dirs:
            new_path = os.path.join(top, name)
            if followlinks or not self.islink(new_path):
                for x in self.walk(new_path, topdown, onerror, followlinks):
                    yield x
        if not topdown:
            yield top, dirs, nondirs
